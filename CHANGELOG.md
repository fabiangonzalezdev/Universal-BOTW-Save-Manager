# Changelog

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
