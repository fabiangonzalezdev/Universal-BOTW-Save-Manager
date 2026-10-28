from pathlib import Path
import hashlib
import struct
import tempfile
import unittest
import zipfile
from package_release import package


class PackagingTests(unittest.TestCase):
    def make_project(self,root):
        (root/'dist').mkdir()
        (root/'dist/Universal-BOTW-Save-Manager.exe').write_bytes(b'MZ synthetic packaging fixture')
        for f in ['README.md','README.es.md','LICENSE','THIRD_PARTY_NOTICES.md','RELEASE_NOTES.md']:
            (root/f).write_text('Release documentation')
        (root/'docs').mkdir();(root/'docs/guide.md').write_text('Guide')
        (root/'assets').mkdir();(root/'assets/sword.svg').write_text('<svg/>')
        (root/'botw_manager/data').mkdir(parents=True)
        (root/'botw_manager/data/LICENSE.test').write_text('License')

    def test_versioned_zip_has_readme_binary_and_matching_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_project(root)
            out=package(root,'windows-x64','1.2.3-test')
            self.assertEqual(out.parent.name,'v1.2.3-test')
            self.assertTrue((out.parent/'README.md').is_file())
            prefix='Universal-BOTW-Save-Manager-v1.2.3-test-windows-x64/'
            with zipfile.ZipFile(out) as z:
                names=z.namelist()
                for file in ['Universal-BOTW-Save-Manager.exe','README.md','README.es.md','VERSION.txt','docs/guide.md']:
                    self.assertIn(prefix+file,names)
                self.assertTrue(all(n.startswith(prefix) for n in names))
                self.assertIn('Version: 1.2.3-test',z.read(prefix+'VERSION.txt').decode())
            expected=out.with_suffix('.sha256').read_text().split()[0]
            self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(),expected)

    def test_private_files_are_not_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_project(root)
            (root/'otp.bin').write_bytes(b'never include')
            (root/'game_data.sav').write_bytes(b'never include')
            (root/'_local').mkdir();(root/'_local/token.keys').write_bytes(b'never include')
            (root/'dist/unrelated.zip').write_bytes(b'old archive')
            out=package(root,'windows-x64','1.2.3-test')
            with zipfile.ZipFile(out) as z:
                names='\n'.join(z.namelist())
                for name in ('otp.bin','game_data.sav','token.keys','unrelated.zip','_local'):
                    self.assertNotIn(name,names)

    def test_icon_contains_multiple_windows_sizes(self):
        ico=Path(__file__).resolve().parents[1]/'botw_manager/data/app-icon.ico'
        reserved,kind,count=struct.unpack_from('<HHH',ico.read_bytes())
        self.assertEqual((reserved,kind),(0,1))
        self.assertGreaterEqual(count,8)


if __name__=='__main__':unittest.main()
