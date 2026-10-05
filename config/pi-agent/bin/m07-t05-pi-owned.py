#!/usr/bin/env python3
"""Candidate-only supported command replacement. Never reads ordinary auth.

Paseo supplies PASEO_AGENT_ID after launch overlays. Catalog processes have no
agent ID. Auth comparison is in-memory against the dedicated pointer only;
no value or fingerprint of a credential is persisted.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys


def private_read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ValueError('private input unavailable')
        with os.fdopen(fd, 'r', closefd=False) as stream:
            return stream.read(65537)
    finally:
        os.close(fd)


def main():
    module = importlib.util.spec_from_file_location('applied_interval', '/home/paseo/.pi/agent/bin/m07-t05-applied.py')
    observer = importlib.util.module_from_spec(module)
    module.loader.exec_module(observer)
    observer.observe('/home/paseo/.m07-t05/applied.json')
    # Frozen executable selection, no runtime override/PATH selection.
    executable = '/usr/local/bin/pi'
    pointer = os.environ.get('META_API_KEY_FILE', '/run/secrets/pi-unraid-meta')
    lines = [line.strip() for line in private_read(pointer).splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if len(lines) != 1:
        raise ValueError('dedicated input shape unavailable')
    value = lines[0]
    if '=' in value:
        name, value = value.split('=', 1)
        if name != 'META_API_KEY':
            raise ValueError('dedicated input name unavailable')
    if not value or any(c.isspace() for c in value) or value != os.environ.get('META_API_KEY'):
        raise ValueError('dedicated auth inheritance unavailable')
    for key in ('PASEO_WORKSPACE_ID', 'PASEO_HOST', 'PASEO_SERVER', 'PASEO_PASSWORD',
                'NODE_OPTIONS', 'PI_CODING_AGENT_DIR', 'PI_AGENT_DIR'):
        if os.environ.get(key):
            raise ValueError('ambient selector at Pi boundary')
    agent = os.environ.get('PASEO_AGENT_ID')
    if agent:
        if not all(c.isalnum() or c in '._-' for c in agent) or len(agent) > 128:
            raise ValueError('unusable actual agent identity')
        directory = Path(os.environ['M07_T05_PROCESS_DIR'])
        st = directory.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ValueError('process directory unavailable')
        proof = {'agent_id': agent, 'test_id': os.environ['M07_T05_TEST_ID'],
                 'pid': os.getpid(), 'ppid': os.getppid(),
                 'start_time': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
                 'parent_start_time': Path(f'/proc/{os.getppid()}/stat').read_text().rsplit(')', 1)[1].split()[19],
                 'executable': executable,
                 'sha256': 'sha256:' + hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                 'auth_inherited': True}
        # Exclusive acquisition: never overwrite another launch/agent proof.
        fd = os.open(directory / (agent + '.json'), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(proof, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
    os.execv(executable, [executable, *sys.argv[1:]])


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('candidate Pi process boundary unavailable', file=sys.stderr)
        sys.exit(42)
