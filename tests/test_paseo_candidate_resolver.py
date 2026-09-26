#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:
    sys.path.insert(0,str(ROOT/"scripts"))
SCRIPT=ROOT/"scripts"/"resolve-paseo-candidate.py"
FIXTURE=ROOT/"tests"/"fixtures"/"paseo-candidate"/"facts.json"
REQUIRED={"paseo","node","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"}

spec=importlib.util.spec_from_file_location("m05_inventory",ROOT/"scripts"/"environment_capability_inventory.py")
inventory=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(inventory)

rspec=importlib.util.spec_from_file_location("m05_resolver",SCRIPT)
resolver=importlib.util.module_from_spec(rspec)
assert rspec.loader is not None
rspec.loader.exec_module(resolver)

class ResolverTests(unittest.TestCase):
    def invoke(self,*args):
        return subprocess.run(["python3",str(SCRIPT),*args],cwd=ROOT,text=True,capture_output=True)

    def test_fixture_is_deterministic_complete_and_secret_free(self):
        a=self.invoke("--fixture",str(FIXTURE),"--check")
        b=self.invoke("--fixture",str(FIXTURE),"--check")
        self.assertEqual(a.returncode,0,a.stderr); self.assertEqual(a.stdout,b.stdout)
        c=json.loads(a.stdout)
        self.assertEqual(set(c["components"]),{"paseo","node","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"})
        self.assertEqual(c["components"]["paseo"]["artifact"]["digest"],"sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136")
        self.assertEqual(c["components"]["playwright"]["chromium"]["revision"],"1243")
        self.assertNotIn("password",a.stdout.lower()); self.assertNotIn("access_token",a.stdout.lower())

    def test_validate_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"candidate.json"
            r=self.invoke("--fixture",str(FIXTURE),"--check"); self.assertEqual(r.returncode,0,r.stderr)
            p.write_text(r.stdout)
            v=self.invoke("--validate",str(p)); self.assertEqual(v.returncode,0,v.stderr)
            self.assertTrue(v.stdout.strip().startswith("sha256:"))

    def test_failure_does_not_replace_existing_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); facts=json.loads(FIXTURE.read_text())
            del facts["components"]["specpi"]
            broken=td/"broken.json"; broken.write_text(json.dumps(facts))
            out=td/"candidate.json"; out.write_text("sentinel\n")
            r=self.invoke("--fixture",str(broken),"--output",str(out))
            self.assertNotEqual(r.returncode,0); self.assertEqual(out.read_text(),"sentinel\n")

    def test_bad_npm_integrity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); facts=json.loads(FIXTURE.read_text())
            facts["components"]["pi"]["npm"]["integrity"]="missing"
            broken=td/"broken.json"; broken.write_text(json.dumps(facts))
            r=self.invoke("--fixture",str(broken),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("integrity",r.stderr)

class CoordinatedResolverTests(unittest.TestCase):
    def invoke(self,*args):
        return subprocess.run(["python3",str(SCRIPT),*args],cwd=ROOT,text=True,capture_output=True)

    def base_facts(self):
        return json.loads(FIXTURE.read_text())

    def write(self,td,data,name="facts.json"):
        p=Path(td)/name; p.write_text(json.dumps(data)); return p

    def test_stable_line_selection_and_derived_provenance(self):
        r=self.invoke("--fixture",str(FIXTURE),"--check"); self.assertEqual(r.returncode,0,r.stderr)
        c=json.loads(r.stdout)
        self.assertEqual(set(c["components"]),REQUIRED)
        for name, comp in c["components"].items():
            line=comp.get("stable_line")
            self.assertIsInstance(line,dict,name)
            self.assertTrue(line.get("channel"),name); self.assertTrue(line.get("source"),name)
            self.assertTrue(line.get("rationale"),name)
        self.assertEqual(c["components"]["node"]["stable_line"]["channel"],"derived")
        for name in ("paseo","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"):
            self.assertEqual(c["components"][name]["stable_line"]["channel"],"latest-stable",name)
        node=c["components"]["node"]; paseo=c["components"]["paseo"]
        self.assertEqual(node["version"],paseo["artifact"]["node_version"])
        self.assertEqual(node["immutable_parent"],paseo["artifact"]["reference"])
        self.assertEqual(c["components"]["playwright"]["chromium"]["revision"],"1243")
        self.assertEqual(c["components"]["playwright"]["chromium"]["browser_version"],"153.0.8010.12")
        self.assertEqual(c["components"]["docker_cli"]["stable_line_source"]["repository"],"moby/moby")
        tmp=json.loads(r.stdout); claimed=tmp.pop("candidate_id")
        expected="sha256:"+hashlib.sha256(json.dumps(tmp,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        self.assertEqual(claimed,expected)
        self.assertEqual(c["policy"]["channel"],"latest-stable")
        self.assertTrue(c["policy"]["build_must_not_reresolve"])
        self.assertEqual(c["policy"]["compatibility_exceptions"],[])

    def test_m04_t03_binding_and_approved_inventory(self):
        board=(ROOT/"implementation"/"workstreams"/"feature-paseo-gui-runtime"/"TASK_BOARD.toml").read_text()
        self.assertIn("fb6195831d047ede2f359146b69ede2690e84ef3",board)
        self.assertIn("e31658fda900d748010bedc6caa0bb3aacf8c430",board)
        blob=subprocess.run(["git","rev-parse","fb6195831d047ede2f359146b69ede2690e84ef3:implementation/workstreams/feature-paseo-gui-runtime/results/M04-T03.md"],
                            cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(blob.returncode,0,blob.stderr)
        self.assertEqual(blob.stdout.strip(),"e31658fda900d748010bedc6caa0bb3aacf8c430")
        result=(ROOT/"implementation"/"workstreams"/"feature-paseo-gui-runtime"/"results"/"M04-T03.md").read_text()
        self.assertIn("8914f92b3f832e81c28b276e0ebee08d374f5013",result)
        definition=json.loads((ROOT/"config"/"environment-capabilities.json").read_text())
        inventory.validate_definition(definition)
        candidate=json.loads((ROOT/"config"/"paseo-candidate.json").read_text())
        derived=inventory.derive_inventory(definition,candidate,ROOT)
        self.assertEqual(derived["candidate_id"],candidate["candidate_id"])
        selected={item["desired"]["component"] for item in definition["capabilities"] if item["desired"]["kind"]=="candidate_component"}
        self.assertEqual(selected,REQUIRED)

    def test_missing_mandatory_sources_fail_closed_without_promotable_output(self):
        cases=[]
        facts=self.base_facts(); del facts["components"]["pi_mcp_adapter"]; cases.append(("missing-component",facts))
        facts=self.base_facts(); del facts["components"]["pi"]["source"]["commit"]; cases.append(("missing-commit",facts))
        facts=self.base_facts(); del facts["components"]["docker_compose"]["artifact"]; cases.append(("missing-artifact",facts))
        for label, broken in cases:
            with self.subTest(label), tempfile.TemporaryDirectory() as td:
                p=self.write(td,broken)
                r=self.invoke("--fixture",str(p),"--check")
                self.assertNotEqual(r.returncode,0,label)
                self.assertNotIn("candidate_id",r.stdout,label)
                self.assertTrue(r.stderr.strip(),label)

    def test_prerelease_channel_substitution_rejected(self):
        mutations=[]
        facts=self.base_facts(); facts["components"]["pi"]["version"]="0.88.0-beta.1"; facts["components"]["pi"]["source"]["tag"]="v0.88.0-beta.1"; mutations.append(facts)
        facts=self.base_facts(); facts["components"]["playwright"]["version"]="nightly"; facts["components"]["playwright"]["source"]["tag"]="nightly"; mutations.append(facts)
        facts=self.base_facts(); facts["components"]["specpi"]["source"]["tag"]="v0.34.0-rc.1"; mutations.append(facts)
        facts=self.base_facts(); facts["channel"]="nightly"; mutations.append(facts)
        for broken in mutations:
            with tempfile.TemporaryDirectory() as td:
                p=self.write(td,broken)
                r=self.invoke("--fixture",str(p),"--check")
                self.assertNotEqual(r.returncode,0)
                lowered=r.stderr.lower()
                self.assertTrue("prerelease" in lowered or "channel" in lowered or "stable" in lowered,r.stderr)
                self.assertNotIn("candidate_id",r.stdout)

    def test_source_and_package_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["pi"]["source"]["repository"]="someone-else/pi"
            r=self.invoke("--fixture",str(self.write(td,facts,"a.json")),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("substitution",r.stderr)
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["playwright"]["npm"]["package"]="playwright-next"
            r=self.invoke("--fixture",str(self.write(td,facts,"b.json")),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("substitution",r.stderr)
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["pi"]["source"]["tag"]="v0.87.2"
            r=self.invoke("--fixture",str(self.write(td,facts,"c.json")),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("does not match",r.stderr)

    def test_incompatible_combinations_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts()
            facts["components"]["node"]["version"]="20.0.0"
            facts["components"]["paseo"]["artifact"]["node_version"]="20.0.0"
            r=self.invoke("--fixture",str(self.write(td,facts,"old.json")),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("incompatible",r.stderr.lower())
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["node"]["version"]="22.24.0"
            r=self.invoke("--fixture",str(self.write(td,facts,"drift.json")),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("incompatible",r.stderr.lower())
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["pi_mcp_adapter"]["declared_pi_ai_peer"]="^0.80.0"
            r=self.invoke("--fixture",str(self.write(td,facts,"peer.json")),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("incompatible",r.stderr.lower())

    def test_unapproved_exception_and_lag_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts()
            facts["compatibility_proposals"]=[{"component":"specpi","pinned_version":"0.34.0","reason":"test"}]
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("explicit user approval",r.stderr)
            self.assertNotIn("candidate_id",r.stdout)
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["observed_latest"]={"specpi":"0.35.0"}
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("unapproved compatibility lag",r.stderr)
            self.assertNotIn("candidate_id",r.stdout)

    def approval_pair(self,td,component="specpi",pinned="0.34.0",scope="specpi-only",rationale="test-approved-lag"):
        td=Path(td)
        record={"schema_version":1,"approvals":[{"component":component,"pinned_version":pinned,"scope":scope,"rationale":rationale}]}
        rp=td/"authority.json"; raw=json.dumps(record,sort_keys=True).encode(); rp.write_bytes(raw)
        digest="sha256:"+hashlib.sha256(raw).hexdigest()
        ap=td/"approved.json"
        ap.write_text(json.dumps({"schema_version":1,"exceptions":[
            {"component":component,"pinned_version":pinned,"scope":scope,"rationale":rationale,
             "authority":{"record":str(rp),"digest":digest}}]}))
        return ap,rp,digest

    def test_approved_exception_durable_and_reevaluated(self):
        with tempfile.TemporaryDirectory() as td:
            approved,record,digest=self.approval_pair(td)
            first=self.base_facts()
            first["compatibility_proposals"]=[{"component":"specpi","pinned_version":"0.34.0","reason":"test"}]
            first["observed_latest"]={"specpi":"0.35.0"}
            a=self.invoke("--fixture",str(self.write(td,first,"first.json")),"--check","--approved-exceptions",str(approved))
            self.assertEqual(a.returncode,0,a.stderr)
            ca=json.loads(a.stdout)
            self.assertEqual(len(ca["policy"]["compatibility_exceptions"]),1)
            entry=ca["policy"]["compatibility_exceptions"][0]
            self.assertEqual((entry["scope"],entry["rationale"]),("specpi-only","test-approved-lag"))
            self.assertEqual(entry["authority"],{"record":str(record),"digest":digest})
            self.assertNotIn("approved_by",entry)
            self.assertEqual(entry["recheck"]["status"],"still_required")
            self.assertEqual(entry["recheck"]["observed_latest"],"0.35.0")
            second=self.base_facts(); second["observed_latest"]={"specpi":"0.34.0"}
            b=self.invoke("--fixture",str(self.write(td,second,"second.json")),"--check","--approved-exceptions",str(approved))
            self.assertEqual(b.returncode,0,b.stderr)
            cb=json.loads(b.stdout)
            again=cb["policy"]["compatibility_exceptions"][0]
            self.assertEqual((again["scope"],again["rationale"]),("specpi-only","test-approved-lag"))
            self.assertEqual(again["authority"],{"record":str(record),"digest":digest})
            self.assertEqual(again["recheck"]["status"],"no_longer_lagging")
            self.assertNotEqual(again["recheck"]["facts_digest"],entry["recheck"]["facts_digest"])
            p=Path(td)/"candidate.json"; p.write_text(b.stdout)
            v=self.invoke("--validate",str(p)); self.assertEqual(v.returncode,0,v.stderr)

    def test_self_asserted_approval_text_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bad=self.write(td,{"schema_version":1,"exceptions":[
                {"component":"specpi","pinned_version":"0.34.0","scope":"specpi-only",
                 "rationale":"test-approved-lag","approved_by":"user:test"}]},"legacy-approved.json")
            facts=self.base_facts()
            facts["compatibility_proposals"]=[{"component":"specpi","pinned_version":"0.34.0"}]
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check","--approved-exceptions",str(bad))
            self.assertNotEqual(r.returncode,0); self.assertIn("authority",r.stderr.lower())
            self.assertNotIn("candidate_id",r.stdout)

    def test_bound_authority_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            approved,record,digest=self.approval_pair(td)
            record.write_bytes(json.dumps({"schema_version":1,"approvals":[
                {"component":"specpi","pinned_version":"0.34.0","scope":"tampered","rationale":"test-approved-lag"}]}).encode())
            facts=self.base_facts()
            facts["compatibility_proposals"]=[{"component":"specpi","pinned_version":"0.34.0"}]
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check","--approved-exceptions",str(approved))
            self.assertNotEqual(r.returncode,0); self.assertIn("authority mismatch",r.stderr)
            self.assertNotIn("candidate_id",r.stdout)
        with tempfile.TemporaryDirectory() as td:
            approved,record,digest=self.approval_pair(td)
            record.unlink()
            facts=self.base_facts()
            facts["compatibility_proposals"]=[{"component":"specpi","pinned_version":"0.34.0"}]
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check","--approved-exceptions",str(approved))
            self.assertNotEqual(r.returncode,0); self.assertIn("unavailable",r.stderr)
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            record={"schema_version":1,"approvals":[
                {"component":"specpi","pinned_version":"0.34.0","scope":"other-scope","rationale":"test-approved-lag"}]}
            rp=td/"authority.json"; raw=json.dumps(record,sort_keys=True).encode(); rp.write_bytes(raw)
            approved=self.write(td,{"schema_version":1,"exceptions":[
                {"component":"specpi","pinned_version":"0.34.0","scope":"specpi-only","rationale":"test-approved-lag",
                 "authority":{"record":str(rp),"digest":"sha256:"+hashlib.sha256(raw).hexdigest()}}]},"approved.json")
            facts=self.base_facts()
            facts["compatibility_proposals"]=[{"component":"specpi","pinned_version":"0.34.0"}]
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check","--approved-exceptions",str(approved))
            self.assertNotEqual(r.returncode,0); self.assertIn("no matching authority approval",r.stderr)
        with tempfile.TemporaryDirectory() as td:
            approved,record,digest=self.approval_pair(td)
            dup=self.write(td,{"schema_version":1,"exceptions":[
                {"component":"specpi","pinned_version":"0.34.0","scope":"specpi-only","rationale":"test-approved-lag",
                 "authority":{"record":str(record),"digest":digest}},
                {"component":"specpi","pinned_version":"0.33.0","scope":"specpi-only","rationale":"second",
                 "authority":{"record":str(record),"digest":digest}}]},"dup-approved.json")
            r=self.invoke("--fixture",str(FIXTURE),"--check","--approved-exceptions",str(dup))
            self.assertNotEqual(r.returncode,0); self.assertIn("multiple approved",r.stderr)
        with tempfile.TemporaryDirectory() as td:
            approved,record,digest=self.approval_pair(td,component="node",pinned="22.23.3")
            r=self.invoke("--fixture",str(FIXTURE),"--check","--approved-exceptions",str(approved))
            self.assertNotEqual(r.returncode,0); self.assertIn("derived component node",r.stderr)

    def test_partial_write_preserves_accepted_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); facts=self.base_facts(); del facts["components"]["node"]
            out=td/"candidate.json"; out.write_text("sentinel\n")
            before=set(p.name for p in td.iterdir())
            r=self.invoke("--fixture",str(self.write(td,facts,"broken.json")),"--output",str(out))
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(out.read_text(),"sentinel\n")
            self.assertEqual(r.stdout,"")
            leftovers=[p.name for p in td.iterdir() if p.name not in before and p.name not in ("broken.json","candidate.json")]
            self.assertEqual(leftovers,[])

    def test_secret_safe_output_and_errors(self):
        secret="s3cr3t-value-xyz-987"
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["pi"]["password"]=secret
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check")
            self.assertNotEqual(r.returncode,0)
            self.assertNotIn(secret,r.stdout); self.assertNotIn(secret,r.stderr)
        r=self.invoke("--fixture",str(FIXTURE),"--check"); self.assertEqual(r.returncode,0,r.stderr)
        lowered=r.stdout.lower()
        for forbidden in ('"password"','"authorization"','"access_token"','"private_key"','"secret"'):
            self.assertNotIn(forbidden,lowered)

    def test_changed_capability_set_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            definition=json.loads((ROOT/"config"/"environment-capabilities.json").read_text())
            definition["capabilities"].append({"id":"new_tool","approval":"accepted","delivery_mode":"npm_global",
                "desired":{"kind":"candidate_component","component":"new_tool"},
                "runtime_location":{"kind":"command","value":"new_tool"},"probe":{"kind":"command_version"}})
            inv=self.write(td,definition,"inventory.json")
            r=self.invoke("--fixture",str(FIXTURE),"--check","--inventory",str(inv))
            self.assertNotEqual(r.returncode,0); self.assertIn("capability set",r.stderr)
        with tempfile.TemporaryDirectory() as td:
            facts=self.base_facts(); facts["components"]["new_tool"]={"version":"1.0.0"}
            r=self.invoke("--fixture",str(self.write(td,facts)),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("capability set",r.stderr)

    def test_build_inputs_consume_only_frozen_candidate(self):
        dockerfile=(ROOT/"Dockerfile").read_text()
        candidate=json.loads((ROOT/"config"/"paseo-candidate.json").read_text())
        paseo=candidate["components"]["paseo"]
        self.assertIn(f"FROM {paseo['artifact']['reference']}",dockerfile)
        for env_name, comp in (("PI_UNRAID_PI_VERSION","pi"),("PI_UNRAID_PLAYWRIGHT_VERSION","playwright"),
                               ("PI_UNRAID_GH_VERSION","github_cli"),("PI_UNRAID_DOCKER_CLI_VERSION","docker_cli"),
                               ("PI_UNRAID_DOCKER_COMPOSE_VERSION","docker_compose")):
            self.assertIn(f'{env_name}="{candidate["components"][comp]["version"]}"',dockerfile)
        lowered=dockerfile.lower()
        self.assertNotIn("releases/latest",lowered)
        self.assertNotIn(":latest",lowered)
        self.assertNotIn("@latest",lowered)
        self.assertNotIn("npm install -g @earendil",dockerfile)
        self.assertIn("never re-resolve",dockerfile)

    def test_project_local_locks_untouched(self):
        targets=[p for pattern in ("package.json","package-lock.json","yarn.lock","pnpm-lock.yaml","requirements*.txt","poetry.lock")
                 for p in ROOT.glob(pattern)]+[ROOT/"tests"/"fixtures"/"m02"/"pi-package"/"package.json"]
        before={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in targets if p.is_file()}
        self.assertTrue(before)
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"candidate.json"
            r=self.invoke("--fixture",str(FIXTURE),"--output",str(out))
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue(out.is_file())
        after={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in targets if p.is_file()}
        self.assertEqual(before,after)

    def test_accepted_candidate_immutable_through_resolver(self):
        accepted=ROOT/"config"/"paseo-candidate.json"
        digest=hashlib.sha256(accepted.read_bytes()).hexdigest()
        for spelling in ("config/paseo-candidate.json","./config/paseo-candidate.json",str(accepted)):
            r=self.invoke("--fixture",str(FIXTURE),"--output",spelling)
            self.assertNotEqual(r.returncode,0,spelling)
            self.assertIn("accepted candidate",r.stderr,spelling)
            self.assertIn("staged update path",r.stderr,spelling)
            self.assertEqual(hashlib.sha256(accepted.read_bytes()).hexdigest(),digest,spelling)
        with tempfile.TemporaryDirectory() as td:
            facts_path=self.write(td,self.base_facts())
            r=self.invoke("--fixture",str(facts_path),"--output",str(facts_path))
            self.assertNotEqual(r.returncode,0); self.assertIn("resolver input fixture",r.stderr)
            inv=ROOT/"config"/"environment-capabilities.json"
            r=self.invoke("--fixture",str(FIXTURE),"--output",str(inv))
            self.assertNotEqual(r.returncode,0); self.assertIn("resolver input",r.stderr)
        self.assertEqual(hashlib.sha256(accepted.read_bytes()).hexdigest(),digest)

    def test_default_output_is_read_only_stdout(self):
        accepted=ROOT/"config"/"paseo-candidate.json"
        digest=hashlib.sha256(accepted.read_bytes()).hexdigest()
        before=sorted(p.name for p in (ROOT/"config").iterdir())
        r=self.invoke("--fixture",str(FIXTURE))
        self.assertEqual(r.returncode,0,r.stderr)
        c=json.loads(r.stdout)
        self.assertTrue(c["candidate_id"].startswith("sha256:"))
        self.assertEqual(set(c["components"]),REQUIRED)
        self.assertEqual(hashlib.sha256(accepted.read_bytes()).hexdigest(),digest)
        self.assertEqual(sorted(p.name for p in (ROOT/"config").iterdir()),before)

class LivePinResolutionTests(unittest.TestCase):
    FIXTURE_FACTS=json.loads(FIXTURE.read_text())["components"]
    LATEST_TAGS={"getpaseo/paseo":"v0.9.2","earendil-works/pi":"v0.87.1","microsoft/playwright":"v1.63.0",
                 "tannermidd/SpecPi":"v0.34.0","nicobailon/pi-mcp-adapter":"v2.37.0","cli/cli":"v2.101.0",
                 "docker/compose":"v5.5.1","moby/moby":"docker-v29.8.1"}
    PINNED_SPECPI={"version":"0.33.0","integrity":"sha512-pinned-specpi-test","shasum":"e"*40,
                   "commit":"f"*40,"tag":"v0.33.0"}

    def stubs(self, pin_ok=True):
        facts=copy.deepcopy(self.FIXTURE_FACTS)
        commits={(c["source"]["repository"],c["source"]["tag"]): c["source"]["commit"]
                 for name, c in facts.items() if "source" in c}
        commits[("tannermidd/SpecPi","v0.33.0")]="f"*40
        def fake_latest(repo):
            return {"tag_name":self.LATEST_TAGS[repo],"draft":False,"prerelease":False}
        def fake_npm_component(name,repo):
            comp=next(c for n, c in facts.items() if c.get("npm",{}).get("package")==name)
            ndata={"peerDependencies":{"@earendil-works/pi-ai":facts["pi_mcp_adapter"]["declared_pi_ai_peer"]}}
            return copy.deepcopy(comp),ndata
        def fake_binary(repo,pattern):
            comp=next(c for n, c in facts.items() if c.get("source",{}).get("repository")==repo)
            return copy.deepcopy(comp)
        def fake_peel(repo,tag):
            if (repo,tag) in commits: return commits[(repo,tag)]
            raise resolver.ResolutionError(f"cannot peel {repo}:{tag}")
        def fake_release_by_tag(repo,tag):
            if pin_ok and (repo,tag)==("tannermidd/SpecPi","v0.33.0"):
                return {"tag_name":tag,"draft":False,"prerelease":False}
            raise resolver.ResolutionError(f"cannot verify pinned release {repo} {tag}")
        def fake_npm_version(name,version):
            if pin_ok and (name,version)==("specpi","0.33.0"):
                pin=self.PINNED_SPECPI
                return {"version":version,"dist":{"integrity":pin["integrity"],"shasum":pin["shasum"]}}
            raise resolver.ResolutionError(f"cannot verify pinned {name} {version}")
        return {"latest":fake_latest,"npm_component":fake_npm_component,"binary":fake_binary,"peel":fake_peel,
                "release_by_tag":fake_release_by_tag,"npm_version":fake_npm_version,
                "paseo_image":lambda v: copy.deepcopy(facts["paseo"]["artifact"]),
                "playwright_chromium":lambda v: copy.deepcopy(facts["playwright"]["chromium"])}

    def approval(self,td,pinned="0.33.0"):
        td=Path(td)
        record={"schema_version":1,"approvals":[{"component":"specpi","pinned_version":pinned,
                                                 "scope":"specpi-only","rationale":"test-live-pin"}]}
        rp=td/"authority.json"; raw=json.dumps(record,sort_keys=True).encode(); rp.write_bytes(raw)
        ap=td/"approved.json"
        ap.write_text(json.dumps({"schema_version":1,"exceptions":[
            {"component":"specpi","pinned_version":pinned,"scope":"specpi-only","rationale":"test-live-pin",
             "authority":{"record":str(rp),"digest":"sha256:"+hashlib.sha256(raw).hexdigest()}}]}))
        return ap

    def test_live_approved_pin_resolves_exact_provenance(self):
        definition=json.loads((ROOT/"config"/"environment-capabilities.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            approved=resolver.load_approved_exceptions(self.approval(td))
            stubs=self.stubs(pin_ok=True)
            with mock.patch.object(resolver,"latest",side_effect=lambda r: stubs["latest"](r)), \
                 mock.patch.object(resolver,"npm_component",side_effect=lambda n,r: stubs["npm_component"](n,r)), \
                 mock.patch.object(resolver,"binary",side_effect=lambda r,p: stubs["binary"](r,p)), \
                 mock.patch.object(resolver,"peel",side_effect=lambda r,t: stubs["peel"](r,t)), \
                 mock.patch.object(resolver,"release_by_tag",side_effect=lambda r,t: stubs["release_by_tag"](r,t)), \
                 mock.patch.object(resolver,"npm_version",side_effect=lambda n,v: stubs["npm_version"](n,v)), \
                 mock.patch.object(resolver,"paseo_image",side_effect=stubs["paseo_image"]), \
                 mock.patch.object(resolver,"playwright_chromium",side_effect=stubs["playwright_chromium"]):
                c=resolver.resolve_live(definition,approved)
            pin=self.PINNED_SPECPI
            specpi=c["components"]["specpi"]
            self.assertEqual(specpi["version"],"0.33.0")
            self.assertEqual(specpi["npm"]["integrity"],pin["integrity"])
            self.assertEqual(specpi["npm"]["shasum"],pin["shasum"])
            self.assertEqual(specpi["source"]["commit"],pin["commit"])
            self.assertEqual(specpi["source"]["tag"],"v0.33.0")
            self.assertEqual(c["components"]["pi"]["version"],"0.87.1")
            self.assertEqual(len(c["policy"]["compatibility_exceptions"]),1)
            entry=c["policy"]["compatibility_exceptions"][0]
            self.assertEqual(entry["pinned_version"],"0.33.0")
            self.assertEqual(entry["recheck"]["status"],"still_required")
            self.assertEqual(entry["recheck"]["observed_latest"],"0.34.0")
            resolver.validate(c,definition)

    def test_live_unverifiable_pin_fails_closed(self):
        definition=json.loads((ROOT/"config"/"environment-capabilities.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            approved=resolver.load_approved_exceptions(self.approval(td))
            stubs=self.stubs(pin_ok=False)
            with mock.patch.object(resolver,"latest",side_effect=lambda r: stubs["latest"](r)), \
                 mock.patch.object(resolver,"npm_component",side_effect=lambda n,r: stubs["npm_component"](n,r)), \
                 mock.patch.object(resolver,"binary",side_effect=lambda r,p: stubs["binary"](r,p)), \
                 mock.patch.object(resolver,"peel",side_effect=lambda r,t: stubs["peel"](r,t)), \
                 mock.patch.object(resolver,"release_by_tag",side_effect=lambda r,t: stubs["release_by_tag"](r,t)), \
                 mock.patch.object(resolver,"npm_version",side_effect=lambda n,v: stubs["npm_version"](n,v)), \
                 mock.patch.object(resolver,"paseo_image",side_effect=stubs["paseo_image"]), \
                 mock.patch.object(resolver,"playwright_chromium",side_effect=stubs["playwright_chromium"]):
                with self.assertRaisesRegex(resolver.ResolutionError,"cannot verify pinned"):
                    resolver.resolve_live(definition,approved)

if __name__=="__main__": unittest.main()
