#!/usr/bin/env bash
# Diagnostico SOLO LECTURA de la primera malla C3D-02.
# Prohibido volver a correr mesh, recortar, reparar o borrar en este paso.
set -euo pipefail
CASE="${1:-$HOME/OpenFOAM/C3D02_mesh}"

for file in "$CASE/log.snappyHexMesh" "$CASE/log.checkMesh.full" \
            "$CASE/system/snappyHexMeshDict" "$CASE/constant/polyMesh/boundary"; do
    if [[ ! -f "$file" ]]; then
        printf 'ERROR: no existe %s; este script no creara nuevos casos.\n' "$file"
        exit 2
    fi
done

echo "======= CASO EXISTENTE (SOLO LECTURA) ======="
printf 'Ruta: %s\n' "$CASE"
echo "======= 1. SELECCION DE CELDAS EN SNAPPY ======="
# Palabras que distinguen conservacion completa, zonas desconectadas y remocion.
grep -Ein -C 2 \
  'Keeping all cells|Selected for keeping|Removing (cells|outside)|Removed [0-9]+|cell(s)? to keep|insidePoints|insidePoint|location[s]?InMesh|Number of regions|mesh regions|keep.*region|cellZone.*found point|region containing' \
  "$CASE/log.snappyHexMesh" | tail -n 110 || true

echo "======= 2. RESULTADO Y ESTADISTICAS DE SNAPPY ======="
grep -Ein \
  'Created cell|cellZones:|faceZones:|cellZone|faceZone|Patch|snapping|castellated|Finished meshing|^End$|Number of cells' \
  "$CASE/log.snappyHexMesh" | tail -n 65 || true

echo "======= 3. TRES METRICAS DECISIVAS (CHECKMESH) ======="
grep -Ei \
  'cells:|boundary patches:|Number of regions:|Total volume|face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' \
  "$CASE/log.checkMesh.full" | tail -n 26 || true

echo "======= 4. PARCHES RESULTANTES ======="
# Solo muestra nombres, tipos y cantidad de caras. No modifica la malla.
awk '
  /^[[:space:]]*[A-Za-z_][A-Za-z0-9_.-]*[[:space:]]*$/ {candidate=$1}
  /\{/ {if (candidate != "") {patch=candidate; candidate=""}}
  /type[[:space:]]/ {type=$2; gsub(/;/, "", type)}
  /nFaces[[:space:]]/ {
      n=$2; gsub(/;/, "", n);
      if (patch != "") {print patch, "type=" type, "nFaces=" n}
      patch=""; type=""
  }
' "$CASE/constant/polyMesh/boundary" | tail -n 45

echo "======= 5. ZONAS DISPONIBLES ======="
for zone in cellZones faceZones; do
    file="$CASE/constant/polyMesh/$zone"
    if [[ -f "$file" ]]; then
        printf '%s: PRESENTE\n' "$zone"
        grep -Ei '^[[:space:]]*(metal|mold|metalInterface)([[:space:]]|$)|nCells|nFaces' "$file" | head -n 25 || true
    else
        printf '%s: AUSENTE\n' "$zone"
    fi
done

echo "======= FIN (NO SE HA EJECUTADO NINGUNA UTILIDAD DE MALLADO) ======="
