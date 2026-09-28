#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

cases="
B10_airGapOF14
C10_airGapOF14
B11_topFixedFlux_airGapOF14
C11_topFixedFlux_airGapOF14
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
