# v0.3.0-alpha.1

Brown cloud interface, bundled Open Sans, gold console silhouettes, multi-profile BOTW discovery, Cemu copy confirmation and final output-folder prompt. See docs/DISCOVERY.md for search scope.

# Changelog

## 0.2.1-alpha.1 — 2026-10-28

- Original sword artwork as editable SVG, PNG, multi-resolution Windows ICO and macOS ICNS.
- Embedded EXE/application icon and native window icon.
- Versioned distribution ZIPs with a single application folder, README, release notes, licenses and VERSION.txt.
- Local releases/v<VERSION>/ folders contain ZIP, SHA-256 and a bilingual upload README; binaries stay out of Git.
- One-command Windows build script and a shared native-platform packager for CI.

## 0.2.0-alpha.2 — 2026-10-28

- Normalize temporary-path expectations in Windows/macOS tests (short names and /private aliases). Application path resolution remains unchanged.
- Includes all multilingual UI and optional save-delivery features from alpha.1.

## 0.2.0-alpha.1 — 2026-10-28

- Native-name language selector: English, Français, Deutsch, 日本語, Español, Português (Brasil).
- Direction cards with original Wii U/Switch icons and automatic input swapping.
- Native folder/file drops select a complete backup from its .sav file.
- Persistent local Other paths profiles for Ryujinx, Eden, Savage Wind, Cemu and custom targets.
- Confirmed copying, independent progress, SHA-256 validation, full previous-save backups and replacement rollback.
- Savage Wind supports both direct save folders and unique save/save_N profiles, without confusing backup siblings with profiles.
- Regression tests cover locale completeness, drops, Unicode config, invalid targets, tampering, rollback and changing destination saves. An end-to-end GUI test uses temporary synthetic data only.
- No installed game or emulator save was modified during development. Physical gameplay validation remains pending.

## 0.1.0-alpha.1 — 2026-10-28

- First Windows-priority desktop preview with English/Spanish labels.
- Wii U ↔ Switch conversion checked against a destination backup.
- Separate output, source hash rechecks and SHA-256 manifest.
- Known newer-format field adaptation behind explicit experimental opt-in.
- Native destination options retained; photos and tracker handled separately.
- Synthetic regression suite and Windows packaging smoke tests.
- Full 897160-byte public reference save roundtrip checked locally (112143 records, exact byte equality). This is structural validation, not console validation.
- GitHub Actions builds for Windows x64, Linux x64 and macOS ARM64.

Known limitations: no physical console validation for this app yet; no automatic restore, Nintendo Cloud integration or game-stat editing. Unknown schemas are rejected. No code signing or macOS notarization.
