#!/usr/bin/env bash
# C3D-02: ONE isolated test of a corrected mold insidePoint.
# The original seed x=3 mm coincided with a background-mesh face.
# Leaves $HOME/OpenFOAM/C3D02_materials/{metal,mold} untouched.
source /opt/openfoam14/etc/bashrc
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$HOME/OpenFOAM/C3D02_materials"
SUB="$WORK/mold_offface_01"
STL="mold_repaired.stl"
POINT="(0.0043 -0.0207 0.0259)"
REF_VOL="0.00010284309608"

[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || {
    echo "ERROR: se requiere OpenFOAM Foundation 14."; exit 2;
}
bash "$ROOT/tests/test_sources.sh"

# Protect existing evidence and the metal mesh. No overwrites.
[[ -f "$WORK/metal/log.checkMesh.retry1" ]] || {
    echo "ERROR: no se encuentra la malla de hierro previamente ensayada."; exit 2;
}
[[ -f "$WORK/mold/log.checkMesh.retry1" ]] || {
    echo "ERROR: no se encuentra el log anterior del molde."; exit 2;
}
[[ ! -e "$SUB" ]] || {
    echo "ERROR: la prueba $SUB ya existe. No sobrescribir ni repetir."; exit 2;
}
[[ -f "$ROOT/constant/geometry/$STL" ]] || {
    echo "ERROR: STL reparado no encontrado."; exit 2;
}

mkdir -p "$SUB/system" "$SUB/constant/geometry"
cp -p "$ROOT/system/controlDict" "$ROOT/system/blockMeshDict" "$SUB/system/"
cp -p "$ROOT/constant/geometry/$STL" "$SUB/constant/geometry/"
sed -e "s/MATERIAL_STL_PLACEHOLDER/$STL/g" \
    -e "s/MATERIAL_POINT_PLACEHOLDER/$POINT/g" \
    "$ROOT/system/materialSingle/snappyHexMeshDict.template" \
    > "$SUB/system/snappyHexMeshDict"

echo "===== UNA SOLA PRUEBA: MOLDE CON PUNTO FUERA DE CARA ====="
echo "Geometria: $STL; insidePoint: $POINT m"
foamDictionary -case "$SUB" system/snappyHexMeshDict \
    -entry castellatedMeshControls/insidePoint \
    > "$SUB/log.preflight" 2>&1 || {
        tail -n 30 "$SUB/log.preflight"; exit 3;
    }

if ! blockMesh -case "$SUB" > "$SUB/log.blockMesh" 2>&1; then
    tail -n 40 "$SUB/log.blockMesh"; exit 3
fi
if ! snappyHexMesh -case "$SUB" -overwrite \
    > "$SUB/log.snappyHexMesh" 2>&1; then
    tail -n 60 "$SUB/log.snappyHexMesh"; exit 4
fi

set +e
checkMesh -case "$SUB" -allGeometry -allTopology \
    > "$SUB/log.checkMesh.full" 2>&1
RC=$?
set -e

echo "===== RESULTADO ====="
grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' \
    "$SUB/log.checkMesh.full" | tail -n 32 || true
echo "===== SELECCION REAL DE SNAPPY ====="
grep -Ei 'Cell selection insidePoints|Keeping all cells|Selected for keeping|Finished meshing with' \
    "$SUB/log.snappyHexMesh" | tail -n 12 || true

VOL="$(sed -n -E 's/.*Total volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+).*/\1/p' \
     "$SUB/log.checkMesh.full" | tail -n 1)"
OUT="$(awk '/^[[:space:]]*outerBox[[:space:]]*$/ {seen=1;next} seen && /nFaces[[:space:]]/ {gsub(/;/,"",$2);print $2;exit}' \
     "$SUB/constant/polyMesh/boundary")"
OUT="${OUT:-0}"

echo "Volumen molde: ${VOL:-no disponible} m3; CAD: $REF_VOL m3."
echo "Caras outerBox: $OUT"
echo "Logs conservados en $SUB."
echo "Hierro original y otros mallados SIN CAMBIOS."

PASS=1
if ((RC != 0)) || grep -Eq 'Failed [1-9][0-9]* mesh checks' "$SUB/log.checkMesh.full" || \
    ! grep -q 'Mesh OK' "$SUB/log.checkMesh.full"; then PASS=0; fi
if [[ ! "$VOL" =~ ^[0-9.eE+-]+$ ]] || \
    ! awk -v v="$VOL" -v ref="$REF_VOL" 'BEGIN {exit !((v+0)>0 && (v+0)>=ref*0.9 && (v+0)<=ref*1.1)}'; then PASS=0; fi
if [[ ! "$OUT" =~ ^[0-9]+$ ]] || ((OUT != 0)); then PASS=0; fi

if ((PASS)); then
    echo "FILTROS GEOMETRICOS INICIALES APROBADOS; INTERFAZ TERMICA AUN PENDIENTE."
else
    echo "MALLA TODAVIA NO APROBADA. Revisar la seleccion/topologia antes de otro intento."
    exit 5
fi
