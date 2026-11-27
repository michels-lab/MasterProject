> **27-11-2026 — Estado vigente:** A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29% hitos. Campaña histórica 2D 26/26, V14 aparte. Laptop adaptativa 6/8 calculadas, 5/8 publicadas, B14-2D sin tope pendiente, A fallida en ambas variantes. FS-C08 lote 12 75/75 pasos, 4/4 variantes, no independencia temporal ni validación física. Los estados anteriores son históricos. [Historia](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Estado](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json) · [Evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md).

Los comandos históricos no son órdenes vigentes. Usar worktrees aislados, verificar procesos y espacio físico HDD, preservar resultados nativos y manifiestos. No pull/clean/reset sobre checkout activo. Véase RUN_MASTER_PROTOCOL.md.

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — documentation pointer:** For C3D-02, the current **native OpenFOAM 14** meshing path, measured STL v2 trial failures and doctor's original `blockMesh` comparison are documented in [Spanish command manual](OPENFOAM_COMMAND_MANUAL_ES.md), [measured trial report](docs/C3D_02_ABLACION_STL_V2_20261118_ES.md) and [original doctor case study](docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). The older Python builder sections are historical/experimental. No validated 3D CFD or CHT yet.

> **Actualización 2026-11-12:** ambos manuales incluyen una nueva adenda Foundation 14. [Lecciones completas de los ensayos](docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md), [nuevo caso 3D](cases_3d/C3D_02_metal_sand_clean/README.md). El historial 10-11 sigue siendo histórico; no hay solver 3D verificado.

# OpenFOAM Command Manual — MasterProject / QuickCup

> **Actualizado 10-11-2026:** ambos manuales ES/EN incluyen comandos históricos B/C y la secuencia 3D efectivamente ejecutada: `foamDictionary`, `blockMesh`, `snappyHexMesh`, `checkMesh`, `surfaceCheck`, `surfacePointMerge`, `surfaceInertia`, `topoSet`, `subsetMesh -cellSet` y `splitMeshRegions -disconnected`. Distinguen **comandos ya ejecutados y pruebas solo propuestas**, con sintaxis de Foundation 14 corregida. [Bitácora C3D](docs/C3D_01_ESTADO_REAL_20261110_ES.md).


**Actualizado 2026-11-10:** [Geometría/mallado C3D-01 y fallos reales](docs/C3D_01_ESTADO_REAL_20261110_ES.md); ambos manuales incluyen comandos Foundation 14 sin Python para consultar los STL y diagnósticos.

## Choose language / Selecciona idioma

### 🇪🇸 Español
[**Abrir manual en español →**](./OPENFOAM_COMMAND_MANUAL_ES.md)

Manual práctico tipo tutorial, con comandos listos para copiar y pegar, explicación de qué hace cada uno y recetas específicas del proyecto.

### 🇬🇧 English
[**Open English manual →**](./OPENFOAM_COMMAND_MANUAL_EN.md)

Practical tutorial-style manual with copy-ready commands, explanations, and project-specific recipes.

---

Both versions contain the **same commands and structure**. When the manual is expanded, both language versions should be updated together.
