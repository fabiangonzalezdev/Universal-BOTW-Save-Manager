# Universal-BOTW-Save-Manager v0.2.1-alpha.1

[GitHub release / Release en GitHub](https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases/tag/v0.2.1-alpha.1)

## Upload / Subir

Attach each platform ZIP and its matching `.sha256` file to this GitHub release. Source code, build scripts and this README belong in Git; binaries are excluded by `.gitignore`.

Adjuntá el ZIP de cada plataforma y su archivo `.sha256` al release de GitHub. El código, los scripts y este README van en Git; los binarios quedan excluidos.

| Platform / Plataforma | Archive / Archivo |
|---|---|
| Windows x64 | `Universal-BOTW-Save-Manager-v0.2.1-alpha.1-windows-x64.zip` |
| Linux x64 | `Universal-BOTW-Save-Manager-v0.2.1-alpha.1-linux-x64.zip` |
| macOS ARM64 | `Universal-BOTW-Save-Manager-v0.2.1-alpha.1-macos-arm64.zip` |

Only packages that have actually been built are present locally. GitHub Actions creates the other native builds.
Solo están disponibles localmente los paquetes ya compilados. GitHub Actions genera los demás builds nativos.

Extract the ZIP and open the application inside its versioned folder. Windows uses `Universal-BOTW-Save-Manager.exe`; macOS uses the `.app` bundle. No Python installation is required for packaged builds. Binaries are unsigned; validate converted saves in-game.

Extraé el ZIP y abrí la aplicación dentro de la carpeta de esa versión. Windows usa `Universal-BOTW-Save-Manager.exe`; macOS usa el paquete `.app`. No hace falta instalar Python. Los binarios no tienen firma digital; validá los saves dentro del juego.

## Verify / Verificar

Windows PowerShell: `Get-FileHash .\Universal-BOTW-Save-Manager-v0.2.1-alpha.1-windows-x64.zip -Algorithm SHA256`

Compare the result with the accompanying `.sha256` file. / Compará el resultado con el archivo `.sha256` correspondiente.
