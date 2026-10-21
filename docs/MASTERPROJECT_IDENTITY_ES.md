# masterproject — identidad del proyecto científico

**Nombre actual elegido por el propietario (2026-10-21): `masterproject`.** El nombre anterior es `QuickCup-Solidification` y el repositorio GitHub sigue usando temporalmente ese slug mientras su propietario realiza el cambio en la configuración.

## Qué es masterproject

Proyecto de investigación de maestría sobre solidificación y transferencia de calor conjugada con OpenFOAM Foundation v14: sistemas metal/molde, ecuaciones de energía, entalpía-porosidad, flotación, geometría 2D/3D, análisis térmico, registro de sensibilidad B/C y validación con datos experimentales cuando existan.

El nombre del proyecto es distinto del nombre del espécimen, de un caso o de un directorio histórico. Un estudio etiquetado QuickCup, C14, C3D o V15/V16 **no se renombra ni se reinterpreta automáticamente**.

## Fuentes científicas que no cambian por el nuevo nombre

- `RUN_MASTER_PROTOCOL.md` y `RUN_CASE_REGISTRY.csv`
- `cases_controlled_buoyancy/` y `cases_3d/`
- `analysis_results/`, `analysis_tools/`, bitácoras y matrices experimentales
- Datos locales del investigador, propiedades JMatPro y archivos CAD que no deben subirse de forma indiscriminada
- Ramas, PRs abiertos, resultados y compromisos de validación científica

Las corridas CFD siguen siendo **exclusivamente locales** en la laptop del investigador. FoamLens y el repositorio de coordinación OpenFOAM son opcionales, no dependencias de masterproject.

## Transición de repositorio

La carpeta Git y el nombre del repositorio son independientes de los nombres internos de casos/archivos. El cambio de nombre del repositorio en GitHub se realiza desde su configuración general, pasando de `michels-lab/QuickCup-Solidification` a `michels-lab/masterproject`. No afirmar que el cambio ya se completó hasta comprobar la ruta nueva.

Una vez realizada la migración, actualizar git remote, enlaces, documentación visible y configuraciones de automatización sin destruir los registros anteriores. Los scripts de investigación y los PRs existentes mantienen su fuente de verdad aquí.
