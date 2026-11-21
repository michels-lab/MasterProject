# freesurface — Casos de prueba


> **20-11-2026 — FS-C06 10/10 monitores NATIVOS confirmados:** en la segunda corrida real WSL (HEAD `608332778`), `foamMultiRun` y `checkMesh` de ambas regiones pasaron y se escribieron los diez archivos `.dat` de `system/functions`. Sigue pendiente verificar los valores de los archivos; **el modelo físico de contracción/alimentación no existe todavía**. [Evidencia precisa y ruta aislada](../docs/granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md).



> **20-11-2026 FS-C06 DATOS NATIVOS:** se observaron `4.801191628e-5 m³` de metal VOF, **0 metal sólido** a `1e-7` y `2e-7 s`, temperatura final media `1499.996564 K`; sin contracción de volumen ni alimentación. Los monitores de masa/calor de Foundation14 estaban colocados en el `controlDict` legado y no generaron `.dat` en cuatro rutas consultadas; ahora residen en `system/functions`, con aceptación endurecida en Git **todavía pendiente de WSL**. [Bitácora](../docs/granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md). Entradas antiguas de «no ejecutado» son historia, no estado actual.



> **20-11-2026 — FS-C06, primera aceptación nativa WSL Foundation14:** dos pasos `foamMultiRun`, campo `alpha.metal.solid` y `checkMesh` de `fluid/mold` reportados PASS en consola del investigador; datos crudos pendientes de revisión. No equivale a contracción física ni alimentación. [Bitácora FS-C06](../docs/granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md). Los bloques antiguos que declaran FS-C06 no ejecutado son históricos.


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

## 20-11-2026 — FS-C06 VOF-native solidification (compatibilidad, NO contracción aún)

Nuevo candidato [FS-C06](FS-C06_vof_solidification/README.md), aislado de FS-C05, de B14 y de los casos C3D. Se verificó en la fuente **Foundation 14** que `VoFSolidificationMelting` incorpora término de entalpía y amortiguamiento Darcy en el solver `compressibleVoF`, y escribe `alpha.metal.solid` (fracción sólida volumétrica absoluta) sin sustituir `alpha.metal` (VOF metal/aire). El generador [stage_fs_c06_vof_solidification.py](../analysis_tools/stage_fs_c06_vof_solidification.py) crea una copia nueva, conserva las propiedades FS-C05, usa parámetros numéricos de C14 con SHA verificable, activa el modelo nativo y permite un **único smoke test opcional** de dos pasos en WSL mediante `--native`. El repositorio NO ejecutó CFD. Pruebas sintéticas: [workflow de FS-C06](../.github/workflows/fs-c06-static.yml); el resultado Actions debe revisarse antes de declarar CI aprobada. **No hay cambio de densidad por fase sólido/líquido, descenso de superficie, alimentación, validación de masa/entalpía ni curvas QuickCup**. No incrementar porcentaje de tesis.

## FS-C06 (20-11-2026) — pantalla de densidades sin resultados CFD nuevos

Se preparó la herramienta de solo lectura [screen_fs_c06_density_contraction.py](../analysis_tools/screen_fs_c06_density_contraction.py), que exige informe FS-C06 de ejecución nativa **y** densidades trazables con fuente original y SHA verificable; compara una hipótesis de volumen a masa fija sin alimentar con los volúmenes VOF medidos. No hay material JMatPro calibrado versionado, no se ejecutó FS-C06 y no se añadió contracción al solver. Consulte [FS-C06](FS-C06_vof_solidification/README.md).

## Granada P — FS-C06 OpenFOAM native input overlay

Se añadieron diccionarios ejecutables propios de Foundation14 en [FS-C06/native](FS-C06_vof_solidification/native): `fvModels` con modelo VOF de solidificación más el amortiguamiento turbulento conservado, y `controlDict` multirregión con mediciones `volFieldValue` nativas para metal total y sólido. El stager auxiliar copia los archivos OpenFOAM; ninguna CI corre CFD. FS-C06 todavía no ha ejecutado el solver ni simula contracción conservativa.
