#!/usr/bin/env bash
# ONE single non-destructive C3D-05 acceptance review for saved HEX8 pilot.
# Native logs + CAD audit + contact only. No remesh, no checkMesh execution,
# no OpenFOAM solver and no overwriting any existing case evidence.
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
TESTS="$HERE/../tests"
# The first independent review failed a bundled CAD provenance condition.
# Keep the original output immutable and emit the expanded per-predicate audit
# at a NEW path. Never overwrite either audit, logs or meshes.
PREVIOUS="$CASE/HEX8_NATIVE_ACCEPTANCE_REVIEW_20261119.json"
OUTPUT="$CASE/HEX8_NATIVE_ACCEPTANCE_REVIEW_PROVENANCE_DETAIL_20261119.json"

if [[ ! -d "$CASE/constant/metal/polyMesh" || ! -d "$CASE/constant/mold/polyMesh" ]]; then
    echo "BLOCKED: preserved native HEX8 mesh missing: $CASE" >&2
    exit 2
fi
echo "=== C3D-05 CASO B | SECOND INDEPENDENT ACCEPTANCE REVIEW ==="
echo "Read-only mesh evidence: $CASE"
echo "No Gmsh/OpenFOAM/CFD executed. All earlier trials preserved."
if [[ ! -f "$PREVIOUS" ]]; then
    echo "NOTICE: previous bundled-gate report not found: $PREVIOUS" >&2
else
    echo "Original independent audit preserved unchanged: $PREVIOUS"
fi
echo
echo "=== 1/2: Source checks and real-problem regressions ==="
bash "$TESTS/test_step_gmsh_static.sh"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s "$TESTS" -p 'test_review_accepted_hex_mesh.py' -v
echo
echo "=== 2/2: Expanded STRICT source provenance values and all native gates ==="
if [[ -e "$OUTPUT" ]]; then
    echo "PRESERVED: audit evidence already exists; refusing to overwrite: $OUTPUT"
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/review_accepted_hex_mesh.py" "$CASE"
else
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/review_accepted_hex_mesh.py" "$CASE" --out "$OUTPUT"
fi
echo
echo "REVIEW FINISHED. Only geometric-topological acceptance; no mesh convergence or CFD."
echo "Risk: >70-degree non-orthogonal faces remain, so validate numerical schemes and stability before solving."
