from pathlib import Path
import tempfile
import unittest
from test_core import backup
from botw_manager.discovery import scan

class DiscoveryTests(unittest.TestCase):
    def test_all_profiles_and_formats_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            cemu=root/'Cemu'/'mlc01';cemu.mkdir(parents=True)
            for user in ('80000001','80000002'): backup(cemu/user,'>')
            port=root/'Savage Wind'/'save';port.mkdir(parents=True)
            for user in ('save_0','save_1'): backup(port/user,'<')
            ignored=root/'keys';ignored.mkdir();backup(ignored/'private','<')
            before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result=scan([root,port])
            self.assertEqual(len(result),4)
            self.assertEqual([x.kind for x in result].count('Cemu'),2)
            self.assertEqual([x.kind for x in result].count('Savage Wind'),2)
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_bounds_invalid_and_backups(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();backup(root/'old.ubsm-backup-123','<')
            broken=root/'broken';broken.mkdir();(broken/'option.sav').write_bytes(b'not BOTW')
            self.assertEqual(scan([root]),[])
            with self.assertRaises(ValueError): scan([root],max_dirs=1)
