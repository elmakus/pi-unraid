#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"resolve-paseo-candidate.py"
FIXTURE=ROOT/"tests"/"fixtures"/"paseo-candidate"/"facts.json"

class ResolverTests(unittest.TestCase):
    def run(self,*args):
        return subprocess.run(["python3",str(SCRIPT),*args],cwd=ROOT,text=True,capture_output=True)

    def test_fixture_is_deterministic_complete_and_secret_free(self):
        a=self.run("--fixture",str(FIXTURE),"--check")
        b=self.run("--fixture",str(FIXTURE),"--check")
        self.assertEqual(a.returncode,0,a.stderr); self.assertEqual(a.stdout,b.stdout)
        c=json.loads(a.stdout)
        self.assertEqual(set(c["components"]),{"paseo","node","pi","playwright","specpi","pi_mcp_adapter","github_cli","docker_cli","docker_compose"})
        self.assertEqual(c["components"]["paseo"]["artifact"]["digest"],"sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136")
        self.assertEqual(c["components"]["playwright"]["chromium"]["revision"],"1243")
        self.assertNotIn("password",a.stdout.lower()); self.assertNotIn("access_token",a.stdout.lower())

    def test_validate_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"candidate.json"
            r=self.run("--fixture",str(FIXTURE),"--check"); self.assertEqual(r.returncode,0,r.stderr)
            p.write_text(r.stdout)
            v=self.run("--validate",str(p)); self.assertEqual(v.returncode,0,v.stderr)
            self.assertTrue(v.stdout.strip().startswith("sha256:"))

    def test_failure_does_not_replace_existing_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); facts=json.loads(FIXTURE.read_text())
            del facts["components"]["specpi"]
            broken=td/"broken.json"; broken.write_text(json.dumps(facts))
            out=td/"candidate.json"; out.write_text("sentinel\n")
            r=self.run("--fixture",str(broken),"--output",str(out))
            self.assertNotEqual(r.returncode,0); self.assertEqual(out.read_text(),"sentinel\n")

    def test_bad_npm_integrity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); facts=json.loads(FIXTURE.read_text())
            facts["components"]["pi"]["npm"]["integrity"]="missing"
            broken=td/"broken.json"; broken.write_text(json.dumps(facts))
            r=self.run("--fixture",str(broken),"--check")
            self.assertNotEqual(r.returncode,0); self.assertIn("integrity",r.stderr)

if __name__=="__main__": unittest.main()
