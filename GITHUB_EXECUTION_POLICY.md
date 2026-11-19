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
