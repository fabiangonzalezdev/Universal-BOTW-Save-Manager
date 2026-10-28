# Universal-BOTW-Save Manager v0.1.0-alpha.1

First Windows-priority preview. Select an extracted source backup, a native destination backup from the other platform, and a new output directory. Inspect, then convert Wii U ↔ Switch.

- English/Spanish desktop interface.
- Preserves shared game values and target options; originals stay untouched.
- SHA-256 conversion report and strict schema checks.
- Experimental cross-version conversion requires opt-in.

**Validation:** automated synthetic tests, exact full-reference roundtrip, and Windows packaged resource/UI smoke tests. Physical Wii U/Switch loading still needs validation. macOS/Linux availability is determined by the attached artifacts; CI configuration is not a hardware-test claim.

**Windows:** extract the ZIP and launch `Universal-BOTW-Save-Manager.exe`. No Python installation needed. Binaries are unsigned. Keep source and destination backups until you have loaded the result in-game.

**Español:** seleccioná origen, respaldo nativo de destino y carpeta nueva. Revisá y convertí. No sobrescribe originales. Los cambios de versión son experimentales; falta probar el resultado en consolas físicas. El ejecutable Windows no requiere instalar Python.
