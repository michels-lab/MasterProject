#!/usr/bin/env bash
# C3D-02: material-specific meshes from CLOSED source STLs.
# Two independent OpenFOAM14 snappy jobs in ONE protected workspace.
# NO subsetMesh, NO splitMeshRegions, NO CFD, NO overwriting old logs.
source /opt/openfoam14/etc/bashrc
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${1:-$HOME/OpenFOAM/C3D02_materials}"
TEMPLATE="$ROOT/system/materialSingle/snappyHexMeshDict.template"
[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || { echo "ERROR: requiere OpenFOAM Foundation 14"; exit 2; }
bash "$ROOT/tests/test_sources.sh"
[[ -f "$TEMPLATE" ]] || { echo "FALTA plantilla $TEMPLATE"; exit 2; }

if [[ -e "$WORK" ]]; then
    echo "CARPETA YA EXISTE: $WORK"
    echo "No se sobrescribe. Conserva sus logs para evaluar el resultado."
    exit 2
fi
mkdir -p "$WORK"

n_failed=0
for material in metal mold; do
    case "$material" in
        metal)
            stl="metal.stl"
            inside="(0.0259 -0.0200 0.0259)"
            expected="0.0000479874896432"
            ;;
        mold)
            stl="mold_repaired.stl"
            inside="(0.003 -0.0200 0.0259)"
            expected="0.00010284309608"
            ;;
    esac

    SUB="$WORK/$material"
    mkdir -p "$SUB/system" "$SUB/constant/geometry"
    cp -p "$ROOT/system/controlDict" "$ROOT/system/blockMeshDict" "$SUB/system/"
    cp -p "$ROOT/constant/geometry/$stl" "$SUB/constant/geometry/"
    sed -e "s/MATERIAL_STL_PLACEHOLDER/$stl/g" \
        -e "s/MATERIAL_POINT_PLACEHOLDER/$inside/g" \
        "$TEMPLATE" > "$SUB/system/snappyHexMeshDict"

    echo ""
    echo "====== $material: punto interior $inside; $stl ======"
    if ! foamDictionary -case "$SUB" system/snappyHexMeshDict \
        -entry castellatedMeshControls/insidePoint > "$SUB/log.preflight" 2>&1; then
        echo "ERROR EN DICCIONARIO ($material):"
        tail -n 30 "$SUB/log.preflight"
        n_failed=$((n_failed+1))
        continue
    fi
    if ! blockMesh -case "$SUB" > "$SUB/log.blockMesh" 2>&1; then
        echo "ERROR blockMesh ($material):"
        tail -n 35 "$SUB/log.blockMesh"
        n_failed=$((n_failed+1))
        continue
    fi
    if ! snappyHexMesh -case "$SUB" -overwrite > "$SUB/log.snappyHexMesh" 2>&1; then
        echo "ERROR snappyHexMesh ($material):"
        tail -n 50 "$SUB/log.snappyHexMesh"
        n_failed=$((n_failed+1))
        continue
    fi

    set +e
    checkMesh -case "$SUB" -allGeometry -allTopology > "$SUB/log.checkMesh.full" 2>&1
    check_rc=$?
    set -e

    grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' \
        "$SUB/log.checkMesh.full" | tail -n 22 || true

    # Geometry and quality checks independent of mere command completion.
    vol="$(sed -n -E 's/.*Total volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+).*/\1/p' "$SUB/log.checkMesh.full" | tail -n 1)"
    outCount="$(awk '
        /^[[:space:]]*outerBox[[:space:]]*$/ {found=1}
        found && /nFaces[[:space:]]/ {gsub(/;/, "", $2); print $2; exit}
    ' "$SUB/constant/polyMesh/boundary")"
    outCount="${outCount:-0}"

    good=true
    if ((check_rc != 0)) || grep -Eq 'Failed [1-9][0-9]* mesh checks' "$SUB/log.checkMesh.full" || ! grep -q 'Mesh OK' "$SUB/log.checkMesh.full"; then
        echo "RECHAZADO $material: calidad geométrica."
        good=false
    fi
    if [[ ! "$vol" =~ ^[0-9.eE+-]+$ ]] || ! awk -v v="$vol" -v ref="$expected" 'BEGIN {if (v<ref*0.90 || v>ref*1.10) exit 1}'; then
        echo "RECHAZADO $material: volumen $vol m3; esperado $expected m3 ±10% (filtro inicial)."
        good=false
    fi
    if [[ ! "$outCount" =~ ^[0-9]+$ ]] || ((outCount != 0)); then
        echo "RECHAZADO $material: outerBox tiene $outCount caras; posible exterior retenido."
        good=false
    fi
    if [[ "$good" == true ]]; then
        echo "MALLA $material: checkMesh y filtros geométricos iniciales aprobados."
        echo "NO demuestra todavía contacto térmico con la otra malla."
    else
        n_failed=$((n_failed+1))
    fi
done

echo ""
echo "====== RESUMEN FINAL ======"
echo "Carpeta única de trabajo: $WORK"
echo "Regiones físicas aún INDEPENDIENTES: metal/ y mold/"
echo "NO existe interfaz CHT / mappedWall validada ni solver ejecutado."
echo "Archivos de física C14 y malla original C3D02 sin modificaciones."
if ((n_failed>0)); then
    echo "RESULTADO: $n_failed/2 mallas RECHAZADAS o incompletas."
    exit 5
fi
echo "RESULTADO: 2/2 controles iniciales de material pasados; pendiente interfaz CHT."
