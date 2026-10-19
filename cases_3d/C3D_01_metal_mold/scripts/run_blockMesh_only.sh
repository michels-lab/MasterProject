#!/usr/bin/env bash
# C3D-01 stage 1: local background mesh only. Never delete prior CFD results.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v blockMesh >/dev/null 2>&1 || ! command -v checkMesh >/dev/null 2>&1; then
  echo "ERROR: carga OpenFOAM Foundation v14 con source /opt/openfoam14/etc/bashrc" >&2
  exit 2
fi
if [[ -d constant/polyMesh || -d constant/metal/polyMesh || -d constant/mold/polyMesh ]]; then
  echo "ERROR: ya existe una malla; usa una copia nueva del caso en lugar de sobrescribirla." >&2
  exit 3
fi
for p in constant/triSurface/mold.stl constant/triSurface/metal.stl; do
  if [[ ! -s "$p" ]]; then
    echo "ERROR: falta $p. Primero prepara los STL con prepare_geometry.py." >&2
    exit 4
  fi
done
python3 ../../analysis_tools/preflight_c3d_stl.py \
  --stl-dir constant/triSurface \
  --manifest geometry_reference.json \
  --json geometry_preflight_runtime.json

blockMesh > log.blockMesh 2>&1
checkMesh -allTopology -allGeometry > log.checkMesh.background 2>&1
echo "Malla de fondo construida y auditada; revisar logs. NO se ejecuto CFD."
