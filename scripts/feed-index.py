#!/usr/bin/env python3
"""Create the opkg index from the package control record, without extracting files."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile


def package_index(package):
    if package.is_symlink() or not package.is_file():
        raise ValueError('Package must be a regular file')
    with tarfile.open(package) as outer:
        member = next(m for m in outer.getmembers() if m.name.removeprefix('./') == 'control.tar.gz')
        if not member.isfile() or member.size > 1024 * 1024:
            raise ValueError('Invalid control archive')
        with tarfile.open(fileobj=io.BytesIO(outer.extractfile(member).read())) as control:
            entry = next(m for m in control.getmembers() if m.name.removeprefix('./') == 'control')
            if not entry.isfile() or entry.size > 65536:
                raise ValueError('Invalid control record')
            text = control.extractfile(entry).read().decode().rstrip('\n')
    fields = dict(line.split(': ', 1) for line in text.splitlines() if ': ' in line and not line[0].isspace())
    if fields.get('Package') != 'luci-theme-athena' or fields.get('Architecture') != 'all':
        raise ValueError('Unexpected package or architecture')
    if any(key in fields for key in ['Filename', 'Size', 'SHA256sum']):
        raise ValueError('Control record contains index-only fields')
    data = package.read_bytes()
    result = (text + '\nFilename: ' + package.name + '\nSize: ' + str(len(data)) +
              '\nSHA256sum: ' + hashlib.sha256(data).hexdigest() + '\n\n').encode()
    # Match OpenWrt's padding workaround for the usign SHA-512 boundary case.
    if (64 + len(result)) % 128 in (110, 111):
        result += b'\n\n'
    return result, fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    packages = sorted(args.directory.glob('*.ipk'))
    if len(packages) != 1:
        raise ValueError('Exactly one Athena IPK is required')
    index, _ = package_index(packages[0])
    (args.directory / 'Packages').write_bytes(index)
    (args.directory / 'Packages.gz').write_bytes(gzip.compress(index, mtime=0))


if __name__ == '__main__':
    main()
