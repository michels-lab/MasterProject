#!/usr/bin/env bash
# ONE-COMMAND C3D-05 CASE B: isolated HXT-10 volume meshing candidate.
# Never delete or reuse earlier Delaunay or Netgen-blocked Frontal output.
# Pilot mesh and audits only: no solver, no CFD, no change to tolerances.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TESTS="$ROOT/tests"
BASE="$HOME/OpenFOAM/C3D05_STEP_GMSH_PILOT_01"
FRONTAL="$HOME/OpenFOAM/C3D05_STEP_GMSH_FRONTAL_01"
OUT="$HOME/OpenFOAM/C3D05_STEP_GMSH_HXT_01"

if [[ -e "$OUT" || -L "$OUT" ]]; then
    echo "PRESERVED: HXT result directory already exists: $OUT" >&2
    echo "No overwrite or rerun. Inspect this existing case separately." >&2
    exit 2
fi
if [[ ! -s "$BASE/PILOT_MESH_REPORT.tsv" || ! -s "$BASE/STEP_CAD_AUDIT.json" ]]; then
    echo "BLOCKED: original Delaunay experiment evidence is unavailable: $BASE" >&2
    exit 2
fi
if [[ ! -f "$FRONTAL/log.gmsh3d" ]]; then
    echo "BLOCKED: expected Frontal dependency-failure evidence not found: $FRONTAL/log.gmsh3d" >&2
    exit 2
fi

echo "=== CASO B C3D-05: ENSAYO HXT — UN SOLO COMANDO, NO CFD ==="
echo "Original Delaunay: $BASE — PRESERVED"
echo "Frontal/Netgen unavailable: $FRONTAL — PRESERVED"
echo "Candidate HXT: $OUT — FRESH OUTPUT ONLY"
echo "Same STEP, fragmentation, sizing 1.8 mm, scaling, checkMesh and contact gates"
echo "Only 3D meshing algorithm changes from 1 (Delaunay) to 10 (HXT)"
echo
echo "=== 1/4: Verify sources and Python scripts ==="
bash "$TESTS/test_step_gmsh_static.sh"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$TESTS" -p 'test_diagnose_existing_mesh.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
    -s "$TESTS" -p 'test_audit_underdetermined_topology.py' -v

echo
echo "=== 2/4: Check whether THIS Gmsh build supports HXT, using in-memory test only ==="
if ! PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/preflight_hxt.py"; then
    echo "BLOCKED_HXT_CAPABILITY: no production mesh started; all saved cases preserved" >&2
    exit 3
fi

echo
echo "=== 3/4: Generate CAD/STEP mesh with HXT and run OpenFOAM14 native gates ==="
if C3D05_OUT="$OUT" C3D05_ALGORITHM3D=10 bash "$ROOT/Allmesh"; then
    native="ACCEPTED"
else
    code=$?
    native="NOT_ACCEPTED"
    echo "Candidate did not pass all native gates (runner exit $code). Preserved: $OUT"
fi

echo
echo "=== 4/4: Read native logs/topology/contact without remeshing ==="
if [[ -d "$OUT/constant/metal/polyMesh" && -d "$OUT/constant/mold/polyMesh" ]]; then
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/diagnose_existing_mesh.py" "$OUT" ||
        echo "WARNING: diagnostic reader failed; inspect preserved log.checkMesh.* files" >&2
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_underdetermined_topology.py" "$OUT" ||
        echo "WARNING: underdetermined cellSet not available for topology reader" >&2
    if [[ -e "$OUT/CONTACT_AREA_REPORT.json" ]]; then
        echo "Contact area was already computed by Allmesh:"
        python3 -m json.tool "$OUT/CONTACT_AREA_REPORT.json"
    elif [[ ! -e "$OUT/CONTACT_AREA_DIAGNOSTIC_ONLY.json" ]]; then
        if ! PYTHONDONTWRITEBYTECODE=1 python3 -B \
            "$HERE/measure_interface_area.py" "$OUT" \
            --out "$OUT/CONTACT_AREA_DIAGNOSTIC_ONLY.json"; then
            echo "WARNING: contact-area gate failed; retain report for comparison" >&2
        fi
    fi
else
    echo "No complete regional meshes; inspect preserved early failure."
    if [[ -f "$OUT/NATIVE_BUILD_STATUS.txt" ]]; then
        cat "$OUT/NATIVE_BUILD_STATUS.txt"
    fi
    if [[ -f "$OUT/log.gmsh3d" ]]; then
        tail -n 24 "$OUT/log.gmsh3d"
    fi
fi
echo
echo "=== HXT EXPERIMENT RESULT: $native | NO CFD ==="
echo "Control: 306 low determinant parent, 96 metal, 402 mold; contact area gate PASSED"
echo "Candidate output: $OUT"
echo "HXT is tetrahedral too: zero low-determinant cells is NOT guaranteed."
echo "Next action must be based on measured checkMesh + cell topology evidence."
[[ "$native" == ACCEPTED ]] || exit 5
