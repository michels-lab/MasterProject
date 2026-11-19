#!/usr/bin/env bash
# Stage T0b: ONE COMMAND, explicit case materialization AFTER vetted inputs.
# NEVER executes foamMultiRun or changes the accepted HEX8 source.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T0="$(cd "$HERE/.." && pwd)"
SRC="$HOME/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
OUT="$HOME/OpenFOAM/C3D05_T0_CONDUCTION_01"
INPUTS="${C3D05_T0_INPUTS:-$T0/T0_INPUTS.json}"
if [[ -e "$OUT" || -L "$OUT" ]]; then
    echo "PRESERVED: never overwrite the new thermal case: $OUT" >&2
    exit 2
fi
echo "=== C3D-05 T0 MATERIALIZATION GATED (NO CFD) ==="
echo "=== 1/3: source+material input preflight ==="
bash "$HERE/run_t0_preflight.sh"
echo "=== 2/3: render OpenFOAM Foundation14 dictionaries and COPY accepted meshes ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/prepare_t0.py" \
    --inputs "$INPUTS" --source "$SRC" --out "$OUT"
echo "=== 3/3: check parsed dictionary syntax with native foamDictionary ==="
for file in \
    "$OUT/system/controlDict" "$OUT/system/fvSolution" \
    "$OUT/system/metal/fvSchemes" "$OUT/system/metal/fvSolution" \
    "$OUT/system/mold/fvSchemes" "$OUT/system/mold/fvSolution" \
    "$OUT/constant/metal/physicalProperties" "$OUT/constant/mold/physicalProperties" \
    "$OUT/0/metal/T" "$OUT/0/mold/T"
do
    foamDictionary "$file" >/dev/null
    echo "PARSE_OK: ${file#"$OUT/"}"
done
echo "T0_DICTIONARIES_PARSED: NO CFD. No claim of material or solver validation."
echo "NEXT GATE: region thermophysics and coupled flux + energy conservation on authorized test."
