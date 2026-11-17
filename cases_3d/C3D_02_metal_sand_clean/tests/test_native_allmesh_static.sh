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
echo "OK: native Allmesh syntax, direct zone declarations, quality gates and no Python."
