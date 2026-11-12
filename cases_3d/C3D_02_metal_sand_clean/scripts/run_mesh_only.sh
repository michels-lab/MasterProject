#!/usr/bin/env bash
# C3D-02: One clean, guarded OpenFOAM Foundation 14 meshing attempt.
# Mesh only: does NOT run foamMultiRun / subsetMesh / topoSet / splitMeshRegions.
# No results or existing directories are deleted or overwritten.
source /opt/openfoam14/etc/bashrc
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${1:-$HOME/OpenFOAM/C3D02_mesh}"
EXPECTED_VERSION=14

if [[ "${WM_PROJECT_VERSION:-}" != "$EXPECTED_VERSION" ]]; then
    echo "ERROR: se requiere OpenFOAM Foundation 14 (detectado: ${WM_PROJECT_VERSION:-sin definir})"
    exit 2
fi

bash "$ROOT/scripts/validate_sources.sh"
bash "$ROOT/tests/test_template_static.sh"

if [[ -e "$WORK" ]]; then
    echo "ERROR: existe $WORK"
    echo "No se modifica la malla existente. Revisa sus logs antes de otro ensayo."
    exit 2
fi

echo "=== C3D02 - una sola carpeta de mallado: $WORK ==="
mkdir -p "$WORK/system" "$WORK/constant/geometry"
cp -p "$ROOT/system/controlDict" "$ROOT/system/blockMeshDict" \
      "$ROOT/system/snappyHexMeshDict" "$WORK/system/"
cp -p "$ROOT/constant/geometry/metal.stl" \
      "$ROOT/constant/geometry/mold_repaired.stl" \
      "$WORK/constant/geometry/"

# Parse the intended native Foundation 14 dictionary before meshing.
foamDictionary -case "$WORK" system/snappyHexMeshDict \
    -entry castellatedMeshControls/insidePoints > "$WORK/log.preflight.insidePoints" 2>&1 || {
    tail -n 35 "$WORK/log.preflight.insidePoints"
    echo "ERROR: configuración insidePoints rechazada."
    exit 3
}

echo "1/3 - blockMesh (caja auxiliar, NO volumen físico)"
if ! blockMesh -case "$WORK" > "$WORK/log.blockMesh" 2>&1; then
    tail -n 60 "$WORK/log.blockMesh"
    exit 3
fi

echo "2/3 - snappyHexMesh (dos puntos interiores, sin punto en aire)"
if ! snappyHexMesh -case "$WORK" -overwrite > "$WORK/log.snappyHexMesh" 2>&1; then
    tail -n 80 "$WORK/log.snappyHexMesh"
    echo "ERROR: snappyHexMesh no completó el mallado."
    exit 4
fi

echo "3/3 - checkMesh exhaustivo (NO CFD)"
set +e
checkMesh -case "$WORK" -allGeometry -allTopology \
    > "$WORK/log.checkMesh.full" 2>&1
CHECK_RC=$?
set -e

echo "=== Resumen de geometría ==="
grep -Ei 'cells:|Total volume|Number of regions:|boundary patches|face tets|concave cells|small determinant|Failed [0-9]+ mesh checks|Mesh OK' \
    "$WORK/log.checkMesh.full" | tail -n 55 || true

echo "=== Zonas y parches disponibles ==="
if [[ -f "$WORK/constant/polyMesh/cellZones" ]]; then
    grep -E '^([[:space:]]*)metal([[:space:]]|$)' "$WORK/constant/polyMesh/cellZones" | head -n 4 || true
else
    echo "ALERTA: no existe constant/polyMesh/cellZones"
fi
if [[ -f "$WORK/constant/polyMesh/boundary" ]]; then
    grep -E '^(outerBox|metal|mold|metalInterface)' "$WORK/constant/polyMesh/boundary" || true
fi

echo "Logs completos: $WORK/log.blockMesh, log.snappyHexMesh, log.checkMesh.full"

if [[ "$CHECK_RC" -ne 0 ]] || grep -Eq 'Failed [1-9][0-9]* mesh checks' "$WORK/log.checkMesh.full"; then
    echo "MALLA NO APROBADA: checkMesh -allGeometry -allTopology detectó fallos."
    exit 5
fi

if ! grep -Eq 'Mesh OK' "$WORK/log.checkMesh.full"; then
    echo "MALLA NO APROBADA: no existe confirmación Mesh OK en el chequeo exhaustivo."
    exit 5
fi

echo "CHECKMESH COMPLETO: sin fallos reportados."
echo "ATENCIÓN: esto NO certifica todavía ausencia total de exterior ni interfaces CHT."
echo "No se ejecuta splitMeshRegions ni solver hasta analizar celdas, volumen, zonas e interfaz."
