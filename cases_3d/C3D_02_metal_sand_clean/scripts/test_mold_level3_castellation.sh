#!/usr/bin/env bash
# C3D-02 — one controlled, independent mold castellation test at level 3.
# Tests whether 0.25-mm nominal surface resolution closes the mold volume.
# NO snap, NO CFD, no changes to metal or earlier mold attempts.
source /opt/openfoam14/etc/bashrc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$HOME/OpenFOAM/C3D02_materials"
SUB="$WORK/mold_level3_cast_01"
TEMPLATE="$ROOT/system/materialSingle/snappyHexMeshDict.template"
STL="mold_repaired.stl"
POINT="(0.0043 -0.0207 0.0259)"
CAD_VOLUME=0.00010284309608

[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || {
    echo "ERROR: se requiere OpenFOAM Foundation 14"; exit 2;
}
bash "$ROOT/tests/test_sources.sh"
[[ -f "$WORK/mold_offface_01/log.checkMesh.full" ]] || {
    echo "ERROR: falta evidencia del ensayo off-face anterior"; exit 2;
}
[[ -f "$WORK/metal/log.checkMesh.retry1" ]] || {
    echo "ERROR: falta evidencia del ensayo de hierro anterior"; exit 2;
}
[[ ! -e "$SUB" ]] || {
    echo "ERROR: $SUB ya existe. No se sobrescriben resultados"; exit 2;
}

# Only difference from off-face attempt: refinement level 2 -> 3, snap off,
# and safety cap. Isolates the cell-selection stage before mesh snapping.
mkdir -p "$SUB/system" "$SUB/constant/geometry"
cp -p "$ROOT/system/controlDict" "$ROOT/system/blockMeshDict" "$SUB/system/"
cp -p "$ROOT/constant/geometry/$STL" "$SUB/constant/geometry/"

sed -e "s/MATERIAL_STL_PLACEHOLDER/$STL/g" \
    -e "s/MATERIAL_POINT_PLACEHOLDER/$POINT/g" \
    -e 's/^[[:space:]]*level (2 2);/            level (3 3);/' \
    -e 's/^snap true;/snap false;/' \
    -e 's/^[[:space:]]*maxGlobalCells 3000000;/    maxGlobalCells 3200000;/' \
    -e 's/^[[:space:]]*maxLocalCells 400000;/    maxLocalCells 3200000;/' \
    "$TEMPLATE" > "$SUB/system/snappyHexMeshDict"

# The experiment must not run unless EVERY intended change actually applies.
grep -Fq 'level (3 3);' "$SUB/system/snappyHexMeshDict"
grep -Fxq 'snap false;' "$SUB/system/snappyHexMeshDict"
grep -Fq 'maxGlobalCells 3200000;' "$SUB/system/snappyHexMeshDict"
grep -Fq 'allowFreeStandingZoneFaces false;' "$SUB/system/snappyHexMeshDict"
foamDictionary -case "$SUB" system/snappyHexMeshDict \
    -entry castellatedMeshControls/insidePoint > "$SUB/log.preflight" 2>&1 || {
    tail -n 30 "$SUB/log.preflight"; exit 3;
}

echo "=== MOLDE: nivel (3 3), SIN snap, UNA SOLA PRUEBA ==="
echo "STL $STL; insidePoint $POINT m; celdas base 2 mm."
echo "Superficie refinada a tamaño nominal 0.25 mm."
echo "Limite de refinamiento: 3,200,000 celdas."
if ! blockMesh -case "$SUB" > "$SUB/log.blockMesh" 2>&1; then
    tail -n 50 "$SUB/log.blockMesh"; exit 3;
fi
if ! snappyHexMesh -case "$SUB" -overwrite > "$SUB/log.snappyHexMesh" 2>&1; then
    tail -n 65 "$SUB/log.snappyHexMesh"
    echo "Fallo de snappyHexMesh; conserva logs para inspeccion."
    exit 4
fi

echo "=== RECORTE DE CELDAS (antes de snapping) ==="
grep -Ei 'After introducing baffles|Selected for keeping|After subsetting|Cells per refinement level|Maximum number of cells|Reached.*cell' \
    "$SUB/log.snappyHexMesh" | tail -n 30 || true

set +e
checkMesh -case "$SUB" -allGeometry -allTopology > "$SUB/log.checkMesh.full" 2>&1
mesh_rc=$?
set -e
echo "=== CHECKMESH CASTELLATED ONLY — NO ES CALIDAD FINAL ==="
grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' \
    "$SUB/log.checkMesh.full" | tail -n 28 || true

VOL="$(sed -n -E 's/.*Total volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+).*/\1/p' \
    "$SUB/log.checkMesh.full" | tail -n 1)"
[[ -f "$SUB/constant/polyMesh/boundary" ]] || {
    echo "ERROR: falta polyMesh/boundary"; exit 5;
}
OUT="$(awk '/^[[:space:]]*outerBox[[:space:]]*$/ {seen=1;next} seen && /nFaces[[:space:]]/ {gsub(/;/,"",$2);print $2;exit}' \
    "$SUB/constant/polyMesh/boundary")"
OUT="${OUT:-0}"

echo "Volumen ${VOL:-no-disponible} m3 (CAD $CAD_VOLUME m3); outerBox $OUT caras."
echo "checkMesh rc=$mesh_rc; snap=false y no hay interfaces CHT."
echo "Logs: $SUB. Hierro y anteriores SIN MODIFICACIONES."

# Gate only the targeted scientific question: is the external domain removed?
# The castellation checkMesh is reported, not accepted as final mesh quality.
if [[ ! "$VOL" =~ ^[0-9.eE+-]+$ ]] || \
   ! awk -v v="$VOL" -v ref="$CAD_VOLUME" \
       'BEGIN {exit !((v+0)>0 && v>=ref*.90 && v<=ref*1.10)}' || \
   [[ ! "$OUT" =~ ^[0-9]+$ ]] || ((OUT != 0)); then
    echo "FUGA PERSISTE: nivel 3 NO aisló el molde. No seguir a snap ni CFD."
    exit 5
fi
echo "AISLAMIENTO VOLUMETRICO PRELIMINAR: la malla castellated se acerca al CAD."
echo "PENDIENTE: snapping, calidad exhaustiva, interfaz termica y CFD."
