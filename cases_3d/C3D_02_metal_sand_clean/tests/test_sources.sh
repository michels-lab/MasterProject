#!/usr/bin/env bash
# Verificación completa SOLO tras importar las tres geometrías STL.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$ROOT/tests/test_template_static.sh"
bash "$ROOT/scripts/validate_sources.sh"
echo "Integridad de fuentes y CAD verificada. NO valida CFD."
