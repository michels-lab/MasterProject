#!/usr/bin/env bash
# Synthetic OpenFOAM polyBoundaryMesh regression: no solver, no mesh.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/constant/metal/polyMesh" "$tmp/constant/mold/polyMesh"
cat > "$tmp/constant/metal/polyMesh/boundary" <<'EOF'
FoamFile
{
    version 2.0;
    format ascii;
    class polyBoundaryMesh;
}
2
(
    outerBox
    {
        type patch;
        nFaces 11;
        startFace 50;
    }
    metal_to_mold
    {
        type mappedWall;
        neighbourRegion mold;
        neighbourPatch mold_to_metal;
        nFaces 270;
        startFace 61;
    }
)
EOF
cat > "$tmp/constant/mold/polyMesh/boundary" <<'EOF'
FoamFile
{
    version 2.0;
    format ascii;
    class polyBoundaryMesh;
}
1
(
    exterior_to_mold
    {
        type patch;
        nFaces 5;
        startFace 50;
    }
)
EOF
out="$(bash "$ROOT/scripts/native_interface_audit.sh" "$tmp")"
grep -Fq 'PATCH name=metal_to_mold type=mappedWall nFaces=270 neighbourRegion=mold neighbourPatch=mold_to_metal' <<< "$out" || {
    echo "Failed to parse real mappedWall" >&2; exit 1;
}
grep -Fq 'PATCH name=exterior_to_mold type=patch nFaces=5' <<< "$out" || {
    echo "Failed to report actual mold patch" >&2; exit 1;
}
if grep -q 'PATCH name=mold_to_metal' <<< "$out"; then
    echo "False positive: missing reciprocal patch was invented" >&2; exit 1;
fi
bash -n "$ROOT/scripts/native_interface_audit.sh"
bash -n "$ROOT/Allmesh"
echo "OK: regional native interface audit differentiates mapped and missing patches."
