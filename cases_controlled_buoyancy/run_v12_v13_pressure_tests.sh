#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

cases="
B12_fixedValueP_rgh
C12_fixedValueP_rgh
B13_prghPressureAtmosphere
C13_prghPressureAtmosphere
"

for c in $cases
do
    echo "============================================================"
    echo "Running $c"
    echo "============================================================"
    (
        cd "$c"
        ./Allclean
        ./Allrun
    )
done
