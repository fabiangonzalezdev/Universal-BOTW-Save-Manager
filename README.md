<p align="center"><img src="docs/banner.svg" alt="Universal-BOTW-Save Manager — Wii U ↔ Switch" width="100%"></p>

<h1 align="center">Universal-BOTW-Save Manager</h1>
<p align="center">A visual, offline save converter for <em>The Legend of Zelda: Breath of the Wild</em>.</p>
<p align="center"><img alt="Status" src="https://img.shields.io/badge/status-alpha-c8ac6c"> <img alt="Windows first" src="https://img.shields.io/badge/Windows-first-2879bd"> <img alt="Platforms" src="https://img.shields.io/badge/macOS%20%7C%20Linux-build%20targets-536b76"> <img alt="License" src="https://img.shields.io/badge/license-MIT-4a8b71"></p>
<p align="center"><a href="README.es.md">Español</a> · <a href="https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases">Downloads</a> · <a href="docs/FORMAT.md">Format and compatibility</a></p>

> [!IMPORTANT]
> **Early preview, developed with AI assistance and human direction.** Automated tests verify file handling, roundtrips and preservation of values. Real-console validation is still required. “Universal” is the project name, not a promise of support for every save, mod or game version.

## What it does

Convert **Wii U → Switch** or **Switch → Wii U** using a native backup from the destination platform as a structural template. The desktop interface detects the platforms, previews slots and player stats, then writes a separate output folder and a SHA-256 report. Original backups stay untouched.

- Checkpoint, JKSV and SaveMii **extracted user saves**.
- Numbered save slots, screenshots, album, compendium and Hero's Path blocks.
- Preserves hearts, stamina, inventory and other shared record values; this is not a stat editor.
- Keeps `option.sav` from the destination backup.
- Bilingual English/Spanish interface; no accounts, telemetry, console keys or network needed by the app.

> [!WARNING]
> Cross-version conversion is **experimental and disabled by default**. The five identified newer Switch fields can be removed when absent from the destination, or initialized from the destination template when missing from the source. Other schema differences are rejected. Neither a successful conversion nor a matching header proves that the game will load the save.

## Getting started

1. Download the **Windows x64 ZIP** from [Releases](https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases), extract it and launch `Universal-BOTW-Save-Manager.exe`. Python is not required for packaged builds. Builds are unsigned.
2. **Source backup:** choose your extracted user folder, containing `option.sav` and numbered slots such as `0/game_data.sav`. If a SaveMii backup includes several users, select the intended user explicitly.
3. **Destination backup:** choose a native save made by the target game/version on the other platform. This supplies the schema and native settings; its gameplay progress is not merged into the source save. Only the identified missing newer-format fields use template defaults.
4. **New output folder:** choose a parent folder; the app proposes `BOTW-converted`. Edit the path if necessary. The output directory must not already exist or overlap either backup.
5. Click **Inspect backups**. Review direction, game version, hearts and stamina. Enable experimental conversion only when deliberately changing versions.
6. Click **Convert save**. Read `conversion-report.json`; restore the contents of `user-save/` with your console save manager using a new backup slot and the correct user. The app does not write to console storage or upload Nintendo Cloud saves.
7. Load the game and check your progress before making a new in-game save. Retain the original backups until the destination has been validated.

## What you need

- Your own **BOTW save backups from both platforms**. A destination backup is mandatory; no reference game saves are distributed.
- A compatible game update and the DLC needed by your save on the target console.
- Windows 10/11 x64 for the first packaged build. macOS ARM64 and Linux x64 are separate CI build targets; see the actual release assets and workflow results for availability.
- For source execution: Python 3.11+ with Tk (Python 3.12 recommended). Linux may need `python3-tk` from its package manager.

Tears of the Kingdom is not supported. Do not select `progress.sav`, raw encrypted NAND save containers, or console keys. The app intentionally does not automate Nintendo Cloud, CFW installation or console restoration.

## Status

| Component | Status | Meaning |
|---|---|---|
| Windows desktop interface | Implemented | Native Tk interface; source UI smoke-tested locally |
| Wii U ↔ Switch shared records | Implemented | Uses destination schema and preserves string byte order |
| Newer Switch → Wii U 1.5 | Experimental | Five identified extra fields; opt-in required |
| Wii U → newer Switch | Experimental | Five identified missing fields use destination values |
| Unknown fields / array changes | Rejected | No guessing or silent truncation |
| macOS / Linux packaging | CI configured | Requires successful native runner build; not locally hardware-tested |
| Physical console load | Pending | No claim of end-to-end hardware validation for this app |

## Before reporting a bug

Use the newest release, search existing issues, and include OS, app version, source/target game versions, save-manager names and the exact error. `conversion-report.json` contains record changes, slot stats and hashes rather than absolute source paths. Review it before sharing. **Never upload keys, full console backups, account credentials or serial numbers.** Share personal saves only if you intend to make their contents public.

## Build from source

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
python main.py
python build.py
```

The binary is generated in `dist/`. Build on the target OS; PyInstaller does not cross-compile. On tag pushes, GitHub Actions tests and builds Windows x64, Linux x64 and macOS ARM64, then publishes ZIPs and SHA-256 files as a prerelease after all build jobs pass. A manual workflow run creates artifacts without publishing a release.

## Roadmap

- Physical Wii U/Switch validation matrix and additional fixtures supplied privately by testers.
- Richer preview, backup comparison and optional console-specific packaging.
- Signed/notarized builds and additional architectures.
- More schemas only when their semantics are understood and tested.

## Credits and license

Original application code: MIT. The field-type table is from [Marc Robledo's savegame-editors](https://github.com/marcrobledo/savegame-editors) (MIT), with datamining credited there to MrCheeze. Format research and conversion tooling: [ZeldaMods](https://zeldamods.org/wiki/Save_Files) and [BotW Save Manager](https://github.com/DeltaJordan/BotW-Save-Manager). The latter is a reference, not bundled application code. README presentation inspired by [SavageWindRecomp](https://github.com/Revivedx/SavageWindRecomp); no branding or game assets copied. See [third-party notices](THIRD_PARTY_NOTICES.md).

Independent fan utility; not affiliated with Nintendo. No game binaries, keys, firmware, personal saves or game artwork are included.
