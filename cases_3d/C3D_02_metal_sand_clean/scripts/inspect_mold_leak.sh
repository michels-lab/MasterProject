#!/usr/bin/env bash
# Read-only evidence for the persistent mold leak in C3D-02.
# Does not mesh, subset, edit CAD, launch CFD, or create another case.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${1:-$HOME/OpenFOAM/C3D02_materials}"
STL="$ROOT/constant/geometry/mold_repaired.stl"

for f in "$STL"          "$WORK/mold/log.snappyHexMesh.retry1"          "$WORK/mold_offface_01/log.snappyHexMesh"          "$WORK/mold/log.checkMesh.retry1"          "$WORK/mold_offface_01/log.checkMesh.full"; do
    [[ -f "$f" ]] || { printf 'FALTA %s\n' "$f"; exit 2; }
done

echo "=== A. RESULTADOS OBTENIDOS (SIN RE-EJECUTAR) ==="
for name in mold mold_offface_01; do
    case "$name" in
        mold) log="$WORK/$name/log.snappyHexMesh.retry1"
              qc="$WORK/$name/log.checkMesh.retry1" ;;
        mold_offface_01) log="$WORK/$name/log.snappyHexMesh"
                         qc="$WORK/$name/log.checkMesh.full" ;;
    esac
    echo "--- $name: seleccion y topologia ---"
    grep -Ei 'Cell selection insidePoints|Keeping all cells|Selected for keeping|Number of intersected edges|Number of regions|Finished meshing' "$log" | tail -n 24 || true
    echo "--- $name: volumen, caras y calidad ---"
    grep -Ei 'cells:|Total volume|Number of regions:|Face tets|Concave cells|Failed [0-9]+ mesh checks|Mesh OK' "$qc" | tail -n 15 || true
    if [[ -f "$WORK/$name/constant/polyMesh/boundary" ]]; then
        awk '/^[[:space:]]*outerBox[[:space:]]*$/ {found=1;next} found && /nFaces[[:space:]]/ {print "outerBox nFaces:", $2; exit}'             "$WORK/$name/constant/polyMesh/boundary"
    fi
done

echo "=== B. ETAPA DE RECORTE DE CELDAS: CONTEXTO ORIGINAL ==="
log="$WORK/mold_offface_01/log.snappyHexMesh"
grep -Ein -B 16 -A 10 'Selected for keeping' "$log" | tail -n 55 || true

echo "=== C. VERIFICACION DE AUTO-INTERSECCIONES DEL STL SIN MODIFICARLO ==="
if ! command -v surfaceCheck >/dev/null 2>&1; then
    echo "surfaceCheck no disponible. Cargar OpenFOAM Foundation 14 antes de ejecutar."
    exit 2
fi
if surfaceCheck -help 2>&1 | grep -Fq -- '-checkSelfIntersection' &&    surfaceCheck -help 2>&1 | grep -Fq -- '-outputThreshold'; then
    set +e
    output="$(cd "$WORK/mold_offface_01" && surfaceCheck -checkSelfIntersection -outputThreshold 0 "$STL" 2>&1)"
    rc=$?
    set -e
    printf '%s\n' "$output" | grep -Ei -C 2 'Statistics|closed|non-manifold|intersect|problem|degenerate|illegal|bounding|triangle|face' | tail -n 78 || true
    echo "surfaceCheck exit code: $rc (la existencia de intersecciones se interpreta por el texto)."
else
    echo "Esta instalacion no declara ambas opciones en surfaceCheck -help."
    echo "No se ha ejecutado una alternativa que pudiera escribir archivos."
fi
echo "=== FIN: NO SE HA MODIFICADO NINGUNA MALLA NI EL STL ==="
