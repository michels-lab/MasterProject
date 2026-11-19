#!/usr/bin/env bash
# CASO A only: bounded V4 native checkMesh experiments, one terminal command.
# Do not delete V1, V2, V3 or any other evidence. No CFD.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$ROOT/tests/test_v4_static.sh"

BASE="${C3D04_V4_SWEEP_OUT:-$HOME/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01}"
if [[ "$BASE" != /* ]]; then
    echo "ERROR: V4 output root must be absolute" >&2
    exit 2
fi
if [[ -e "$BASE" || -L "$BASE" ]]; then
    echo "PRESERVED: V4 sweep output already exists: $BASE" >&2
    exit 2
fi
T06="$HOME/OpenFOAM/C3D04_V3_BASAL_SWEEP_01/T06/system/blockMeshDict"
[[ -s "$T06" ]] || { echo "Cannot find preserved V3/T06 baseline: $T06" >&2; exit 2; }

mkdir -p "$BASE"
report="$BASE/C3D04_V4_SWEEP_SUMMARY.tsv"
python3 "$ROOT/scripts/summarize_trial.py" --header > "$report"
cat > "$BASE/SWEEP_PARAMETERS.txt" <<'EOF'
C3D04_CASE_A_V4 / NATIVE_MESH_ONLY / NO_CFD
Baseline: V3/T06 (metal 4 bad determinant cells, mold Mesh OK)
First test ONLY interior Y positions; if unsuccessful, test the rounded
metal transition contour at Y=-39.8 using interpolation between the two
already documented stations Y=-40 and Y=-39.8.
Do not conflate area/topology with 3D CAD surface fit.
Do not change mesh-quality criteria; retain all rejected meshes and logs.
EOF

# Category 1 is CAD-boundary preserving. Category 2 changes only the
# interface profile at one station; verify contact area and CAD fit again.
TRIALS=(
  "T01 inner_y -0.12"
  "T02 inner_y 0.12"
  "T03 inner_y 0.18"
  "T04 profile 0.90"
  "T05 profile 0.78"
  "T06 profile 0.65"
  "T07 profile 0.50"
)
winner=""
for item in "${TRIALS[@]}"; do
    read -r id mode value <<< "$item"
    OUT="$BASE/$id"
    echo
    echo "=== CASO A V4 $id : $mode = $value ==="
    rc=0
    C3D04_V4_OUT="$OUT" \
    C3D04_V4_MODE="$mode" \
    C3D04_V4_VALUE="$value" \
    C3D04_V4_BASE_DICT="$T06" \
      bash "$ROOT/Allmesh" > "$BASE/log.runner.$id" 2>&1 || rc=$?
    python3 "$ROOT/scripts/summarize_trial.py" "$OUT" \
      --trial "$id" --mode "$mode" --value "$value" --rc "$rc" >> "$report"
    tail -n 1 "$report" | tr '\t' ' '
    if [[ "$rc" == 0 ]] &&
       grep -Fq 'MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED' \
         "$OUT/NATIVE_BUILD_STATUS.txt"; then
        winner="$id"
        printf "NATIVE_MESH_AND_AREA_PRELIMINARILY_ACCEPTED / %s / NO_CFD\n" "$OUT" \
            > "$BASE/SWEEP_FINAL_STATUS.txt"
        echo "PASSED NATIVE CHECKMESH + AREA. Candidate preserved: $OUT"
        break
    fi
    echo "NOT_ACCEPTED: $id; details and spatial errors preserved in $OUT."
done
echo
echo "===== C3D04 V4 NATIVE COMPARISON ====="
cat "$report"
if [[ -z "$winner" ]]; then
    echo "ALL_V4_TRIALS_REJECTED_OR_BLOCKED / NO_CFD" > "$BASE/SWEEP_FINAL_STATUS.txt"
    echo "All V4 attempts retained; no validated native mesh, NO CFD."
    exit 5
fi
echo "SELECTED PRELIMINARY NATIVE MESH: $BASE/$winner"
echo "Before CFD: compare complete 3D CAD surfaces, check high non-orthogonality,"
echo "test mesh independence and transfer/validate CHT and phase-change physics."
