import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from botw_manager.core import RecordFile, SaveError, convert_records, convert_tracker, convert, discover

HEART, STAMINA, STRING, MODERN = 0x2906F327, 0x3ADFF047, 0x5F283289, 0x62133C14


def fixture(endian, version=0x471B, modern=False, hearts=48):
    records = [(HEART, struct.pack(endian+'I', hearts)), (STAMINA, struct.pack(endian+'f', 1000.0))]
    records += [(STRING, x) for x in (b'Weap', b'on_S', b'word', b'_001', b'\0\0\0\0')]
    if modern:
        records.append((MODERN, struct.pack(endian+'I', 7)))
    return struct.pack(endian+'III', version, 0xFFFFFFFF, 1) + b''.join(struct.pack(endian+'I', h)+v for h,v in records) + b'\xff'*4


def backup(path, endian, version=0x471B, modern=False):
    path.mkdir()
    data=fixture(endian, version, modern)
    (path/'option.sav').write_bytes(data)
    (path/'0').mkdir()
    for f in ['game_data.sav', 'caption.sav']:
        (path/'0'/f).write_bytes(data)
    (path/'0'/'caption.jpg').write_bytes(b'jpeg-unchanged')


class ConversionTests(unittest.TestCase):
    def test_roundtrip_numeric_and_strings(self):
        src=fixture('<')
        dst, details=convert_records(src,fixture('>'))
        self.assertIn(b'Weap',dst)
        self.assertEqual(RecordFile.parse(dst).stats(),{'hearts':12,'stamina':1000})
        rt,_=convert_records(dst,fixture('<'))
        self.assertEqual(rt,src)
        self.assertEqual(details['removed'],[])

    def test_modern_downgrade_and_upgrade(self):
        old=fixture('>')
        new=fixture('<',0x4730,True)
        downgraded,report=convert_records(new,old)
        self.assertEqual(downgraded,old)
        self.assertEqual(report['removed'],['0x62133c14'])
        upgraded,report=convert_records(old,new)
        self.assertEqual(upgraded,new)
        self.assertEqual(report['initialized_from_target'],['0x62133c14'])

    def test_unknown_fields_rejected(self):
        src=fixture('<').replace(struct.pack('<I',HEART),struct.pack('<I',0x12345678))
        with self.assertRaises(SaveError):convert_records(src,fixture('>'))

    def test_unknown_version_and_corruption_rejected(self):
        for data in [b'',b'not a save',fixture('<')[:-1],b'\0'*4+fixture('<')[4:]]:
            with self.assertRaises(SaveError):RecordFile.parse(data)

    def test_tracker_roundtrip(self):
        b=bytes(range(256))*256
        out=convert_tracker(b)
        self.assertEqual(out[:4],b[:4])
        self.assertEqual(out[4:6],b[4:6][::-1])
        self.assertEqual(convert_tracker(out),b)

    def test_full_conversion_preserves_backups_and_destination_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a=p/'source';b=p/'target';out=p/'converted'
            backup(a,'<');backup(b,'>')
            original={str(f):f.read_bytes() for root in [a,b] for f in root.rglob('*') if f.is_file()}
            report=convert(a,b,out)
            self.assertEqual((out/'user-save/option.sav').read_bytes(),(b/'option.sav').read_bytes())
            self.assertEqual((out/'user-save/0/caption.jpg').read_bytes(),b'jpeg-unchanged')
            self.assertFalse(report['game_tested'])
            for f,data in original.items():self.assertEqual(Path(f).read_bytes(),data)
            for f in report['files']:
                self.assertEqual(hashlib.sha256((out/'user-save'/f['file']).read_bytes()).hexdigest(),f['output_sha256'])
            with self.assertRaises(SaveError):convert(a,b,out)

    def test_cross_version_opt_in_and_no_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a=p/'a';b=p/'b';out=p/'result'
            backup(a,'<',0x4730,True);backup(b,'>')
            with self.assertRaises(SaveError):convert(a,b,out)
            self.assertFalse(out.exists())
            self.assertTrue(convert(a,b,out,True)['experimental'])

    def test_nested_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a=p/'a';b=p/'b'
            backup(a,'<');backup(b,'>')
            with self.assertRaises(SaveError):convert(a,b,a/'new')

    def test_ambiguous_users_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);backup(p/'u1','>');backup(p/'u2','>')
            with self.assertRaises(SaveError):discover(p)

    def test_unsupported_array_length_rejected(self):
        s=fixture('<');t=fixture('>')
        t=t[:-4]+struct.pack('>I',STRING)+b'aaaa'+t[-4:]
        with self.assertRaises(SaveError):convert_records(s,t)


if __name__=='__main__':unittest.main()
