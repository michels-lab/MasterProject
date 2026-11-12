> **12-11-2026, actualización posterior al registro de 10-11:** [Reinicio limpio C3D_02](cases_3d/C3D_02_metal_sand_clean/README.md) preparado como nuevo caso fuente, sin ejecución; se preserva C3D-01. La prueba local conectada `splitMeshRegions -cellZones 'metal'` sí generó 5,334 caras `metal_to_surrounding`, **sin resolver separación molde/exterior ni calidad de malla**. [Bitácora de reinicio](docs/C3D_REINICIO_20261112_ES.md); [Manual/errores reales](docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md). NO se ha ejecutado CFD 3D.

# MasterProject — Project Audit Log (formerly QuickCup-Solidification)

> **Estado científico actualizado, 10-11-2026 — C3D-01:** recorte local metal + arena: **1,209,777 celdas; 151.230 cm³; 15 celdas cóncavas, 8 face-tets deficientes, 17 celdas de determinante pequeño; 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` separó `region1` (probable arena, **825,994 celdas; 103.256 cm³; 3 fallos**) y `region2` (probable metal, **383,783 celdas; 47.9735 cm³; 2 fallos**); **`No interfaces to add`**. **Sin interfaz CHT, sin CFD 3D ni malla aprobada.** El ensayo `-cellZones 'metal'` aún **NO** se ejecutó. [Evidencia](docs/C3D_01_ESTADO_REAL_20261110_ES.md) · [Manual](OPENFOAM_COMMAND_MANUAL_ES.md).


**Updated 2026-11-10:** [full local 3D mesh evidence](docs/C3D_01_ESTADO_REAL_20261110_ES.md) covers material subset, separate regions and **missing thermal interface**. Both regions still fail quality checks. This page is a language selector; see dated entries in the underlying logs.

## Choose language / Selecciona idioma

### 🇪🇸 Español
[**Abrir bitácora en español →**](./PROJECT_AUDIT_LOG_ES.md)

Bitácora técnica cronológica completa: cambios, pruebas, evidencia, resultados, interpretación y estado.

### 🇬🇧 English
[**Open English audit log →**](./PROJECT_AUDIT_LOG_EN.md)

Complete chronological technical audit trail: changes, tests, evidence, results, interpretation, and status.

---

Both versions preserve the same technical history, evidence labels, dates, commands, filenames, numerical values, and status markers. New audit entries should be added to both language versions.


## 2026-10-20 — Orden permanente GRANADA GRANDE (gobernanza; no release)

- El propietario exige bloques **más grandes y ambiciosos**, con entregables relacionados y funcionamiento de extremo a extremo. Vigente el protocolo maestro en `michels-lab/Michel-Software-Standards/standards/GRANADA_CONTINUOUS_BLOCK_PROTOCOL.md` y la copia local `.michelslab/GRANADA.md`.
- Para el siguiente comando GRANADA: leer HEAD, issues, PR abiertos, claims y este log; escoger un paquete de **tres o más entregables sustanciales relacionados cuando haya alcance real**, incluyendo implementación, prueba del flujo principal, errores/reintentos y validación. Un solo P0 indivisible puede ser suficiente; no inventar trabajo artificial.
- Si cualquier parte está ocupada por otra rama, requiere equipo físico, una cuenta de proveedor, resultados científicos que solo existen en el portátil o autorización del propietario, **aparcar con evidencia y pasar a otra subparte independiente**. Conservar identidad visual, datos, credenciales y estándares de publicación.
- Registro obligatorio: A/B/C con estados separados, ruta/PR/sha, QA **ejecutado** (no simplemente escrito), bloqueos, recuperación, reentrada. Esta actualización de política **no significa ninguna funcionalidad del producto implementada, probada ni publicada**.
- Repositorio: `michels-lab/QuickCup-Solidification`. En los siguientes bloques aplicar este alcance sin modificar los PR activos o trabajos no relacionados.

## GRANADA GRANDE — 2026-10-20

Registro independiente de la política de bloques ambiciosos y de la separación OpenFOAM ↔ FoamLens: [Bitácora de coordinación](docs/granada/GRANADA_GRANDE_GOVERNANCE_20261020.md).

Avance científico no destructivo V15/V16: [Documento de evidencia y controles (todavía en PR #20)](https://github.com/michels-lab/MasterProject/pull/20/files) propuesto en el [PR #20](https://github.com/michels-lab/QuickCup-Solidification/pull/20). El documento nuevo está en una rama candidata; no se considera integrado antes de su revisión y merge. Los informes de malla, energía y validación experimental permanecen abiertos.

**Evidencia científica auditada en CI:** [V15/V16 — desviaciones de temperatura, Courant y continuidad (2026-10-20)](analysis_results/granada_v15v16_postrun_20261020/summary.md). El análisis es solo lectura y aún no cierra validación física/experimental.
