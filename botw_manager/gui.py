"""Native, offline desktop interface; Python/Tk on all supported platforms."""
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from . import __version__
from .core import SaveError, inspect, convert

BG, PANEL, TEXT, MUTED, ACCENT = "#101920", "#192630", "#eef4ed", "#a6b6bf", "#c8ac6c"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal-BOTW-Save Manager")
        self.geometry("1000x800")
        self.minsize(900, 740)
        self.configure(bg=BG)
        self.events = queue.Queue()
        self.busy = False
        self.last_output = None
        self.vars = {k: tk.StringVar() for k in ("source", "template", "output")}
        self.experimental = tk.BooleanVar()
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", background=ACCENT, troughcolor=PANEL)
        self.build()
        self.after(100, self.poll)

    def label(self, parent, text, size=11, color=TEXT, **kw):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color, font=("Segoe UI", size), **kw)

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else "#2c404c",
                         fg=BG if primary else TEXT, activebackground="#dfc88d", activeforeground=BG,
                         relief="flat", bd=0, padx=17, pady=9, cursor="hand2", font=("Segoe UI", 10, "bold"))

    def build(self):
        head = tk.Frame(self, bg=BG, padx=32, pady=20)
        head.pack(fill="x")
        self.label(head, "UNIVERSAL / BOTW", 10, ACCENT).pack(anchor="w")
        self.label(head, "Your adventure. Across platforms.", 25).pack(anchor="w", pady=(7, 4))
        self.label(head, "Wii U  ⇄  Nintendo Switch     •     Offline conversion     •     Original saves stay untouched", 10, MUTED).pack(anchor="w")
        body = tk.Frame(self, bg=PANEL, padx=24, pady=18)
        body.pack(fill="x", padx=32)
        self.label(body, "01   CHOOSE YOUR BACKUPS / ELEGÍ TUS RESPALDOS", 10, ACCENT).pack(anchor="w", pady=(0, 12))
        for key, title, hint in (
            ("source", "Source backup / Respaldo de origen", "Checkpoint, JKSV or SaveMii user folder"),
            ("template", "Destination backup / Respaldo de destino", "A native save from the other platform; keeps its options and validates the format"),
            ("output", "New output folder / Carpeta de salida nueva", "The folder must not exist; neither backup will be overwritten")):
            row = tk.Frame(body, bg=PANEL)
            row.pack(fill="x", pady=(0, 12))
            self.label(row, title, 11).pack(anchor="w")
            self.label(row, hint, 9, MUTED).pack(anchor="w", pady=(1, 5))
            entryrow = tk.Frame(row, bg=PANEL)
            entryrow.pack(fill="x")
            tk.Entry(entryrow, textvariable=self.vars[key], bg=BG, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True, ipady=9)
            self.button(entryrow, "Browse…", lambda k=key: self.browse(k)).pack(side="right", padx=(8, 0))
        check = tk.Checkbutton(body, text="Allow experimental cross-version conversion / Permitir cambio de versión experimental",
                               variable=self.experimental, bg=PANEL, fg=MUTED, selectcolor=BG,
                               activebackground=PANEL, activeforeground=TEXT, font=("Segoe UI", 10))
        check.pack(anchor="w")
        actions = tk.Frame(self, bg=BG, padx=32, pady=14)
        actions.pack(fill="x")
        self.preview_btn = self.button(actions, "Inspect backups / Revisar", self.preview)
        self.preview_btn.pack(side="left")
        self.convert_btn = self.button(actions, "Convert save / Convertir", self.start, True)
        self.convert_btn.pack(side="left", padx=10)
        self.button(actions, "Open result / Abrir resultado", self.open_result).pack(side="right")
        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", padx=32)
        self.log = tk.Text(self, height=10, bg=BG, fg=MUTED, relief="flat", wrap="word",
                           font=("Consolas", 10), padx=8, pady=10, state="disabled")
        self.log.pack(fill="both", expand=True, padx=24, pady=8)
        self.write("Choose both backups, inspect the detected platforms, then convert.\nSeleccioná ambos respaldos, revisá las plataformas detectadas y convertí.\n\nThis app does not restore to consoles or access Nintendo Cloud. / No restaura en consolas ni accede a Nintendo Cloud.")
        self.label(self, f"v{__version__}  •  Preview release: console validation required / Requiere prueba en consola", 9, MUTED).pack(pady=(0, 12))

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def browse(self, key):
        if self.busy:
            return
        p = filedialog.askdirectory(title="Select backup folder" if key != "output" else "Select output parent folder")
        if p:
            if key == "output":
                p = str(Path(p) / "BOTW-converted")
            self.vars[key].set(p)

    def paths(self):
        if any(not self.vars[k].get().strip() for k in self.vars):
            raise SaveError("Select source, destination backup and a new output folder. / Completá las tres carpetas.")
        return [Path(self.vars[k].get().strip()) for k in ("source", "template", "output")]

    def preview(self):
        try:
            source, target, _ = self.paths()
            a, b = inspect(source), inspect(target)
            if a["platform"] == b["platform"]:
                raise SaveError("Both backups are from the same platform. / Ambos respaldos son de la misma plataforma.")
            self.write(f"\n{a['platform']} → {b['platform']}\nSource / Origen: {a['root']}\nDestination / Destino: {b['root']}")
            for s in a["slots"]:
                self.write(f"  Slot {s['slot']} · v{s['version']} · hearts/corazones: {s.get('hearts', '?')} · stamina: {s.get('stamina', '?')}")
            self.write("Target versions / Versiones de destino: " + ", ".join(sorted({s['version'] for s in b['slots']})))
            self.write("Options will be preserved from the target. Cross-version changes require explicit opt-in.\nSe conservan las opciones del destino. Los cambios de versión son experimentales.")
        except (OSError, ValueError) as e:
            messagebox.showerror("Inspect / Revisar", str(e))

    def start(self):
        if self.busy:
            return
        try:
            source, target, output = self.paths()
        except ValueError as e:
            messagebox.showerror("Convert", str(e))
            return
        self.busy = True
        self.convert_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")
        allow = self.experimental.get()
        self.write("\nValidating and converting… / Validando y convirtiendo…")
        def task():
            try:
                report = convert(source, target, output, allow, lambda n, total, name: self.events.put(("progress", (n, total, name))))
                self.events.put(("done", (output, report)))
            except Exception as e:
                self.events.put(("error", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "progress":
                    n, total, _ = data
                    self.progress["value"] = n / max(total, 1) * 100
                else:
                    self.busy = False
                    self.convert_btn.configure(state="normal")
                    self.preview_btn.configure(state="normal")
                    if kind == "done":
                        self.last_output, report = data
                        self.write(f"SUCCESS / COMPLETADO: {self.last_output}\n{len(report['files'])} files verified. Restore user-save with your console save manager.\nArchivos verificados. Restaurá user-save con el gestor de tu consola.\nConsole test still required / Falta prueba en consola.")
                    else:
                        self.write("ERROR: " + data)
                        messagebox.showerror("Conversion stopped / Conversión detenida", data)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def open_result(self):
        if not self.last_output:
            return
        p = str(self.last_output)
        if sys.platform == "win32":
            os.startfile(p)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", p])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="Check bundled resources without opening a window")
    parser.add_argument("--smoke-test", action="store_true", help="Open the UI, then close automatically")
    args = parser.parse_args()
    if args.self_test:
        from .core import TYPES
        if not TYPES or TYPES.get(0x5F283289) != 16:
            raise RuntimeError("Bundled field types are missing")
        return
    app = App()
    if args.smoke_test:
        app.after(1000, app.destroy)
    app.mainloop()
