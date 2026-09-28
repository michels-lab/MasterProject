#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

cases="
B8_adaptiveOuter4
C8_adaptiveOuter4
B9_topFixedFlux
C9_topFixedFlux
"

for c in $cases
do
    echo "============================================================"
    echo "Running $c"
    echo "============================================================"
    (
        cd "$c"
        ./Allrun
    )
done
