# Languages, file drops and other paths

## English

Choose a language using its native name: **English, Français, Deutsch, 日本語, Español, Português (Brasil)**. The choice is saved locally and takes effect immediately. Interface messages are translated; low-level filesystem/format diagnostics remain technical details and may be in English.

Select **Wii U → Switch** or **Switch → Wii U** using the console cards. The source and destination backups must match that direction. Switching direction swaps the two input paths. Choose folders or drag `game_data.sav`, `caption.sav`, `option.sav`, or a complete backup folder onto either input. Dropping a file selects its containing complete backup: an isolated `.sav` is insufficient. You must still provide native destination settings and a new output directory.

### Copy to emulators and PC ports

1. Open **Settings · Other paths**, then **Add**.
2. Name the target; choose **Ryujinx**, **Eden**, **Savage Wind**, **Cemu**, or **Custom**. Cemu defaults to Wii U format; the others default to Switch. This is a format choice, not automatic game-version adaptation.
3. Select the actual user-save folder. In Ryujinx/Eden, use their **Open User Save Directory** command for BOTW and select the resulting user directory. Do not select the emulator installation or an entire NAND tree.
4. For Savage Wind, choose its game folder, `save/`, or the precise `save_N/` profile. A single initialized `save/save_N/` is detected automatically; if several profiles exist, select the intended profile explicitly. Timestamped backup siblings are ignored when detecting profiles. Example: `D:\Games\BOTW-SavageWind` resolves to `D:\Games\BOTW-SavageWind\save\save_0` when that is the unique initialized profile. Older layouts using `save/option.sav` are also recognized. A nonempty directory must already contain a recognizable BOTW save; an empty, existing folder is also accepted. Initialize the port in-game before copying; an empty save_N profile can be selected explicitly. No guessed default paths are used.
5. Enable the target and save settings. Multiple destinations are supported. Keep the target game update/DLC compatible with the converted save.
6. After a successful conversion, the app offers to copy to enabled targets of the matching platform. It lists the resolved paths and asks for confirmation. **Close the games/emulators before accepting.** You can decline and use **Copy converted save** later.
7. Copy progress is separate from conversion progress. The source output is checked against its SHA-256 manifest. Each old target directory is retained next to it as `<save-folder>.ubsm-backup-<UTC timestamp>-<id>`. Stale managed save slots are replaced, unrelated metadata is retained, and a failed final replacement attempts to restore the original directory. No backup is automatically deleted.
8. Read the result and `copy-report.json`. A failed destination does not invalidate the converted output or hide successful copies to other targets.

To roll back, close the game, move the new save directory somewhere safe, then rename the corresponding `.ubsm-backup-...` directory to the original save-directory name. Do not merge the old and new save trees.

Configuration is user-local, outside the executable and Git repository:

- Windows: `%APPDATA%\Universal-BOTW-Save-Manager\config.json`
- macOS: `~/Library/Application Support/Universal-BOTW-Save-Manager/config.json`
- Linux: `$XDG_CONFIG_HOME/Universal-BOTW-Save-Manager/config.json` (defaults to `~/.config/...`).

Personal paths are never included in release packages. Changing language does not send a save anywhere. Real game/emulator validation remains required; testing the copy mechanism is not proof of compatibility with every port or update.

## Español

Elegí el idioma por su nombre nativo: **English, Français, Deutsch, 日本語, Español, Português (Brasil)**. Se guarda en esta computadora y se aplica inmediatamente. La interfaz está traducida; los errores técnicos del sistema o del formato pueden aparecer en inglés.

Elegí **Wii U → Switch** o **Switch → Wii U** con las tarjetas de consolas. Los respaldos deben corresponder a esa dirección. Cambiarla intercambia las dos rutas de entrada. Podés elegir carpetas o arrastrar `game_data.sav`, `caption.sav`, `option.sav` o una carpeta de respaldo sobre cada entrada. Al arrastrar un archivo se selecciona el respaldo completo que lo contiene: un `.sav` aislado no alcanza. Sigue siendo necesario un respaldo nativo de destino y una carpeta de salida nueva.

### Copiar a emuladores y ports

1. Abrí **Configuración · Otras rutas → Agregar**.
2. Poné un nombre y elegí **Ryujinx**, **Eden**, **Savage Wind**, **Cemu** o **Custom**. Cemu propone formato Wii U; los demás, Switch. Esto no adapta automáticamente la versión del juego.
3. En Ryujinx/Eden usá **Open User Save Directory** para BOTW y elegí la carpeta de ese usuario. No selecciones toda la instalación ni una NAND completa.
4. Para Savage Wind podés elegir la carpeta del juego, `save/` o el perfil `save_N/` concreto. Se detecta un único perfil inicializado; si hay varios, hay que elegir uno. Los respaldos vecinos no se confunden con perfiles. Ejemplo: `D:\Games\BOTW-SavageWind` se resuelve a `D:\Games\BOTW-SavageWind\save\save_0` si ese es el único perfil inicializado. También se reconoce el formato anterior con `save/option.sav`. Una carpeta con contenido debe tener un save reconocible de BOTW; también se acepta una carpeta vacía existente. Iniciá antes una partida en el port; un perfil save_N vacío puede seleccionarse explícitamente. La app no adivina rutas de instalación.
5. Activá el destino y guardá. Podés agregar varios. Usá las actualizaciones y DLC compatibles con el save convertido.
6. Al terminar de convertir, se ofrece copiar a los destinos activados del formato correcto. La app muestra las rutas y pide confirmación. **Cerrá antes los juegos y emuladores.** Podés rechazar y usar luego **Copiar save convertido**.
7. Hay una barra independiente para la copia. Se verifica el informe SHA-256 y se conserva cada carpeta anterior junto al destino como `<carpeta>.ubsm-backup-<fecha UTC>-<id>`. Se reemplazan las ranuras antiguas, se conserva la metadata ajena al save y, si falla el reemplazo final, se intenta restaurar el original. No se borran los respaldos automáticamente.
8. Revisá el resultado y `copy-report.json`. Un fallo en un destino no elimina la conversión ni oculta las copias que sí terminaron.

Para volver al save anterior, cerrá el juego, mové la carpeta nueva a un lugar seguro y renombrá el respaldo `.ubsm-backup-...` con el nombre original. No mezcles ambos árboles de guardado.

La configuración queda en `%APPDATA%\Universal-BOTW-Save-Manager\config.json` en Windows; las rutas de macOS/Linux están arriba. No se publica con los binarios. Cambiar de idioma no envía archivos. Las pruebas de la copia no sustituyen probar cada juego, port y versión.
