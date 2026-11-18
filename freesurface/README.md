# freesurface — Casos de prueba

El caso **[FS-C01](FS-C01/)** es el primer banco de referencia de superficie libre de la ruta científica B-FS-01. Usa **agua–aire**, no hierro fundido; su estado es **PREPARED_NOT_MESHED_OR_RUN**, por lo que todavía no hay resultados CFD ni evidencia de contracción.

Consulte el [registro del caso](FS-C01/CASE_NOTES.md) y la [bitácora técnica B-FS-01](../docs/granada/B_FS_01_VOF_HYDRO_ANALOGUE_20261020.md). El manifiesto de FS-C01 contiene los SHA-256 de los 20 archivos de entrada.

## 2026-11-17 — Resultado local FS-C01

Una **copia externa aislada** de FS-C01 se sometió a mallado local Foundation 14: blockMesh y checkMesh -allGeometry -allTopology **PASS**. foamRun **falló durante la inicialización** por ausencia del requisito writeFields en la función waterVolume; no se obtuvieron pasos físicos CFD ni datos de contracción. La copia fallida se conserva. Se corrigió la entrada a writeFields false;, el generador y la trazabilidad SHA-256 en una rama específica con PR; queda **PENDIENTE repetir una nueva corrida FS-C01**. La carpeta fuente del repositorio sigue siendo un caso de entradas (sin malla de ejecución ni outputs CFD). Véase [registro FS-C01](FS-C01/CASE_NOTES.md) y [ejecución aislada en WSL](FS-C01/RUN_ISOLATED_UBUNTU_ES.md). Esta rama es independiente de C3D-02.


## 2026-11-17 hora local — Reintento FS-C01 exitoso, pendientes las verificaciones físicas

El investigador informó que la **segunda ejecución aislada** `FS-C01_20261118T003425Z_da7504c3` (Foundation 14, SHA `16fa1498f`) pasó `blockMesh`, `checkMesh`, `foamRun` y la auditoría automática inicial de volumen. El caso **fuente** versionado sigue limpio y preparado, mientras que los resultados reales permanecen en la laptop, fuera del repositorio; todavía no se han inspeccionado el `volume_screen.json`, las series de alpha, masa por fase y consistencia hidrostática. Estado de la *corrida local*: **LOCAL_RUN_AND_VOLUME_SCREEN_REPORTED**. No significa validación física de contracción ni hierro–aire. Véase [bitácora](FS-C01/CASE_NOTES.md).

## FS-C02 — hierro fundido–aire, continuación de B14

[FS-C02](FS-C02/README.md) dispone de un **generador y ejecutor aislado** de entradas para un smoke test VOF hierro–aire (Foundation 14), con lecturas de referencia de B14 sin modificación. **No se ha ejecutado CFD ni validado solidificación, contracción, masa, interfaz o acoplamiento a molde.** La fase agua–aire FS-C01 permanece como benchmark separado; el proyecto 3D C3D-02 no es modificado.


## FS-C02 — Primer solver local completado, 2026-11-17

El investigador reportó Foundation 14, worktree FS-C02 y corrida independiente `FS-C02_20261118T005412Z_c04dfcf6`. El ejecutor indicó `foamRun completed`. **Solo queda verificada la puerta de ejecución reportada**, no masa/interfaz/termofísica/superficie ni contracción. Para usar los resultados reales sin repetir el solver, el nuevo script `analysis_tools/audit_fs_c02_local.py` audita la carpeta FS-C02 anterior, reportando volúmenes, alpha, Courant y masa derivada (no medida). Véase [procedimiento FS-C02](FS-C02/README.md). C3D-02 y B14 siguen aislados.
