"""Template-checked BOTW conversion. No console keys or network access."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
from dataclasses import dataclass

VERSIONS = {0x24E2: "1.0", 0x24EE: "1.1", 0x2588: "1.2", 0x29C0: "1.3",
            0x2A46: "1.3.1", 0x3EF8: "1.3.3", 0x3EF9: "1.3.4", 0x471A: "1.4",
            0x471B: "1.5", 0x471E: "1.6", 0x4730: "1.8/1.9"}
MODERN_FIELDS = {0x62133C14, 0x8DAFA42C, 0xCF031EFD, 0xF3316ABB, 0xFA050B46}
DATA = Path(__file__).parent / "data" / "hashes.csv"
TYPES = {int(row[0]): int(row[1]) for row in csv.reader(DATA.open(encoding="utf-8-sig"), delimiter=";") if len(row) >= 3}


class SaveError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class RecordFile:
    endian: str
    version: int
    records: list[tuple[int, bytes]]

    @classmethod
    def parse(cls, data: bytes) -> "RecordFile":
        if len(data) < 16 or (len(data) - 16) % 8:
            raise SaveError("Invalid BOTW record file size.")
        endian = next((e for e in ("<", ">") if struct.unpack_from(e + "I", data)[0] in VERSIONS), None)
        if endian is None:
            raise SaveError("Unknown BOTW version. TOTK progress.sav and encrypted containers are unsupported.")
        version, marker, one = struct.unpack_from(endian + "III", data)
        if marker != 0xFFFFFFFF or one != 1 or data[-4:] != b"\xff" * 4:
            raise SaveError("Invalid BOTW header or end marker.")
        records = [(struct.unpack_from(endian + "I", data, i)[0], data[i + 4:i + 8])
                   for i in range(12, len(data) - 4, 8)]
        return cls(endian, version, records)

    @property
    def platform(self) -> str:
        return "Switch" if self.endian == "<" else "Wii U"

    def stats(self) -> dict:
        values = dict(self.records)
        result = {}
        if 0x2906F327 in values:
            result["hearts"] = struct.unpack(self.endian + "I", values[0x2906F327])[0] / 4
        if 0x3ADFF047 in values:
            result["stamina"] = struct.unpack(self.endian + "f", values[0x3ADFF047])[0]
        return result


def discover(folder: Path) -> Path:
    """Accept a user save or a backup containing exactly one user save."""
    folder = folder.expanduser()
    if not folder.is_dir() or folder.is_symlink():
        raise SaveError("Select a real backup directory.")
    folder = folder.resolve()
    def valid(p):
        return (p / "option.sav").is_file() and any((p / str(i) / "game_data.sav").is_file() for i in range(8))
    if valid(folder):
        return folder
    candidates = [p.parent for p in folder.rglob("option.sav") if valid(p.parent)]
    if len(candidates) != 1:
        raise SaveError(f"Found {len(candidates)} user saves. Select the specific user directory containing option.sav and numbered slots.")
    return candidates[0]


def inspect(folder: Path) -> dict:
    root = discover(folder)
    option = RecordFile.parse((root / "option.sav").read_bytes())
    slots = []
    for i in range(8):
        f = root / str(i) / "game_data.sav"
        if not f.exists():
            continue
        game = RecordFile.parse(f.read_bytes())
        caption = root / str(i) / "caption.sav"
        if not caption.is_file():
            raise SaveError(f"Slot {i} has no caption.sav.")
        cap = RecordFile.parse(caption.read_bytes())
        if game.endian != option.endian or cap.endian != game.endian:
            raise SaveError("Mixed platforms in one backup.")
        slots.append({"slot": str(i), "version": VERSIONS[game.version], **game.stats()})
    return {"root": root, "platform": option.platform, "slots": slots}


def convert_records(source: bytes, template: bytes) -> tuple[bytes, dict]:
    src, dst = RecordFile.parse(source), RecordFile.parse(template)
    if src.endian == dst.endian:
        raise SaveError("Source and destination must be different platforms.")
    # Group repeating hashes: arrays and strings occupy multiple records.
    def group(records):
        groups = {}
        for h, v in records:
            groups.setdefault(h, []).append(v)
        return groups
    a, b = group(src.records), group(dst.records)
    removed, added = set(a) - set(b), set(b) - set(a)
    if (removed | added) - MODERN_FIELDS:
        raise SaveError("Unsupported schema difference: " + ", ".join(hex(h) for h in sorted((removed | added) - MODERN_FIELDS)))
    for h in set(a) & set(b):
        if len(a[h]) != len(b[h]):
            raise SaveError(f"Array size mismatch for {h:#010x}.")
        if h not in TYPES and h not in MODERN_FIELDS:
            raise SaveError(f"Unknown field type {h:#010x}; refusing to guess.")
    out = bytearray(struct.pack(dst.endian + "III", dst.version, 0xFFFFFFFF, 1))
    index = {}
    for h, default in dst.records:
        n = index.get(h, 0)
        index[h] = n + 1
        value = a[h][n] if h in a else default
        if h in a and TYPES.get(h, 0) < 13:
            value = value[::-1]
        out += struct.pack(dst.endian + "I", h) + value
    out += b"\xff" * 4
    parsed = RecordFile.parse(out)
    if parsed.stats() != src.stats():
        raise SaveError("Heart/stamina preservation check failed.")
    return bytes(out), {"removed": [f"{h:#010x}" for h in sorted(removed)],
                         "initialized_from_target": [f"{h:#010x}" for h in sorted(added)]}


def convert_tracker(data: bytes) -> bytes:
    # BOTW tracker: unchanged first 4 bytes, u16 at 4, bytes 6..7 unchanged,
    # then 32-bit values. Same operation in either direction.
    if len(data) != 65536:
        raise SaveError("Unsupported Hero's Path block size.")
    out = bytearray(data)
    out[4:6] = data[4:6][::-1]
    for i in range(8, len(data), 4):
        out[i:i+4] = data[i:i+4][::-1]
    return bytes(out)


def convert(source: Path, template: Path, output: Path, allow_version_change=False, progress=None) -> dict:
    src, dst = inspect(source), inspect(template)
    if src["platform"] == dst["platform"]:
        raise SaveError("Select a destination backup from the other platform.")
    output = output.expanduser().resolve()
    for root in (src["root"], dst["root"]):
        if output == root or output.is_relative_to(root) or root.is_relative_to(output):
            raise SaveError("Output must be separate from both backups, not inside them or a parent directory.")
    if output.exists():
        raise SaveError("Output already exists. Choose a new folder name.")
    files = []
    nested = []
    for p in src["root"].rglob("*"):
        if p.is_symlink():
            raise SaveError("Symbolic links are unsupported in backups.")
    for slot in src["slots"]:
        s = slot["slot"]
        for f in ("game_data.sav", "caption.sav", "caption.jpg"):
            p = src["root"] / s / f
            if p.is_file():
                files.append(p)
        nested.extend(str(p.relative_to(src["root"])) for p in (src["root"] / s).iterdir() if p.is_dir())
    for folder in ("album", "pict_book", "tracker"):
        p = src["root"] / folder
        if p.exists():
            for item in p.iterdir():
                if not item.is_file() or (folder == "tracker" and not item.name.startswith("trackblock")) or (folder != "tracker" and item.suffix.lower() != ".jpg"):
                    raise SaveError(f"Unexpected backup entry: {item.name}")
                files.append(item)
    # Plan and validate every conversion before touching output.
    plan = []
    changes = []
    experimental = False
    for i, p in enumerate(files):
        rel = p.relative_to(src["root"])
        original = p.read_bytes()
        details = {}
        if p.name in ("game_data.sav", "caption.sav"):
            target = dst["root"] / rel
            if not target.exists():
                # Never mix Master Mode and normal slot templates.
                candidates = [s for s in dst["slots"] if (int(s["slot"]) >= 6) == (int(rel.parts[0]) >= 6)]
                if not candidates:
                    raise SaveError("Destination template lacks a matching normal/Master Mode slot.")
                target = dst["root"] / candidates[0]["slot"] / p.name
            reference = target.read_bytes()
            before, after = RecordFile.parse(original), RecordFile.parse(reference)
            experimental |= before.version != after.version
            converted, details = convert_records(original, reference)
            if details["removed"] or details["initialized_from_target"]:
                experimental = True
            changes.append({"file": rel.as_posix(), **details})
        elif rel.parts[0] == "tracker":
            converted = convert_tracker(original)
            if convert_tracker(converted) != original:
                raise SaveError("Tracker roundtrip check failed.")
        else:
            converted = original
        plan.append((rel, converted, digest(original), p))
        if progress:
            progress(i+1, 2*len(files)+1, rel.as_posix())
    if experimental and not allow_version_change:
        raise SaveError("Different game versions/schema: enable experimental cross-version conversion after reviewing the preview.")
    option_path = dst["root"] / "option.sav"
    option = option_path.read_bytes()
    report = {"app": "Universal-BOTW-Save Manager", "source_platform": src["platform"],
              "target_platform": dst["platform"], "experimental": experimental,
              "game_tested": False, "options": "preserved from destination backup", "slots": src["slots"],
              "excluded_nested_directories": nested, "schema_changes": changes, "files": []}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Stage adjacent to output so final rename is on the same filesystem.
    with tempfile.TemporaryDirectory(prefix=".ubsm-", dir=output.parent) as tmp:
        stage = Path(tmp) / "result"
        payload = stage / "user-save"
        payload.mkdir(parents=True)
        for written, (rel, data, original_hash, original_path) in enumerate(plan, 1):
            dest = payload / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            if digest(dest.read_bytes()) != digest(data) or digest(original_path.read_bytes()) != original_hash:
                raise SaveError("File integrity check failed; source may have changed during conversion.")
            report["files"].append({"file": rel.as_posix(), "source_sha256": original_hash, "output_sha256": digest(data)})
            if progress:
                progress(len(files)+written, 2*len(files)+1, rel.as_posix())
        (payload / "option.sav").write_bytes(option)
        if option_path.read_bytes() != option:
            raise SaveError("Destination options changed during conversion.")
        report["files"].append({"file": "option.sav", "output_sha256": digest(option)})
        (stage / "conversion-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if output.exists():
            raise SaveError("Output appeared during conversion; refusing overwrite.")
        os.rename(stage, output)
    if progress:
        progress(2*len(files)+1, 2*len(files)+1, 'completed')
    return report
