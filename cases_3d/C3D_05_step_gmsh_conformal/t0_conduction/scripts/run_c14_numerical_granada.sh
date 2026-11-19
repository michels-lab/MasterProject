#!/usr/bin/env bash
# ONE complete Case B T0 numerical-reference Granada handoff.
# C14 ARCHIVED model values ONLY; not JMatPro/experiment; no accepted mesh changes.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
MODE="${1:---prepare}"
if [[ "$MODE" != "--prepare" && "$MODE" != "--solve" ]]; then
    echo "Usage: bash $0 [--prepare | --solve]" >&2
    exit 2
fi
INPUTS="${C3D05_C14_NUMERICAL_INPUTS:-$HOME/OpenFOAM/C3D05_T0_C14_NUMERICAL_INPUTS.json}"
OUTPUT="${C3D05_C14_NUMERICAL_OUT:-$HOME/OpenFOAM/C3D05_T0_C14_SHK_01}"
NATIVE="${C3D05_ACCEPTED_NATIVE:-$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02}"
RUNLOG="$OUTPUT/log.foamMultiRun.C14_NUMERICAL_T0"
RUNREPORT="$OUTPUT/T0_NUMERICAL_RUN_STATUS.json"

echo "=== MASTERPROJECT B C3D-05 | ETAPA 3/7 | 2/7=29% technical gates (NO thesis) ==="
echo "=== C14-ARCHIVED two-SOLID numerical shakedown, NOT real QuickCup parameters ==="
python3 -B "$REPO/tools/check_project_delivery_contract.py" --status

# Verify native installed Foundation14 before generating a new destination.
if [[ "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    for bashrc in /opt/openfoam14/etc/bashrc "$HOME/OpenFOAM/OpenFOAM-14/etc/bashrc"; do
        if [[ -r "$bashrc" ]]; then
            set +u
            source "$bashrc"
            set -u
            break
        fi
    done
fi
if [[ "${WM_PROJECT_VERSION:-}" != "14" ]] ||
   ! command -v foamMultiRun >/dev/null 2>&1 ||
   ! command -v foamDictionary >/dev/null 2>&1; then
    echo "BLOCKED: OpenFOAM Foundation14 must exist. No simulation or reference case created." >&2
    exit 4
fi
echo "=== 1/3: source C14 parameters by real source SHA and strict hypotheses ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/c14_numerical_reference.py" --out "$INPUTS"

echo "=== 2/3: one-shot case materialization and ten native dictionary parses ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/run_t0_granada.py" \
    --inputs "$INPUTS" --source "$NATIVE" --out "$OUTPUT"

echo "=== 3/3: independent closed-energy equilibrium target from ORIGINAL checkMesh volumes ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/t0_energy_reference.py" \
    --inputs "$INPUTS" --source "$NATIVE" \
    --out "$OUTPUT/T0_CLOSED_ENERGY_REFERENCE.json"

if [[ "$MODE" == "--prepare" ]]; then
    echo "PACKAGE_PREPARED_C14_NUMERICAL_ONLY: No foamMultiRun executed; experimental C3D-05 G3 still open."
    exit 0
fi

# --solve is an explicit user-initiated numerical solver experiment.
# One invocation performs both preparation and run, never returns success
# merely because the executable exited with 0.
if [[ -e "$RUNLOG" || -L "$RUNLOG" || -e "$RUNREPORT" || -L "$RUNREPORT" ]]; then
    echo "BLOCKED: previous local numerical solver attempt/report exists; no rerun/overwrite." >&2
    exit 2
fi
echo "=== EXPLICIT --solve: executing isolated 100-step numerical shakedown ==="
set +e
foamMultiRun -case "$OUTPUT" > "$RUNLOG" 2>&1
result=$?
set -e
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_t0_numerical_run.py" \
    --inputs "$INPUTS" --log "$RUNLOG" --exit-code "$result" --out "$RUNREPORT"
echo "NUMERICAL_RUN_RECORDED: solver completion classified; energy/interface/experiment NOT validated."
