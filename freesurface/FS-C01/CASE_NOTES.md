# FS-C01 — Caso de prueba de superficie libre

**Identificador definitivo:** FS-C01 (`freesurface/FS-C01/`). La etapa científica correspondiente se denomina B-FS-01.

**Estado:** PREPARED_NOT_MESHED_OR_RUN. Los datos son un **análogo hidrodinámico agua–aire** basado en `compressibleVoF/damBreak` de OpenFOAM Foundation v14. No representa hierro fundido, contracción, alimentación, porosidad, solidificación ni molde térmicamente acoplado.

Dimensiones nominales 40×60×10 mm, malla 80×120×1, llenado inicial 40 mm, atmósfera superior y gravedad −Y. Volumen inicial de líquido 1.6e−5 m³; horizonte 0.1 s.

Los 20 archivos de entrada en `0/`, `constant/` y `system/` son idénticos a los del artefacto certificado estáticamente en [GitHub Actions #39409347758](https://github.com/michels-lab/QuickCup-Solidification/actions/runs/39409347758). Sus hashes de contenido están en `BFS01_MANIFEST.json`. El nombre B-FS-01 permanece en el esquema de procedencia para conservar compatibilidad con el auditor.

**Para validar en Ubuntu/OpenFOAM 14:** dentro de este caso ejecutar `blockMesh`, `checkMesh`, revisar logs/parches y luego `foamRun`. Guardar las salidas reales y revisar `alpha.water`, volumen, masa, Co y estabilidad de la interfaz. El script `analysis_tools/granada_bfs01_vof_benchmark.py audit` comprueba volumen mediante postprocesamiento auténtico, pero no masa ni shrinkage.

**Origen y licencia:** entradas derivadas del [tutorial oficial de OpenFOAM Foundation 14](https://github.com/OpenFOAM/OpenFOAM-14/tree/master/tutorials/compressibleVoF/damBreak), bajo GNU GPL. No se han incluido datos de una corrida ni se han modificado casos históricos del investigador.
