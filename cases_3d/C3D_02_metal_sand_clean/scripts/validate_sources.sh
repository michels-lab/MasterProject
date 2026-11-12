#!/usr/bin/env bash
# Solo lectura: propiedades C14 + STL / SHA + plantillas
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
C14="$REPO/cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant"
for file in \
    metal/materials/castIron metal/physicalProperties metal/fvModels metal/g metal/pRef \
    mold/materials/silica mold/physicalProperties
do
    [[ -f "$ROOT/constant/$file" ]] || { echo "FALTA: $file"; exit 1; }
    cmp -s "$ROOT/constant/$file" "$C14/$file" || { echo "FÍSICA DIFERENTE DE C14: $file"; exit 1; }
    echo "C14 IDENTICO: $file"
done
for pair in "metal.stl fc8e6b7f3c229369b856aca7dab936347732028d9cd695499bf0e249363fb810" \
            "mold.stl 2e62e31875dc3c86dd7e6f2efe60d4c173ee4cee5e4f6ff63205c08efee3a638" \
            "mold_repaired.stl 860525e8a9fb2de483cf90f331f2753a339d82c5eee706ecfc1b8186bf49e9fe"
do
    read -r name expected <<< "$pair"
    actual="$(sha256sum "$ROOT/constant/geometry/$name" | cut -d' ' -f1)"
    [[ "$actual" == "$expected" ]] || { echo "SHA NO COINCIDE: $name"; exit 1; }
    echo "STL VERIFICADO: $name"
done
echo "Fuente y CAD íntegros. Esto NO valida mallado ni ejecución CFD."
