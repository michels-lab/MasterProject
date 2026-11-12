#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for script in "$ROOT"/scripts/*.sh; do
    bash -n "$script"
done
bash "$ROOT/scripts/validate_sources.sh"
awk '
  /vertices/ {active=1; next}
  active && /^\);/ {active=0; exit}
  active && /^[[:space:]]*\(/ {n++}
  END {if (n!=8) {print "ERROR: se esperan 8 vértices, encontrados " n; exit 1}; print "8 vertices declarados"}
' "$ROOT/system/blockMeshDict"
echo "Pruebas estáticas de fuentes completas. NO implican validación OpenFOAM."
