#!/usr/bin/env bash
# Importacion unica de CAD a C3D-02. Nunca sobrescribe los STL nuevos.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/../C3D_01_metal_mold/constant/geometry"
DEST="$ROOT/constant/geometry"

if [[ ! -d "$SOURCE" ]]; then
    echo "FALTA fuente CAD: $SOURCE"
    echo "No borres respaldos originales; restaura las tres geometrías desde Git/CAD."
    exit 1
fi
mkdir -p "$DEST"
for pair in "metal.stl fc8e6b7f3c229369b856aca7dab936347732028d9cd695499bf0e249363fb810" \
            "mold.stl 2e62e31875dc3c86dd7e6f2efe60d4c173ee4cee5e4f6ff63205c08efee3a638" \
            "mold_repaired.stl 860525e8a9fb2de483cf90f331f2753a339d82c5eee706ecfc1b8186bf49e9fe"
do
    read -r name expected <<< "$pair"
    [[ -f "$SOURCE/$name" ]] || { echo "FALTA: $SOURCE/$name"; exit 1; }
    actual="$(sha256sum "$SOURCE/$name" | cut -d' ' -f1)"
    [[ "$actual" == "$expected" ]] || { echo "SHA NO COINCIDE: $name ($actual)"; exit 1; }
    if [[ -e "$DEST/$name" ]]; then
        cmp -s "$SOURCE/$name" "$DEST/$name" || { echo "CONFLICTO: $DEST/$name; NO SOBRESCRITO"; exit 1; }
        echo "YA IDENTICO: $name"
    else
        cp -p -- "$SOURCE/$name" "$DEST/$name"
        echo "COPIADO Y VERIFICADO: $name"
    fi
done
echo "CAD local C3D-02 completo. Confirma el commit/push de estos STL antes de borrar carpetas históricas."
