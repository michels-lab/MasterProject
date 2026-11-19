#!/usr/bin/env bash
# C3D-04 CASO A ONLY. One command, a bounded controlled V3 native mesh sweep.
# All candidates are generated into FRESH folders; previous evidence is immutable.
# No C14 field modifications, NO CFD and NO unrelated Case B (C3D-05) changes.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${C3D04_V3_SWEEP_OUT:-$HOME/OpenFOAM/C3D04_V3_BASAL_SWEEP_01}"
if [[ "$BASE" != /* ]]; then
    echo "ERROR: C3D04_V3_SWEEP_OUT must be an absolute path" >&2
    exit 2
fi
if [[ -e "$BASE" || -L "$BASE" ]]; then
    echo "PRESERVED: this V3 sweep already exists. Refusing to overwrite: $BASE" >&2
    exit 2
fi

# One new immutable sweep root; no touching V1, V2 or other projects.
mkdir -p "$BASE"
summary="$BASE/C3D04_V3_SWEEP_SUMMARY.tsv"
python3 "$ROOT/scripts/summarize_trial.py" --header > "$summary"
cat > "$BASE/SWEEP_PARAMETERS.txt" <<'EOF'
CASE_A_ONLY / C3D04_V3_BASAL_SWEEP / NO_CFD
Parameters:
  Metal corner: symmetric adjustment (mm) of four INTERIOR vertices at Y=-39.8.
  Mold radial: simpleGrading for all 108 ring blocks, baseline V2 = 1.5.
  Metal/mold boundary surfaces, arcs, section Y, zones, patch labels, and cell counts unchanged.
  Early stop on the first fully ACCEPTED native candidate.
  Rejected runs and logs are retained. No parameter will suppress a checkMesh failure.
EOF

# Short bounded experiment: increase sand grading while testing both
# directions of corner movement. Native checkMesh selects the winner.
TRIALS=(
    "T01 -0.15 1.75"
    "T02  0.15 1.90"
    "T03 -0.30 2.10"
    "T04  0.30 2.30"
    "T05 -0.45 2.50"
    "T06  0.45 2.65"
)

echo "C3D04 CASO A / V3 experiment starts. No CFD."
echo "Evidence root: $BASE"
winner=""
for item in "${TRIALS[@]}"; do
    read -r id delta grade <<< "$item"
    out="$BASE/$id"
    echo
    echo "=== C3D04 V3 $id : interior delta=$delta mm | mold radial grading=$grade ==="
    rc=0
    C3D04_V3_OUT="$out" \
    C3D04_V3_CORE_DELTA="$delta" \
    C3D04_V3_SAND_GRADING="$grade" \
        bash "$ROOT/Allmesh" > "$BASE/log.runner.$id" 2>&1 || rc=$?

    python3 "$ROOT/scripts/summarize_trial.py" "$out" \
        --trial "$id" --delta "$delta" --grading "$grade" --rc "$rc" >> "$summary"
    # Display concise summary; detailed VTK, logs and diagnostic remain local.
    tail -n 1 "$summary" | tr '\t' ' '
    if [[ "$rc" == 0 ]] &&
       grep -Fq "MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED" \
           "$out/NATIVE_BUILD_STATUS.txt"; then
        winner="$id"
        printf "PRELIMINARILY_ACCEPTED / %s / NO_CFD\n" "$out" \
            > "$BASE/SWEEP_FINAL_STATUS.txt"
        echo "PRELIMINARY NATIVE QUALITY + CONTACT GATES PASSED: $id"
        break
    fi
    echo "REJECTED_OR_BLOCKED: $id. Preserved its log, mesh and defect evidence."
done

echo
echo "=== FINAL COMPARATIVE SUMMARY ==="
cat "$summary"
if [[ -z "$winner" ]]; then
    printf "ALL_TRIALS_REJECTED_OR_BLOCKED / NO_CFD\n" \
        > "$BASE/SWEEP_FINAL_STATUS.txt"
    echo
    echo "No accepted native mesh in this bounded V3 sweep. No CFD."
    echo "Inspect: $BASE and its logs, diagnostics, summary."
    exit 5
fi
echo
echo "Preliminarily accepted native candidate: $BASE/$winner"
echo "Still mandatory: full CAD surface-distance check, 3D initial/boundary conditions,"
echo "mesh independence, physical-field transfer, and solver validation. NO CFD yet."
