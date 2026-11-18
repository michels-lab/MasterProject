#!/usr/bin/env bash
# Static-only source contract, independent from C3D-04 and C3D-03.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$ROOT/Allmesh"
CAD="$ROOT/scripts/build_step_mesh.py"
AREA="$ROOT/scripts/measure_interface_area.py"
[[ -s "$RUN" && -s "$CAD" && -s "$AREA" && -s "$ROOT/system/controlDict" ]] || exit 1
METAL="$ROOT/constant/geometry/metalmm.STEP"
MOLD="$ROOT/constant/geometry/QuickCupmm.STEP"
[[ -s "$METAL" && -s "$MOLD" ]] || { echo "Missing versioned source STEP"; exit 1; }
echo 'ea5f65796c5156e4931eaec29ff656c279120925ebc083767a16b80892d0f475  '"$METAL" | sha256sum -c --status ||
    { echo "Original metalmm.STEP SHA mismatch"; exit 1; }
echo 'fe126d23bb639196258551fd156591d7fe2b0b4ce1d7c9ece47016e8ad08a40c  '"$MOLD" | sha256sum -c --status ||
    { echo "Original QuickCupmm.STEP SHA mismatch"; exit 1; }
grep -Fq 'METAL_STEP="${C3D05_METAL_STEP:-$ROOT/constant/geometry/metalmm.STEP}"' "$RUN"
grep -Fq 'MOLD_STEP="${C3D05_MOLD_STEP:-$ROOT/constant/geometry/QuickCupmm.STEP}"' "$RUN"
bash -n "$RUN"
python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(p).read_text()) for p in sys.argv[1:]]' "$CAD" "$AREA"
for expected in 'C3D05_METAL_STEP' 'C3D05_MOLD_STEP' 'C3D05_OUT' 'gmshToFoam' "splitMeshRegions -case" "checkMesh -case" 'measure_interface_area.py' 'NO_CFD' 'PILOT_MESH_REPORT.tsv'; do
  grep -Fq -- "$expected" "$RUN" || { echo "Runner missing $expected"; exit 1; }
done
for expected in 'occ.importShapes' 'occ.fragment' 'Geometry.OCCTargetUnit' 'Mesh.ScalingFactor' '0.001' 'Mesh.MshFileVersion' 'getMass' 'getBoundary' 'metal_mold_contact' 'moldOuterUnclassified' 'STEP_CAD_AUDIT.json'; do
  grep -Fq -- "$expected" "$CAD" || { echo "CAD script missing $expected"; exit 1; }
done
! grep -Eq '^[[:space:]]*(foamMultiRun|runApplication[[:space:]]+foamMultiRun|rm[[:space:]]+-rf)' "$RUN"
echo "OK: C3D-05 original STEP SHA256s, automatic CAD paths, independent Gmsh pipeline and OpenFOAM 14 mesh-only static contract"
echo "NOT EXECUTED: CAD import, Gmsh, gmshToFoam, splitMeshRegions, CFD"
