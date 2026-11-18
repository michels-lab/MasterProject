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


## 2026-11-17 hora local / 2026-11-18 UTC — Primer FS-C01 con foamRun y cribado VOF exitosos

**Evidencia comunicada por el investigador (stdout local, sin archivos numéricos completos aún).** OpenFOAM Foundation 14, worktree independiente `~/OpenFOAM/FS_C01_WORKTREE`, commit `16fa1498f0b638d615922c4d69807c6eae129e62`. Corrida externa nueva:
`/home/michel/OpenFOAM/FS_C01_RUNS/FS-C01_20261118T003425Z_da7504c3`.

Las siguientes etapas del ejecutor `analysis_tools/run_fs_c01_local.py` reportaron **gate passed**: `--preflight` (20 SHA-256), `blockMesh`, `checkMesh -allGeometry -allTopology`, `foamRun` y `volumeAudit`. La salida final dice `FS-C01 volume screening passed; mass, alpha bounds and physics remain UNVERIFIED.` El gate de solver exige código de salida 0 y marcador `End`; la auditoría de volumen exige procedencia y tolerancia de deriva, pero **el valor medido de deriva no fue aportado en el chat**, ni los campos, series ni los registros completos del solver. Este resultado se registra como **LOCAL_RUN_AND_VOLUME_SCREEN_REPORTED**, no `ANALYSIS_VERIFIED`, no `EXPERIMENTALLY_VALIDATED` ni física de contracción. No se ejecutó CFD en GitHub.

**Siguiente puerta (sin repetir CFD):** leer el `FS-C01_VOLUME_AUDIT/volume_screen.json`, `volume_times.csv`, `FS-C01_RUN_STATUS.json`, últimos valores y advertencias de `FS-C01_foamRun.log`, campos `alpha.water`, `rho`/mezcla y caudales para balance de masa; evaluar altura/interfaz y Courant antes de promover esta corrida como benchmark. No se deben inferir porosidad ni contracción. Se mantiene independiente de C3D-02. La corrida anterior `FS-C01_20261118T001239Z_656d1a84` permanece como evidencia del fallo de `writeFields`.

## 2026-11-17 hora local — Lectura de resultados numéricos FS-C01 (aportados por investigador)

El investigador consultó la ejecución externa `FS-C01_20261118T003425Z_da7504c3` y aportó directamente `FS-C01_VOLUME_AUDIT/volume_screen.json` y los últimos valores de Courant del log de `foamRun`. **Datos observados:** `VOLUME_SCREEN_PASSED`, 11 puntos entre 0 y 0.1 s, volumen inicial y final = `1.6e-5 m3`, deriva máxima de volumen integrada = `0.0` según precisión del registro, umbral = `0.005` (0.5%), sin alertas, altura equivalente final = 0.04 m (NO es elevación interfacial medida). Último Courant medio `7.23395e-05`, máximo `7.34532e-04`, Courant de interfaz informado = 0.

**Alcance:** volumen de fracción de agua integrado en 11 tiempos, NO medición de masa metalúrgica ni prueba de que la interfaz se haya movido. El Courant de interfaz 0 no demuestra dinámica interfacial por sí solo. No se ha inspeccionado todavía `alpha.water` espacial, ni `rho` en el dominio ni `phi` de cada patch; no se atribuye contracción física a este resultado. El caso fuente en Git permanece sin malla ni outputs CFD, mientras la corrida externa sí ha completado `foamRun` y cribado de volumen. B14 y C3D-02 no se modifican. **Siguiente paso paralelo:** nuevo FS-C02 hierro–aire, con termofísica provisional, sin afirmar solidificación ni contracción.
