#!/usr/bin/env bash
# Ensayo mínimo e independiente. NUNCA ejecuta snappyHexMesh ni foamMultiRun.
source /opt/openfoam14/etc/bashrc
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${1:-$HOME/OpenFOAM/C3D02_background}"

bash "$ROOT/scripts/validate_sources.sh"
if [[ -e "$WORK" ]]; then
    echo "La carpeta de trabajo ya existe: $WORK"
    echo "Sin sobrescritura. Selecciona otra ruta explícita si necesitas repetir."
    exit 1
fi
mkdir -p "$WORK/system" "$WORK/constant"
cp "$ROOT/system/controlDict" "$ROOT/system/blockMeshDict" "$WORK/system/"
cp -a "$ROOT/constant/geometry" "$WORK/constant/"

blockMesh -case "$WORK" > "$WORK/log.blockMesh" 2>&1 || {
    tail -n 40 "$WORK/log.blockMesh"
    exit 1
}
checkMesh -case "$WORK" -allGeometry -allTopology > "$WORK/log.checkMesh.background" 2>&1 || {
    tail -n 40 "$WORK/log.checkMesh.background"
    exit 1
}
grep -Ei 'cells:|Overall domain bounding box|Total volume|Mesh OK|Failed' "$WORK/log.checkMesh.background" || true
echo "SOLO malla de fondo en: $WORK"
echo "NO hay malla metal/arena ni interfaz térmica; NO se ejecutó solver."
