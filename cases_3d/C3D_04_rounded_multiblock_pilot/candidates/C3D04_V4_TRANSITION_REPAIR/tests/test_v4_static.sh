#!/usr/bin/env bash
# CASO A V4 static preflight. No OpenFOAM calls, native mesh or CFD.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/../../../.." && pwd)"
CASE="$REPO/cases_3d/C3D_04_rounded_multiblock_pilot"
V2="$CASE/candidates/C3D04_V2_BASAL_QUALITY/system/blockMeshDict"
V3="$CASE/candidates/C3D04_V3_BASAL_SWEEP"
[[ -s "$V2" && -s "$ROOT/Allmesh" && -s "$ROOT/run_v4_sweep.sh" ]]
for entry in "$ROOT/Allmesh" "$ROOT/run_v4_sweep.sh"; do
    bash -n "$entry"
done
python3 - "$ROOT" <<'PY'
import ast
from pathlib import Path
import sys
root = Path(sys.argv[1])
for name in ("scripts/build_v4_dictionary.py",
             "scripts/summarize_trial.py",
             "tests/test_v4_diff.py"):
    ast.parse((root/name).read_text(encoding="utf-8"))
print("V4_PYTHON_AST_OK")
PY
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
python3 "$V3/scripts/build_v3_dictionary.py" "$V2" "$T/T06" --delta 0.45 --grading 2.65 >/dev/null
python3 "$V3/tests/test_v3_diff.py" "$V2" "$T/T06" --delta 0.45 --grading 2.65 >/dev/null
for pair in "inner_y -0.12" "inner_y 0.12" "profile 0.90" "profile 0.78"; do
    read -r mode value <<< "$pair"
    p="$T/v4_${mode}_${value}"
    python3 "$ROOT/scripts/build_v4_dictionary.py" "$T/T06" "$p" \
        --mode "$mode" --value "$value" >/dev/null
    python3 "$ROOT/tests/test_v4_diff.py" "$T/T06" "$p" --mode "$mode" --value "$value"
    python3 "$CASE/scripts/audit_blockmesh_topology.py" "$p" >/dev/null
done
echo "V4_STATIC_SUITE_OK: four synthetic candidates; exact geometry/patch gate"
echo "NOT EXECUTED: blockMesh, native checkMesh or CFD."
