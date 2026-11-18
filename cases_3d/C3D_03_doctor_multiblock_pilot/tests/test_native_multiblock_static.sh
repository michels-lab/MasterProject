#!/usr/bin/env bash
# Offline regression for the prepared C3D-03 3D blockMesh pilot: never runs OpenFOAM.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DICT="$ROOT/system/blockMeshDict"
RUN="$ROOT/Allmesh"
CONTROL="$ROOT/system/controlDict"
[[ -s "$DICT" && -s "$CONTROL" && -s "$RUN" && -s "$ROOT/README.md" ]] || { echo "Missing pilot source file"; exit 1; }
bash -n "$RUN"
bash -n "$0"
grep -Fq 'units [mm];' "$DICT"
grep -Fq 'cellZones metal/mold' "$DICT"
grep -Fq 'metalTop' "$DICT"
grep -Fq 'moldRecessRoof' "$DICT"
grep -Fq 'moldRecessWall' "$DICT"
grep -Fq 'unexpectedFaces' "$DICT"
[[ "$(grep -Ec '^[[:space:]]*hex[[:space:]]*\(' "$DICT")" -eq 24 ]]
[[ "$(grep -Ec '^[[:space:]]*hex[[:space:]]*\([^)]*\)[[:space:]]+metal[[:space:]]*\(' "$DICT")" -eq 3 ]]
[[ "$(grep -Ec '^[[:space:]]*hex[[:space:]]*\([^)]*\)[[:space:]]+mold[[:space:]]*\(' "$DICT")" -eq 21 ]]
for x in 'blockMesh -case "$OUT"' 'checkMesh -case "$OUT"' 'splitMeshRegions -case "$OUT"' '-cellZones '\''metal mold'\''' '-region "$region"' 'mappedWall' 'NO_CFD' '1248' 'PILOT_MESH_REPORT.tsv' 'NATIVE_BUILD_STATUS.txt'; do
    grep -Fq -- "$x" "$RUN" || { echo "Missing runner requirement: $x"; exit 1; }
done
! grep -Eq '^[[:space:]]*(runApplication[[:space:]]+foamMultiRun|foamMultiRun([[:space:]]|$)|python(3)?[[:space:]])' "$RUN" || { echo "Unexpected CFD/Python execution in mesh-only runner"; exit 1; }
echo "OK: C3D03 3D pilot static integrity, block zones, recess topology and native-only executable"
echo "NOT EXECUTED: blockMesh, checkMesh, splitMeshRegions, CHT, CFD"
