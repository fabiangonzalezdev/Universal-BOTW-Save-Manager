# Conversion contract / Contrato de conversión

BOTW record files use a 12-byte header, repeated 8-byte hash/value pairs and a final `0xffffffff` marker. Switch uses little endian; Wii U uses big endian. String values retain their original byte order; numeric values and hashes change endian. Repeated hashes represent arrays and string chunks.

This implementation uses the destination game's own record ordering and lengths. Unknown fields shared by both saves are rejected unless among the five explicitly identified newer Switch scalar fields. Unknown added/removed hashes and mismatched array lengths stop the conversion before any output is published. Source and destination platforms must differ.

Newer Switch fields observed absent in a native Wii U 1.5.0 schema:

```
0x62133c14
0x8dafa42c
0xcf031efd
0xf3316abb
0xfa050b46
```

Their gameplay semantics have not been fully established. They are only removed or initialized from destination template records with explicit experimental opt-in. This does not establish full downgrade compatibility. Wii U→newer Switch conversions are also experimental. Record checks do not detect game-content requirements or prove hardware loadability.

The destination `option.sav` is copied byte-for-byte. Only top-level slots `0`–`7` are used. A missing slot template can use another slot from the same normal/Master Mode category. Nested slot directories are omitted and listed in the report. JPGs are copied unchanged. Tracker files must be exactly 65536 bytes: preserve bytes 0–3 and 6–7, reverse the u16 at 4 and u32 values from offset 8; a roundtrip check must reproduce the source.

All conversions are planned before writing. A sibling staging directory holds verified files before a final rename to a new output directory. Source hashes are rechecked. No output may overlap a backup. The app never requests console keys or connects to Nintendo services. Public tests use generated records, not personal game saves.

En español: se compara la estructura con una partida nativa de destino y se rechazan diferencias desconocidas. Se conservan los bytes de cadenas y las opciones de destino. Los cinco campos recientes son experimentales; pasar las comprobaciones no reemplaza probar la carga dentro del juego.
