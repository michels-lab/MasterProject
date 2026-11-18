#!/usr/bin/env bash
# Diagnose lost material cellZones from EXISTING native OpenFOAM logs.
# No mesh/solver calls. Does not modify or recreate cases, logs, or CAD files.
set -euo pipefail
if (( $# == 1 )); then CASE="$1"; else CASE="$HOME/OpenFOAM/c3d-better-stl-v2"; fi
[[ -d "$CASE/constant/metal/polyMesh" && -d "$CASE/constant/mold/polyMesh" ]] || {
    echo "ERROR: Existing v2 metal/mold regional meshes missing at $CASE" >&2; exit 2;
}
printf '%s\n' '=== C3D02 v2: evidence from existing OpenFOAM logs ==='
echo "Case: $CASE"
echo "--- source integrity and build status ---"
cat "$CASE/NATIVE_BUILD_STATUS.txt" 2>/dev/null || true
if [[ -f "$CASE/STL_V2_SOURCE_MAP.txt" ]]; then
    sed -n '1,12p' "$CASE/STL_V2_SOURCE_MAP.txt"
fi
echo
echo "--- snappyHexMesh: raw zone/refinement/selection/snap messages with line numbers ---"
log="$CASE/log.snappyHexMesh"
[[ -s "$log" ]] || { echo "ERROR: No existing log.snappyHexMesh" >&2; exit 3; }
grep -nEi 'insidePoints|point.*inside|cell.?zone|face.?zone|surfaces|surface intersection|intersect|remove.*cell|remaining.*cell|region|snap|refin|warn|fatal|error|cell[s]?[[:space:]]*:' "$log" | tail -n 105 || true
echo
echo "--- snappyHexMesh: final 35 lines (unaltered) ---"
tail -n 35 "$log"
echo
echo "--- splitMeshRegions: physical region and interface table with context ---"
split="$CASE/log.splitMeshRegions"
[[ -s "$split" ]] || { echo "ERROR: No existing log.splitMeshRegions" >&2; exit 3; }
grep -n -A 16 -B 2 -Ei 'Region[[:space:]]+nCells|Interface[[:space:]]+Owner Region|Adding interface patches|Creating mesh for region|faceZone::checkAddressing|FOAM Warning' "$split" | head -n 145 || true
echo
echo "--- splitMeshRegions: final 50 lines ---"
tail -n 50 "$split"
echo
echo "--- actual regional interfaces ---"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
bash "$ROOT/scripts/native_interface_audit.sh" "$CASE"
echo
echo "--- native checkMesh volumes (existing logs only) ---"
for region in metal mold; do
    file="$CASE/log.checkMesh.$region"
    echo "[$region]"
    [[ -s "$file" ]] || { echo "No previous checkMesh log"; continue; }
    grep -Ei 'cells:|Total volume|Number of regions|Mesh OK|Failed [0-9]+ mesh checks|determinant|concave' "$file" | tail -n 12 || true
done
echo
echo "EVIDENCE ONLY: no mesh generation, geometry editing, physical-field updates or CFD."
echo "Do not infer good mesh from zero concave cells in four-cell residual zones."
