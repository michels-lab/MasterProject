#!/usr/bin/env bash
# C3D-02. Extract a pre-existing moldVolume cellZone IN A NEW COPY ONLY.
# OpenFOAM Foundation 14: subsetMesh -cellZone moldVolume -noFields.\n# Overwrite is the v14 default, but applies ONLY to the separate copy.
# No snappyHexMesh, no re-meshing, no original-case modification, no CFD.
source /opt/openfoam14/etc/bashrc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$HOME/OpenFOAM/C3D02_materials"
SOURCE="$WORK/mold_zoned_l2_01"
DEST="$WORK/mold_extracted_l2_01"
ZONE="moldVolume"
CAD_VOLUME="0.00010284309608"
MEASURED_ZONE_VOLUME="0.000103409"
EXPECTED_CELLS=274788

[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || {
    echo "ERROR: se requiere OpenFOAM Foundation 14."; exit 2;
}
bash "$ROOT/tests/test_sources.sh"
[[ -d "$SOURCE" ]] || { echo "ERROR: falta $SOURCE"; exit 2; }
[[ ! -e "$DEST" && ! -L "$DEST" ]] || {
    echo "ERROR: $DEST ya existe. No se sobrescribe ni se repite."; exit 2;
}
for f in owner neighbour faces points boundary cellZones faceZones; do
    [[ -f "$SOURCE/constant/polyMesh/$f" ]] || {
        echo "ERROR: falta el archivo original polyMesh/$f"; exit 2;
    }
done
[[ -f "$SOURCE/log.checkMesh.full" && -f "$SOURCE/log.snappyHexMesh" ]] || {
    echo "ERROR: faltan los logs científicos de la zona; no proceder."; exit 2;
}
grep -Fq 'moldVolume' "$SOURCE/constant/polyMesh/cellZones" || {
    echo "ERROR: falta cellZone moldVolume."; exit 2;
}
grep -Fq 'moldInterface' "$SOURCE/constant/polyMesh/faceZones" || {
    echo "ERROR: falta faceZone moldInterface."; exit 2;
}
[[ -z "$(find "$SOURCE/constant/polyMesh" -type l -print -quit)" ]] || {
    echo "ERROR: hay symlinks dentro del polyMesh original. No copiarlos."; exit 2;
}
command -v subsetMesh >/dev/null && command -v checkMesh >/dev/null || {
    echo "ERROR: utilidades de malla no disponibles."; exit 2;
}
help="$(subsetMesh -help 2>&1 || true)"
for opt in -cellZone -noFields; do
    if ! grep -Fq -- "$opt" <<< "$help"; then
        echo "ERROR: Foundation local no anuncia $opt para subsetMesh."; exit 2;
    fi
done

echo "=== C3D-02: EXTRACCION DE moldVolume SOLO EN COPIA ==="
echo "Original INTOCABLE: $SOURCE"
echo "Nuevo destino      : $DEST"
echo "Zona original       : $ZONE ($EXPECTED_CELLS celdas)"
echo "Volumen medido      : $MEASURED_ZONE_VOLUME m3 = 103.409 cm3"
echo "Volumen CAD         : $CAD_VOLUME m3 = 102.8431 cm3"
echo "Nota: subsetMesh no conserva necesariamente los tipos de frontera."

# Create only a fresh physical copy; there must be NO links to the original.
mkdir -p "$DEST/constant" "$DEST/system"
cp -a -- "$SOURCE/constant/polyMesh" "$DEST/constant/polyMesh"
cp -p -- "$SOURCE/system/controlDict" "$DEST/system/controlDict"
[[ -z "$(find "$DEST/constant/polyMesh" -type l -print -quit)" ]] || {
    echo "ERROR: la copia contiene symlinks; no ejecutar subsetMesh."; exit 2;
}
[[ -f "$DEST/constant/polyMesh/owner" ]] || {
    echo "ERROR: copia incompleta."; exit 2;
}

echo "=== UTILIDAD DE EXTRACCION DE FOUNDATION 14 ==="
if ! subsetMesh -case "$DEST" -cellZone "$ZONE" -noFields \
    > "$DEST/log.subsetMesh" 2>&1; then
    echo "subsetMesh no terminó; revisar log.subsetMesh. No se tocó el origen."
    tail -n 65 "$DEST/log.subsetMesh"
    exit 3
fi
echo "subsetMesh terminó; falta VALIDACION de la nueva malla."

set +e
checkMesh -case "$DEST" -allGeometry -allTopology > "$DEST/log.checkMesh.full" 2>&1
check_rc=$?
set -e
echo "=== CHECKMESH DE MALLA EXTRAIDA (calidad exhaustiva) ==="
grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' \
    "$DEST/log.checkMesh.full" | tail -n 35 || true

CELLS="$(sed -n -E 's/^[[:space:]]*cells:[[:space:]]*([0-9]+).*/\1/p' \
    "$DEST/log.checkMesh.full" | head -n 1)"
VOLUME="$(sed -n -E 's/.*Total volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+).*/\1/p' \
    "$DEST/log.checkMesh.full" | tail -n 1)"
REGIONS="$(sed -n -E 's/.*Number of regions:[[:space:]]*([0-9]+).*/\1/p' \
    "$DEST/log.checkMesh.full" | tail -n 1)"

echo "=== PARCHES DESPUES DE LA EXTRACCION ==="
if [[ -f "$DEST/constant/polyMesh/boundary" ]]; then
    awk '
    /^[[:space:]]*[a-zA-Z_][a-zA-Z_0-9]*[[:space:]]*$/ {
        name=$1; type=""; nf="";
    }
    /^[[:space:]]*type[[:space:]]+/ {type=$2;gsub(";","",type)}
    /^[[:space:]]*nFaces[[:space:]]+/ {
        nf=$2;gsub(";","",nf);
        if (name!="") print name, "type=" type, "nFaces=" nf
    }
    ' "$DEST/constant/polyMesh/boundary"
fi
OUT="$(awk '/^[[:space:]]*outerBox[[:space:]]*$/ {hit=1;next} hit && /nFaces[[:space:]]/ {gsub(/;/,"",$2);print $2;exit}' \
    "$DEST/constant/polyMesh/boundary")"
OUT="${OUT:-0}"

echo "=== RESUMEN DE GEOMETRIA (SOLO COPIA) ==="
echo "cellZone esperada: $EXPECTED_CELLS celdas"
echo "Malla extraida   : ${CELLS:-DESCONOCIDO} celdas"
echo "Volumen extraido : ${VOLUME:-DESCONOCIDO} m3"
echo "Zonal anterior   : $MEASURED_ZONE_VOLUME m3"
echo "CAD arena        : $CAD_VOLUME m3"
echo "Conectividad     : ${REGIONS:-DESCONOCIDO} region(es)"
echo "outerBox         : $OUT caras"
echo "checkMesh rc     : $check_rc"
echo "Los logs permanecen en $DEST. Las mallas anteriores NO cambian."
echo "No se construyo ni valido interfaz CHT; no se ejecuto CFD."

# Cross-check exact zone cell count and zonal volume; if fails, STOP.
if [[ ! "$CELLS" =~ ^[0-9]+$ || ! "$VOLUME" =~ ^[0-9.eE+-]+$ || \
      ! "$REGIONS" =~ ^[0-9]+$ || ! "$OUT" =~ ^[0-9]+$ ]]; then
    echo "RECHAZADO: métricas incompletas."; exit 5;
fi
if (( CELLS != EXPECTED_CELLS || REGIONS != 1 || OUT != 0 )) || \
   ! awk -v v="$VOLUME" -v ref="$MEASURED_ZONE_VOLUME" \
     'BEGIN {exit !((v+0)>0 && v>=ref*0.999 && v<=ref*1.001)}'; then
    echo "RECHAZADO: extracción no coincide con la zona o conserva exterior."
    exit 5
fi
echo "EXTRACCION GEOMETRICA COHERENTE EN COPIA: volumen/celdas concordantes."
echo "Debe evaluarse la calidad y los nuevos parches por separado."
if (( check_rc != 0 )) || \
    grep -Eq 'Failed [1-9][0-9]* mesh checks' "$DEST/log.checkMesh.full" || \
    ! grep -q 'Mesh OK' "$DEST/log.checkMesh.full"; then
    echo "CALIDAD NO APROBADA: revisar celdas concavas y otras fallas."
    exit 5
fi
echo "CHECKMESH APROBADO EN COPIA (no significa interfaz metal-arena lista)."
