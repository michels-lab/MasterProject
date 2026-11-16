#!/usr/bin/env bash
# C3D-02 — generate checkMesh defect evidence for existing iron/sand meshes.
# Strictly copies: NEVER alters earlier meshes, STL or C14; NO CFD, NO remeshing.
source /opt/openfoam14/etc/bashrc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${1:-$HOME/OpenFOAM/C3D02_materials}"
OUT="$BASE/quality_evidence_01"

[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || {
    echo "ERROR: se requiere OpenFOAM Foundation 14"; exit 2;
}
bash "$ROOT/tests/test_sources.sh"
[[ -d "$BASE/metal" && -d "$BASE/mold_extracted_l2_01" ]] || {
    echo "ERROR: faltan subcasos metal o mold_extracted_l2_01"; exit 2;
}
[[ ! -e "$OUT" && ! -L "$OUT" ]] || {
    echo "ERROR: $OUT ya existe. No se sobrescribe evidencia"; exit 2;
}

# Check prerequisites for BOTH materials before making new files.
for mat in metal mold; do
    case "$mat" in
        metal) SRC="$BASE/metal"; LOG="$SRC/log.checkMesh.retry1" ;;
        mold) SRC="$BASE/mold_extracted_l2_01"; LOG="$SRC/log.checkMesh.full" ;;
    esac
    for p in "$SRC/constant/polyMesh/owner" "$SRC/constant/polyMesh/points" \
             "$SRC/constant/polyMesh/faces" "$SRC/constant/polyMesh/boundary" \
             "$SRC/system/controlDict" "$LOG"; do
        [[ -f "$p" ]] || { echo "ERROR: falta $p"; exit 2; }
    done
    [[ -z "$(find "$SRC/constant/polyMesh" -type l -print -quit)" ]] || {
        echo "ERROR: $mat contiene symlinks internos; no copiar"; exit 2;
    }
    grep -Eq 'Failed [1-9][0-9]* mesh checks' "$LOG" || {
        echo "ERROR: evidencia previa no demuestra calidad rechazada para $mat"; exit 2;
    }
done

command -v checkMesh >/dev/null 2>&1 || {
    echo "ERROR: checkMesh no disponible"; exit 2;
}
help="$(checkMesh -help 2>&1 || true)"
opts=(-allGeometry -allTopology)
if printf '%s\n' "$help" | grep -Fq -- '-writeSurfaces'; then
    opts+=(-writeSurfaces)
fi
if printf '%s\n' "$help" | grep -Fq -- '-writeSets'; then
    opts+=(-writeSets)
fi
echo "Opciones verificadas por checkMesh -help: ${opts[*]}"
echo "Se generará evidencia SÓLO en $OUT; la carpeta anterior no se modifica."

mkdir -p "$OUT"
failed=0
for mat in metal mold; do
    case "$mat" in
        metal) SRC="$BASE/metal" ;;
        mold) SRC="$BASE/mold_extracted_l2_01" ;;
    esac
    DEST="$OUT/$mat"
    mkdir -p "$DEST/constant" "$DEST/system"
    cp -a -- "$SRC/constant/polyMesh" "$DEST/constant/polyMesh"
    cp -p -- "$SRC/system/controlDict" "$DEST/system/controlDict"

    echo ""
    echo "====== $mat: checkMesh exhaustivo sobre COPIA INDEPENDIENTE ======"
    set +e
    checkMesh -case "$DEST" "${opts[@]}" > "$DEST/log.checkMesh.evidence" 2>&1
    rc=$?
    set -e
    echo "checkMesh codigo de retorno: $rc (no basta para aprobar calidad)."
    grep -Ei 'cells:|boundary patches:|Number of regions:|Total volume|small determinant|Concave cells|Face tets|Failed [0-9]+ mesh checks|Mesh OK|Writing|write' \
        "$DEST/log.checkMesh.evidence" | tail -n 38 || true

    if ((rc != 0)) || grep -Eq 'Failed [1-9][0-9]* mesh checks' "$DEST/log.checkMesh.evidence" || \
       ! grep -q 'Mesh OK' "$DEST/log.checkMesh.evidence"; then
        echo "CALIDAD: NO APROBADA para $mat (resultado esperado, sin suavizar umbrales)."
        failed=$((failed+1))
    else
        echo "CALIDAD: checkMesh completo reporta Mesh OK para $mat."
    fi

    echo "--- Parches (tipo y numero de caras) ---"
    awk '
        /^[[:space:]]*[A-Za-z_][A-Za-z_0-9]*[[:space:]]*$/ {
            name=$1; type=""; nf="";
        }
        /^[[:space:]]*type[[:space:]]+/ {
            type=$2; gsub(";", "", type)
        }
        /^[[:space:]]*nFaces[[:space:]]+/ {
            nf=$2; gsub(";", "", nf);
            if (name!="") print name, "type=" type, "nFaces=" nf
        }
    ' "$DEST/constant/polyMesh/boundary"

    echo "--- Archivos de problemas exportados ---"
    if [[ -d "$DEST/postProcessing" ]]; then
        find "$DEST/postProcessing" -type f \
            \( -name '*.vtk' -o -name '*.vtp' -o -name '*.vtu' \) \
            -printf '%P\n' | head -n 25 || true
        nfiles="$(find "$DEST/postProcessing" -type f \
            \( -name '*.vtk' -o -name '*.vtp' -o -name '*.vtu' \) | wc -l)"
        echo "Archivos VTK generados: $nfiles"
    else
        echo "No se generó postProcessing (revisar opciones en log)."
    fi

    if [[ "$mat" == "mold" ]]; then
        echo "AVISO: oldInternalFaces type=internal NO es una pared térmica validada."
    fi
    echo "Diagnóstico y VTK, si fueron generados: $DEST"
done

echo ""
echo "====== RESUMEN ======"
echo "2 fuentes originales SIN CAMBIOS; 2 copias independientes creadas."
echo "Materiales con calidad rechazada en esta revisión: $failed/2."
echo "Este paso NO alisa, repara, remalla ni crea interfaz CHT."
echo "Siguiente puerta: localizar y explicar celdas malas antes de optimizar mallas."
