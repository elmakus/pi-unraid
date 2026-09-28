from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "config/unraid/templates/pi-unraid-paseo.xml"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64

def docker_man_update_ready(local_digest: str, remote_digest: str) -> bool:
    return bool(local_digest and remote_digest and local_digest != remote_digest)

class UnraidPaseoTemplateTests(unittest.TestCase):
    def test_template_uses_only_accepted_signal(self):
        root = ET.parse(TEMPLATE).getroot()
        self.assertEqual(root.findtext("Repository"), "ghcr.io/elmakus/pi-unraid:accepted")
        self.assertNotIn("@sha256:", root.findtext("Repository"))
        self.assertEqual(root.findtext("Privileged"), "false")
        self.assertEqual(root.findtext("Network"), "pi-unraid_default")

    def test_template_preserves_production_mounts_and_identity(self):
        root = ET.parse(TEMPLATE).getroot()
        configs = {node.attrib["Target"]: node for node in root.findall("Config")}
        self.assertEqual(configs["/home/paseo"].text, "/mnt/user/appdata/pi-unraid/paseo-home")
        self.assertEqual(configs["/projects"].text, "/mnt/user/projects")
        self.assertEqual(configs["/worktrees"].text, "/mnt/user/pi-worktrees")
        self.assertEqual(configs["/etc/passwd"].text, "/mnt/user/appdata/pi-unraid/m07-t02/passwd")
        self.assertEqual(configs["/etc/passwd"].attrib["Mode"], "ro")
        self.assertEqual(configs["/run/secrets/pi-unraid-codex-lb"].attrib["Mode"], "ro")
        self.assertEqual(configs["/run/secrets/unraid-api.key"].attrib["Mode"], "ro")
        extra = root.findtext("ExtraParams")
        self.assertIn("--user=99:100", extra)
        self.assertIn("--shm-size=1g", extra)
        self.assertIn("--add-host=host.docker.internal:host-gateway", extra)

    def test_update_ready_is_exact_digest_inequality(self):
        self.assertFalse(docker_man_update_ready(DIGEST_A, DIGEST_A))
        self.assertTrue(docker_man_update_ready(DIGEST_A, DIGEST_B))

if __name__ == "__main__":
    unittest.main()
