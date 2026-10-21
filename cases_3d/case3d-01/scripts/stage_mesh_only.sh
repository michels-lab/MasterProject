#!/usr/bin/env bash
# PLAN D: prepare independent mesh-only canonical case named case3d-01.
# Does not alter old research cases or change STL coordinates/units.
# Usage: bash cases_3d/case3d-01/scripts/stage_mesh_only.sh \
#           /tmp/case3d-01-meshA "$HOME/OpenFOAM/Piezas_STL"
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /absolute/new/case3d-01-test /directory/with/{QuickCup.STL,metal.STL}" >&2
  exit 2
fi

THIS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$THIS_DIR/../../.." && pwd)"
SOURCE="$REPO/cases_3d/C3D_01_metal_mold"
TARGET="$(realpath -m -- "$1")"
STLS="$(realpath -e -- "$2")"
ROOT="$(realpath -e -- "$REPO")"

if [[ -e "$TARGET" || -L "$TARGET" ]]; then
  echo "ERROR: destination exists, refusing overwrite: $TARGET" >&2
  exit 3
fi
case "$TARGET" in
  "$ROOT"|"$ROOT"/*)
    echo "ERROR: staging must remain outside the checked-out repository" >&2
    exit 3 ;;
  "$STLS"|"$STLS"/*)
    echo "ERROR: destination cannot be inside private STL source directory" >&2
    exit 3 ;;
esac

# Source hashes from the model's SolidWorks-native STL files in mm.
# No Python geometry conversion, scaling, rotation or remeshing.
MOLD_EXPECTED="2e62e31875dc3c86dd7e6f2efe60d4c173ee4cee5e4f6ff63205c08efee3a638"
METAL_EXPECTED="fc8e6b7f3c229369b856aca7dab936347732028d9cd695499bf0e249363fb810"

for path in "$STLS/QuickCup.STL" "$STLS/metal.STL"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "ERROR: original STL missing or symbolic link: $path" >&2
    exit 3
  fi
done
MOLD_ACTUAL="$(sha256sum -- "$STLS/QuickCup.STL" | cut -d ' ' -f 1)"
METAL_ACTUAL="$(sha256sum -- "$STLS/metal.STL" | cut -d ' ' -f 1)"
if [[ "$MOLD_ACTUAL" != "$MOLD_EXPECTED" || "$METAL_ACTUAL" != "$METAL_EXPECTED" ]]; then
  echo "ERROR: source STL hashes differ; do not bypass geometry provenance" >&2
  exit 4
fi
for p in system/blockMeshDict system/controlDict \
         geometry_reference.json scripts/run_blockMesh_only.sh \
         constant/geometry/README.md; do
  if [[ ! -f "$SOURCE/$p" || -L "$SOURCE/$p" ]]; then
    echo "ERROR: missing/unsafe legacy mesh source: $p" >&2
    exit 4
  fi
done

mkdir -p -- "$TARGET/system" "$TARGET/scripts" "$TARGET/constant/geometry"
cp -- "$SOURCE/system/blockMeshDict" "$TARGET/system/blockMeshDict"
cp -- "$SOURCE/system/controlDict" "$TARGET/system/controlDict"
cp -- "$SOURCE/geometry_reference.json" "$TARGET/geometry_reference.json"
cp -- "$SOURCE/scripts/run_blockMesh_only.sh" "$TARGET/scripts/run_blockMesh_only.sh"
cp -- "$SOURCE/constant/geometry/README.md" "$TARGET/constant/geometry/README.md"
cp -- "$STLS/QuickCup.STL" "$TARGET/constant/geometry/mold.stl"
cp -- "$STLS/metal.STL" "$TARGET/constant/geometry/metal.stl"

# Fail closed if any private geometry changed during the copying process.
echo "$MOLD_EXPECTED  $TARGET/constant/geometry/mold.stl" | sha256sum --check --status
echo "$METAL_EXPECTED  $TARGET/constant/geometry/metal.stl" | sha256sum --check --status
cat > "$TARGET/PLAN_D_STAGE.txt" <<'EOF'
case_id: case3d-01
physical_case: QuickCup 3D metal and sand
stage: BACKGROUND_MESH_INPUTS_ONLY_NOT_RUN
input_origin: cases_3d/C3D_01_metal_mold (legacy while PR #18 is open)
STL_origin: SolidWorks-native units mm; source SHA verified
OpenFOAM: Foundation 14 only
No command executed: blockMesh, checkMesh, snappyHexMesh, foamMultiRun
mesh_regions: NOT_CREATED
CFD_validation: NOT_VALIDATED
EOF

echo "Created Plan D case3d-01 mesh-only COPY: $TARGET"
echo "Next on Ubuntu with Foundation14 loaded: cd \"$TARGET\" && bash scripts/run_blockMesh_only.sh"
echo "DO NOT run foamMultiRun: snappyHexMesh/regions/thermal BC still unavailable."
