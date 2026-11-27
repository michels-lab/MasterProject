# Uva — conciliación de manifiestos fijos V2 (27-11-2026)

Base fd9ea19f4e51b6eb0e15ca01e224e3b2a1fa3aee. Se encontraron tres incoherencias: el índice omitía el commit de C14-3DA (el recuperador exige SHA40), el estado integrado de A y su registro dueño negaban verificación de manifiesto, y ambos bloques vigentes B conservaban false. Se contrastaron las cuatro ramas con el índice y los informes de analysis_preview. Todos tienen solver_completed, 200000 pasos, 200 s, cobertura declarada completa, sin errores y physical_validation false. Identidades de manifiesto y tamaños declarados coinciden.

| Caso | Commit | Blob manifiesto | Partes | Bytes |
|---|---|---|---:|---:|
| C14-3DA-200s | ba0d4d29a434fa0576372bbdd14385b1663498d7 | 1631f7f1a205374b34da12a5def805e7677d0338 | 24 | 778685468 |
| C14-3DB-200s | 6b012725c860c16cbe3a72cfe7c4a57a6824685c | 58a509cfaafcc6f82694029a4c96dd721f2a2fb9 | 25 | 824832949 |
| B14-2D-200s | 18262a16a19d96decd0b54b39775dd98f28f9a79 | de1308a419cc64a8f64627133bcb99cd803cd005 | 9 | 288901576 |
| C14-2D-200s | f2b4b1901bcde5f22f6625e3554244235b137ea7 | 5336090a406e8cc2178ca716be8f5737940635ec | 8 | 267401563 |

Se actualizan exclusivamente estados de publicación, pin y referencias documentales. Se conservan cortes históricos y puertas científicas A 8/10, B 2/7. No se comprobaron bytes de los archivos binarios ni hash SHA256 de informe/log; no nueva ejecución ni validación física. El índice queda con las cuatro publicaciones seleccionables por SHA en recuperador; sus pruebas estáticas pendientes. La etiqueta de completion_verified de B se refiere a evidencia documental/manifiesto, no ejecución independiente. Próximo: recuperación segura del archivo y catálogo, corregir discrepancias de identidad de archivos sin reescribir resultados.
