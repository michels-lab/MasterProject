> **12-11-2026, candidato de mallado:** [C3D_02_metal_sand_clean](C3D_02_metal_sand_clean/README.md) ahora tiene `snappyHexMeshDict` para **dos interiores sin aire** y comando único `bash scripts/run_mesh_only.sh`. Se verificará en Ubuntu; todavía no existe malla/CFD aceptada. [Procedimiento](../docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

> **Nuevo caso fuente C3D (2026-11-12):** [C3D_02_metal_sand_clean](C3D_02_metal_sand_clean/README.md). C3D-01 es histórico; no reemplazar sus registros. Reinicio desde referencia material C14, dos regiones `metal` + `mold`, sin aire. Las pruebas de 1.5 M celdas, recortes y 5,334 caras `metal_to_surrounding` **no constituyen** malla CHT 3D validada. [Reinicio y trazabilidad](../docs/C3D_REINICIO_20261112_ES.md).

# Plan D — Casos tridimensionales de QuickCup

> **Estado científico actualizado, 10-11-2026 — C3D-01:** recorte local metal + arena: **1,209,777 celdas; 151.230 cm³; 15 celdas cóncavas, 8 face-tets deficientes, 17 celdas de determinante pequeño; 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` separó `region1` (probable arena, **825,994 celdas; 103.256 cm³; 3 fallos**) y `region2` (probable metal, **383,783 celdas; 47.9735 cm³; 2 fallos**); **`No interfaces to add`**. **Sin interfaz CHT, sin CFD 3D ni malla aprobada.** El ensayo `-cellZones 'metal'` aún **NO** se ejecutó. [Evidencia](../docs/C3D_01_ESTADO_REAL_20261110_ES.md) · [Manual](../OPENFOAM_COMMAND_MANUAL_ES.md).


**Estado 2026-11-10:** [diagnóstico experimental C3D-01](../docs/C3D_01_ESTADO_REAL_20261110_ES.md). Se ejecutó una malla de prueba de 1,505,847 celdas en laptop con **dos fallos `checkMesh`**; no existe malla metal–arena aceptada ni CFD 3D. El molde reparado, los dos originales y logs geométricos están en Git. La carpeta local de prueba no está versionada.


**Identificador oficial de caso: [case3d-01](case3d-01/README.md).**

La ruta científica Plan D investiga solidificación y transferencia térmica metal–arena en 3D, independiente de la ruta B de superficie libre [FS-C01](../freesurface/FS-C01/).

- **[case3d-01](case3d-01/README.md)**: documentación canónica, gate de geometría y huellas STL, auditoría de logs OpenFOAM y script que prepara **una copia externa y nueva** del caso de malla de fondo con los STL originales sin cambiarlos. No es todavía un caso CFD completo. Los STL original/reparado sí están actualmente publicados en el repositorio público.
- **[C3D_01_metal_mold](C3D_01_metal_mold/README.md)**: ubicación técnica heredada de los archivos CAD/inputs de malla mientras están abiertos los PR #18 y #19. Este nombre de carpeta no sustituye el identificador canónico `case3d-01`. No mover ni duplicar silenciosamente sus datos hasta reconciliar dichos PR.

Ambos directorios se refieren a la **misma línea de investigación Plan D**, no a dos simulaciones ni a resultados distintos. `blockMesh`, `checkMesh`, `snappyHexMesh` y los cálculos CFD requieren ejecución y validación en el Ubuntu del investigador; GitHub Actions únicamente verifica datos e integridad estática.

**Escala:** `units [mm];` en OpenFOAM Foundation 14; conservar STL SolidWorks en mm sin convertirlos por Python. La meta propuesta de 0.5 mm nominal en volúmenes completos continúa **en revisión científica**, no es una resolución comprobada.
