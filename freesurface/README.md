# freesurface — Casos de prueba

El caso **[FS-C01](FS-C01/)** es el primer banco de referencia de superficie libre de la ruta científica B-FS-01. Usa **agua–aire**, no hierro fundido; su estado es **PREPARED_NOT_MESHED_OR_RUN**, por lo que todavía no hay resultados CFD ni evidencia de contracción.

Consulte el [registro del caso](FS-C01/CASE_NOTES.md) y la [bitácora técnica B-FS-01](../docs/granada/B_FS_01_VOF_HYDRO_ANALOGUE_20261020.md). El manifiesto de FS-C01 contiene los SHA-256 de los 20 archivos de entrada.

## 2026-11-17 — Resultado local FS-C01

Una **copia externa aislada** de FS-C01 se sometió a mallado local Foundation 14: blockMesh y checkMesh -allGeometry -allTopology **PASS**. foamRun **falló durante la inicialización** por ausencia del requisito writeFields en la función waterVolume; no se obtuvieron pasos físicos CFD ni datos de contracción. La copia fallida se conserva. Se corrigió la entrada a writeFields false;, el generador y la trazabilidad SHA-256 en una rama específica con PR; queda **PENDIENTE repetir una nueva corrida FS-C01**. La carpeta fuente del repositorio sigue siendo un caso de entradas (sin malla de ejecución ni outputs CFD). Véase [registro FS-C01](FS-C01/CASE_NOTES.md) y [ejecución aislada en WSL](FS-C01/RUN_ISOLATED_UBUNTU_ES.md). Esta rama es independiente de C3D-02.
