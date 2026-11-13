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

echo "=== C. SURFACECHECK: SOLAMENTE LECTURA DEL STL ORIGINAL ==="
if ! command -v surfaceCheck >/dev/null 2>&1; then
    echo "ERROR: surfaceCheck no está en PATH; carga OpenFOAM Foundation 14."
    exit 2
fi

# Foundation 14 may expose -checkSelfIntersection without -outputThreshold.
# Some surfaceCheck builds write supplementary OBJ/problem-face files
# unconditionally. Run in an OWN temporary directory, not in the source case.
# A cleanup trap removes ONLY the exact new directory made by mktemp.
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/c3d02-surfaceCheck-XXXXXXXX")"
cleanup() { [[ -n "$SCRATCH" && -d "$SCRATCH" ]] && rm -rf -- "$SCRATCH"; }
trap cleanup EXIT

help_text="$(surfaceCheck -help 2>&1 || true)"
if printf '%s\n' "$help_text" | grep -Fq -- 'checkSelfIntersection'; then
    echo "Opción autointersección: anunciada en esta versión; comprobando..."
    args=(-checkSelfIntersection)
else
    echo "Opción autointersección no anunciada; realizando revisión topológica básica."
    args=()
fi
echo "surfaceCheck se ejecuta desde carpeta temporal; el STL es solo ENTRADA."
set +e
output="$(cd "$SCRATCH" && surfaceCheck "${args[@]}" "$STL" 2>&1)"
rc=$?
set -e

echo "---- RESULTADOS SURFACECHECK (salida filtrada) ----"
printf '%s\n' "$output" | grep -Ei -C 1 \
    'statistics|closed|self.intersect|non.manifold|unconnected|number of parts|normal orientation|degenerate|illegal|bad quality|problem|nearby points|triangles|bounding|found|error|FOAM FATAL|face|edge' \
    | tail -n 105 || true
echo "---- ÚLTIMAS LÍNEAS ORIGINALES ----"
printf '%s\n' "$output" | tail -n 12
echo "surfaceCheck código de salida: $rc"
echo "Nota: éxito del comando NO equivale a ausencia de intersecciones."
echo "Los archivos auxiliares, si los hubo, se escribieron SOLO en el directorio temporal."
echo "=== FIN: las mallas de metal y arena, sus logs y las geometrías originales siguen intactos ==="
