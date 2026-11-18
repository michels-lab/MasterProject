#!/usr/bin/env bash
# Static-only contract checks. NO blockMesh, NO CFD.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DICT="$ROOT/system/blockMeshDict"
RUN="$ROOT/Allmesh"
AREA="$ROOT/scripts/measure_interface_area.py"
[[ -s "$DICT" && -s "$RUN" && -s "$ROOT/system/controlDict" && -s "$AREA" ]] || exit 1
bash -n "$RUN"
python3 -m py_compile "$AREA" >/dev/null
[[ "$(grep -Ec '^[[:space:]]*hex[[:space:]]*\(' "$DICT")" -eq 180 ]]
[[ "$(grep -Ec '^[[:space:]]*hex[[:space:]]*\([^)]*\)[[:space:]]+metal[[:space:]]*\(' "$DICT")" -eq 63 ]]
[[ "$(grep -Ec '^[[:space:]]*hex[[:space:]]*\([^)]*\)[[:space:]]+mold[[:space:]]*\(' "$DICT")" -eq 117 ]]
[[ "$(grep -Ec '^[[:space:]]*arc[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+\(' "$DICT")" -eq 144 ]]
for marker in 'units [mm];' 'moldRecessRoof' 'moldRecessWall' 'moldExterior' 'unexpectedFaces'; do
  grep -Fq "$marker" "$DICT"
done
for marker in 'blockMesh -case "$OUT"' 'splitMeshRegions -case "$OUT"' '-cellZones '\''metal mold'\''' 'checkMesh -case "$OUT"' 'expected=8960' 'expected=12352' '2496' 'measure_interface_area.py' 'NO_CFD' 'PILOT_MESH_REPORT.tsv'; do
  grep -Fq -- "$marker" "$RUN" || { echo "Missing in Allmesh: $marker"; exit 1; }
done
! grep -Eq '^[[:space:]]*(foamMultiRun|runApplication[[:space:]]+foamMultiRun)' "$RUN"
echo "OK: C3D-04 rounded multiblock 180 blocks, 144 arcs, two material cellZones and read-only area gates"
echo "NOT EXECUTED: OpenFOAM blockMesh, checkMesh, CHT, CFD"
