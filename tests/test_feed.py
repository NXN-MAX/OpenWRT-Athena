import gzip
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('feed_index', Path(__file__).resolve().parents[1] / 'scripts/feed-index.py')
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)


def archive(files):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, value in files.items():
            entry = tarfile.TarInfo(name); entry.size = len(value)
            tar.addfile(entry, io.BytesIO(value))
    return stream.getvalue()


class FeedIndex(unittest.TestCase):
    def test_index_binds_control_to_exact_package_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'luci-theme-athena_1.2.3-r1_all.ipk'
            control = b'Package: luci-theme-athena\nVersion: 1.2.3-r1\nArchitecture: all\nDescription: first line\n continuation\nDepends: luci-base\n'
            file.write_bytes(archive({'./control.tar.gz': archive({'./control': control})}))
            data, fields = index.package_index(file)
            self.assertEqual(fields['Version'], '1.2.3-r1')
            self.assertIn(b'\n continuation\n', data)
            self.assertIn(('SHA256sum: ' + hashlib.sha256(file.read_bytes()).hexdigest()).encode(), data)
            self.assertIn(('Size: ' + str(file.stat().st_size)).encode(), data)
            self.assertEqual(index.package_index(file)[0], data)
            file.write_bytes(file.read_bytes() + b'changed')
            self.assertNotEqual(index.package_index(file)[0], data)

    def test_rejects_foreign_packages_and_control_index_injection(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'fixture.ipk'
            for control in [b'Package: libc\nArchitecture: all\n',
                            b'Package: luci-theme-athena\nArchitecture: x86_64\n',
                            b'Package: luci-theme-athena\nArchitecture: all\nFilename: elsewhere.ipk\n']:
                file.write_bytes(archive({'control.tar.gz': archive({'control': control})}))
                with self.assertRaises(ValueError): index.package_index(file)

    def test_rejects_symlink_package_and_control_record(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'real.ipk'; file.write_bytes(b'not a package')
            link = Path(temp) / 'link.ipk'; link.symlink_to(file)
            with self.assertRaises(ValueError): index.package_index(link)
            nested = io.BytesIO()
            with tarfile.open(fileobj=nested, mode='w:gz') as tar:
                entry = tarfile.TarInfo('control'); entry.type = tarfile.SYMTYPE; entry.linkname = '/etc/passwd'; tar.addfile(entry)
            file.write_bytes(archive({'control.tar.gz': nested.getvalue()}))
            with self.assertRaises(ValueError): index.package_index(file)


if __name__ == '__main__': unittest.main()
