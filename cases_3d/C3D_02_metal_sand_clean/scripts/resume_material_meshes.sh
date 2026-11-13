#!/usr/bin/env bash
# One-shot recovery from the observed missing-key abort in two C3D-02 meshes.
# Same workspace, same blockMesh, prior logs preserved, NO CFD or subsetMesh.
source /opt/openfoam14/etc/bashrc
set -eo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${1:-$HOME/OpenFOAM/C3D02_materials}"
TEMPLATE="$ROOT/system/materialSingle/snappyHexMeshDict.template"
[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || { echo "Requiere OpenFOAM Foundation 14"; exit 2; }
bash "$ROOT/tests/test_sources.sh"

# Fail safely BEFORE modifying anything if this is not exactly the documented abort.
for material in metal mold; do
    case "$material" in
        metal) stl=metal.stl; point="(0.0259 -0.0200 0.0259)" ;;
        mold) stl=mold_repaired.stl; point="(0.003 -0.0200 0.0259)" ;;
    esac
    SUB="$WORK/$material"
    for file in "$SUB/log.blockMesh" "$SUB/log.snappyHexMesh"         "$SUB/system/snappyHexMeshDict" "$SUB/constant/polyMesh/owner"         "$SUB/constant/polyMesh/boundary" "$SUB/constant/geometry/$stl"; do
        [[ -f "$file" ]] || { echo "Falta $file; ABORTADO SIN CAMBIOS"; exit 2; }
    done
    grep -Fq 'keyword allowFreeStandingZoneFaces is undefined' "$SUB/log.snappyHexMesh" || {
        echo "Fallo previo distinto en $material; no se sobrescribe."; exit 2;
    }
    grep -Eq '^End$' "$SUB/log.blockMesh" || {
        echo "blockMesh no terminó en $material; no se reanuda."; exit 2;
    }
    [[ ! -e "$SUB/log.snappyHexMesh.retry1" && ! -e "$SUB/log.checkMesh.retry1" && ! -e "$SUB/log.checkMesh.full" ]] || {
        echo "Existen logs de reintento/validación en $material; no sobrescribir."; exit 2;
    }
    cmp -s "$ROOT/constant/geometry/$stl" "$SUB/constant/geometry/$stl" || {
        echo "STL distinto en $material; abortado."; exit 2;
    }
    # Match exactly the previously generated dictionary, minus the new key.
    cmp -s "$SUB/system/snappyHexMeshDict" <(
        sed '/^[[:space:]]*allowFreeStandingZoneFaces[[:space:]]/d' "$TEMPLATE" |
        sed -e "s/MATERIAL_STL_PLACEHOLDER/$stl/g"             -e "s/MATERIAL_POINT_PLACEHOLDER/$point/g"
    ) || { echo "Diccionario de $material diferente del anterior; abortado."; exit 2; }
    echo "PRECHECK OK: $material."
done

failed=0
for material in metal mold; do
    case "$material" in
        metal) stl=metal.stl; point="(0.0259 -0.0200 0.0259)"; reference=0.0000479874896432 ;;
        mold) stl=mold_repaired.stl; point="(0.003 -0.0200 0.0259)"; reference=0.00010284309608 ;;
    esac
    SUB="$WORK/$material"
    cp -p "$SUB/system/snappyHexMeshDict" "$SUB/system/snappyHexMeshDict.before_zonefaces_fix"
    tmp="$(mktemp "$SUB/system/.snappyHexMeshDict.XXXXXX")"
    sed -e "s/MATERIAL_STL_PLACEHOLDER/$stl/g"         -e "s/MATERIAL_POINT_PLACEHOLDER/$point/g"         "$TEMPLATE" > "$tmp"
    mv "$tmp" "$SUB/system/snappyHexMeshDict"

    echo "===== $material: reintentando snappy, SIN blockMesh ====="
    if ! foamDictionary -case "$SUB" system/snappyHexMeshDict          -entry castellatedMeshControls/allowFreeStandingZoneFaces          > "$SUB/log.preflight.retry1" 2>&1; then
        tail -n 20 "$SUB/log.preflight.retry1"
        failed=$((failed+1)); continue
    fi
    if ! snappyHexMesh -case "$SUB" -overwrite         > "$SUB/log.snappyHexMesh.retry1" 2>&1; then
        tail -n 45 "$SUB/log.snappyHexMesh.retry1"
        failed=$((failed+1)); continue
    fi
    set +e
    checkMesh -case "$SUB" -allGeometry -allTopology         > "$SUB/log.checkMesh.retry1" 2>&1
    rc=$?
    set -e
    grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK'         "$SUB/log.checkMesh.retry1" | tail -n 25 || true

    vol="$(sed -n -E 's/.*Total volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+).*/\1/p' "$SUB/log.checkMesh.retry1" | tail -n 1)"
    outer="$(awk '/^[[:space:]]*outerBox[[:space:]]*$/ {seen=1;next} seen && /nFaces[[:space:]]/ {gsub(/;/,"",$2);print $2;exit}' "$SUB/constant/polyMesh/boundary")"
    outer="${outer:-0}"
    echo "$material: volumen=${vol:-no disponible} m3, outerBox=$outer caras"
    good=1
    if ((rc != 0)) || ! grep -q 'Mesh OK' "$SUB/log.checkMesh.retry1" ||         grep -Eq 'Failed [1-9][0-9]* mesh checks' "$SUB/log.checkMesh.retry1"; then good=0; fi
    if [[ ! "$vol" =~ ^[0-9.eE+-]+$ ]] ||         ! awk -v v="$vol" -v ref="$reference" 'BEGIN {exit !((v+0)>0 && (v+0)>=ref*.9 && (v+0)<=ref*1.1)}'; then good=0; fi
    if [[ ! "$outer" =~ ^[0-9]+$ ]] || ((outer != 0)); then good=0; fi

    if ((good)); then
        echo "PASÓ control geométrico preliminar: $material (sin interfaz térmica)."
    else
        echo "RECHAZADO: $material. Logs conservados para diagnóstico."
        failed=$((failed+1))
    fi
done
echo "Resultados en $WORK/{metal,mold}/log.{snappyHexMesh,checkMesh}.retry1"
echo "No se modificaron casos anteriores ni se ejecutó CFD."
((failed==0)) || { echo "Mallas con fallos: $failed/2"; exit 5; }
echo "DOS MALLAS CON FILTROS PRELIMINARES APROBADOS; INTERFAZ CHT PENDIENTE."
