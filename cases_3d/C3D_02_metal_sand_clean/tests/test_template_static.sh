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
# Independent-material runner: the new approach after the retained-exterior failure.
material_template="$ROOT/system/materialSingle/snappyHexMeshDict.template"
material_runner="$ROOT/scripts/run_material_meshes.sh"
test -f "$material_template"
test -f "$material_runner"
grep -Fq 'insidePoint MATERIAL_POINT_PLACEHOLDER;' "$material_template"
grep -Fq 'file "MATERIAL_STL_PLACEHOLDER";' "$material_template"
grep -Eq '^[[:space:]]*units[[:space:]]+\[mm\];' "$material_template"
grep -Fq 'for material in metal mold; do' "$material_runner"
grep -Fq 'C3D02_materials' "$material_runner"
if grep -Eq '^[[:space:]]*(foamMultiRun|splitMeshRegions|subsetMesh|topoSet)([[:space:]]|$)' "$material_runner"; then
    echo "ERROR: un runner de mallas independientes intenta CFD/separación"
    exit 1
fi
echo "OK: dos STL de materiales y un insidePoint por malla, sin solver."
# Regression for required Foundation 14 option and safe resume of the exact abort.
grep -Eq '^[[:space:]]*allowFreeStandingZoneFaces[[:space:]]+false;' "$material_template" || {
    echo "ERROR: Foundation 14 exige allowFreeStandingZoneFaces en castellatedMeshControls"
    exit 1
}
resume_script="$ROOT/scripts/resume_material_meshes.sh"
test -f "$resume_script"
grep -Fq 'keyword allowFreeStandingZoneFaces is undefined' "$resume_script"
grep -Fq 'log.snappyHexMesh.retry1' "$resume_script"
if grep -Eq '^[[:space:]]*(blockMesh|foamMultiRun|subsetMesh|splitMeshRegions|topoSet)([[:space:]]|$)' "$resume_script"; then
    echo "ERROR: reanudar no debe reconstruir blockMesh ni ejecutar CFD"
    exit 1
fi
echo "OK: clave Foundation 14 obligatoria y reanudación protegida."

# Off-face seed: previous x=3 mm was exactly a face of the 2 mm blockMesh.
# Test both future fresh runs and the isolated mold-only candidate script.
grep -Fq 'inside="(0.0043 -0.0207 0.0259)"' "$material_runner" || {
    echo "ERROR: punto de molde del runner antiguo coincide con cara de blockMesh."
    exit 1
}
offface="$ROOT/scripts/try_mold_offface.sh"
test -f "$offface"
grep -Fq 'POINT="(0.0043 -0.0207 0.0259)"' "$offface"
grep -Fq 'mold_offface_01' "$offface"
if grep -Eq '^[[:space:]]*(foamMultiRun|subsetMesh|splitMeshRegions|topoSet)([[:space:]]|$)' "$offface"; then
    echo "ERROR: esta etapa no puede ejecutar CFD ni modificadores de malla."
    exit 1
fi
echo "OK: nuevo insidePoint de arena fuera de cara y prueba exclusiva de mold."
# The next operation must diagnose existing evidence, not rerun the mesh.
inspector="$ROOT/scripts/inspect_mold_leak.sh"
test -f "$inspector"
grep -Fq 'mold_offface_01/log.snappyHexMesh' "$inspector"
grep -Fq 'surfaceCheck -checkSelfIntersection -outputThreshold 0' "$inspector"
if grep -Eq '^[[:space:]]*(blockMesh|snappyHexMesh|subsetMesh|topoSet|splitMeshRegions|foamMultiRun)([[:space:]]|$)' "$inspector"; then
    echo "ERROR: la inspección no debe crear/modificar mallas ni ejecutar CFD."
    exit 1
fi
echo "OK: diagnóstico de fuga utiliza logs existentes y STL sin remallar."
echo "NO certifica malla física, contacto térmico ni CFD."
