#!/usr/bin/env bash
# Caso B C3D-05: ONE-COMMAND bounded, topology-only CAD/Gmsh HEX8 pilot.
# All earlier Delaunay, Frontal and HXT outputs are preserved.
# This is deliberately a COARSER mesh to control resource use; NOT a
# grid-independence study and no assertion of comparable CFD accuracy.
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TESTS="$ROOT/tests"
BASE="$HOME/OpenFOAM/C3D05_STEP_GMSH_PILOT_01"
HXT="$HOME/OpenFOAM/C3D05_STEP_GMSH_HXT_01"
OUT="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01"

if [[ -e "$OUT" || -L "$OUT" ]]; then
    echo "PRESERVED: output already exists, refusing overwrite: $OUT" >&2
    exit 2
fi
if [[ ! -s "$BASE/PILOT_MESH_REPORT.tsv" || ! -s "$HXT/PILOT_MESH_REPORT.tsv" ]]; then
    echo "BLOCKED: source Delaunay and HXT results must both be preserved" >&2
    exit 2
fi
if [[ -r /proc/meminfo ]]; then
    available_kib="$(awk '/^MemAvailable:/{print $2;exit}' /proc/meminfo)"
    if [[ "$available_kib" =~ ^[0-9]+$ ]] && ((available_kib < 4194304)); then
        echo "RESOURCE_GATE: fewer than 4 GiB RAM currently available in WSL; no new mesh attempted" >&2
        exit 3
    fi
fi

echo "=== C3D-05 CASO B: PILOTO CAD HEX8 DE UNA SOLA INVOCACIÓN ==="
echo "BASELINE Delaunay: $BASE — PRESERVED"
echo "CONTROL HXT: $HXT — PRESERVED"
echo "CANDIDATE HEX8: $OUT — FRESH OUTPUT ONLY"
echo "Method: CAD STEP -> Delaunay coarse (3.6 mm) -> all-hexa subdivision"
echo "Resource cap: <= 150000 initial tetra; no unbounded 2M-cell experiment"
echo "This is a topology proof of concept; mesh-size also changed."
echo "Same CAD STEP solid geometry, physical groups, SI conversion and strict OpenFOAM checks."
echo "NO CFD, NO solver, NO lower checkMesh determinant tolerance."

echo
echo "=== 1/4: Read-only source checks and regression tests ==="
bash "$TESTS/test_step_gmsh_static.sh"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s "$TESTS" -p 'test_diagnose_existing_mesh.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s "$TESTS" -p 'test_audit_underdetermined_topology.py' -v

echo
echo "=== 2/4: Tiny in-memory TWO-MATERIAL hex/quad capability preflight ==="
if ! PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/preflight_hex_subdivision.py"; then
    echo "BLOCKED_HEX_CAPABILITY: no QuickCup mesh attempted" >&2
    exit 3
fi

echo
echo "=== 3/4: Fresh bounded CAD to HEX8, convert, split, check native mesh ==="
if C3D05_OUT="$OUT" \
   C3D05_ALGORITHM3D=1 \
   C3D05_MESH_SIZE_MM=3.6 \
   C3D05_SUBDIVIDE_HEX=1 \
   C3D05_MAX_BASE_TETS=150000 \
   bash "$ROOT/Allmesh"; then
    native=ACCEPTED
else
    code=$?
    native=NOT_ACCEPTED
    echo "Pilot failed or stopped safely (runner exit $code), results preserved: $OUT"
fi

echo
echo "=== 4/4: Native log gate diagnosis and exact contact area ==="
if [[ -d "$OUT/constant/metal/polyMesh" && -d "$OUT/constant/mold/polyMesh" ]]; then
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/diagnose_existing_mesh.py" "$OUT" ||
      echo "WARNING: read-only log diagnosis incomplete" >&2
    if [[ -s "$OUT/CONTACT_AREA_REPORT.json" ]]; then
        echo "Official area result from accepted Allmesh:"
        python3 -B -m json.tool "$OUT/CONTACT_AREA_REPORT.json"
    elif [[ ! -e "$OUT/CONTACT_AREA_HEX_DIAGNOSTIC_ONLY.json" ]]; then
        if ! PYTHONDONTWRITEBYTECODE=1 python3 -B \
            "$HERE/measure_interface_area.py" "$OUT" \
            --out "$OUT/CONTACT_AREA_HEX_DIAGNOSTIC_ONLY.json"; then
            echo "WARNING: contact area/recriprocity gate failed, audit retained" >&2
        fi
    fi
else
    echo "No complete regional HEX8 mesh: inspect preserved early-stage logs."
    if [[ -s "$OUT/NATIVE_BUILD_STATUS.txt" ]]; then
        cat "$OUT/NATIVE_BUILD_STATUS.txt"
    fi
    if [[ -s "$OUT/log.gmsh3d" ]]; then
        tail -n 35 "$OUT/log.gmsh3d"
    fi
fi

echo
echo "=== HEX8 PILOT: $native | NO CFD ==="
echo "Candidate: $OUT"
echo "Control geometries and outputs retained; do not overwrite."
echo "Do not claim Mesh OK or physical validity without strict parent, regional and contact gates."
[[ "$native" == ACCEPTED ]] || exit 5
