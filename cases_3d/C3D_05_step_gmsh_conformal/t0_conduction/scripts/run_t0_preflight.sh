#!/usr/bin/env bash
# C3D-05 T0 — ONE COMMAND. Check actual OF14 installation and existing accepted
# CAD/HEX8 evidence. Never execute foamMultiRun or change original mesh.
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T0="$(cd "$HERE/.." && pwd)"
CASE_B="$(cd "$T0/.." && pwd)"
SOURCE="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
OUTPUT="$HOME/OpenFOAM/C3D05_T0_CONDUCTION_01"
INPUTS="${C3D05_T0_INPUTS:-$T0/T0_INPUTS.json}"

echo "=== CASE B C3D-05 | T0 CLOSED TWO-SOLID CONDUCTION PREFLIGHT (NO CFD) ==="
echo "Accepted geometry: $SOURCE"
echo "New thermal output (ONLY after vetted inputs): $OUTPUT"
echo "Inputs: $INPUTS"
echo "=== 1/4: isolated T0 regression and full case source protection ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$T0/tests" -p 'test_prepare_t0.py' -v
bash "$CASE_B/tests/test_step_gmsh_static.sh"

echo "=== 2/4: preserve/verify native parent+regions+CAD/HEX8/contact gates ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$CASE_B/scripts/review_accepted_hex_mesh.py" "$SOURCE"

echo "=== 3/4: installed OpenFOAM Foundation 14 capability only (no solve) ==="
if [[ "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    echo "T0_BLOCKED_ENVIRONMENT: source local OpenFOAM Foundation 14 bashrc; observed WM_PROJECT_VERSION='${WM_PROJECT_VERSION:-unset}'" >&2
    exit 4
fi
if ! command -v foamMultiRun >/dev/null 2>&1; then
    echo "T0_BLOCKED_ENVIRONMENT: Foundation 14 foamMultiRun not on PATH" >&2
    exit 4
fi
if ! command -v foamDictionary >/dev/null 2>&1; then
    echo "T0_BLOCKED_ENVIRONMENT: Foundation 14 foamDictionary not on PATH" >&2
    exit 4
fi
echo "PASS: Foundation 14 in WSL; executable foamMultiRun and foamDictionary discovered."
echo "IMPORTANT: availability/syntax in WSL does NOT prove T0 runs or conserves energy."

echo "=== 4/4: material/initial T provenance and numerical assumptions ==="
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/prepare_t0.py" \
    --inputs "$INPUTS" --source "$SOURCE" --out "$OUTPUT" --check-only
code=$?
set -e
if [[ "$code" == "3" ]]; then
    echo "T0_SCAFFOLD_VERIFIED_BUT_INPUTS_PENDING: all source geometry preserved; NO CASE CREATED, NO CFD."
    echo "Fill T0_INPUTS.json using evidence for rho, Cv, kappa, model molWeight and T for EACH material."
    echo "Then rerun same ONE command; materialization is a separate explicitly authorized stage."
    exit 0
fi
if [[ "$code" != "0" ]]; then
    echo "T0_PREFLIGHT_FAILED: missing or inconsistent source evidence; no CFD" >&2
    exit "$code"
fi
echo "T0_CONFIG_INPUTS_VALIDATED: ready to MATERIALIZE a separate case in a future controlled stage; NOT run or solved."
echo "NO CFD. NO SOLVER. No changes to accepted CAD/HEX8 mesh."
