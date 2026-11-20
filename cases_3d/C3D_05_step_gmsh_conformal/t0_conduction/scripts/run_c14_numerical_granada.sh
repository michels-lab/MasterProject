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
echo "=== 1/6: source C14 parameters by real source SHA and strict hypotheses ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/c14_numerical_reference.py" --out "$INPUTS"

echo "=== 2/6: one-shot case materialization and ten native dictionary parses ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/run_t0_granada.py" \
    --inputs "$INPUTS" --source "$NATIVE" --out "$OUTPUT"

echo "=== 3/6: independent closed-energy equilibrium target from ORIGINAL checkMesh volumes ==="
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
# If a native run was ALREADY completed, resume its energy diagnostics
# without rerunning the solver or overwriting its original evidence.
if [[ -L "$RUNLOG" || -L "$RUNREPORT" ]]; then
    echo "BLOCKED: native report/log symlink is not trusted." >&2
    exit 2
fi
if [[ -e "$RUNLOG" || -e "$RUNREPORT" ]]; then
    if [[ ! -f "$RUNLOG" || ! -f "$RUNREPORT" ]]; then
        echo "BLOCKED: incomplete prior solver attempt preserved for forensic review; not restarted." >&2
        exit 2
    fi
    echo "=== Reuse previous native solver evidence (SHA-verified below), NO rerun ==="
else
    echo "=== EXPLICIT --solve: executing isolated 100-step numerical shakedown ==="
    set +e
    foamMultiRun -case "$OUTPUT" > "$RUNLOG" 2>&1
    result=$?
    set -e
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_t0_numerical_run.py" \
        --inputs "$INPUTS" --log "$RUNLOG" --exit-code "$result" --out "$RUNREPORT"
fi

echo "=== 4/6: FOUNDATION14 native regional volAverage(T), volumetric energy and effective exchange ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/postprocess_t0_energy.py" \
    --case "$OUTPUT" --inputs "$INPUTS" \
    --reference "$OUTPUT/T0_CLOSED_ENERGY_REFERENCE.json" \
    --run-status "$RUNREPORT" --solver-log "$RUNLOG" \
    --out "$OUTPUT/T0_NATIVE_ENERGY_HISTORY.json" --native
echo "NUMERICAL_ENERGY_METRICS_RECORDED: native volumetric balance is observed, not physically accepted."
echo "=== 5/6: native Foundation14 bilateral mappedWall q on ALL 12636 faces per side ==="
bash "$HERE/run_native_t0_patch_flux.sh" "$OUTPUT" "$INPUTS" "$RUNLOG" "$RUNREPORT"
echo "=== 6/6: consolidate hashed regional T energy + 12636 native face pairs into ONE readable result ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/finalize_t0_granada.py" \
    --case "$OUTPUT" --inputs "$INPUTS"
echo "GRANADA_B_T0_NUMERICAL_DIAGNOSTICS_COMPLETE: Evidence summarized; NO mesh/time convergence or experimental validation."
