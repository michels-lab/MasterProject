#!/usr/bin/env bash
# Stage byte-identical C14 material dictionaries onto EXISTING split meshes.
# No OpenFOAM solver or mesh generation, no Python, no silent overwrites.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
C14="$REPO/cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant"
[[ $# -eq 1 ]] || { echo "Usage: stage_c14_materials.sh /absolute/case" >&2; exit 2; }
CASE="$1"
[[ "$CASE" == /* && -d "$CASE/constant/metal/polyMesh" && -d "$CASE/constant/mold/polyMesh" ]] || {
    echo "ERROR: expected an existing 3D case with metal and mold meshes" >&2
    exit 2
}
for item in metal/materials/castIron metal/physicalProperties metal/fvModels metal/g metal/pRef mold/materials/silica mold/physicalProperties; do
    src="$ROOT/constant/$item"
    ref="$C14/$item"
    dst="$CASE/constant/$item"
    [[ -f "$src" && -f "$ref" ]] || { echo "Missing controlled source: $item" >&2; exit 5; }
    cmp -s "$src" "$ref" || { echo "C14 mismatch at source: $item" >&2; exit 5; }
    mkdir -p "$(dirname "$dst")"
    if [[ -e "$dst" ]]; then
        cmp -s "$dst" "$ref" || { echo "Refusing to overwrite different material: $item" >&2; exit 5; }
    else
        cp -p "$src" "$dst"
    fi
    cmp -s "$dst" "$ref" || { echo "3D material mismatch after staging: $item" >&2; exit 5; }
done
manifest="$CASE/C14_MATERIALS_VERIFIED.txt"
{
    echo "C14 material inputs byte-identical to the 2D source"
    echo "3D: $CASE"
    for item in metal/materials/castIron metal/physicalProperties metal/fvModels metal/g metal/pRef mold/materials/silica mold/physicalProperties; do
        sha256sum "$CASE/constant/$item"
    done
    echo "NO mesh, boundary conditions, original source or CFD changed."
    echo "This does not certify mesh quality or OpenFOAM solver-read validity."
} > "$manifest"
echo "C14 material fidelity verified: $manifest"
