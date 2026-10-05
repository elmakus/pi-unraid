#!/usr/bin/env python3
"""Candidate-local applied payload interval, Linux inotify + Unix peer credentials.
No credentials or provider API. Expected content is frozen public companion source;
actual bytes/modes/identities and kernel changes, never caller PASS, decide binding.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import stat
import struct
import subprocess
import sys
import time


def private(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o600 or s.st_uid != os.getuid() or s.st_size > 1048576:
            raise ValueError('private interval input unavailable')
        return json.loads(os.read(fd, s.st_size + 1))
    finally:
        os.close(fd)


def stamp(pid):
    return Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()[19]


def snapshot(root, rows):
    expected_dirs = {'.'}
    for name in rows:
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or not p.parts:
            raise ValueError('unsafe companion member')
        expected_dirs.update(str(a) for a in p.parents)
    found, dirs, identities = {}, set(), {}
    for p in [root, *sorted(root.rglob('*'))]:
        s = p.lstat()
        rel = p.relative_to(root).as_posix()
        if stat.S_ISDIR(s.st_mode):
            dirs.add(rel)
        elif stat.S_ISREG(s.st_mode):
            fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                before = os.fstat(fd)
                raw = b''
                while True:
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    raw += chunk
                    if len(raw) > 1048576:
                        raise ValueError('companion member too large')
                after = os.fstat(fd)
                if (before.st_ino, before.st_ctime_ns, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_ctime_ns, after.st_mtime_ns, after.st_size):
                    raise ValueError('member changed during read')
                found[rel] = {'content': raw.decode('utf8'), 'mode': '%04o' % stat.S_IMODE(after.st_mode)}
            finally:
                os.close(fd)
        else:
            raise ValueError('nonregular companion member')
        identities[rel] = [s.st_dev, s.st_ino, s.st_mode, s.st_ctime_ns, s.st_mtime_ns, s.st_size]
    if found != rows or dirs != expected_dirs:
        raise ValueError('applied companion bytes/set/modes unavailable')
    return identities


def serve(manifest, reference):
    doc = private(manifest)
    root = Path(doc['root'])
    rows = doc['files']
    if root.is_symlink() or not isinstance(rows, dict) or not rows:
        raise ValueError('applied root unavailable')
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    if fd < 0:
        raise ValueError('Linux interval observation unavailable')
    # Mutation-only mask. Reads do not invalidate; writes, chmod, replacement,
    # move/delete/unmount/overflow invalidate irreversibly, even if bytes restored.
    mask = 0x2 | 0x4 | 0x8 | 0x40 | 0x80 | 0x100 | 0x200 | 0x400 | 0x800 | 0x2000
    parent_wd = libc.inotify_add_watch(fd, os.fsencode(root.parent), mask)
    if parent_wd < 0:
        raise ValueError('parent interval watch unavailable')
    for p in [root, *sorted(root.rglob('*'))]:
        if p.is_symlink() or libc.inotify_add_watch(fd, os.fsencode(p), mask) < 0:
            raise ValueError('member interval watch unavailable')
    baseline = snapshot(root, rows)
    ever_changed = False
    def check():
        nonlocal ever_changed
        while True:
            try:
                data = os.read(fd, 65536)
            except BlockingIOError:
                break
            if not data:
                ever_changed = True
                break
            pos = 0
            while pos < len(data):
                wd, event, cookie, size = struct.unpack_from('iIII', data, pos)
                name = data[pos + 16:pos + 16 + size].split(b'\0', 1)[0]
                pos += 16 + size
                if wd != parent_wd or name in (b'', os.fsencode(root.name)) or event & (0x4000 | 0x8000 | 0x400 | 0x800):
                    ever_changed = True
        try:
            if snapshot(root, rows) != baseline:
                ever_changed = True
        except (OSError, ValueError, KeyError):
            ever_changed = True
        return not ever_changed
    if not check():
        raise ValueError('initial applied interval changed')
    endpoint = str(reference) + '.sock'
    server = socket.socket(socket.AF_UNIX)
    server.bind(endpoint)
    os.chmod(endpoint, 0o600)
    server.listen(4)
    info = {'schema_version': 1, 'pid': os.getpid(), 'start': stamp(os.getpid()),
            'nonce': doc['nonce'], 'socket': endpoint,
            'manifest_sha256': hashlib.sha256(Path(manifest).read_bytes()).hexdigest()}
    out = os.open(reference, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(out, json.dumps(info).encode()); os.fsync(out)
    finally:
        os.close(out)
    print(json.dumps(info), flush=True)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        ready, _, _ = select.select([server, fd], [], [], min(1, deadline - time.monotonic()))
        if fd in ready:
            check()
        if server in ready:
            connection, _ = server.accept()
            with connection:
                connection.settimeout(2)
                peer = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                if peer[1] != os.getuid():
                    continue
                request = connection.recv(1024)
                ok = check() and hashlib.sha256(Path(manifest).read_bytes()).hexdigest() == info['manifest_sha256']
                connection.sendall(json.dumps({'bound': ok, 'nonce': doc['nonce'], 'pid': os.getpid()}).encode())
                if request == b'stop':
                    break
    server.close(); os.close(fd)


def observe(reference, stop=False):
    info = private(reference)
    if stamp(info['pid']) != info['start']:
        raise ValueError('interval process replaced')
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(3)
        client.connect(info['socket'])
        peer = struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if peer[:2] != (info['pid'], os.getuid()):
            raise ValueError('interval peer replaced')
        client.sendall(b'stop' if stop else b'check')
        result = json.loads(client.recv(4096))
    if result != {'bound': True, 'nonce': info['nonce'], 'pid': info['pid']}:
        raise ValueError('applied interval changed')
    return result


if __name__ == '__main__':
    try:
        mode, manifest, reference = sys.argv[1:]
        if mode == 'serve':
            serve(manifest, reference)
        elif mode == 'start':
            process = subprocess.Popen([sys.executable, __file__, 'serve', manifest, reference],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                start_new_session=True)
            if not select.select([process.stdout], [], [], 5)[0]:
                raise ValueError('interval startup unknown')
            line = process.stdout.readline()
            if not line:
                raise ValueError('interval startup unavailable')
            info = json.loads(line)
            if info['pid'] != process.pid or info['start'] != stamp(process.pid):
                raise ValueError('interval startup identity unavailable')
            print(json.dumps(info))
        else:
            print(json.dumps(observe(reference, mode == 'stop')))
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        print(json.dumps({'bound': False})); sys.exit(20)
