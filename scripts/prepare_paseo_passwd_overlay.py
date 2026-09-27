#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


class OverlayError(RuntimeError):
    pass


def read_image_passwd(image: str) -> str:
    proc = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "cat", image, "/etc/passwd"],
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise OverlayError("failed to read /etc/passwd from candidate image")
    return proc.stdout


def build_overlay(source: str, uid: int, gid: int) -> str:
    lines = [line for line in source.splitlines() if line]
    for line in lines:
        parts = line.split(":")
        if len(parts) < 7:
            raise OverlayError("candidate /etc/passwd contains malformed entry")
        if int(parts[2]) == uid:
            raise OverlayError(f"candidate image already assigns UID {uid} to {parts[0]}")
        if parts[0] == "paseo-unraid":
            raise OverlayError("candidate image already contains paseo-unraid")
    lines.append(f"paseo-unraid:x:{uid}:{gid}:Paseo Unraid runtime:/home/paseo:/bin/false")
    return "\n".join(lines) + "\n"


def install_overlay(output: Path, content: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".passwd.", dir=output.parent)
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, output)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--uid", type=int, default=99)
    parser.add_argument("--gid", type=int, default=100)
    args = parser.parse_args()

    if args.uid < 1 or args.gid < 1:
        raise SystemExit("uid/gid must be positive")
    source = read_image_passwd(args.image)
    content = build_overlay(source, args.uid, args.gid)
    output = Path(args.output)
    install_overlay(output, content)

    entry = next(line for line in content.splitlines() if line.split(":")[2] == str(args.uid))
    parts = entry.split(":")
    print("ok=true")
    print(f"path={output}")
    print(f"uid={parts[2]}")
    print(f"gid={parts[3]}")
    print(f"home={parts[5]}")
    print(f"mode={oct(output.stat().st_mode & 0o777)[2:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
