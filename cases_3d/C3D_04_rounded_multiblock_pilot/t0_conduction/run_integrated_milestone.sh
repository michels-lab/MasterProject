#!/usr/bin/env bash
# CASO A C3D-04 V4/T02: one end-to-end PRE-CFD milestone entrypoint.
# NO blockMesh, checkMesh, foamMultiRun execution, or modifications to T02.
# Do not ask user to run until this is a meaningful end-to-end milestone.
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_A="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$CASE_A/../.." && pwd)"
INPUTS="${C3D04_T0_INPUTS:-$HERE/T0_INPUTS.json}"
SOURCE="${C3D04_NATIVE_SOURCE:-$HOME/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02}"
OUTPUT="${C3D04_T0_OUT:-$HOME/OpenFOAM/C3D04_A_T0_CONDUCTION_01}"
MODE="${1:---preflight}"
# OpenFOAM Foundation documents an Ubuntu 26.04 pvdataserver hang
# unless HWLOC_COMPONENTS=-gl is exported before sourcing its bashrc.
# Source at most once; do not trigger an avoidable GUI/ParaView hang.
load_openfoam14_once() {
    if [[ "${WM_PROJECT_VERSION:-}" == "14" ]] &&
       command -v foamDictionary >/dev/null 2>&1 &&
       command -v foamMultiRun >/dev/null 2>&1; then
        return 0
    fi
    if [[ ! -r /opt/openfoam14/etc/bashrc ]]; then
        return 0
    fi
    local ubuntu_version=""
    if [[ -r /etc/os-release ]]; then
        ubuntu_version="$(. /etc/os-release; printf '%s' "${VERSION_ID:-}")"
    fi
    if [[ "$ubuntu_version" == "26.04" ]]; then
        export HWLOC_COMPONENTS=-gl
        echo "Ubuntu 26.04 Foundation14 HWLOC workaround active"
    fi
    set +u
    source /opt/openfoam14/etc/bashrc
    set -u
}


if [[ "$MODE" != "--preflight" && "$MODE" != "--materialize" ]]; then
    echo "Usage: bash $0 [--preflight | --materialize]" >&2
    exit 2
fi

echo "=== MASTERPROJECT CASO A: INTEGRATED T0 STAGE (NO CFD) ==="
echo "=== A/4: canonical roadmap and explicit completion fraction ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$CASE_A/scripts/report_case_a_progress.py"
echo "=== B/4: bundled static positive+negative and source protection regressions ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$HERE/tests" -p 'test_integrated_case_a.py' -v
echo "=== C/4: native saved V4/T02 gates and thermal inputs ==="
# Do not create even a separate materialized case if the real Foundation14
# executable environment is absent. Pre-check this BEFORE any side effects.
if [[ "$MODE" == "--materialize" ]]; then
    load_openfoam14_once
    if [[ "${WM_PROJECT_VERSION:-}" != "14" ]] ||
       ! command -v foamMultiRun >/dev/null 2>&1 ||
       ! command -v foamDictionary >/dev/null 2>&1; then
        echo "BLOCKED_BEFORE_MATERIALIZATION: OpenFOAM Foundation14 foamMultiRun+foamDictionary required; nothing created" >&2
        exit 4
    fi
    if [[ -e "$OUTPUT" || -L "$OUTPUT" ]]; then
        echo "BLOCKED_NO_OVERWRITE: existing T0 output preserved at $OUTPUT" >&2
        exit 4
    fi
fi
if [[ "$MODE" == "--materialize" ]]; then
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/scripts/prepare_case_a_t0.py" --inputs "$INPUTS" --source "$SOURCE" --out "$OUTPUT" --materialize
else
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/scripts/prepare_case_a_t0.py" --inputs "$INPUTS" --source "$SOURCE" --out "$OUTPUT"
fi

echo "=== D/4: Foundation14 availability, without running solver ==="
load_openfoam14_once
if [[ "${WM_PROJECT_VERSION:-}" == "14" ]] &&
   command -v foamMultiRun >/dev/null 2>&1 &&
   command -v foamDictionary >/dev/null 2>&1; then
    echo "ENV_OF14_AVAILABLE: foamMultiRun and foamDictionary found; NO solver executed."
else
    echo "ENV_OF14_PENDING: OpenFOAM Foundation 14 executable environment not verified."
    if [[ "$MODE" == "--materialize" ]]; then
        echo "MATERIALIZED_BUT_NATIVE_DICTIONARY_SYNTAX_NOT_YET_CHECKED" >&2
        exit 4
    fi
fi

if [[ "$MODE" == "--materialize" ]]; then
    echo "T0_ATOMICALLY_PUBLISHED_AND_ALL_10_NATIVE_DICTIONARIES_PARSED; NO CFD."
    echo "Verified report: $OUTPUT/T0_PREPARATION_REPORT.json"
fi
echo "INTEGRATED_T0_SOURCE_AND_STATIC_CHECKS_FINISHED; THIS IS NOT A COMPLETED PHYSICAL OR CFD HITO."
