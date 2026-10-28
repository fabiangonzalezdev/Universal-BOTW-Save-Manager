# Universal-BOTW-Save Manager v0.2.0-alpha.2

## New

- Language dropdown with native names: English, Français, Deutsch, 日本語, Español, Português (Brasil). The selected language is remembered locally.
- Two conversion cards with original Wii U/Switch schematic icons and explicit Wii U → Switch / Switch → Wii U directions.
- Choose a backup folder or drop a save file from a complete backup onto either input.
- Separate conversion and copying progress/status indicators.
- Settings → Other paths: Ryujinx, Eden, Savage Wind, Cemu and custom save destinations.
- Optional post-conversion copying, only after confirmation, to enabled targets with matching formats. Savage Wind game folders resolve to `save/` when present.
- Prior target folders are retained as timestamped sibling backups; staged writes, hash checks and rollback protect replacements. Reports record each result. No automatic backup deletion.

## Validation and limits

Synthetic conversion/copy regression tests and an end-to-end GUI test exercise languages, direction changes, dropped paths, settings dialogs and confirmed copying using temporary saves. The Windows binary includes native drag-and-drop support. Platform-specific CI results and artifacts are available in Actions.

Physical-console and real port gameplay validation are still required. Cross-version conversion remains experimental. This release does not edit player stats, access Nintendo Cloud or install CFW. Binaries are unsigned.

## Español

Selector de seis idiomas, tarjetas Wii U ↔ Switch, arrastrar saves, configuración de destinos y copia opcional con barra independiente. Antes de copiar, se muestran los destinos y se pide confirmación. Los saves anteriores quedan respaldados junto a cada destino. No se copiaron ni modificaron los juegos instalados del usuario durante el desarrollo.
