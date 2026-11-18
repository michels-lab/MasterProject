#!/usr/bin/env bash
# Simple reproducible exercise of zone audit on fake historical logs only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
bash -n "$ROOT/scripts/diagnose_stl_v2_zones.sh"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/constant/metal/polyMesh" "$work/constant/mold/polyMesh"
for r in metal mold; do
cat > "$work/constant/$r/polyMesh/boundary" <<'EOF'
FoamFile
{
    class polyBoundaryMesh;
}
1
(
    outerBox
    {
        type patch;
        nFaces 8;
        startFace 30;
    }
)
EOF
cat > "$work/log.checkMesh.$r" <<'EOF'
    cells: 4
 *Number of regions: 4
    Total volume = 7.46352e-12. Cell volumes OK.
Failed 1 mesh checks.
EOF
done
cat > "$work/log.snappyHexMesh" <<'EOF'
snappyHexMesh
Refined mesh : cells: 300000
Assigning cellZones
End
EOF
cat > "$work/log.splitMeshRegions" <<'EOF'
 Region nCells cellZone
 metal 4 metal
 mold 4 mold
 exterior 299992 exterior
 Interface Owner Region Neighbour Region nFaces
 End
EOF
out="$(bash "$ROOT/scripts/diagnose_stl_v2_zones.sh" "$work")"
grep -Fq 'metal 4 metal' <<< "$out"
grep -Fq 'mold 4 mold' <<< "$out"
grep -Fq 'exterior 299992 exterior' <<< "$out"
grep -Fq 'Total volume = 7.46352e-12' <<< "$out"
grep -Fq 'PATCH name=outerBox type=patch nFaces=8' <<< "$out"
echo "OK: raw logging exposes lost zones and no fictional metal-to-mold interface."
