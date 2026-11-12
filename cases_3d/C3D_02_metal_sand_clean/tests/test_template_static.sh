#!/usr/bin/env bash
# Verificación estática: NO requiere STL, OpenFOAM ni solver.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
C14="$REPO/cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant"
for file in \
    metal/materials/castIron metal/physicalProperties metal/fvModels metal/g metal/pRef \
    mold/materials/silica mold/physicalProperties
do
    cmp -s "$ROOT/constant/$file" "$C14/$file" || { echo "DIFERENCIA DE C14: $file"; exit 1; }
done
for s in "$ROOT"/scripts/*.sh "$ROOT"/tests/*.sh; do
    bash -n "$s"
done
awk '
  /^[[:space:]]*vertices[[:space:]]*$/ {active=1; next}
  active && /^[[:space:]]*\);[[:space:]]*$/ {active=0; exit}
  active && /^[[:space:]]*\([[:space:]]*-?[0-9]/ {
    line=$0; gsub(/[()[:space:]]/, "", line)
    if (seen[line]++) duplicate=1
    n++
  }
  END {
    if (n!=8 || duplicate) {
      print "ERROR: se requieren 8 vertices unicos, se encontraron " n
      exit 1
    }
    print "OK: ocho vertices unicos"
  }
' "$ROOT/system/blockMeshDict"
if grep -Eq '^[[:space:]]*application[[:space:]]+foamMultiRun;' "$ROOT/system/controlDict"; then
    echo "ERROR: no se permite activar solver CFD sin G1/G2"
    exit 1
fi
echo "OK: siete materiales C14 exactos, scripts sintácticos y caja base de 8 vertices."
# Foundation 14 two-material meshing source checks.
mesh_dict="$ROOT/system/snappyHexMeshDict"
mesh_script="$ROOT/scripts/run_mesh_only.sh"
test -f "$mesh_dict"
test -f "$mesh_script"
grep -Eq '^[[:space:]]*insidePoints([[:space:]]|$)' "$mesh_dict"
grep -Eq '^[[:space:]]*cellZone[[:space:]]+metal;' "$mesh_dict"
grep -Eq '^[[:space:]]*faceZone[[:space:]]+metalInterface;' "$mesh_dict"
grep -Eq '^[[:space:]]*units[[:space:]]+\[mm\];' "$mesh_dict"
if grep -Eq '^[[:space:]]*(locationInMesh|locationsInMesh)[[:space:]]' "$mesh_dict"; then
    echo "ERROR: se mezcló sintaxis OpenCFD con Foundation 14"
    exit 1
fi
if grep -Eq '^[[:space:]]*(foamMultiRun|subsetMesh|topoSet|splitMeshRegions)([[:space:]]|$)' "$mesh_script"; then
    echo "ERROR: el script de malla ejecutaría solver/recortes/separación"
    exit 1
fi
echo "OK: fuente de mallado Foundation 14 de dos puntos interiores, sin CFD."
echo "NO certifica malla física, contacto térmico ni CFD."
