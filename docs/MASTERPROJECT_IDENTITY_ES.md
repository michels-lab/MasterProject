# MasterProject — identidad del proyecto científico

> **C3D-01 al 10-11-2026:** las mallas 3D y diagnósticos se ejecutaron **solo en la laptop**. `subsetMesh -cellSet materialVolume` conservó **1,209,777 celdas; 151.230 cm³; 15 concavidades, 8 face-tets deficientes, 17 determinantes pequeños y 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` produjo `region1` (molde probable, **825,994 celdas; 3 fallos**) y `region2` (metal probable, **383,783 celdas; 2 fallos**), pero informó **`No interfaces to add`**: no hay interfaz térmica acoplada ni solver CFD 3D ejecutado. `-cellZones 'metal'` permanece **sin ejecutar**. [Registro experimental](C3D_01_ESTADO_REAL_20261110_ES.md). El repositorio y la carpeta local mantienen su identidad MasterProject.


**Estado operativo 2026-11-10:** el usuario confirmó `~/OpenFOAM/MasterProject`, Git `main` y OpenFOAM Foundation 14. Los STL `metal.stl`, `mold.stl` y `mold_repaired.stl` están disponibles en GitHub. La línea Plan D ya cuenta con una primera malla **local y no aceptada** por fallos de calidad; [evidencia y límites](C3D_01_ESTADO_REAL_20261110_ES.md).


**Nombre actual y repositorio GitHub verificado (2026-10-21): `MasterProject`.** El nombre anterior era `QuickCup-Solidification`. GitHub confirmó el mismo ID `1381015792` en el URL nuevo y en el redireccionamiento anterior; no es un segundo repositorio.

## Qué es MasterProject

Proyecto de investigación de maestría sobre solidificación y transferencia de calor conjugada con OpenFOAM Foundation v14: sistemas metal/molde, ecuaciones de energía, entalpía-porosidad, flotación, geometría 2D/3D, análisis térmico, registro de sensibilidad B/C y validación con datos experimentales cuando existan.

El nombre del proyecto es distinto del nombre del espécimen, de un caso o de un directorio histórico. Un estudio etiquetado QuickCup, C14, C3D o V15/V16 **no se renombra ni se reinterpreta automáticamente**.

## Fuentes científicas que no cambian por el nuevo nombre

- `RUN_MASTER_PROTOCOL.md` y `RUN_CASE_REGISTRY.csv`
- `cases_controlled_buoyancy/` y `cases_3d/`
- `analysis_results/`, `analysis_tools/`, bitácoras y matrices experimentales
- Datos locales del investigador, propiedades JMatPro y archivos CAD que no deben subirse de forma indiscriminada
- Ramas, PRs abiertos, resultados y compromisos de validación científica

Las corridas CFD siguen siendo **exclusivamente locales** en la laptop del investigador. FoamLens y el repositorio de coordinación OpenFOAM son opcionales, no dependencias de MasterProject.

## Transición de repositorio

La carpeta Git y el nombre del repositorio son independientes de los nombres internos de casos/archivos. El cambio del nombre en GitHub **ya se completó**: `michels-lab/QuickCup-Solidification` → `michels-lab/MasterProject`. La estructura de los casos, las bitácoras y los resultados siguen intactos.

Una vez realizada la migración, actualizar git remote, enlaces, documentación visible y configuraciones de automatización sin destruir los registros anteriores. Los scripts de investigación y los PRs existentes mantienen su fuente de verdad aquí.
