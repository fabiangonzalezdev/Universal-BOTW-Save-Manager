from pathlib import Path
from string import Formatter
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from test_core import backup, fixture
from botw_manager import settings
from botw_manager.core import SaveError, convert
from botw_manager.delivery import save_input, resolve_target, plan_targets, verified_payload, copy_one, deliver
from botw_manager.i18n import CATALOGS, EN, text
from botw_manager.settings import Settings, Target


class LanguageSettingsTests(unittest.TestCase):
    def test_six_complete_catalogs_and_matching_format_parameters(self):
        self.assertEqual(set(CATALOGS), set(settings.LANGUAGES))
        for code, catalog in CATALOGS.items():
            self.assertEqual(set(catalog), set(EN), code)
            for key, translated in catalog.items():
                expected = {name for _, name, _, _ in Formatter().parse(EN[key]) if name}
                actual = {name for _, name, _, _ in Formatter().parse(translated) if name}
                self.assertEqual(actual, expected, (code, key))
                self.assertTrue(translated)
                self.assertTrue(text(code, key, **{n: "sample" for n in actual}))

    def test_settings_roundtrip_unicode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"config.json"
            cfg = Settings("ja", [Target("冒険 / São Paulo", str(Path(tmp)/"Juegos 日本語"), kind="Eden")])
            settings.save(cfg, path)
            self.assertEqual(settings.load(path), cfg)
            self.assertIn("冒険", path.read_text(encoding="utf-8"))

    def test_invalid_config_rejected_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"config.json"
            original = '{"targets": "broken"}'
            p.write_text(original)
            with self.assertRaises(ValueError): settings.load(p)
            self.assertEqual(p.read_text(), original)


class DeliveryTests(unittest.TestCase):
    def setup_case(self, root):
        root = Path(root)
        source, template, output, dest = (root / n for n in ("source", "template", "result", "emulator-save"))
        backup(source, ">")
        backup(template, "<")
        convert(source, template, output)
        backup(dest, "<")
        return source, template, output, dest

    def test_file_drop_finds_complete_backup_and_rejects_isolated_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"save 日本語"
            backup(p, ">")
            self.assertEqual(save_input(p/"0/game_data.sav"), p)
            self.assertEqual(save_input(p/"option.sav"), p)
            lone = Path(tmp)/"game_data.sav"
            lone.write_bytes(fixture("<"))
            with self.assertRaises(SaveError):save_input(lone)

    def test_savage_wind_game_folder_resolves_only_save_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)/"Savage Wind"; game.mkdir()
            backup(game/"save", "<")
            (game/"game.bin").write_bytes(b'keep')
            target = Target("Savage Wind", str(game), kind="Savage Wind")
            self.assertEqual(resolve_target(target, "Switch"), game/"save")
            self.assertEqual((game/"game.bin").read_bytes(), b'keep')

    def test_savage_wind_save_profile_and_backup_siblings(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)/"Savage Wind";(game/"save").mkdir(parents=True)
            backup(game/"save/save_0", "<")
            backup(game/"save/save_0.ubsm-backup-old", "<")
            target=Target("Savage Wind",str(game),kind="Savage Wind")
            self.assertEqual(resolve_target(target,"Switch"),game/"save/save_0")
            backup(game/"save/save_1","<")
            with self.assertRaises(SaveError):resolve_target(target,"Switch")
            target.path=str(game/"save/save_0")
            self.assertEqual(resolve_target(target,"Switch"),game/"save/save_0")

    def test_savage_wind_empty_save_root_requires_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)/"Savage Wind";(game/"save").mkdir(parents=True)
            with self.assertRaises(SaveError):resolve_target(Target("port",str(game),kind="Savage Wind"),"Switch")

    def test_non_save_installation_wrong_platform_and_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest = self.setup_case(tmp)
            for folder in (a,b,out,out/"user-save"):
                with self.assertRaises(SaveError):
                    resolve_target(Target("bad", str(folder)), "Switch", (a,b,out))
            game=Path(tmp)/"game";game.mkdir();(game/"app.exe").write_bytes(b'app')
            with self.assertRaises(SaveError):resolve_target(Target("bad", str(game)), "Switch")
            with self.assertRaises(SaveError):resolve_target(Target("bad", str(dest)), "Wii U")

    def test_duplicate_targets_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            with self.assertRaises(SaveError):
                plan_targets([Target("one",str(dest)),Target("two",str(dest))],out/"user-save","Switch",(a,b,out))

    def test_copy_preserves_previous_save_metadata_and_removes_stale_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            old=fixture('<',hearts=80)
            (dest/"0/game_data.sav").write_bytes(old)
            (dest/"metadata.txt").write_text("emulator metadata")
            (dest/"1").mkdir()
            (dest/"1/game_data.sav").write_bytes(old)
            (dest/"1/caption.sav").write_bytes(old)
            updates=[]
            result=deliver(out,[Target("Eden",str(dest),kind="Eden")],(a,b),lambda n,total,name:updates.append((n,total)))
            self.assertTrue(result[0]["success"])
            original=Path(result[0]["backup"])
            self.assertEqual((original/"0/game_data.sav").read_bytes(),old)
            self.assertTrue((original/"1/game_data.sav").is_file())
            self.assertFalse((dest/"1").exists())
            self.assertEqual((dest/"metadata.txt").read_text(),"emulator metadata")
            self.assertEqual((dest/"0/game_data.sav").read_bytes(),(out/"user-save/0/game_data.sav").read_bytes())
            self.assertEqual(updates[-1][0],updates[-1][1])
            self.assertTrue((out/"copy-report.json").is_file())

    def test_tampered_payload_is_not_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            original=(dest/"0/game_data.sav").read_bytes()
            (out/"user-save/0/game_data.sav").write_bytes(b'tampered')
            with self.assertRaises(SaveError):deliver(out,[Target("Eden",str(dest))],(a,b))
            self.assertEqual((dest/"0/game_data.sav").read_bytes(),original)
            self.assertFalse(list(Path(tmp).glob("*.ubsm-backup-*")))

    def test_failed_replacement_rolls_back_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            payload,_,expected=verified_payload(out)
            original=(dest/"0/game_data.sav").read_bytes()
            rename=os.rename
            calls=[]
            def fail_second(src,dst):
                calls.append((src,dst))
                if len(calls)==2:raise OSError("simulated locked destination")
                rename(src,dst)
            with patch("botw_manager.delivery.os.rename",side_effect=fail_second):
                with self.assertRaises(OSError):copy_one(payload,dest,expected)
            self.assertEqual((dest/"0/game_data.sav").read_bytes(),original)
            self.assertEqual(len(calls),3)

    def test_game_changes_during_copy_prevent_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            payload,_,expected=verified_payload(out)
            changed=fixture('<',hearts=60)
            def update_game(n,total,rel):
                if n==1:(dest/"0/game_data.sav").write_bytes(changed)
            with self.assertRaises(SaveError):copy_one(payload,dest,expected,update_game)
            self.assertEqual((dest/"0/game_data.sav").read_bytes(),changed)
            self.assertFalse(list(Path(tmp).glob("*.ubsm-backup-*")))

    def test_empty_destination_and_disabled_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            empty=Path(tmp)/"new-save";empty.mkdir()
            profiles=[Target("new",str(empty)),Target("disabled",str(dest),enabled=False)]
            results=deliver(out,profiles,(a,b))
            self.assertEqual(len(results),1)
            self.assertTrue(results[0]["success"])
            self.assertTrue((empty/"option.sav").is_file())

    @unittest.skipIf(os.name=="nt","Windows symlink privilege varies")
    def test_symlink_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b,out,dest=self.setup_case(tmp)
            link=Path(tmp)/"link";link.symlink_to(dest,target_is_directory=True)
            with self.assertRaises(SaveError):resolve_target(Target("link",str(link)),"Switch")


if __name__=="__main__":unittest.main()
