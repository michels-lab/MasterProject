#!/bin/sh

# Canonical V12/V13 local runner.
# Runs all four cases even if one fails, then prints a single status table.
# The simulation passes only if foamMultiRun ends normally and latestTime=10.

set -u

if [ -z "${WM_PROJECT_DIR:-}" ]; then
    if [ -f /opt/openfoam14/etc/bashrc ]; then
        . /opt/openfoam14/etc/bashrc
    else
        echo "ERROR: OpenFOAM environment is not loaded and /opt/openfoam14/etc/bashrc was not found."
        exit 2
    fi
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR" || exit 2

cases="
B12_topFixedValue_airGapOF14
C12_topFixedValue_airGapOF14
B13_prghPressure_airGapOF14
C13_prghPressure_airGapOF14
"

summary_file=$(mktemp)
overall=0

for c in $cases
do
    echo "============================================================"
    echo "Running $c"
    echo "============================================================"

    (
        cd "$c" || exit 99
        ./Allclean || true
        ./Allrun
    )
    allrun_rc=$?

    log="$c/log.foamMultiRun"
    latest="MISSING"
    end_flag="NO"
    fatal_count="NA"

    if [ -d "$c" ]; then
        latest=$(
            cd "$c" &&
            foamListTimes -latestTime 2>/dev/null
        )
        [ -n "$latest" ] || latest="NONE"
    fi

    if [ -f "$log" ]; then
        if grep -q '^[[:space:]]*End[[:space:]]*$' "$log"; then
            end_flag="YES"
        fi

        fatal_count=$(
            grep -c -E 'FOAM FATAL|Floating point|Segmentation fault' "$log" 2>/dev/null || true
        )
    fi

    case_status="FAIL"
    if [ "$end_flag" = "YES" ] && [ "$latest" = "10" ] && [ "${fatal_count:-1}" = "0" ]; then
        case_status="PASS"
    else
        overall=1
    fi

    printf '%-36s  %-4s  latest=%-8s  End=%-3s  fatal=%s  AllrunRC=%s\n' \
        "$c" "$case_status" "$latest" "$end_flag" "$fatal_count" "$allrun_rc" | tee -a "$summary_file"

    if [ "$case_status" = "FAIL" ] && [ -f "$log" ]; then
        echo
        echo "---- Last 40 lines: $c ----"
        tail -40 "$log"
        echo
    fi
done

echo
echo "==================== V12/V13 SUMMARY ===================="
cat "$summary_file"
rm -f "$summary_file"

echo
if [ "$overall" -eq 0 ]; then
    echo "All four canonical V12/V13 cases completed to 10 s."
else
    echo "One or more canonical V12/V13 cases did not complete cleanly."
fi

exit "$overall"
