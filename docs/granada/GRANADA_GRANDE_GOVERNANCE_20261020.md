# GRANADA GRANDE — bitácora de coordinación científica (2026-10-20)

La nueva regla del propietario exige **bloques grandes y ambiciosos** con entregables científicos conectados y pruebas reproducibles, respetando PRs, trazabilidad y protección de resultados. Autoridad: [protocolo maestro](https://github.com/michels-lab/Michel-Software-Standards/blob/main/standards/GRANADA_CONTINUOUS_BLOCK_PROTOCOL.md).

**Interoperabilidad:** QuickCup es el productor de entradas/salidas científicas OpenFOAM; FoamLens es plataforma complementaria de CAD, auditoría de mallado, postprocesamiento, diagnóstico físico/numerico y validación experimental. Los contratos de archivo, tiempo físico, región, dimensión, procedencia y estado de verificación deben ser explícitos. FoamLens no altera evidencia histórica del solver.

**Bloques ocupados:** C3D-01 PR #18 (refinamiento) y #19 (gates científicos). No modificar el mallado, geometrías CAD/STL, esas ramas ni sus ficheros asignados. Ambos mantienen controles pendientes de Ubuntu/OpenFOAM. C14/B14 y casos V15/V16 no reciben nueva corrida desde GitHub.

**Bloque independiente objetivo:** cierre reproducible de revisión de evidencia V15/V16; construir auditorías de series térmicas, Courant y continuidad con reportes trazables y tests sintéticos sin reescribir datos CFD. Ninguna prueba de archivos exportados equivale a validación física o experimental.

Esta bitácora paralela no edita PROJECT_AUDIT_LOG_ES/EN, archivos ocupados en el PR #18; se deberá integrar la referencia a ambas bitácoras al resolver la colisión.

**Estado:** lineamiento y scope, no constituye una simulación CFD ni validación.
