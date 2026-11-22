#!/usr/bin/env python3
"""Verify a signed feed in isolated /tmp roots on an OpenWrt SSH test host."""
import argparse
import io
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
import uuid

BASE = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feed', type=Path)
    parser.add_argument('--ssh', type=Path, required=True)
    args = parser.parse_args()
    stage = '/tmp/athena-feed-test-' + uuid.uuid4().hex
    payload = io.BytesIO()
    with tempfile.TemporaryDirectory(prefix='athena-wrong-key-') as directory:
        private = Path(directory) / 'test.pem'
        public = Path(directory) / 'test.pub'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'EC', '-pkeyopt',
                        'ec_paramgen_curve:P-256', '-out', str(private)], check=True)
        subprocess.run(['openssl', 'pkey', '-in', str(private), '-pubout',
                        '-out', str(public)], check=True)
        with tarfile.open(fileobj=payload, mode='w:gz') as archive:
            archive.add(args.feed.resolve(), 'public')
            archive.add(public, 'wrong-apk.pub')
            for name in ['enable-feed.sh', 'test-feed-remote.sh']:
                archive.add(BASE / 'scripts' / name, name)
    quoted = shlex.quote(stage)
    command = ('set -eu; umask 077; mkdir ' + quoted + '; trap ' +
               shlex.quote('rm -rf ' + quoted) + ' EXIT; tar -xzf - -C ' + quoted +
               '; sh ' + shlex.quote(stage + '/test-feed-remote.sh') + ' ' + quoted)
    subprocess.run([str(args.ssh.resolve()), command], input=payload.getvalue(), check=True)


if __name__ == '__main__':
    main()
