#!/bin/sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "$SCRIPT_DIR" || exit 1

cases="
B3_reference
B4_energy2
B5_outer3
B6_adaptiveDt
B7_outer4
C3_reference
C4_energy2
C5_outer3
C6_adaptiveDt
C7_outer4
"

fields="(phaseChangeSolidFraction phaseChangeDarcyCoeff phaseChangeModelDeltaT phaseChangeDarcyAcceleration phaseChangeBuoyancyAcceleration pRghAcceleration magPhaseChangeDarcyAcceleration magPhaseChangeBuoyancyAcceleration magPRghAcceleration phaseChangeDragToBuoyancy phaseChangeDragToPressure)"

status=0

for c in $cases
do
    echo "============================================================"
    echo "Momentum post-processing: $c"
    echo "============================================================"

    if [ ! -f "$c/log.foamMultiRun" ]
    then
        echo "SKIP: solver log is missing."
        status=1
        continue
    fi

    if ! find "$c" -mindepth 3 -maxdepth 3 -path "*/metal/phaseChangeDarcyCoeff" -print -quit | grep -q .
    then
        echo "SKIP: no calculated phaseChangeDarcyCoeff fields were found."
        status=1
        continue
    fi

    (
        cd "$c" || exit 1

        foamPostProcess \
            -region metal \
            -dict system/momentumPostProcessing \
            -time '0:' \
            -fields "$fields" \
            > log.momentumPostProcess 2>&1

        rc=$?

        if [ $rc -eq 0 ]
        then
            echo "OK: $c"
        else
            echo "FAILED: $c (see $c/log.momentumPostProcess)"
        fi

        exit $rc
    )

    [ $? -eq 0 ] || status=1
done

exit $status
