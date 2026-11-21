#!/usr/bin/env bash
# ONE native integrated milestone command for ORIGINAL C14 physics on V4/T02.
# --preflight read-only / --materialize original 10s inputs only
# --smoke diagnostic 2 native steps / --run-full original 10s C14 native CFD.
# Original accepted mesh is immutable. Never overwrite a previous output.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_A="$(cd "$HERE/.." && pwd)"
MODE="${1:---smoke}"
SOURCE="${C3D04_NATIVE_SOURCE:-$HOME/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02}"
OUTPUT="${C3D04_C14_NATIVE_OUT:-$HOME/OpenFOAM/C3D04_A_C14_FLUID_SOLID_SMOKE_01}"

if [[ "$MODE" != "--smoke" && "$MODE" != "--materialize" && "$MODE" != "--preflight" && "$MODE" != "--run-full" ]]; then
    printf 'Usage: bash %s [--preflight|--materialize|--smoke|--run-full]\n' "$0" >&2
    exit 2
fi
if [[ "$MODE" == "--materialize" && -z "${C3D04_C14_NATIVE_OUT:-}" ]]; then
    OUTPUT="$HOME/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_INPUTS_01"
fi
if [[ "$MODE" == "--run-full" && -z "${C3D04_C14_NATIVE_OUT:-}" ]]; then
    OUTPUT="$HOME/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01"
fi
if [[ -z "${WM_PROJECT_VERSION:-}" || "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    if [[ ! -r /opt/openfoam14/etc/bashrc ]]; then
        echo 'Cannot source real OpenFOAM Foundation14; no files were created.' >&2
        exit 4
    fi
    # Official Ubuntu26.04 hwloc precaution. Only one source in one runner.
    if [[ -r /etc/os-release ]] && [[ "$(. /etc/os-release; echo "${VERSION_ID:-}")" == "26.04" ]]; then
        export HWLOC_COMPONENTS=-gl
    fi
    set +u
    source /opt/openfoam14/etc/bashrc
    set -u
fi
if [[ "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    echo 'BLOCKED: expected Foundation14' >&2
    exit 4
fi

echo "=== C3D04 CASO 3D-A: ORIGINAL C14 physics, no solid-solid surrogate ==="
echo "=== 1/3: Original C14 source thermophysics/phase-change checksum and regressions ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s "$HERE/tests" -p 'test_stage_c14_fluid_solid.py' -v
echo "=== 2/3: Native V4/T02 original mesh audited once (read-only) ==="
# Native gate includes prior accepted mesh logs, actual region patch names,
# reciprocal contact and all original C14 source hashes.
if [[ "$MODE" != "--preflight" ]]; then
    if [[ -e "$OUTPUT" || -L "$OUTPUT" ]]; then
        echo "BLOCKED: destination already exists, preserving prior results: $OUTPUT" >&2
        exit 4
    fi
fi
echo "=== 3/3: $MODE; new isolated case only; C14 metal=fluid, mold=solid ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/stage_c14_3d_case_a.py" \
  --source "$SOURCE" --out "$OUTPUT" "$MODE"

echo "C3D04_A_C14_3D_MILESTONE_COMMAND_ENDED; check native report for real result."
