"""End-to-end GUI smoke test using synthetic backups only. Run under Xvfb on Linux."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).parent))
from test_core import backup
from botw_manager.gui import App, PathsDialog, TargetDialog
from botw_manager.settings import LANGUAGES, Target


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        source, template, destination=(root/n for n in ('source 日本語','template','emulator-save'))
        backup(source, '>');backup(template, '<');backup(destination, '<')
        app=App(config=root/'local-config.json')
        failures=[]
        completed=[]
        def fail(error):
            failures.append(str(error))
            app.destroy()
        app.report_error=fail
        # A synthetic native-drop payload, including spaces and Japanese path text.
        app.on_drop(SimpleNamespace(data=app.tk.call('list',str(source/'0/game_data.sav'))),'source')
        app.on_drop(SimpleNamespace(data=app.tk.call('list',str(template))),'template')
        app.vars['output'].set(str(root/'converted'))
        for code, name in LANGUAGES.items():
            app.language.set(name);app.change_language();app.update()
            assert app.settings.language==code
            assert app.vars['source'].get()==str(source)
            app.choose_direction('Switch');app.update()
            assert app.vars['source'].get()==str(template)
            app.choose_direction('Wii U');app.update()
        # Rebuilding UI after modal dialogs must not retain dead button references.
        dialog=PathsDialog(app)
        editor=TargetDialog(dialog)
        editor.cancel();dialog.destroy();app.set_busy(False)
        app.settings.targets=[Target('Synthetic emulator',str(destination))]
        app.preview()
        import botw_manager.gui as gui
        ask=gui.messagebox.askyesno
        gui.messagebox.askyesno=lambda *args,**kwargs:True  # test folders only
        def finish():
            if app.copy_state=='copied' and not app.busy:
                assert (destination/'0/game_data.sav').read_bytes()==(root/'converted/user-save/0/game_data.sav').read_bytes()
                assert list(root.glob('emulator-save.ubsm-backup-*'))
                completed.append(True)
                app.destroy()
            else:
                app.after(80,finish)
        app.after(80,app.start)
        app.after(150,finish)
        app.after(15000,lambda:fail('GUI smoke test timed out'))
        try:
            app.mainloop()
        finally:
            gui.messagebox.askyesno=ask
        if failures or not completed:
            raise AssertionError(failures or 'GUI conversion and copy were not completed')
        print('GUI verified: 6 languages, 2 directions, file drops, settings dialogs, conversion and confirmed copy.')


if __name__=='__main__':main()
