#!/usr/bin/env bash
# Regression for 3D C14 material fidelity; no OpenFOAM run, no Python.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case_tmp="$(mktemp -d)"
trap 'rm -rf "$case_tmp"' EXIT
mkdir -p "$case_tmp/constant/metal/polyMesh" "$case_tmp/constant/mold/polyMesh"
bash "$ROOT/scripts/stage_c14_materials.sh" "$case_tmp" >/dev/null
test -f "$case_tmp/C14_MATERIALS_VERIFIED.txt"
for item in metal/materials/castIron metal/physicalProperties metal/fvModels metal/g metal/pRef mold/materials/silica mold/physicalProperties; do
    cmp -s "$ROOT/constant/$item" "$case_tmp/constant/$item"
done
bash "$ROOT/scripts/stage_c14_materials.sh" "$case_tmp" >/dev/null
printf '\n// induced mismatch must fail without overwrite\n' >> "$case_tmp/constant/metal/physicalProperties"
if bash "$ROOT/scripts/stage_c14_materials.sh" "$case_tmp" >/dev/null 2>&1; then
    echo "ERROR: modified material was accepted" >&2
    exit 1
fi
grep -Fq 'induced mismatch' "$case_tmp/constant/metal/physicalProperties"
bash -n "$ROOT/Allmesh"
echo "OK: C14 material staging is byte-identical, idempotent and refuses overwrites."
