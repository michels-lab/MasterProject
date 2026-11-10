# GitHub execution boundary — MasterProject / QuickCup

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
