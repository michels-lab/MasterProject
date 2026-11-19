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
bash -n "$ROOT/scripts/run_frontal_pilot.sh"
grep -Fq 'ALGORITHM3D="${C3D05_ALGORITHM3D:-1}"' "$RUN"
grep -Fq -- '--algorithm-3d "$ALGORITHM3D"' "$RUN"
grep -Fq 'Mesh.Algorithm3D' "$CAD"
grep -Fq 'choices=(1, 4, 10)' "$CAD"
grep -Fq 'C3D05_ALGORITHM3D=4' "$ROOT/scripts/run_frontal_pilot.sh"
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

# HXT trial: verify safe one-command runner and no-write capability preflight.
HXT="$ROOT/scripts/run_hxt_pilot.sh"
PREFLIGHT="$ROOT/scripts/preflight_hxt.py"
[[ -s "$HXT" && -s "$PREFLIGHT" ]] || { echo "HXT runner/preflight absent"; exit 1; }
bash -n "$HXT"
python3 -c 'import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text())' "$PREFLIGHT"
for expected in 'C3D05_ALGORITHM3D=10' 'preflight_hxt.py' 'C3D05_STEP_GMSH_HXT_01' 'diagnose_existing_mesh.py' 'measure_interface_area.py' 'NO CFD'; do
  grep -Fq -- "$expected" "$HXT" || { echo "HXT runner missing $expected"; exit 1; }
done
grep -Fq '"Mesh.Algorithm3D", 10' "$PREFLIGHT"
grep -Fq -- '--algorithm-3d "$ALGORITHM3D"' "$RUN"

# Pure static gates for a separately preserved CAD -> HEX8/QUAD4 topology pilot.
HEX_RUN="$ROOT/scripts/run_hex_subdivision_pilot.sh"
HEX_PREFLIGHT="$ROOT/scripts/preflight_hex_subdivision.py"
[[ -s "$HEX_RUN" && -s "$HEX_PREFLIGHT" ]] || { echo "Missing HEX8 runner or preflight"; exit 1; }
bash -n "$HEX_RUN"
python3 -c 'import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text())' "$HEX_PREFLIGHT"
for token in 'C3D05_SUBDIVIDE_HEX=1' 'C3D05_MESH_SIZE_MM=3.6' 'C3D05_MAX_BASE_TETS=150000' 'C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02' 'preflight_hex_subdivision.py' 'NO CFD'; do
  grep -Fq -- "$token" "$HEX_RUN" || { echo "HEX8 runner missing safety contract: $token"; exit 1; }
done
for token in 'Mesh.SubdivisionAlgorithm' 'gmsh.model.mesh.refine()' 'volume_types' 'surface_types' 'max_base_tets' 'SUBDIVISION_INCOMPLETE'; do
  grep -Fq -- "$token" "$CAD" || { echo "CAD generator missing HEX8 contract: $token"; exit 1; }
done
for token in 'C3D05_SUBDIVIDE_HEX' 'C3D05_MESH_SIZE_MM' 'C3D05_MAX_BASE_TETS' 'run_stage gmsh3d'; do
  grep -Fq -- "$token" "$RUN" || { echo "Allmesh missing HEX8 option: $token"; exit 1; }
done
grep -Fq 'gmsh.model.mesh.refine()' "$HEX_PREFLIGHT"
grep -Fq 'final_volume != {5} or final_surface != {3}' "$HEX_PREFLIGHT"

# Regression contract: the HEX8 path must NOT bind 'volume_tags' inside
# main(), since this hides the global CAD import helper (previous failure).
REGRESS="$ROOT/tests/test_build_step_mesh_regressions.py"
[[ -s "$REGRESS" ]] || { echo "Missing Python helper name-collision regression"; exit 1; }
grep -Fq "test_build_step_mesh_regressions.py" "$HEX_RUN"
grep -Fq 'FAILED_HEX="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01"' "$HEX_RUN"
grep -Fq 'OUT="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"' "$HEX_RUN"
grep -Fq 'volume_types, hex_element_tags, _ = gmsh.model.mesh.getElements(3)' "$CAD"
python3 -c 'import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text())' "$REGRESS"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s "$ROOT/tests" -p 'test_build_step_mesh_regressions.py' -v

# Successful HEX8 provenance review: no checkMesh rerun, only saved logs.
HEX_REVIEW="$ROOT/scripts/review_accepted_hex_mesh.py"
HEX_REVIEW_RUN="$ROOT/scripts/run_hex_readiness_review.sh"
[[ -s "$HEX_REVIEW" && -s "$HEX_REVIEW_RUN" ]] ||
    { echo "Missing native HEX8 readiness review or one-command runner"; exit 1; }
bash -n "$HEX_REVIEW_RUN"
python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(p).read_text()) for p in sys.argv[1:]]' "$HEX_REVIEW" "$ROOT/tests/test_review_accepted_hex_mesh.py"
for needle in 'native_quality' 'minimum_cell_determinant' 'severely_nonorthogonal_faces_above_70deg' 'geometry_topology_gate_passed' 'mesh_element_topology' 'source_STEP_authentic_and_expected_hex8_topology'; do
    grep -Fq "$needle" "$HEX_REVIEW" ||
        { echo "HEX8 independent review missing contract: $needle"; exit 1; }
done
grep -Fq 'C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02' "$HEX_REVIEW_RUN"
grep -Fq 'test_review_accepted_hex_mesh.py' "$HEX_REVIEW_RUN"
! grep -Eq '^[[:space:]]*(gmshToFoam|checkMesh|blockMesh|foamMultiRun)[[:space:]]' "$HEX_REVIEW_RUN"

# Preserve original rejected provenance review and expose its exact predicates.
grep -Fq 'cad_provenance_checks' "$HEX_REVIEW"
grep -Fq 'cad_provenance_details' "$HEX_REVIEW"
grep -Fq 'post_subdivision_hex_count_vs_native_parent_cells' "$HEX_REVIEW"
grep -Fq 'HEX8_NATIVE_ACCEPTANCE_REVIEW_CANONICAL_SHA_20261119.json' "$HEX_REVIEW_RUN"
grep -Fq 'PREVIOUS="$CASE/HEX8_NATIVE_ACCEPTANCE_REVIEW_20261119.json"' "$HEX_REVIEW_RUN"

# C3D-05 accepted-HEX8 severe nonorth faceSet diagnosis is READ-ONLY.
NONORTH="$ROOT/scripts/audit_nonorthogonal_faces.py"
NONORTH_RUN="$ROOT/scripts/run_nonorth_face_audit.sh"
NONORTH_TEST="$ROOT/tests/test_audit_nonorthogonal_faces.py"
[[ -s "$NONORTH" && -s "$NONORTH_RUN" && -s "$NONORTH_TEST" ]] || {
  echo "Missing C3D-05 nonorth read-only diagnostics"; exit 1;
}
bash -n "$NONORTH_RUN"
python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(p).read_text()) for p in sys.argv[1:]]' "$NONORTH" "$NONORTH_TEST"
grep -Fq 'NATIVE_FACESET_AUDIT: PASSED' "$NONORTH"
grep -Fq 'nonOrthoFaces' "$NONORTH"
grep -Fq 'NONORTH_FACESET_TOPOLOGY_AUDIT_20261119.json' "$NONORTH_RUN"
grep -Fq 'test_audit_nonorthogonal_faces.py' "$NONORTH_RUN"
! grep -Eq '^[[:space:]]*(gmshToFoam|checkMesh|blockMesh|foamMultiRun|rm -rf)[[:space:]]' "$NONORTH_RUN"

# Read-only CSR graph distance from severe internal faces to physical interface:
# new diagnostics must not run mesh generators/checkMesh or a solver.
HOPS="$ROOT/scripts/audit_nonorth_hop_distance.py"
HOPS_TEST="$ROOT/tests/test_audit_nonorth_hop_distance.py"
HOPS_RUN="$ROOT/scripts/run_nonorth_hop_distance.sh"
[[ -s "$HOPS" && -s "$HOPS_TEST" && -s "$HOPS_RUN" ]] ||
  { echo "C3D-05 cell-hop audit files missing"; exit 1; }
bash -n "$HOPS_RUN"
python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(s).read_text()) for s in sys.argv[1:]]' "$HOPS" "$HOPS_TEST"
for token in "build_graph" "bfs_hops" "find_native_set" "graph"; do
  grep -Fiq "$token" "$HOPS" || { echo "Hop audit contract missing: $token"; exit 1; }
done
grep -Fq 'NONORTH_CELL_HOP_DISTANCE_20261119.json' "$HOPS_RUN"
grep -Fq 'test_audit_nonorth_hop_distance.py' "$HOPS_RUN"
grep -Fq 'NONORTH_FACESET_TOPOLOGY_AUDIT_20261119.json' "$HOPS_RUN"
! grep -Eq '^[[:space:]]*(gmsh|gmshToFoam|checkMesh|blockMesh|foamMultiRun|rm -rf)[[:space:]]' "$HOPS_RUN"

# T0 (two solids, NO CFD) model preparation uses Foundation14 templates and
# refuses *all* uncited material/thermal inputs and overwriting accepted mesh.
T0="$ROOT/t0_conduction"
T0_CHECK="$T0/scripts/run_t0_preflight.sh"
T0_PREP="$T0/scripts/run_t0_materialize.sh"
T0_PY="$T0/scripts/prepare_t0.py"
T0_UNIT="$T0/tests/test_prepare_t0.py"
[[ -s "$T0_CHECK" && -s "$T0_PREP" && -s "$T0_PY" && -s "$T0_UNIT" ]] ||
  { echo "Missing T0 strict generator, runner or tests"; exit 1; }
bash -n "$T0_CHECK"
bash -n "$T0_PREP"
python3 -c 'import ast,pathlib,sys; [ast.parse(pathlib.Path(p).read_text()) for p in sys.argv[1:]]' "$T0_PY" "$T0_UNIT"
for p in "$T0_CHECK" "$T0_PREP"; do
  ! grep -Eq '^[[:space:]]*(foamMultiRun|foamRun|gmshToFoam|checkMesh|blockMesh)[[:space:]]' "$p" ||
    { echo "T0 runner would execute a solver or mesh tool: $p"; exit 1; }
done
grep -Fq 'C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02' "$T0_CHECK"
grep -Fq 'C3D05_T0_CONDUCTION_01' "$T0_PREP"
grep -Fq '"schema": "C3D05_T0_1"' "$T0/T0_INPUTS.json"
for p in \
  "$T0/templates/0/metal/T.tpl" "$T0/templates/0/mold/T.tpl" \
  "$T0/templates/constant/metal/physicalProperties.tpl" \
  "$T0/templates/constant/mold/physicalProperties.tpl" \
  "$T0/templates/system/metal/fvSchemes.tpl" "$T0/templates/system/mold/fvSchemes.tpl" \
  "$T0/templates/system/metal/fvSolution.tpl" "$T0/templates/system/mold/fvSolution.tpl" \
  "$T0/templates/system/controlDict.tpl"
do
  [[ -s "$p" ]] || { echo "Missing T0 template: $p"; exit 1; }
done
grep -Fq 'regionSolvers' "$T0/templates/system/controlDict.tpl"
grep -Fq 'coupledTemperature' "$T0/templates/0/metal/T.tpl"
grep -Fq 'coupledTemperature' "$T0/templates/0/mold/T.tpl"
grep -Eq '^[[:space:]]*thermo[[:space:]]+eConst;' "$T0/templates/constant/metal/physicalProperties.tpl"
grep -Fq 'no_solver_executed' "$T0_PY"
grep -Fq 'T0_BLOCKED_MISSING_PHYSICAL_INPUTS_OR_EVIDENCE' "$T0_PY"
