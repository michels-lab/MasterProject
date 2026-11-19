#!/usr/bin/env bash
# Static preflight for CASO A V3. No OpenFOAM call, no native mesh, no CFD.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/../../../.." && pwd)"
V2="$REPO/cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/system/blockMeshDict"
[[ -s "$V2" && -s "$ROOT/Allmesh" && -s "$ROOT/run_v3_sweep.sh" ]]
bash -n "$ROOT/Allmesh" "$ROOT/run_v3_sweep.sh"
python3 - "$ROOT" <<'PY'
import ast
from pathlib import Path
import sys
root = Path(sys.argv[1])
for p in (root / "scripts/build_v3_dictionary.py",
          root / "scripts/summarize_trial.py",
          root / "tests/test_v3_diff.py"):
    ast.parse(p.read_text(encoding="utf-8"))
print("V3_PYTHON_AST_OK")
PY
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
for param in "-0.15 1.75" "0.30 2.30"; do
    read -r delta grade <<< "$param"
    test_out="$TEMP/dict_$grade"
    python3 "$ROOT/scripts/build_v3_dictionary.py" \
        "$V2" "$test_out" --delta "$delta" --grading "$grade" >/dev/null
    python3 "$ROOT/tests/test_v3_diff.py" \
        "$V2" "$test_out" --delta "$delta" --grading "$grade"
    python3 "$REPO/cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_blockmesh_topology.py" \
        "$test_out" > /dev/null
done
python3 "$ROOT/scripts/summarize_trial.py" --header >/dev/null
echo "V3_STATIC_SUITE_OK: 2 generator variants, diff contract and mesh topology"
echo "NOT EXECUTED: Foundation 14, checkMesh or CFD."
