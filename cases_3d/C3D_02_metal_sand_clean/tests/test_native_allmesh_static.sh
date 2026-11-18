#!/usr/bin/env bash
# Static safety regression only: NO OpenFOAM run, no CAD edits, no Python.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/Allmesh"
DICT="$ROOT/system/snappyHexMeshDict"

test -f "$RUN"
bash -n "$RUN"
for cmd in blockMesh snappyHexMesh splitMeshRegions checkMesh foamDictionary; do
    grep -Fq "$cmd" "$RUN" || { echo "Missing native utility: $cmd"; exit 1; }
done
if grep -Eq '(^|[[:space:]])(python|python3)[[:space:]]' "$RUN"; then
    echo "Python must not appear as executable in the native workflow"
    exit 1
fi
for region in metal mold; do
    grep -Eq "cellZone[[:space:]]+$region;" "$DICT" || {
        echo "Missing $region cellZone in native dictionary"
        exit 1
    }
    grep -Fq "mode        inside;" "$DICT" || {
        echo "Missing Foundation 14 mode inside"
        exit 1
    }
done
grep -Fq -- "-cellZones 'metal mold'" "$RUN"
grep -Fq "NO_CFD" "$RUN"
grep -Fq -- '--diagnose' "$RUN"
grep -Fq -- 'native_quality' "$RUN"
grep -Fq -- 'checkMesh -case "$dest" -allGeometry -allTopology' "$RUN"
grep -Fq -- '-writeSurfaces -writeSets' "$RUN"
grep -Fq "Mesh OK" "$RUN"
grep -Fq "Failed[[:space:]]+" "$RUN"
grep -Fq 'validate_sources.sh' "$RUN"
grep -Fq -- '--compare' "$RUN"
grep -Fq -- 'foam_checkmesh_total_volume "$log"' "$RUN"
grep -Fq -- 'CANDIDATE_COMPARISON_CORRECTED.tsv' "$RUN"
bash "$ROOT/tests/test_native_checkmesh_report.sh"
grep -Fq -- '--stage-c14-better' "$RUN"
grep -Fq -- 'STAGE=STAGE_C14_MATERIALS' "$RUN"
grep -Fq -- 'stage_c14_materials.sh' "$RUN"
bash "$ROOT/tests/test_native_stage_c14.sh"
bash "$ROOT/tests/test_native_interface_audit.sh"
bash "$ROOT/tests/test_stl_v2_zone_diagnosis.sh"
grep -Fq -- '--audit-stl-v2' "$RUN"
grep -Fq 'STAGE=CHECK_INTERFACE' "$RUN"
grep -Fq -- 'STL_V2_INTERFACE_AUDIT.txt' "$RUN"
grep -Fq -- 'STL_V2_COMPARISON_AUDIT.tsv' "$RUN"
grep -Fq -- '--candidate-smooth' "$RUN"
grep -Fq -- '--better' "$RUN"
grep -Fq -- 'c3d-better' "$RUN"
grep -Fq -- 'C3D_BETTER_COMPARISON.tsv' "$RUN"
grep -Fq -- '--stl-v2' "$RUN"
grep -Fq -- '--v2-metal-only' "$RUN"
grep -Fq -- '--v2-mold-only' "$RUN"
grep -Fq -- 'c3d-better-v2-metal-only' "$RUN"
grep -Fq -- 'c3d-better-v2-mold-only' "$RUN"
grep -Fq -- 'stl_v2_metal_only' "$RUN"
grep -Fq -- 'stl_v2_mold_only' "$RUN"
grep -Fq -- 'STAGE=CHECK_INTERFACE' "$RUN"
bash -n "$ROOT/scripts/run_stl_v2_ablation.sh"
grep -Fq 'NO CFD' "$ROOT/scripts/run_stl_v2_ablation.sh"
grep -Fq 'log.splitMeshRegions' "$ROOT/scripts/run_stl_v2_ablation.sh"
grep -Fq -- 'STL_V2_COMPARISON.tsv' "$RUN"
grep -Fq -- 'c3d-better-stl-v2' "$RUN"
grep -Fq -- 'check_stl_v2.sh' "$RUN"
grep -Fq -- 'mold_v2.stl' "$RUN"
bash -n "$ROOT/scripts/check_stl_v2.sh"
grep -Fq -- 'f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf' "$ROOT/scripts/check_stl_v2.sh"
grep -Fq -- 'ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32' "$ROOT/scripts/check_stl_v2.sh"
grep -Fq -- 'nSmoothPatch=3; no change to STLs' "$RUN"
grep -Fq -- 'C3D02_NATIVE_SMOOTH_01' "$RUN"
grep -Fq -- '-entry snapControls/nSmoothPatch -set 6' "$RUN"
grep -Fq -- 'CANDIDATE_COMPARISON.tsv' "$RUN"
grep -Fq -- 'candidate_rejected=0' "$RUN"
echo "OK: native Allmesh syntax, direct zone declarations, quality gates and no Python."
