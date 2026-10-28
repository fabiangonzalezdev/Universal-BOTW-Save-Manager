"""Explicit, verified deployment to user-selected save directories, with rollback."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import shutil
import tempfile
import uuid
from .core import RecordFile, SaveError, digest, discover, inspect

MANAGED = {str(i) for i in range(8)} | {"option.sav", "album", "pict_book", "tracker"}


def save_input(value):
    p = Path(value).expanduser()
    if p.is_file():
        if p.name not in {"game_data.sav", "caption.sav", "option.sav"}:
            raise SaveError("Drop a BOTW .sav file from a complete backup, or the backup directory.")
        for parent in (p.parent, p.parent.parent):
            if (parent / "option.sav").is_file():
                return discover(parent)
        raise SaveError("This file is not inside a complete backup. option.sav and the slot files are required.")
    return discover(p)


def reject_links(root):
    if root.is_symlink() or any(p.is_symlink() for p in root.rglob("*")):
        raise SaveError("Symbolic links are unsupported in save destinations.")


def resolve_target(target, platform, protected=()):
    target.validate()
    if target.platform != platform:
        raise SaveError("Destination platform does not match the converted save.")
    selected = Path(target.path).expanduser()
    if target.kind == "Savage Wind" and (selected / "save").is_dir():
        selected = selected / "save"
    if not selected.is_dir():
        raise SaveError(f"Destination must be an existing save directory: {selected}")
    reject_links(selected)
    if target.kind == "Savage Wind" and not (selected / "option.sav").is_file():
        profiles = [p for p in selected.iterdir() if p.is_dir() and re.fullmatch(r"save_\d+", p.name) and (p / "option.sav").is_file()]
        if len(profiles) == 1:
            selected = profiles[0]
        elif len(profiles) > 1:
            raise SaveError("Savage Wind has multiple save profiles. Select the intended save_N folder explicitly.")
        elif any(selected.iterdir()) or not re.fullmatch(r"save_\d+", selected.name):
            raise SaveError("Initialize a Savage Wind save first, then select its save folder or save_N profile.")
    dest = selected.resolve()
    if dest == Path(dest.anchor) or dest == Path.home().resolve():
        raise SaveError("A filesystem root or home directory cannot be a save destination.")
    for path in protected:
        root = Path(path).resolve()
        if dest == root or dest.is_relative_to(root) or root.is_relative_to(dest):
            raise SaveError("Destination overlaps a source backup, template or conversion output.")
    if any(dest.iterdir()):
        if not (dest / "option.sav").is_file():
            raise SaveError("Select the actual save directory, not the game installation or emulator root.")
        existing = inspect(dest)
        if existing["root"] != dest or existing["platform"] != platform:
            raise SaveError("Existing destination save is for another platform or user directory.")
    return dest


def plan_targets(targets, payload, platform, protected=()):
    """Validate all targets before asking confirmation or writing any file."""
    roots = [Path(payload), *map(Path, protected)]
    plans = []
    for target in targets:
        if not target.enabled or target.platform != platform:
            continue
        dest = resolve_target(target, platform, roots)
        for other in plans:
            old = other[1]
            if dest == old or dest.is_relative_to(old) or old.is_relative_to(dest):
                raise SaveError("Configured destinations overlap or repeat. Select each save directory once.")
        plans.append((target, dest))
    return plans


def verified_payload(output):
    output = Path(output).resolve()
    payload = output / "user-save"
    reject_links(payload)
    report = json.loads((output / "conversion-report.json").read_text(encoding="utf-8"))
    expected = {f["file"]: f["output_sha256"] for f in report["files"]}
    actual = {p.relative_to(payload).as_posix(): p for p in payload.rglob("*") if p.is_file()}
    if expected.keys() != actual.keys():
        raise SaveError("Converted payload changed: file list no longer matches the conversion report.")
    for rel, p in actual.items():
        if digest(p.read_bytes()) != expected[rel]:
            raise SaveError(f"Converted payload integrity mismatch: {rel}")
    platform = inspect(payload)["platform"]
    if platform != report["target_platform"]:
        raise SaveError("Conversion report platform mismatch.")
    return payload, platform, expected


def copy_one(payload, dest, expected, progress=None):
    """Stage new managed files; retain the full old directory as a sibling backup."""
    payload, dest = Path(payload).resolve(), Path(dest).resolve()
    reject_links(dest)
    old_files = [p for p in dest.rglob("*") if p.is_file()]
    old_hashes = {p.relative_to(dest).as_posix(): digest(p.read_bytes()) for p in old_files}
    backup = dest.parent / f"{dest.name}.ubsm-backup-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    if backup.parent.resolve() != dest.parent or backup.exists():
        raise SaveError("Invalid backup path.")
    with tempfile.TemporaryDirectory(prefix=".ubsm-copy-", dir=dest.parent) as tmp:
        stage = Path(tmp) / "new-save"
        stage.mkdir()
        # Keep non-save metadata in place in the replacement directory.
        for entry in dest.iterdir():
            if entry.name not in MANAGED:
                target = stage / entry.name
                if entry.is_dir():
                    shutil.copytree(entry, target)
                else:
                    shutil.copy2(entry, target)
        total = len(expected)
        for n, (rel, checksum) in enumerate(expected.items(), 1):
            src, target = payload / rel, stage / rel
            if Path(rel).is_absolute() or ".." in Path(rel).parts or not src.resolve().is_relative_to(payload):
                raise SaveError("Unsafe payload path.")
            target.parent.mkdir(parents=True, exist_ok=True)
            data = src.read_bytes()
            if digest(data) != checksum:
                raise SaveError("Payload changed while copying.")
            target.write_bytes(data)
            if digest(target.read_bytes()) != checksum:
                raise SaveError("Destination verification failed.")
            if progress:
                progress(n, total, rel)
        # Do not replace a save changed by a running game during staging.
        current = {p.relative_to(dest).as_posix(): digest(p.read_bytes()) for p in dest.rglob("*") if p.is_file()}
        if current != old_hashes:
            raise SaveError("Destination changed during copying. Close the game and retry.")
        os.rename(dest, backup)
        try:
            os.rename(stage, dest)
        except BaseException as e:
            try:
                os.rename(backup, dest)
            except OSError as rollback:
                raise SaveError(f"Copy stopped; restore your original from {backup}. Rollback failed: {rollback}") from e
            raise
    return backup


def deliver(output, targets, protected=(), progress=None):
    payload, platform, expected = verified_payload(output)
    plans = plan_targets(targets, payload, platform, [output, *protected])
    results = []
    for index, (target, dest) in enumerate(plans):
        def notify(n, total, rel):
            if progress:
                progress(index * len(expected) + n, len(plans) * len(expected), f"{target.name}: {rel}")
        try:
            backup = copy_one(payload, dest, expected, notify)
            results.append({"name": target.name, "destination": str(dest), "backup": str(backup), "success": True})
        except Exception as e:
            results.append({"name": target.name, "destination": str(dest), "success": False, "error": str(e)})
    (Path(output) / "copy-report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results
