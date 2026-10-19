#!/usr/bin/env bash
# C3D-01: OpenFOAM Foundation v14 background mesh ONLY.
# The STL will be used later by snappyHexMesh, NOT by blockMesh.
# No Python, no STL copying/transformation, no CFD, no cleanup.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v blockMesh >/dev/null 2>&1 || ! command -v checkMesh >/dev/null 2>&1; then
  echo "ERROR: primero carga OpenFOAM 14: source /opt/openfoam14/etc/bashrc" >&2
  exit 2
fi

# Preserve previous results, including a failed attempt's diagnostic logs.
for existing in constant/polyMesh constant/metal/polyMesh constant/mold/polyMesh log.blockMesh log.checkMesh.background; do
  if [[ -e "$existing" ]]; then
    echo "ERROR: $existing ya existe; no lo sobrescribire. Prepara una copia nueva del caso." >&2
    exit 3
  fi
done

echo "C3D-01: construyendo exclusivamente la caja inicial con blockMesh (units [mm])."
blockMesh > log.blockMesh 2>&1
echo "C3D-01: revisando la malla de fondo con checkMesh."
checkMesh -allTopology -allGeometry > log.checkMesh.background 2>&1
echo "Listo: revisa log.blockMesh y log.checkMesh.background."
echo "Aun NO se ejecuto snappyHexMesh, no hay regiones metal/arena ni simulacion CFD."
