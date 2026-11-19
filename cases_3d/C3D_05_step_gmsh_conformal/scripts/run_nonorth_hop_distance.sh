#!/usr/bin/env bash
# C3D-05 Case B: ONE-COMMAND read-only spatial *topological* localization.
# No OpenFOAM solver, no checkMesh rerun, no Gmsh, no mesh writes.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CASE="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
TESTS="$ROOT/tests"
REPORT="$CASE/NONORTH_CELL_HOP_DISTANCE_20261119.json"
PREVIOUS="$CASE/NONORTH_FACESET_TOPOLOGY_AUDIT_20261119.json"
if [[ ! -d "$CASE/constant/metal/polyMesh" || ! -d "$CASE/constant/mold/polyMesh" ]]; then
    echo "BLOCKED: accepted QuickCup HEX8 case missing: $CASE" >&2
    exit 2
fi
if [[ ! -s "$PREVIOUS" ]]; then
    echo "BLOCKED: native prior faceSet audit missing; refusing to infer distances" >&2
    exit 2
fi
if [[ -r /proc/meminfo ]]; then
    mem="$(awk '/^MemAvailable:/{print $2;exit}' /proc/meminfo)"
    if [[ "$mem" =~ ^[0-9]+$ ]] && (( mem < 2097152 )); then
        echo "RESOURCE_GATE: less than 2 GiB WSL RAM available for read-only CSR graph" >&2
        exit 3
    fi
fi
echo "=== C3D-05 | 1826 severe internal faces: how MANY cell layers from the interface? ==="
echo "Existing CAD/HEX8 mesh and all past evidence preserved. NO CFD, NO REMESH."
echo "=== 1/3: source safety checks + regression tests ==="
bash "$TESTS/test_step_gmsh_static.sh"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$TESTS" -p 'test_audit_nonorth_hop_distance.py' -v
echo "=== 2/3: revalidate original CAD HEX8 native/reciprocal gates ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/review_accepted_hex_mesh.py" "$CASE"
echo "=== 3/3: compute exact GRAPH hops using only original owner/neighbour/faceSets ==="
if [[ -e "$REPORT" ]]; then
    echo "PRESERVED: prior hop report exists; not overwriting: $REPORT"
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_nonorth_hop_distance.py" "$CASE"
else
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_nonorth_hop_distance.py" "$CASE" --out "$REPORT"
fi
echo "DONE: GRAPH DISTANCE DIAGNOSTIC ONLY; no physical-distance or numerical-accuracy claim."
