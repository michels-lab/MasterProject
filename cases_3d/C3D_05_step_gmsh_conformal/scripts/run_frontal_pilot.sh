#!/usr/bin/env bash
# C3D-05 Caso B: ONE-COMMAND controlled Frontal mesh experiment, NO CFD.
# Baseline is preserved; run only in a brand-new separate output folder.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TESTS="$ROOT/tests"
OUT="$HOME/OpenFOAM/C3D05_STEP_GMSH_FRONTAL_01"
if [[ -e "$OUT" || -L "$OUT" ]]; then
    echo "PRESERVED: $OUT already exists; refusing to overwrite. Review that experiment instead." >&2
    exit 2
fi
BASE="$HOME/OpenFOAM/C3D05_STEP_GMSH_PILOT_01"
if [[ ! -s "$BASE/PILOT_MESH_REPORT.tsv" ]]; then
    echo "ERROR: cannot find preserved original Delaunay control case: $BASE" >&2
    exit 2
fi
echo "=== C3D-05 CASO B: ENSAYO CONTROLADO DE TOPOLOGÍA ==="
echo "Original: $BASE (Delaunay Gmsh=1, kept untouched)"
echo "Candidate: $OUT (Frontal Gmsh=4)"
echo "Fixed variables: BOTH original STEP, same 1.8 mm size, SI units, physical groups, checks"
echo "Only experimental change: Mesh.Algorithm3D 1 -> 4"
echo "NO CFD. Never ignore failed checkMesh determinant criterion."
echo
echo "=== A/3: Source and regression tests ==="
bash "$TESTS/test_step_gmsh_static.sh"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s "$TESTS" -p 'test_diagnose_existing_mesh.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s "$TESTS" -p 'test_audit_underdetermined_topology.py' -v
echo
echo "=== B/3: Generate fresh Frontal alternative and native OpenFOAM checks ==="
if C3D05_OUT="$OUT" C3D05_ALGORITHM3D=4 bash "$ROOT/Allmesh"; then
    native=ACCEPTED
else
    code=$?
    native=REJECTED
    echo "Candidate was NOT accepted (runner exit $code). Preserved: $OUT"
fi
echo
echo "=== C/3: Investigate the generated result without a second mesh ==="
if [[ -d "$OUT/constant/metal/polyMesh" && -d "$OUT/constant/mold/polyMesh" ]]; then
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/diagnose_existing_mesh.py" "$OUT" ||
        echo "WARNING: the native log postmortem needs inspection"
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/audit_underdetermined_topology.py" "$OUT" ||
        echo "WARNING: cellSet topology audit was incomplete"
    if [[ ! -e "$OUT/CONTACT_AREA_DIAGNOSTIC_ONLY.json" ]]; then
        if ! PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/measure_interface_area.py" \
            "$OUT" --out "$OUT/CONTACT_AREA_DIAGNOSTIC_ONLY.json"; then
            echo "WARNING: area computation or gate failed; inspect the preserved JSON/log"
        fi
    fi
else
    echo "Candidate stopped before both regional meshes were produced."
    [[ ! -f "$OUT/NATIVE_BUILD_STATUS.txt" ]] || cat "$OUT/NATIVE_BUILD_STATUS.txt"
fi
echo
echo "=== SCIENTIFIC STATUS: $native | NO CFD ==="
echo "Original Delaunay: 306 parent + 96 metal + 402 mold low-determinant cells."
echo "Frontal candidate: review its checkMesh lines and region contact audit above."
echo "Original and candidate remain separately preserved."
if [[ "$native" != ACCEPTED ]]; then
    exit 5
fi
