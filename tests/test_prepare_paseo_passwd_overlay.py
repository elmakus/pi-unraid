from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_paseo_passwd_overlay",
    ROOT / "scripts" / "prepare_paseo_passwd_overlay.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class PreparePaseoPasswdOverlayTests(unittest.TestCase):
    def test_appends_runtime_identity_without_replacing_image_accounts(self) -> None:
        source = (
            "root:x:0:0:root:/root:/bin/bash\n"
            "paseo:x:1000:1000::/home/paseo:/bin/bash\n"
            "nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin\n"
        )
        out = MOD.build_overlay(source, 99, 100)
        self.assertIn("paseo:x:1000:1000::/home/paseo:/bin/bash", out)
        self.assertIn("paseo-unraid:x:99:100:Paseo Unraid runtime:/home/paseo:/bin/false", out)

    def test_refuses_existing_uid_collision(self) -> None:
        source = "root:x:0:0:root:/root:/bin/bash\nother:x:99:100::/:/bin/false\n"
        with self.assertRaises(MOD.OverlayError):
            MOD.build_overlay(source, 99, 100)

    def test_installs_atomic_world_readable_non_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "passwd"
            MOD.install_overlay(out, "root:x:0:0:root:/root:/bin/bash\n")
            self.assertEqual(out.read_text(), "root:x:0:0:root:/root:/bin/bash\n")
            self.assertEqual(out.stat().st_mode & 0o777, 0o644)


if __name__ == "__main__":
    unittest.main()
