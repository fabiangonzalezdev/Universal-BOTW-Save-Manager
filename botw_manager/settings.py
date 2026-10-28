"""User-local preferences; never stored in the application repository."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import json
import locale
import os
from pathlib import Path
import sys
import tempfile

LANGUAGES = {"en": "English", "fr": "Français", "de": "Deutsch", "ja": "日本語", "es": "Español", "pt_BR": "Português (Brasil)"}
KINDS = ("Ryujinx", "Eden", "Savage Wind", "Cemu", "yuzu", "suyu", "Sudachi", "Custom")


def default_language():
    code = (locale.getlocale()[0] or "en").replace("-", "_")
    if code.startswith("pt"):
        return "pt_BR"
    return code.split("_")[0] if code.split("_")[0] in LANGUAGES else "en"


def config_path():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "Universal-BOTW-Save-Manager" / "config.json"


@dataclass
class Target:
    name: str
    path: str
    platform: str = "Switch"
    kind: str = "Custom"
    enabled: bool = True

    def validate(self):
        if not self.name.strip() or not self.path.strip():
            raise ValueError("Destination name and path are required.")
        if self.platform not in ("Switch", "Wii U") or self.kind not in KINDS or type(self.enabled) is not bool:
            raise ValueError("Invalid destination settings.")


@dataclass
class Settings:
    language: str = field(default_factory=default_language)
    targets: list[Target] = field(default_factory=list)


def load(path=None):
    path = Path(path) if path is not None else config_path()
    if not path.exists():
        return Settings()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("targets"), list):
        raise ValueError("Unsupported or damaged settings file.")
    language = data.get("language", "en")
    if language not in LANGUAGES:
        language = "en"
    targets = []
    for item in data["targets"]:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) for k in ("name", "path", "platform", "kind")):
            raise ValueError("Invalid saved destination.")
        target = Target(**{k: item[k] for k in ("name", "path", "platform", "kind")}, enabled=item.get("enabled", True))
        target.validate()
        targets.append(target)
    return Settings(language, targets)


def save(settings, path=None):
    path = Path(path) if path is not None else config_path()
    if settings.language not in LANGUAGES:
        raise ValueError("Unknown language.")
    for target in settings.targets:
        target.validate()
    data = {"schema_version": 1, "language": settings.language, "targets": [asdict(t) for t in settings.targets]}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".config-", delete=False) as f:
            temporary = Path(f.name)
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
