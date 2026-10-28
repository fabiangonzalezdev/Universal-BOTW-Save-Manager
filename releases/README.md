# Releases / Distribuciones

This directory contains release documentation and local build outputs. **ZIPs and hashes are uploaded as GitHub release assets, not committed to the source repository.**

Esta carpeta contiene la documentación y las distribuciones locales. **Los ZIP y hashes se adjuntan a los releases de GitHub; no se suben como código al repositorio.**

## Windows: build the EXE and ZIP / Compilar EXE y ZIP

Install Python 3.12 with Tk, open PowerShell in the project folder, then run:
Instalá Python 3.12 con Tk, abrí PowerShell en la carpeta del proyecto y ejecutá:

```powershell
.\build_windows.ps1
```

Or run each step manually / O ejecutá los pasos manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe build.py
.\.venv\Scripts\python.exe package_release.py --platform windows-x64
```

- EXE: `dist/Universal-BOTW-Save-Manager.exe`, with an embedded original sword icon.
- ZIP + SHA-256 + README: `releases/v<VERSION>/`.
- The ZIP contains one versioned application folder with the EXE, English/Spanish README, release notes, guides, icon artwork, licenses and `VERSION.txt`.
- El ZIP contiene una carpeta de esa versión con el EXE, README en inglés/español, notas, guías, arte del icono, licencias y `VERSION.txt`.

The icon sources are `assets/sword.svg` and `assets/sword.png`. Generated ICO/ICNS/PNG files are in `botw_manager/data/`. To regenerate them: `python tools/generate_icon.py` (Pillow is included in build requirements).

El icono original está en `assets/sword.svg` y `assets/sword.png`. Los archivos ICO/ICNS/PNG generados están en `botw_manager/data/`. Para regenerarlos: `python tools/generate_icon.py` (Pillow está incluido en las dependencias de compilación).

## Publish / Publicar

1. Commit and push the source and release documentation. / Subí el código y la documentación con Git.
2. Create a tag matching the app version, such as `v0.2.1-alpha.1`. / Creá un tag igual a la versión de la app.
3. GitHub Actions tests and builds all platforms and uploads their ZIPs and hashes to a prerelease. / GitHub Actions prueba y compila todas las plataformas y publica los ZIP y hashes en un prerelease.
4. For a manual release, use the notes in `RELEASE_NOTES.md` and attach only the intended version's ZIP and `.sha256` files. / Para un release manual, usá las notas de `RELEASE_NOTES.md` y adjuntá solo el ZIP y hash de esa versión.

## Release index / Índice

| Version | Changes / Cambios |
|---|---|
| [v0.2.1-alpha.1](https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases/tag/v0.2.1-alpha.1) | Original sword EXE/window icon; versioned ZIP bundles and release-folder README / Icono de espada y distribuciones por versión |
| [v0.2.0-alpha.2](https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases/tag/v0.2.0-alpha.2) | Six languages, native drops and optional emulator/port copying / Seis idiomas, arrastrar saves y copia a emuladores/ports |
| [v0.1.0-alpha.1](https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases/tag/v0.1.0-alpha.1) | Initial desktop converter / Conversor inicial |

Build artifacts are unsigned. Keep backups and verify converted saves in-game. / Binarios sin firma digital. Conservá respaldos y verificá las partidas dentro del juego.
