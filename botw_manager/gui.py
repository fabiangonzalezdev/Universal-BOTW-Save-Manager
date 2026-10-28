"""Six-language desktop UI with native file drops and explicit save delivery."""
import argparse
from copy import deepcopy
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, COPY, TkinterDnD
from . import __version__
from .core import SaveError, inspect, convert
from .delivery import save_input, plan_targets, verified_payload, deliver
from . import settings as preferences
from .settings import LANGUAGES, KINDS, Target
from .i18n import text

BG, PANEL, TEXT, MUTED, ACCENT = "#101920", "#192630", "#eef4ed", "#a6b6bf", "#c8ac6c"


class App(TkinterDnD.Tk):
    def __init__(self, config=None):
        super().__init__()
        self.title("Universal-BOTW-Save Manager")
        icon_dir = Path(__file__).parent / "data"
        self.app_icon = tk.PhotoImage(file=str(icon_dir / "app-icon.png"))
        self.iconphoto(True, self.app_icon)
        if sys.platform == "win32":
            self.iconbitmap(default=str(icon_dir / "app-icon.ico"))
        width, height = min(1100, self.winfo_screenwidth()-70), min(960, self.winfo_screenheight()-90)
        self.geometry(f"{width}x{height}")
        self.minsize(860, 640)
        self.configure(bg=BG)
        self.config_file = Path(config) if config else preferences.config_path()
        self.settings_error = None
        try:
            self.settings = preferences.load(self.config_file)
        except (ValueError, OSError, TypeError) as e:
            self.settings = preferences.Settings()
            self.settings_error = str(e)
        self.events = queue.Queue()
        self.busy = False
        self.last_output = None
        self.last_protected = ()
        self.direction = "Wii U"
        self.vars = {k: tk.StringVar() for k in ("source", "template", "output")}
        self.experimental = tk.BooleanVar()
        self.language = tk.StringVar(value=LANGUAGES[self.settings.language])
        self.conversion_state = "ready"
        self.copy_state = "not_copied"
        self.log_lines = []
        self.controls = []
        self.cards = []
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build()
        for var in self.vars.values():
            var.trace_add("write", self.input_changed)
        self.write(self.t("initial"))
        if self.settings_error:
            self.write(self.t("config_error")+"\n"+self.settings_error)
        self.after(100, self.poll)

    def t(self, key, **values):
        return text(self.settings.language, key, **values)

    @property
    def destination_platform(self):
        return "Switch" if self.direction == "Wii U" else "Wii U"

    def label(self, parent, value, size=10, color=TEXT, **kwargs):
        font = "Yu Gothic UI" if self.settings.language == "ja" else "Segoe UI"
        return tk.Label(parent, text=value, bg=parent["bg"], fg=color, font=(font, size), **kwargs)

    def button(self, parent, title, command, primary=False):
        btn = tk.Button(parent, text=title, command=command, bg=ACCENT if primary else "#2c404c", fg=BG if primary else TEXT,
                        activebackground="#dfc88d", activeforeground=BG, relief="flat", bd=0,
                        padx=12, pady=8, cursor="hand2", font=("Segoe UI", 10, "bold"))
        if parent.winfo_toplevel() is self:
            self.controls.append(btn)
        return btn

    def build(self):
        for child in self.winfo_children():
            child.destroy()
        self.controls, self.cards = [], []
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", background=ACCENT, troughcolor=PANEL)
        head = tk.Frame(self, bg=BG, padx=24, pady=15)
        head.pack(fill="x")
        right = tk.Frame(head, bg=BG)
        right.pack(side="right", anchor="n")
        self.label(right, self.t("language"), 9, MUTED).pack(anchor="w")
        self.language_box = ttk.Combobox(right, textvariable=self.language, values=list(LANGUAGES.values()), state="readonly", width=21)
        self.language_box.pack(pady=(4, 0))
        self.language_box.bind("<<ComboboxSelected>>", self.change_language)
        self.controls.append(self.language_box)
        self.label(head, "UNIVERSAL / BOTW", 10, ACCENT).pack(anchor="w")
        self.label(head, self.t("tagline"), 22).pack(anchor="w", pady=(5, 0))
        # Scrollable main surface keeps long translations usable on short displays.
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)
        self.surface = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=self.surface.yview)
        scroll.pack(side="right", fill="y")
        self.surface.pack(side="left", fill="both", expand=True)
        self.surface.configure(yscrollcommand=scroll.set)
        content = tk.Frame(self.surface, bg=BG, padx=24)
        content_window = self.surface.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: self.surface.configure(scrollregion=self.surface.bbox("all")))
        self.surface.bind("<Configure>", lambda e: self.surface.itemconfigure(content_window, width=e.width))
        self.label(content, self.t("direction"), 10, ACCENT).pack(anchor="w", pady=(2, 8))
        cardrow = tk.Frame(content, bg=BG)
        cardrow.pack(fill="x", pady=(0, 14))
        cardrow.columnconfigure((0, 1), weight=1, uniform="direction")
        for index, source in enumerate(("Wii U", "Switch")):
            card = tk.Canvas(cardrow, height=106, bg=PANEL, highlightthickness=2, cursor="hand2", takefocus=True)
            card.grid(row=0, column=index, sticky="ew", padx=(0, 6) if index == 0 else (6, 0))
            card.bind("<Configure>", lambda e, c=card, s=source: self.draw_card(c, s))
            card.bind("<Button-1>", lambda e, s=source: self.choose_direction(s))
            card.bind("<Return>", lambda e, s=source: self.choose_direction(s))
            card.bind("<space>", lambda e, s=source: self.choose_direction(s))
            self.cards.append((card, source))
        body = tk.Frame(content, bg=PANEL, padx=18, pady=14)
        body.pack(fill="x")
        self.label(body, self.t("backups"), 10, ACCENT).pack(anchor="w", pady=(0, 10))
        for key in ("source", "template", "output"):
            platform = self.direction if key == "source" else self.destination_platform
            title = self.t(key, platform=platform) if key != "output" else self.t("output")
            row = tk.Frame(body, bg=PANEL)
            row.pack(fill="x", pady=(0, 11))
            self.label(row, title, 10).pack(anchor="w")
            self.label(row, self.t("output_hint" if key == "output" else "drop_hint"), 9, MUTED, wraplength=900, justify="left").pack(anchor="w", pady=(1, 4))
            entryrow = tk.Frame(row, bg=PANEL)
            entryrow.pack(fill="x")
            entry = tk.Entry(entryrow, textvariable=self.vars[key], bg=BG, fg=TEXT, insertbackground=TEXT,
                             relief="flat", font=("Segoe UI", 10))
            entry.pack(side="left", fill="x", expand=True, ipady=8)
            self.controls.append(entry)
            self.button(entryrow, self.t("browse"), lambda k=key: self.browse(k)).pack(side="left", padx=(7, 0))
            if key != "output":
                self.button(entryrow, self.t("file"), lambda k=key: self.browse(k, True)).pack(side="left", padx=(7, 0))
                for widget in (row, entry):
                    widget.drop_target_register(DND_FILES)
                    widget.dnd_bind("<<Drop>>", lambda e, k=key: self.on_drop(e, k))
        self.check = tk.Checkbutton(body, text=self.t("experimental"), variable=self.experimental, bg=PANEL, fg=MUTED,
                                   selectcolor=BG, activebackground=PANEL, activeforeground=TEXT, font=("Segoe UI", 10), anchor="w")
        self.check.pack(anchor="w")
        self.controls.append(self.check)
        actions = tk.Frame(content, bg=BG)
        actions.pack(fill="x", pady=12)
        self.button(actions, self.t("inspect"), self.preview).pack(side="left")
        self.convert_btn = self.button(actions, self.t("convert"), self.start, True)
        self.convert_btn.pack(side="left", padx=8)
        self.button(actions, self.t("settings"), self.paths_dialog).pack(side="right")
        self.progress_labels = {}
        self.bars = {}
        for key, title, state in (("conversion", "conversion", self.conversion_state), ("copy", "copy", self.copy_state)):
            group = tk.Frame(content, bg=BG)
            group.pack(fill="x", pady=(0, 8))
            self.label(group, self.t(title), 10).pack(side="left")
            status = self.label(group, self.t(state), 10, ACCENT)
            status.pack(side="right")
            bar = ttk.Progressbar(content, mode="determinate")
            bar.pack(fill="x", pady=(0, 7))
            self.progress_labels[key] = status
            self.bars[key] = bar
        if self.last_output:
            self.bars["conversion"]["value"] = 100
            if self.copy_state == "copied":
                self.bars["copy"]["value"] = 100
        links = tk.Frame(content, bg=BG)
        links.pack(fill="x", pady=(2, 7))
        self.result_btn = self.button(links, self.t("open"), self.open_result)
        self.result_btn.pack(side="left")
        self.copy_btn = self.button(links, self.t("copy_now"), self.ask_copy)
        self.copy_btn.pack(side="left", padx=8)
        self.log = tk.Text(content, height=5, bg=BG, fg=MUTED, relief="flat", wrap="word", font=("Consolas", 9), state="disabled")
        self.log.pack(fill="x", pady=(0, 8))
        if self.log_lines:
            self.log.configure(state="normal")
            self.log.insert("end", "\n".join(self.log_lines)+"\n")
            self.log.configure(state="disabled")
            self.log.see("end")
        self.label(self, f"v{__version__} · {self.t('footer')}", 9, MUTED).pack(pady=8)
        def wheel(event):
            if self.surface.bbox("all")[3] > self.surface.winfo_height():
                step = -int(event.delta / 120) if sys.platform == "win32" else -event.delta
                self.surface.yview_scroll(step, "units")
                return "break"
        def bind_wheel(widget):
            if not isinstance(widget, (tk.Text, ttk.Combobox, ttk.Treeview)):
                widget.bind("<MouseWheel>", wheel)
            for child in widget.winfo_children():
                bind_wheel(child)
        bind_wheel(content)
        self.set_busy(self.busy)

    def icon(self, canvas, platform, x, y, color):
        # Original schematic silhouettes, not Nintendo logos or downloaded art.
        if platform == "Wii U":
            canvas.create_rectangle(x-29, y-16, x+29, y+16, outline=color, width=2)
            canvas.create_rectangle(x-15, y-11, x+15, y+11, outline=color, width=2)
            canvas.create_line(x-25, y, x-19, y, fill=color, width=2)
            canvas.create_line(x-22, y-3, x-22, y+3, fill=color, width=2)
            canvas.create_oval(x+19, y-4, x+23, y, outline=color, fill=color)
            canvas.create_oval(x+23, y+1, x+27, y+5, outline=color, fill=color)
        else:
            canvas.create_rectangle(x-15, y-16, x+15, y+16, outline=color, width=2)
            canvas.create_rectangle(x-28, y-16, x-19, y+16, outline=color, width=2)
            canvas.create_rectangle(x+19, y-16, x+28, y+16, outline=color, width=2)
            canvas.create_oval(x-26, y-10, x-22, y-6, outline=color, fill=color)
            canvas.create_oval(x+22, y+5, x+26, y+9, outline=color, fill=color)

    def draw_card(self, canvas, source):
        canvas.delete("all")
        selected = source == self.direction
        color = ACCENT if selected else MUTED
        canvas.configure(highlightbackground=color if selected else PANEL)
        width = canvas.winfo_width()
        self.icon(canvas, source, width/2-92, 36, color)
        self.icon(canvas, "Switch" if source == "Wii U" else "Wii U", width/2+92, 36, color)
        canvas.create_text(width/2, 36, text="→", fill=color, font=("Segoe UI", 23))
        canvas.create_text(width/2, 80, text=f"{source}  →  {'Switch' if source == 'Wii U' else 'Wii U'}", fill=TEXT, font=("Segoe UI", 13, "bold"))

    def input_changed(self, *_):
        if not self.busy:
            self.last_output = None
            self.conversion_state, self.copy_state = "ready", "not_copied"
            for key, state in (("conversion", "ready"), ("copy", "not_copied")):
                self.progress_labels[key].configure(text=self.t(state))
                self.bars[key]["value"] = 0
            self.set_busy(False)

    def choose_direction(self, source):
        if self.busy or source == self.direction:
            return
        self.direction = source
        a, b = self.vars["source"].get(), self.vars["template"].get()
        self.vars["source"].set(b)
        self.vars["template"].set(a)
        self.build()

    def change_language(self, _=None):
        if self.busy:
            return
        self.settings.language = next(k for k, v in LANGUAGES.items() if v == self.language.get())
        try:
            preferences.save(self.settings, self.config_file)
        except OSError as e:
            self.report_error(e)
        self.build()

    def write(self, value):
        self.log_lines.append(value)
        self.log_lines = self.log_lines[-100:]
        self.log.configure(state="normal")
        self.log.insert("end", value+"\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def report_error(self, error):
        messagebox.showerror(self.t("error"), f"{self.t('details')}:\n{error}", parent=self)

    def browse(self, key, file=False):
        if self.busy:
            return
        if file:
            value = filedialog.askopenfilename(parent=self, title=self.t("choose_file"), filetypes=[("BOTW", "*.sav")])
        else:
            value = filedialog.askdirectory(parent=self, title=self.t("choose_output" if key == "output" else "choose_folder"))
        if value:
            try:
                p = Path(value) / "BOTW-converted" if key == "output" else save_input(value)
                self.vars[key].set(str(p))
            except (ValueError, OSError) as e:
                self.report_error(e)

    def on_drop(self, event, key):
        if self.busy:
            return
        try:
            paths = self.tk.splitlist(event.data)
            if len(paths) != 1:
                raise SaveError(self.t("single_drop"))
            self.vars[key].set(str(save_input(paths[0])))
        except (ValueError, OSError, tk.TclError) as e:
            self.report_error(e)
        return COPY

    def paths(self):
        if any(not self.vars[k].get().strip() for k in self.vars):
            raise SaveError(self.t("required"))
        source = save_input(self.vars["source"].get().strip())
        target = save_input(self.vars["template"].get().strip())
        a, b = inspect(source), inspect(target)
        if a["platform"] != self.direction or b["platform"] != self.destination_platform:
            raise SaveError(self.t("wrong_direction", source=self.direction, target=self.destination_platform))
        return source, target, Path(self.vars["output"].get().strip()), a, b

    def preview(self):
        try:
            _, _, _, a, b = self.paths()
            self.write(self.t("preview", source=a["platform"], target=b["platform"]))
            for s in a["slots"]:
                self.write(self.t("slot", slot=s["slot"], version=s["version"], hearts=s.get("hearts", "?"), stamina=s.get("stamina", "?")))
            self.write(self.t("target_versions", versions=", ".join(sorted({s["version"] for s in b["slots"]}))))
        except (ValueError, OSError) as e:
            self.report_error(e)

    def set_busy(self, busy):
        self.busy = busy
        for widget in self.controls:
            if widget == self.language_box:
                widget.configure(state="disabled" if busy else "readonly")
            else:
                widget.configure(state="disabled" if busy else "normal")
        for widget in (self.result_btn, self.copy_btn):
            widget.configure(state="normal" if not busy and self.last_output else "disabled")

    def start(self):
        if self.busy:
            return
        try:
            source, target, output, _, _ = self.paths()
        except (ValueError, OSError) as e:
            self.report_error(e)
            return
        self.set_busy(True)
        self.conversion_state, self.copy_state = "converting", "not_copied"
        self.progress_labels["conversion"].configure(text=self.t("converting"))
        self.progress_labels["copy"].configure(text=self.t("not_copied"))
        self.bars["conversion"]["value"] = self.bars["copy"]["value"] = 0
        self.write(self.t("converting"))
        allow = self.experimental.get()
        self.last_protected = (source, target)
        def task():
            try:
                result = convert(source, target, output, allow, lambda n, total, name: self.events.put(("conversion_progress", (n, total))))
                self.events.put(("converted", (output.resolve(), result)))
            except Exception as e:
                self.events.put(("conversion_error", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def ask_copy(self):
        if self.busy or not self.last_output:
            return
        try:
            payload, platform, _ = verified_payload(self.last_output)
            plans = plan_targets(self.settings.targets, payload, platform, (self.last_output, *self.last_protected))
            if not plans:
                self.write(self.t("no_targets", platform=platform))
                return
            names = "\n".join(f"• {target.name}\n  {dest}" for target, dest in plans)
            question = self.t("copy_question", platform=platform)+"\n\n"+names+"\n\n"+self.t("copy_warning")
            if not messagebox.askyesno(self.t("copy_title"), question, parent=self):
                return
            targets = deepcopy([target for target, _ in plans])
            output, protected = self.last_output, self.last_protected
            self.set_busy(True)
            self.copy_state = "copying"
            self.progress_labels["copy"].configure(text=self.t("copying"))
            self.bars["copy"]["value"] = 0
            def task():
                try:
                    results = deliver(output, targets, protected, lambda n, total, name: self.events.put(("copy_progress", (n, total))))
                    self.events.put(("copied", results))
                except Exception as e:
                    self.events.put(("copy_error", str(e)))
            threading.Thread(target=task, daemon=True).start()
        except (ValueError, OSError) as e:
            self.report_error(e)

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind.endswith("_progress"):
                    key = kind.split("_")[0]
                    self.bars[key]["value"] = data[0] / max(data[1], 1) * 100
                elif kind == "converted":
                    self.last_output, result = data
                    self.conversion_state = "converted"
                    self.progress_labels["conversion"].configure(text=self.t("converted"))
                    self.bars["conversion"]["value"] = 100
                    self.set_busy(False)
                    self.write(self.t("done", count=len(result["files"]), path=self.last_output))
                    if any(t.enabled and t.platform == result["target_platform"] for t in self.settings.targets):
                        self.after(150, self.ask_copy)
                elif kind == "copied":
                    success = bool(data) and all(item["success"] for item in data)
                    self.copy_state = "copied" if success else "failed"
                    self.progress_labels["copy"].configure(text=self.t(self.copy_state))
                    if success:
                        self.bars["copy"]["value"] = 100
                    self.set_busy(False)
                    for item in data:
                        self.write(self.t("copy_success", name=item["name"], backup=item["backup"]) if item["success"] else self.t("copy_failure", name=item["name"], error=item["error"]))
                    if not success:
                        self.report_error(self.t("copy_partial"))
                else:
                    key = "copy" if kind == "copy_error" else "conversion"
                    if key == "copy":
                        self.copy_state = "failed"
                    else:
                        self.conversion_state = "failed"
                    self.progress_labels[key].configure(text=self.t("failed"))
                    self.set_busy(False)
                    self.write(self.t("error")+": "+data)
                    self.report_error(data)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def paths_dialog(self):
        if self.busy:
            return
        PathsDialog(self)

    def open_result(self):
        if self.last_output:
            if sys.platform == "win32":
                os.startfile(str(self.last_output))
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(self.last_output)])

    def close(self):
        if self.busy:
            messagebox.showinfo(self.t("ready"), self.t("close_busy"), parent=self)
        else:
            self.destroy()


class PathsDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app, self.targets = app, deepcopy(app.settings.targets)
        self.t = app.t
        self.title(self.t("settings"))
        self.geometry("940x450")
        self.minsize(760, 400)
        self.configure(bg=PANEL, padx=16, pady=16)
        self.transient(app)
        self.grab_set()
        app.label(self, self.t("paths_help"), 10, MUTED, wraplength=880, justify="left").pack(anchor="w", pady=(0, 12))
        self.tree = ttk.Treeview(self, columns=("enabled", "name", "kind", "platform", "path"), show="headings", height=8, selectmode="browse")
        for key, width in (("enabled", 75), ("name", 130), ("kind", 110), ("platform", 80), ("path", 390)):
            self.tree.heading(key, text=self.t(key))
            self.tree.column(key, width=width, minwidth=55)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.edit())
        actions = tk.Frame(self, bg=PANEL)
        actions.pack(fill="x", pady=12)
        for key, cmd in (("add", self.add), ("edit", self.edit), ("remove", self.remove)):
            app.button(actions, self.t(key), cmd).pack(side="left", padx=(0, 7))
        app.button(actions, self.t("save"), self.save, True).pack(side="right")
        app.button(actions, self.t("cancel"), self.destroy).pack(side="right", padx=8)
        app.label(self, self.t("settings_location", path=app.config_file), 9, MUTED, wraplength=880, justify="left").pack(anchor="w")
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, target in enumerate(self.targets):
            self.tree.insert("", "end", iid=str(i), values=("✓" if target.enabled else "—", target.name, self.t("custom") if target.kind == "Custom" else target.kind, target.platform, target.path))

    def selected(self):
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def add(self):
        TargetDialog(self)

    def edit(self):
        index = self.selected()
        if index is not None:
            TargetDialog(self, index)

    def remove(self):
        index = self.selected()
        if index is not None:
            self.targets.pop(index)
            self.refresh()

    def save(self):
        updated = preferences.Settings(self.app.settings.language, self.targets)
        try:
            preferences.save(updated, self.app.config_file)
            self.app.settings = updated
            self.app.write(self.t("saved"))
            self.destroy()
        except (OSError, ValueError) as e:
            messagebox.showerror(self.t("error"), str(e), parent=self)


class TargetDialog(tk.Toplevel):
    def __init__(self, parent, index=None):
        super().__init__(parent)
        self.parent, self.index = parent, index
        self.app, self.t = parent.app, parent.t
        self.title(self.t("target_title"))
        self.geometry("760x420")
        self.configure(bg=PANEL, padx=18, pady=16)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        target = parent.targets[index] if index is not None else Target("", "", kind="Ryujinx")
        self.name, self.path = tk.StringVar(value=target.name), tk.StringVar(value=target.path)
        self.kind, self.platform = tk.StringVar(value=target.kind), tk.StringVar(value=target.platform)
        self.enabled = tk.BooleanVar(value=target.enabled)
        for key, variable in (("name", self.name), ("kind", self.kind), ("platform", self.platform), ("path", self.path)):
            self.app.label(self, self.t(key)).pack(anchor="w", pady=(8, 3))
            row = tk.Frame(self, bg=PANEL)
            row.pack(fill="x")
            if key in ("kind", "platform"):
                box = ttk.Combobox(row, textvariable=variable, values=KINDS if key == "kind" else ("Switch", "Wii U"), state="readonly")
                box.pack(fill="x")
                if key == "kind":
                    box.bind("<<ComboboxSelected>>", self.kind_changed)
            else:
                tk.Entry(row, textvariable=variable, bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat").pack(side="left", fill="x", expand=True, ipady=7)
                if key == "path":
                    self.app.button(row, self.t("browse"), self.choose).pack(side="right", padx=(8, 0))
        tk.Checkbutton(self, text=self.t("enabled"), variable=self.enabled, bg=PANEL, fg=TEXT, selectcolor=BG).pack(anchor="w", pady=10)
        actions = tk.Frame(self, bg=PANEL)
        actions.pack(fill="x")
        self.app.button(actions, self.t("save"), self.save, True).pack(side="right")
        self.app.button(actions, self.t("cancel"), self.cancel).pack(side="right", padx=8)

    def kind_changed(self, _=None):
        self.platform.set("Wii U" if self.kind.get() == "Cemu" else "Switch")
        if not self.name.get():
            self.name.set(self.kind.get())

    def cancel(self):
        self.destroy()
        self.parent.grab_set()

    def choose(self):
        path = filedialog.askdirectory(parent=self, title=self.t("path"))
        if path:
            self.path.set(path)

    def save(self):
        target = Target(self.name.get().strip(), self.path.get().strip(), self.platform.get(), self.kind.get(), self.enabled.get())
        try:
            target.validate()
            if not Path(target.path).expanduser().is_dir():
                raise ValueError(self.t("target_required"))
            if self.index is None:
                self.parent.targets.append(target)
            else:
                self.parent.targets[self.index] = target
            self.parent.refresh()
            self.destroy()
            self.parent.grab_set()
        except ValueError as e:
            messagebox.showerror(self.t("error"), str(e), parent=self)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="Check bundled resources without opening the interface")
    parser.add_argument("--smoke-test", action="store_true", help="Exercise all six UI languages and exit")
    parser.add_argument("--config", type=Path, help="Use a specific local configuration file")
    args = parser.parse_args()
    if args.self_test:
        from .core import TYPES
        from .i18n import CATALOGS
        icon_dir = Path(__file__).parent / "data"
        if not (icon_dir / "app-icon.ico").read_bytes().startswith(b"\x00\x00\x01\x00"):
            raise RuntimeError("Bundled Windows icon is missing")
        if not (icon_dir / "app-icon.png").read_bytes().startswith(b"\x89PNG"):
            raise RuntimeError("Bundled window icon is missing")
        if TYPES.get(0x5F283289) != 16 or len(CATALOGS) != 6:
            raise RuntimeError("Bundled resources are missing")
        return
    if args.smoke_test:
        with tempfile.TemporaryDirectory() as tmp:
            app = App(config=Path(tmp)/"config.json")
            languages = iter(LANGUAGES)
            def exercise():
                try:
                    code = next(languages)
                    app.language.set(LANGUAGES[code])
                    app.change_language()
                    app.choose_direction("Switch" if app.direction == "Wii U" else "Wii U")
                    app.update_idletasks()
                    app.after(80, exercise)
                except StopIteration:
                    app.destroy()
            app.after(100, exercise)
            app.mainloop()
    else:
        App(args.config).mainloop()
