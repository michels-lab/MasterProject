#!/usr/bin/env bash
# Static-only source contract, independent from C3D-04 and C3D-03.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$ROOT/Allmesh"
CAD="$ROOT/scripts/build_step_mesh.py"
AREA="$ROOT/scripts/measure_interface_area.py"
[[ -s "$RUN" && -s "$CAD" && -s "$AREA" && -s "$ROOT/system/controlDict" ]] || exit 1
bash -n "$RUN"
python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(p).read_text()) for p in sys.argv[1:]]' "$CAD" "$AREA"
for expected in 'C3D05_METAL_STEP' 'C3D05_MOLD_STEP' 'C3D05_OUT' 'gmshToFoam' "splitMeshRegions -case" "checkMesh -case" 'measure_interface_area.py' 'NO_CFD' 'PILOT_MESH_REPORT.tsv'; do
  grep -Fq -- "$expected" "$RUN" || { echo "Runner missing $expected"; exit 1; }
done
for expected in 'occ.importShapes' 'occ.fragment' 'Geometry.OCCTargetUnit' 'Mesh.ScalingFactor' '0.001' 'Mesh.MshFileVersion' 'getMass' 'getBoundary' 'metal_mold_contact' 'moldOuterUnclassified' 'STEP_CAD_AUDIT.json'; do
  grep -Fq -- "$expected" "$CAD" || { echo "CAD script missing $expected"; exit 1; }
done
! grep -Eq '^[[:space:]]*(foamMultiRun|runApplication[[:space:]]+foamMultiRun|rm[[:space:]]+-rf)' "$RUN"
echo "OK: C3D-05 independent STEP/Gmsh CAD conformity, safety and OpenFOAM 14 mesh-only static contract"
echo "NOT EXECUTED: CAD import, Gmsh, gmshToFoam, splitMeshRegions, CFD"
