# Universal-BOTW-Save Manager

<p align="center"><img src="docs/banner.svg" alt="Universal-BOTW-Save Manager" width="100%"></p>

**Conversor visual y sin conexión para partidas de Breath of the Wild: Wii U ↔ Switch.** [English](README.md) · [Descargas](https://github.com/fabiangonzalezdev/Universal-BOTW-Save-Manager/releases)

> [!IMPORTANT]
> Primera versión alfa, desarrollada con asistencia de IA y dirección humana. Las pruebas automáticas verifican archivos y conservación de valores; falta validación dentro del juego en consolas físicas. «Universal» es el nombre del proyecto, no una garantía de compatibilidad con cualquier versión o mod.

## Compilar EXE y ZIP con el icono de espada

El arte original está en `assets/sword.svg`. El EXE incluye un ICO con varios tamaños y la ventana usa la misma espada. Ejecutá `build_windows.ps1` para probar, compilar y generar el ZIP con documentación y SHA-256 en `releases/v<VERSION>/`. [Guía de la carpeta de releases](releases/README.md).

## Primeros pasos

En el selector aparecen **English, Français, Deutsch, 日本語, Español y Português (Brasil)**. Elegí un idioma y la tarjeta **Wii U → Switch** o **Switch → Wii U**. La elección del idioma se guarda localmente. Podés arrastrar un save de un respaldo completo sobre cada entrada o elegirlo con los botones.

1. Descargá el ZIP **Windows x64** de Releases, extraelo y ejecutá `Universal-BOTW-Save-Manager.exe`. El ejecutable empaquetado no requiere Python y no tiene firma digital.
2. En **Respaldo de origen**, seleccioná tu carpeta de usuario exportada con Checkpoint, JKSV o SaveMii. Debe contener `option.sav` y ranuras como `0/game_data.sav`. Si hay varios usuarios, elegí el correcto.
3. En **Respaldo de destino**, elegí una partida nativa de la otra plataforma y de la versión que vas a usar. Es obligatoria: aporta estructura y opciones. No se mezcla su progreso con la partida de origen; solo los campos nuevos identificados que falten se inicializan con sus valores.
4. Elegí una **carpeta de salida nueva**. Al seleccionar el directorio padre se propone `BOTW-converted`; editá el nombre si ya existe. Debe estar separada de ambos respaldos.
5. Pulsá **Revisar** y comprobá plataformas, versiones, corazones y resistencia.
6. Activá **Permitir cambio de versión experimental** únicamente si aceptás convertir entre actualizaciones diferentes. Pulsá **Convertir**.
7. Revisá `conversion-report.json`. Restaurá el contenido de **`user-save/`** con el gestor de tu consola, en una ranura nueva y para el usuario correcto. La app no restaura en la consola ni accede a Nintendo Cloud.
8. Cargá la partida en el juego y comprobá el resultado. Conservá los respaldos originales.

## Qué conserva y qué cambia

- Conserva los valores compartidos: corazones, resistencia, inventario y progreso. No es un editor de estadísticas.
- Convierte archivos de partida y captions; conserva JPG y convierte los bloques del recorrido.
- Usa el `option.sav` nativo de destino para mantener sus opciones.
- Al convertir formatos nuevos de Switch hacia Wii U puede retirar cinco campos identificados; en el sentido inverso usa los valores de esos campos del respaldo de destino. Es experimental.
- Rechaza diferencias desconocidas y cambios de tamaño de arrays; no inventa datos ni sobrescribe el origen.
- Excluye carpetas anidadas que no sean ranuras válidas, como `0/0`, y lo registra en el informe.

> [!WARNING]
> Que la estructura coincida no demuestra que el juego vaya a cargar la partida. Usá las actualizaciones y DLC necesarios, y validá dentro del juego antes de reemplazar tus respaldos de seguridad.

## Emuladores y ports

En **Configuración · Otras rutas** agregá Ryujinx, Eden, Savage Wind, Cemu o un destino personalizado. Después de convertir, la app muestra las rutas del formato correcto y pregunta si querés copiar. Cerrá los juegos antes de aceptar. Hay una barra independiente de copia; cada save anterior queda en una carpeta vecina `.ubsm-backup-...`. Se verifican hashes y se intenta restaurar el original si falla el reemplazo.

Para Savage Wind se detecta `save/` o un único perfil `save/save_N/`; si hay varios perfiles hay que elegir uno. [Guía de configuración, copia y recuperación](docs/DESTINATIONS.md). Las rutas personales quedan fuera del repositorio y los paquetes.

## Compatibilidad

Windows 10/11 x64 es la prioridad. macOS ARM64 y Linux x64 tienen builds configurados en GitHub Actions: su disponibilidad depende de los resultados de compilación y los assets publicados. No se probaron localmente en esas plataformas.

Requiere respaldos propios de BOTW de ambas plataformas. No incluye saves de referencia, ROMs, claves, firmware ni recursos gráficos de Nintendo. No admite TOTK, contenedores de NAND cifrados ni el archivo `progress.sav`.

## Compilar

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
# Linux: xvfb-run -a python tests/gui_smoke.py
# Windows/macOS: python tests/gui_smoke.py
python main.py
python build.py
```

Usá Python 3.11+ con Tk; se recomienda 3.12. En Linux puede hacer falta instalar `python3-tk`. El resultado queda en `dist/`. Cada sistema se compila en ese sistema. Los tags disparan pruebas, builds y un prerelease con ZIPs y hashes una vez que todos los builds terminan correctamente.

## Reportar errores

Incluí sistema operativo, versión de la app, versiones de BOTW de origen/destino y error exacto. Revisá el informe antes de compartirlo. No publiques claves, contraseñas, respaldos completos de consola ni números de serie. El informe contiene hashes, cambios de campos y estadísticas de ranuras; no rutas absolutas.

## Créditos

Código original con licencia MIT. Tabla de tipos: [Marc Robledo](https://github.com/marcrobledo/savegame-editors), licencia MIT, con investigación de MrCheeze. Referencias: [ZeldaMods](https://zeldamods.org/wiki/Save_Files) y [BotW Save Manager](https://github.com/DeltaJordan/BotW-Save-Manager). Diseño del README inspirado en [SavageWindRecomp](https://github.com/Revivedx/SavageWindRecomp), sin copiar su arte ni marca. [Avisos de terceros](THIRD_PARTY_NOTICES.md).

Proyecto independiente, sin afiliación con Nintendo. [Detalles técnicos y límites](docs/FORMAT.md).


## v0.3 interface / Interfaz v0.3

Brown cloud theme, gold console icons, six languages, profile discovery and Cemu copy confirmation. / Fondo de nubes marrones, iconos dorados, seis idiomas, búsqueda de perfiles y confirmación de copia a Cemu.

[Profiles and path discovery / Perfiles y búsqueda de rutas](docs/DISCOVERY.md).
