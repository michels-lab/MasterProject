#!/usr/bin/env bash
# C3D-02 — diagnostic test of geometrical cellZone classification.
# One isolated L2 mold mesh, no snap, no CFD, no change to previous cases.
source /opt/openfoam14/etc/bashrc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$HOME/OpenFOAM/C3D02_materials"
CASE="$WORK/mold_zoned_l2_01"
TEMPLATE="$ROOT/system/materialSingle/snappyHexMeshDict.template"
STL="mold_repaired.stl"
POINT="(0.0043 -0.0207 0.0259)"
CAD_VOLUME="0.00010284309608"

[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || {
    echo "ERROR: se requiere OpenFOAM Foundation 14."
    exit 2
}
bash "$ROOT/tests/test_sources.sh"
[[ -f "$WORK/mold_level3_cast_01/log.checkMesh.full" ]] || {
    echo "ERROR: no existe el log del nivel 3 anterior; no modificar el workspace."
    exit 2
}
[[ -f "$WORK/metal/log.checkMesh.retry1" ]] || {
    echo "ERROR: no existe la evidencia del metal; no modificar el workspace."
    exit 2
}
[[ ! -e "$CASE" ]] || {
    echo "ERROR: $CASE ya existe. No sobrescribir ni repetir la prueba."
    exit 2
}

mkdir -p "$CASE/system" "$CASE/constant/geometry"
cp -p "$ROOT/system/blockMeshDict" "$ROOT/system/controlDict" "$CASE/system/"
cp -p "$ROOT/constant/geometry/$STL" "$CASE/constant/geometry/"

# Explicit, single-purpose source transformation: no other mesh parameters
# or source CAD differ from the verified L2 mold-only experiment.
python3 - "$TEMPLATE" "$CASE/system/snappyHexMeshDict" "$STL" "$POINT" <<'PY'
import sys
from pathlib import Path

source, destination, stl, point = sys.argv[1:]
data = Path(source).read_text(encoding="utf-8")
replacements = [
    ('MATERIAL_STL_PLACEHOLDER', stl),
    ('MATERIAL_POINT_PLACEHOLDER', point),
    ('snap true;', 'snap false;'),
    ('level (2 2);', '''level (2 2);
            faceZone moldInterface;
            cellZone moldVolume;
            mode inside;
            faceType internal;''')
]
for old, new in replacements:
    if data.count(old) != 1:
        raise SystemExit("ERROR: la plantilla no contiene una unica entrada: " + old)
    data = data.replace(old, new, 1)
Path(destination).write_text(data, encoding="utf-8")
PY

for entry in \
    castellatedMeshControls/refinementSurfaces/material/cellZone \
    castellatedMeshControls/refinementSurfaces/material/faceZone \
    castellatedMeshControls/refinementSurfaces/material/mode; do
    foamDictionary -case "$CASE" system/snappyHexMeshDict -entry "$entry" \
        >> "$CASE/log.preflight" 2>&1 || {
        echo "ERROR: Foundation 14 no reconoció $entry"
        tail -n 30 "$CASE/log.preflight"
        exit 3
    }
done

echo "====== MOLDE: CLASIFICACION GEOMETRICA SIN FLOOD-FILL COMO CRITERIO ======"
echo "STL: $STL; punto: $POINT m; refinamiento L2, snap=false."
echo "cellZone=moldVolume, faceZone=moldInterface, mode=inside."
if ! blockMesh -case "$CASE" > "$CASE/log.blockMesh" 2>&1; then
    tail -n 55 "$CASE/log.blockMesh"
    exit 3
fi
if ! snappyHexMesh -case "$CASE" -overwrite > "$CASE/log.snappyHexMesh" 2>&1; then
    echo "ERROR de snappyHexMesh; se conserva el log completo."
    tail -n 70 "$CASE/log.snappyHexMesh"
    exit 4
fi

set +e
checkMesh -case "$CASE" -allGeometry -allTopology > "$CASE/log.checkMesh.full" 2>&1
CHECK_RC=$?
set -e

echo "===== CELDAS CONSERVADAS Y ZONAS CREADAS ====="
grep -Ei 'After introducing baffles|Selected for keeping|After subsetting|CellZones:|FaceZones:|Assigning cells|Found 1 closed|Finished meshing' \
    "$CASE/log.snappyHexMesh" | tail -n 40 || true

zoneFile="$CASE/constant/polyMesh/cellZones"
faceFile="$CASE/constant/polyMesh/faceZones"
zoneCount=""
faceCount=""
if [[ -f "$zoneFile" ]]; then
    zoneCount="$(awk '
        /^[[:space:]]*moldVolume[[:space:]]*$/ {zone=1; next}
        zone && /cellLabels/ {labels=1; next}
        labels && /^[[:space:]]*[0-9]+[[:space:]]*$/ {print $1; exit}
    ' "$zoneFile")"
fi
if [[ -f "$faceFile" ]]; then
    faceCount="$(awk '
        /^[[:space:]]*moldInterface[[:space:]]*$/ {zone=1; next}
        zone && /faceLabels/ {labels=1; next}
        labels && /^[[:space:]]*[0-9]+[[:space:]]*$/ {print $1; exit}
    ' "$faceFile")"
fi

total="$(sed -n -E 's/.*cells:[[:space:]]*([0-9]+).*/\1/p' "$CASE/log.checkMesh.full" | head -n 1)"
volume="$(sed -n -E 's/.*Total volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+).*/\1/p' \
    "$CASE/log.checkMesh.full" | tail -n 1)"
outer="$(awk '/^[[:space:]]*outerBox[[:space:]]*$/ {found=1;next} found && /nFaces[[:space:]]/ {gsub(/;/,"",$2);print $2;exit}' \
    "$CASE/constant/polyMesh/boundary")"
outer="${outer:-0}"

echo "===== RESULTADOS ====="
echo "Total cells=${total:-DESCONOCIDO}, moldVolume cellZone labels=${zoneCount:-DESCONOCIDO}."
echo "moldInterface faceZone labels=${faceCount:-DESCONOCIDO}."
echo "Volumen global=${volume:-DESCONOCIDO} m3, CAD arena=$CAD_VOLUME m3."
echo "outerBox=${outer:-DESCONOCIDO} caras; checkMesh exit=$CHECK_RC."
grep -Ei 'Face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' \
    "$CASE/log.checkMesh.full" | tail -n 18 || true
echo "Log completo: $CASE/log.snappyHexMesh y log.checkMesh.full."
echo "NO se ejecutó solver, splitMeshRegions, subsetMesh ni snapping."
echo "Ninguna malla existente se modificó."

if [[ ! "$zoneCount" =~ ^[0-9]+$ || ! "$total" =~ ^[0-9]+$ || \
      ! "$faceCount" =~ ^[0-9]+$ ]] || ((zoneCount==0 || zoneCount>=total || faceCount==0)); then
    echo "LA CLASIFICACION GEOMETRICA NO QUEDO DEMOSTRADA."
    exit 5
fi
echo "CLASIFICACION GEOMETRICA CANDIDATA: hay celdas identificadas dentro del STL."
echo "AUN NO HAY MALLA FISICA DE ARENA APROBADA ni interfaz térmica."
