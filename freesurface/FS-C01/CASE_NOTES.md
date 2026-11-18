# FS-C01 — Caso de prueba de superficie libre

**Identificador definitivo:** FS-C01 (`freesurface/FS-C01/`). La etapa científica correspondiente se denomina B-FS-01.

**Estado:** PREPARED_NOT_MESHED_OR_RUN. Los datos son un **análogo hidrodinámico agua–aire** basado en `compressibleVoF/damBreak` de OpenFOAM Foundation v14. No representa hierro fundido, contracción, alimentación, porosidad, solidificación ni molde térmicamente acoplado.

Dimensiones nominales 40×60×10 mm, malla 80×120×1, llenado inicial 40 mm, atmósfera superior y gravedad −Y. Volumen inicial de líquido 1.6e−5 m³; horizonte 0.1 s.

Los 20 archivos de entrada en `0/`, `constant/` y `system/` son idénticos a los del artefacto certificado estáticamente en [GitHub Actions #39409347758](https://github.com/michels-lab/QuickCup-Solidification/actions/runs/39409347758). Sus hashes de contenido están en `BFS01_MANIFEST.json`. El nombre B-FS-01 permanece en el esquema de procedencia para conservar compatibilidad con el auditor.

**Para validar en Ubuntu/OpenFOAM 14:** dentro de este caso ejecutar `blockMesh`, `checkMesh`, revisar logs/parches y luego `foamRun`. Guardar las salidas reales y revisar `alpha.water`, volumen, masa, Co y estabilidad de la interfaz. El script `analysis_tools/granada_bfs01_vof_benchmark.py audit` comprueba volumen mediante postprocesamiento auténtico, pero no masa ni shrinkage.

**Origen y licencia:** entradas derivadas del [tutorial oficial de OpenFOAM Foundation 14](https://github.com/OpenFOAM/OpenFOAM-14/tree/master/tutorials/compressibleVoF/damBreak), bajo GNU GPL. No se han incluido datos de una corrida ni se han modificado casos históricos del investigador.

## 2026-11-17 — Preparación de ejecución local aislada

Se añade el ejecutor de caso exclusivo FS-C01 en `analysis_tools/run_fs_c01_local.py`, junto con `RUN_ISOLATED_UBUNTU_ES.md` y pruebas sintéticas. Crea una copia nueva bajo `~/OpenFOAM/FS_C01_RUNS`, valida los 20 SHA-256 y registra logs/estado por etapa. Rechaza `checkMesh` con errores aunque su retorno sea cero. Para evitar interferencia con C3D-02, usar un worktree FS-C01 separado; NO cambiar de rama sobre el checkout que usa la simulación 3D. El código y sus pruebas estáticas NO significan que se haya ejecutado `blockMesh`, `checkMesh` o `foamRun` en la laptop; conservamos `PREPARED_NOT_MESHED_OR_RUN` y siguen pendientes masa, alpha, hidrostática y contracción.


## 2026-11-17 — Primera ejecución real FS-C01 / diagnóstico de fallo

El investigador ejecutó la prueba FS-C01 en Ubuntu Foundation 14, worktree separado, con carpeta de salida `FS-C01_20261118T001239Z_656d1a84`. **`blockMesh` PASS** y **`checkMesh -allGeometry -allTopology` PASS**, según `FS-C01_RUN_STATUS.json` aportado por el investigador. `foamRun` devolvió código 1 **durante la inicialización, antes de pasos de tiempo**, con `FOAM FATAL IO ERROR: keyword writeFields is undefined in system/functions!waterVolume`. No constituye CFD completada ni validación de volumen.

Causa: el generador `granada_bfs01_vof_benchmark.py` y el caso fuente congelado no incluían la palabra clave obligatoria `writeFields` del `volFieldValue` de Foundation 14. Corregido en esta rama con `writeFields false;`, actualizado **solo** el SHA-256 de `system/controlDict` en el manifiesto de 20 entradas y añadida barrera semántica en el preflight más regresiones positivas y negativas. El expediente original de ejecución se conserva sin modificaciones. **Nueva ejecución FS-C01 en carpeta aislada PENDIENTE**; masa, energía y contracción permanecen NO VERIFICADAS. La rama C3D-02 no se alteró.
