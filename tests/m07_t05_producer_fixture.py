"""Actual producers; only external process/Docker/registry effects are fake.

No daemon, provider, auth store, real Docker executable or remote Git transport.
The archive's local ID is the genuine hash of synthetic configuration bytes.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _synthetic_config():
    if str(ROOT / 'scripts') not in sys.path:
        sys.path.insert(0, str(ROOT / 'scripts'))
    resolver = load('synthetic_config_resolver', 'scripts/resolve-paseo-candidate.py')
    current = json.loads((ROOT / 'config/paseo-candidate.json').read_bytes())
    candidate = resolver.facts_to_candidate({'components': current['components']},
        json.loads((ROOT / 'config/environment-capabilities.json').read_bytes()))
    return {'Env': ['PATH=/usr/local/bin:/usr/bin:/bin',
                    'PI_UNRAID_PI_VERSION=' + candidate['components']['pi']['version'],
                    'PI_UNRAID_CANDIDATE_ID=' + candidate['candidate_id']],
            'Labels': {'io.pi-unraid.pi-version': candidate['components']['pi']['version'],
                       'io.pi-unraid.candidate-id': candidate['candidate_id']}}


IMAGE_CONFIG = _synthetic_config()
CONFIG_BYTES = (json.dumps({'architecture':'amd64','os':'linux','config':IMAGE_CONFIG},
                          sort_keys=True) + '\n').encode()
IMAGE_ID = 'sha256:' + hashlib.sha256(CONFIG_BYTES).hexdigest()


def source_root(td):
    return Path(td) / 'producer-source'


def docker_save(path, tag):
    config_name = IMAGE_ID[7:] + '.json'
    manifest = json.dumps([{'Config': config_name, 'RepoTags': [tag], 'Layers': ['layer/layer.tar']}]).encode()
    with tarfile.open(path, 'w') as archive:
        for name, raw in [('manifest.json', manifest), (config_name, CONFIG_BYTES), ('layer/layer.tar', b'synthetic-layer')]:
            info = tarfile.TarInfo(name); info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))


def produce(td, *, repository, digest, image_id=IMAGE_ID):
    if image_id != IMAGE_ID:
        raise AssertionError('synthetic image ID must hash the actual synthetic configuration')
    td = Path(td)
    source = source_root(td)
    source.mkdir()
    # The used source contains all actual build/validation/delivery configuration.
    for rel in ('scripts', 'config', '.github'):
        shutil.copytree(ROOT / rel, source / rel,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for rel in ('Dockerfile', '.dockerignore', 'compose.yaml'):
        if (ROOT / rel).exists():
            shutil.copy2(ROOT / rel, source / rel)
    if str(ROOT / 'scripts') not in sys.path:
        sys.path.insert(0, str(ROOT / 'scripts'))
    resolver = load('m07_actual_resolver', 'scripts/resolve-paseo-candidate.py')
    build = load('m07_actual_prepare', 'scripts/paseo_candidate_build.py')
    handoff = load('m07_actual_handoff', 'scripts/paseo_candidate_handoff.py')
    buildx = load('m07_actual_buildx', 'scripts/paseo_buildx.py')
    publisher = load('m07_actual_publisher', 'scripts/paseo_candidate_publish.py')
    current = json.loads((ROOT / 'config/paseo-candidate.json').read_bytes())
    definition = json.loads((source / 'config/environment-capabilities.json').read_bytes())
    candidate = resolver.facts_to_candidate({'components': current['components']}, definition)
    # Material update into current candidate from an independently valid predecessor.
    prior_components = json.loads(json.dumps(current['components']))
    prior_components['playwright']['version'] = '1.62.0'
    prior_components['playwright']['source']['tag'] = 'v1.62.0'
    prior = resolver.facts_to_candidate({'components': prior_components}, definition)
    accepted = source / 'config/paseo-candidate.json'
    accepted.write_text(json.dumps(prior, sort_keys=True, indent=2) + '\n')
    (source / 'Dockerfile').write_text(build.render_dockerfile((ROOT / 'Dockerfile').read_text(), current, prior))
    def git(*args):
        command = ['git', '-c', 'core.hooksPath=/dev/null', '-C', str(source), *args]
        proc = subprocess.run(command, text=True, capture_output=True, timeout=30)
        if proc.returncode:
            raise AssertionError('disposable synthetic Git operation failed')
        return proc.stdout.strip()
    git('init', '-b', 'main')
    git('add', '.')
    git('-c', 'user.name=Synthetic Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Synthetic source')
    parent = git('rev-parse', 'HEAD')
    candidate_input = td / 'resolver-output.json'
    candidate_input.write_text(json.dumps(candidate, sort_keys=True, indent=2) + '\n')
    handoff_stage = td / 'handoff-stage'
    handoff.prepare(candidate_input, accepted, handoff_stage, parent, 'refs/heads/main')
    target_dir = source / 'candidates/paseo-update'
    target_dir.mkdir(parents=True)
    shutil.copy2(handoff_stage / 'candidate.json', target_dir / 'candidate.json')
    shutil.copy2(handoff_stage / 'evidence.json', target_dir / 'evidence.json')
    git('checkout', '-b', 'automation/paseo-update-candidate')
    git('add', 'candidates')
    git('-c', 'user.name=Synthetic Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Synthetic handoff only')
    head = git('rev-parse', 'HEAD')
    stage = td / 'prepared-context'
    candidate_path, handoff_path = target_dir / 'candidate.json', target_dir / 'evidence.json'
    build.prepare_context(candidate_path=candidate_path, evidence_path=handoff_path,
        accepted_path=accepted, source_root=source, stage_dir=stage,
        source_head=head, source_parent=parent, expected_source_ref='refs/heads/main')
    build_input = stage / '.pi-unraid-candidate-build-input.json'
    artifact = td / 'producer-artifact'; artifact.mkdir()
    record = artifact / 'build-record.json'
    calls = []
    def external(argv, env, timeout):
        calls.append(list(argv))
        if argv[:3] == ['docker', 'buildx', 'inspect']:
            return subprocess.CompletedProcess(argv, 0, 'Name: pi-unraid-paseo-ci\nDriver: docker-container\n', '')
        if argv[:3] == ['docker', 'buildx', 'build']:
            return subprocess.CompletedProcess(argv, 0, 'synthetic build effect', '')
        if argv[:3] == ['docker', 'image', 'inspect']:
            return subprocess.CompletedProcess(argv, 0, json.dumps([{'Id':IMAGE_ID, 'RepoDigests':[],
                'Config':{'Labels':{'io.pi-unraid.candidate-id':candidate['candidate_id']}}}]), '')
        if Path(argv[0]).name in ('python3', 'bash') and str(stage / 'scripts') in argv[1]:
            # Process effect only. Real smoke_suite + fail-fast aggregation run.
            return subprocess.CompletedProcess(argv, 0, 'synthetic mechanical smoke process', '')
        raise AssertionError(argv)
    args = buildx.build_parser().parse_args(['build', '--candidate', str(stage / 'config/paseo-candidate.json'),
        '--context', str(stage), '--build-input', str(build_input), '--record', str(record),
        '--state-dir', str(td / 'build-state'), '--builder', 'pi-unraid-paseo-ci',
        '--with-smoke', '--smoke-profile', 'core'])
    with mock.patch.object(buildx, '_run', side_effect=external), contextlib.redirect_stdout(io.StringIO()):
        if buildx.cmd_build(args) != 0:
            raise AssertionError(record.read_text())
    actual_record = json.loads(record.read_bytes())
    smokes = actual_record['phases']['test']['detail']['smokes']
    if [row['name'] for row in smokes] != ['image_provenance', 'persistence_ownership', 'instruction_plane']:
        raise AssertionError('actual smoke dispatch/aggregation was not reached')
    tested = artifact / 'tested-image-evidence.json'
    def packaging(argv):
        if argv[:3] == ['docker', 'image', 'inspect']:
            return subprocess.CompletedProcess(argv, 0, IMAGE_ID + '\n', '')
        if argv[:3] == ['docker', 'image', 'save']:
            docker_save(Path(argv[4]), actual_record['tag'])
            return subprocess.CompletedProcess(argv, 0, '', '')
        raise AssertionError(argv)
    with mock.patch.object(build, 'run_checked', side_effect=packaging):
        build.package_tested_image(candidate_path=candidate_path, handoff_evidence_path=handoff_path,
            build_record_path=record, archive_path=artifact / 'image.tar', evidence_path=tested,
            source_head=head, build_input_path=build_input)
    publication = td / 'publication.json'
    def publishing(argv):
        if argv[:3] == ['docker', 'image', 'inspect']:
            return subprocess.CompletedProcess(argv, 0, IMAGE_ID + '\n', '')
        if argv[:4] == ['docker', 'buildx', 'imagetools', 'inspect']:
            return subprocess.CompletedProcess(argv, 0, 'Digest: ' + digest + '\n', '')
        if argv[:3] in (['docker', 'image', 'load'], ['docker', 'image', 'tag'], ['docker', 'image', 'push']):
            return subprocess.CompletedProcess(argv, 0, '', '')
        raise AssertionError(argv)
    with mock.patch.object(publisher, 'run_checked', side_effect=publishing):
        publisher.publish(artifact_dir=artifact, candidate_path=candidate_path, handoff_path=handoff_path,
            source_head=head, repository=repository, output_path=publication)
    return candidate_path, handoff_path, build_input, tested, record, publication
