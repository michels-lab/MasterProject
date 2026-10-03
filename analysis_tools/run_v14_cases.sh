#!/usr/bin/env bash
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES_ROOT="$REPO_ROOT/cases_controlled_buoyancy"
STATUS_DIR="$REPO_ROOT/analysis_results/v14_run"
STATUS_FILE="$STATUS_DIR/status.tsv"

CASES=(
  B14_topFixedFlux_explicitRef
  C14_topFixedFlux_explicitRef
)

mkdir -p "$STATUS_DIR"
printf "case\tstatus\tnote\n" > "$STATUS_FILE"

echo "============================================================"
echo "QuickCup V14 controlled run"
echo "Cases: B14 + C14"
echo "Baseline: V11 fixedFluxPressure + slip"
echo "============================================================"

completed=0
for CASE in "${CASES[@]}"; do
    CASE_DIR="$CASES_ROOT/$CASE"

    echo
    echo "============================================================"
    echo "[$((completed+1))/${#CASES[@]}] CLEANING: $CASE"
    echo "============================================================"

    if [ ! -f "$CASE_DIR/Allclean" ] || [ ! -f "$CASE_DIR/Allrun" ]; then
        printf "%s\tFAILED\tmissing_Allclean_or_Allrun\n" "$CASE" >> "$STATUS_FILE"
        echo "ERROR: missing Allclean or Allrun in $CASE_DIR"
        exit 2
    fi

    if ! bash "$CASE_DIR/Allclean"; then
        printf "%s\tFAILED\tAllclean_failed\n" "$CASE" >> "$STATUS_FILE"
        echo "ERROR: Allclean failed for $CASE"
        exit 3
    fi

    echo
    echo "============================================================"
    echo "[$((completed+1))/${#CASES[@]}] RUNNING: $CASE"
    echo "============================================================"

    if bash "$CASE_DIR/Allrun"; then
        printf "%s\tCOMPLETED\tok\n" "$CASE" >> "$STATUS_FILE"
        completed=$((completed+1))
        echo "COMPLETED: $CASE"
    else
        rc=$?
        printf "%s\tFAILED\tAllrun_exit_%s\n" "$CASE" "$rc" >> "$STATUS_FILE"
        echo "ERROR: $CASE failed with exit code $rc"
        echo "V14 stopped here so the first failing configuration can be audited."
        exit "$rc"
    fi
done

echo
echo "============================================================"
echo "V14 RUN COMPLETE"
echo "Completed: $completed / ${#CASES[@]}"
echo "Status: $STATUS_FILE"
echo "============================================================"
