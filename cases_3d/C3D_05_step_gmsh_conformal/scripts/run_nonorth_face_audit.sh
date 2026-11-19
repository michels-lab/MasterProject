#!/usr/bin/env bash
# ONE-COMMAND C3D-05 follow-up: no meshing/checkMesh/solver; only preserved evidence.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TESTS="$ROOT/tests"
CASE="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
REPORT="$CASE/NONORTH_FACESET_TOPOLOGY_AUDIT_20261119.json"

if [[ ! -d "$CASE/constant/metal/polyMesh" || ! -d "$CASE/constant/mold/polyMesh" ]]; then
    echo "BLOCKED: preserved accepted Case B HEX8 meshes missing: $CASE" >&2
    exit 2
fi
echo "=== C3D-05 CASE B: WHERE ARE THE 1826 NONORTHOGONAL FACES? ==="
echo "Only saved polyMesh, faceSets and checkMesh logs. No CFD; no mesh writes."
echo "=== 1/3 source/static and isolated synthetic regressions ==="
bash "$TESTS/test_step_gmsh_static.sh"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$TESTS" -p 'test_audit_nonorthogonal_faces.py' -v
echo "=== 2/3 verify accepted original mesh evidence remains accepted ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/review_accepted_hex_mesh.py" "$CASE"
echo "=== 3/3 classify REAL native faceSets relative to coupled interface ==="
if [[ -e "$REPORT" ]]; then
    echo "Previous faceSet report preserved without overwrite: $REPORT"
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_nonorthogonal_faces.py" "$CASE"
else
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_nonorthogonal_faces.py" "$CASE" --out "$REPORT"
fi
echo "DONE: Native FACESET review only. Thermal solver, convergence, physics: NOT RUN."
