> **20-11-2026 | GRANADA_C3D05_PATCH_Q_12636_20261120 — separacion de evidencia:** el extractor C++ `c3d05PatchFlux` se compila exclusivamente mediante `wmake` Foundation14 **en copia aislada del caso WSL**, nunca en GitHub Actions ni en el árbol del repo. La CI solo verifica código/CSV sintéticos y scripts Bash; no demuestra compilación nativa, flujo por cara, continuidad térmica ni validación física. Caso B **etapa 3/7, 2/7=29% hitos técnicos**. [Informe](docs/granada/C3D05_T0_FLUJO_INTERFAZ_12636_CARAS_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_NATIVE_ENERGY_20261120:** GitHub CI prueba parsers de `volFieldValue`, balances e integridad SHA con fixtures, pero nunca ejecuta `foamMultiRun` ni `foamPostProcess` nativos; la única futura acción WSL de Caso B es `run_c14_numerical_granada.sh --solve`, que incluye postprocesamiento y métricas sin validar aún energía ni interfaz cara-cara. Caso B **3/7, 2/7 hitos=29% técnico**. [Criterios](docs/granada/C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md).

> **19-11-2026 | GRANADA_C3D05_C14_NUMERIC_SHK_20261119 — SEPARACIÓN CI/WSL:** GitHub prueba puente C14, equilibrio teórico, auditores de log y sintaxis Bash, pero NUNCA ejecuta `foamMultiRun`. Un único `--solve` manual de la laptop puede generar la referencia numérica aislada del Caso B, sin realizar pruebas individuales. Sin resultados CFD aún; etapa 3/7, avance 2/7 hitos (29% técnico). [Informe](docs/granada/C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md).

> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119 — REGLA PERMANENTE PARA TODOS LOS CASOS:** entregar hitos integrales con QA interno y corrección de raíz, sin muchas pruebas WSL por pieza; comunicar SIEMPRE **ETAPA + AVANCE + evidencia + bloqueo + siguiente hito**. Caso B C3D-05: **etapa 3/7 T0; 2/7 hitos = 29% técnico** (NO tesis, CFD o validación). CAD/HEX8 y contacto aceptados; 1,826 caras >70°; T0 preparado, faltan propiedades físicas y no se ha ejecutado. [Política](docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [estado canónico](docs/PROJECT_STAGE_STATUS.json). La evidencia histórica permanece intacta.

# GitHub execution boundary — MasterProject / QuickCup

> **C3D-01 al 10-11-2026:** las mallas 3D y diagnósticos se ejecutaron **solo en la laptop**. `subsetMesh -cellSet materialVolume` conservó **1,209,777 celdas; 151.230 cm³; 15 concavidades, 8 face-tets deficientes, 17 determinantes pequeños y 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` produjo `region1` (molde probable, **825,994 celdas; 3 fallos**) y `region2` (metal probable, **383,783 celdas; 2 fallos**), pero informó **`No interfaces to add`**: no hay interfaz térmica acoplada ni solver CFD 3D ejecutado. `-cellZones 'metal'` permanece **sin ejecutar**. [Estado de malla](docs/C3D_01_ESTADO_REAL_20261110_ES.md). **Ningún proceso CFD se trasladó a Actions.**


Original policy: 2026-10-08; current clarification: 2026-11-10

**Only the researcher runs CFD on a laptop.** The repository receives completed case outputs through `git push`, then performs read-only, non-CFD scientific evidence checks. No GitHub Actions workflow is authorized to install OpenFOAM, generate variants, execute `Allrun`, `Allclean`, `blockMesh` or `foamMultiRun`, or overwrite existing simulation results.

**November 2026 evidence boundary:** STL binaries and local `surfaceCheck`/repair logs are versioned. The `~/OpenFOAM/C3D01_snappy_NTC8Dj` trial produced a rejected 3D mesh (two `checkMesh` failures) **on the laptop only**. Its full meshing logs have not yet been archived to Git; [current register](docs/C3D_01_ESTADO_REAL_20261110_ES.md). No GitHub action ran the OpenFOAM mesher or solver.

## Disabled historical workflows

The following GitHub Actions workflow files were intentionally removed from the active `.github/workflows/` directory, preserving all scientific case data:
- `run-v10-v11-openfoam14.yml` (previously installed OpenFOAM and ran B10/C10/B11/C11)
- `run-v12-v13-openfoam14.yml` (previously installed OpenFOAM and ran B12/C12/B13/C13)
- `generate-v8-v9-cases.yml` (previously generated and committed case variants from GitHub; variant creation now remains under the user's control)

The currently authorized workflow for new results is `quickcup-research-audit.yml`: checks committed logs, `postProcessing/`, case registry and documentation, produces an audit artifact without any solver run.

**Agent role files are guidance, not continuously operating autonomous AI.** GitHub Actions success must be separately verified. Historic workflow runs remain accessible in GitHub's run history even though their workflow definitions were retired.
