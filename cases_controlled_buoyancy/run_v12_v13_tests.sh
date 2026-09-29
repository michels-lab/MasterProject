#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

cases="
B12_topFixedValue_airGapOF14
C12_topFixedValue_airGapOF14
B13_prghPressure_airGapOF14
C13_prghPressure_airGapOF14
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
