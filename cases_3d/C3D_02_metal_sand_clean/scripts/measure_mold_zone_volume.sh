#!/usr/bin/env bash
# C3D-02 — volume of the EXISTING moldVolume cellZone, OpenFOAM Foundation 14.
# NO new mesh, NO solver, NO changes to any case, STL or source polyMesh.
# Uses a disposable shadow case, symlinking the existing polyMesh read-only.
set -euo pipefail
source /opt/openfoam14/etc/bashrc

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${1:-$HOME/OpenFOAM/C3D02_materials/mold_zoned_l2_01}"
ZONE=moldVolume
CAD_VOLUME=0.00010284309608

[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || {
    echo "ERROR: requiere OpenFOAM Foundation 14."
    exit 2
}
bash "$ROOT/tests/test_sources.sh"

for file in "$SOURCE/constant/polyMesh/cellZones" \
            "$SOURCE/constant/polyMesh/owner" \
            "$SOURCE/constant/polyMesh/boundary" \
            "$SOURCE/log.snappyHexMesh" "$SOURCE/log.checkMesh.full" \
            "$SOURCE/system/controlDict"; do
    [[ -f "$file" ]] || { echo "ERROR: falta $file"; exit 2; }
done
grep -Fq 'moldVolume' "$SOURCE/constant/polyMesh/cellZones" || {
    echo "ERROR: no existe la zona $ZONE en el polyMesh generado."
    exit 2
}
grep -Fq 'moldInterface' "$SOURCE/constant/polyMesh/faceZones" || {
    echo "ERROR: falta la faceZone moldInterface de la prueba."
    exit 2
}
command -v foamPostProcess >/dev/null 2>&1 || {
    echo "ERROR: no está disponible foamPostProcess."
    exit 2
}

# The official Foundation 14 volFieldValue directly logs zone_.V() when
# constructed; this does NOT need temperature fields or a CFD simulation.
# The -constant switch is used because the case contains no time=0 fields.
# Running -case on a SHADOW case keeps postProcessing and logs away from the
# real C3D02_materials meshes. The polyMesh is referenced by a symlink ONLY.
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/c3d02-zone-volume-XXXXXXXX")"
cleanup() {
    [[ -n "$SCRATCH" && -d "$SCRATCH" ]] && rm -rf -- "$SCRATCH"
}
trap cleanup EXIT

mkdir -p "$SCRATCH/constant" "$SCRATCH/system"
ln -s "$SOURCE/constant/polyMesh" "$SCRATCH/constant/polyMesh"
cp -p "$SOURCE/system/controlDict" "$SCRATCH/system/controlDict"

cat > "$SCRATCH/system/functions" <<'EOF'
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      functions;
}

moldZoneVolume
{
    type               volFieldValue;
    libs               ("libfieldFunctionObjects.so");
    log                true;
    writeFields        false;
    writeVolume        true;
    writeNumberOfCells true;
    cellZone           moldVolume;
    operation          none;
    fields             ();
}
EOF

echo "=== C3D02 — MEDICION EXACTA DE ZONA SEGUN fvMesh Foundation 14 ==="
echo "Malla EXISTENTE: $SOURCE"
echo "cellZone solicitada: $ZONE"
echo "Volumen CAD molde: $CAD_VOLUME m3"
echo "Shadow case temporal: $SCRATCH"
echo "No se remalla; no se ejecuta solver ni cambia el caso original."

if ! foamPostProcess -case "$SCRATCH" \
    -dict "$SCRATCH/system/functions" -constant \
    > "$SCRATCH/log.foamPostProcess" 2>&1; then
    echo "ERROR: foamPostProcess no pudo leer la zona (se conserva la malla original)."
    tail -n 65 "$SCRATCH/log.foamPostProcess"
    exit 3
fi

echo "=== SALIDA DE LA ZONA ==="
grep -Ei -C 2 'moldZoneVolume|number of cells|volume =|FoamPostProcess|Time =|End$' \
    "$SCRATCH/log.foamPostProcess" | tail -n 55 || true

# Foundation's volFieldValue::read outputs this on initialisation:
#    number of cells = N
#    volume = V
# "Total volume" from the original checkMesh refers to ALL cells and MUST
# NOT be mistaken for this zone-specific value.
VOLUME="$(sed -n -E 's/^[[:space:]]*volume[[:space:]]*=[[:space:]]*([0-9.eE+-]+)[[:space:]]*$/\1/p' \
    "$SCRATCH/log.foamPostProcess" | tail -n 1)"
COUNT="$(sed -n -E 's/^[[:space:]]*number of cells[[:space:]]*=[[:space:]]*([0-9]+)[[:space:]]*$/\1/p' \
    "$SCRATCH/log.foamPostProcess" | tail -n 1)"

if [[ ! "$VOLUME" =~ ^[0-9.eE+-]+$ || ! "$COUNT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: la utilidad no reportó volumen y conteo de cellZone."
    echo "No usar el volumen global de checkMesh como sustituto."
    exit 4
fi

python3 - "$VOLUME" "$COUNT" "$CAD_VOLUME" <<'PY'
import sys
v, n, cad = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
delta_pct = 100.0*(v-cad)/cad
print("==== RESULTADO DE moldVolume (SOLO LA ZONA) ====")
print(f"Celdas etiquetadas             : {n:,d}")
print(f"Volumen cellZone                : {v:.9g} m3 = {v*1e6:.5f} cm3")
print(f"Volumen CAD arena               : {cad:.9g} m3 = {cad*1e6:.5f} cm3")
print(f"Desviación contra CAD           : {delta_pct:+.3f}%")
if n <= 0 or v <= 0:
    print("RECHAZADO: zone vacía o volumen no físico.")
    sys.exit(5)
if abs(delta_pct) > 5:
    print("RECHAZADO: gran discrepancia volumétrica de zone (>5%).")
else:
    print("VOLUMEN ZONAL PLAUSIBLE (±5%); todavía NO es malla válida.")
print("PENDIENTE: extraer EN COPIA, validar fronteras, checkMesh y acoplamiento térmico.")
print("NO se alteraron C14 ni las mallas históricas.")
PY
