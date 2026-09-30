#!/usr/bin/env bash
set -u -o pipefail

# Clean, rerun and post-process the full controlled-buoyancy campaign.
# Each case Allrun performs:
#   blockMesh -> splitMeshRegions -> foamMultiRun
#   -> standard diagnostics -> momentum post-processing
#   -> spatial metalTop post-processing for FoamLens
#
# Runs serially on purpose for reproducibility and to avoid resource contention.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES_ROOT="$REPO_ROOT/cases_controlled_buoyancy"
STATUS_DIR="$REPO_ROOT/analysis_results/full_campaign_run"
STATUS_FILE="$STATUS_DIR/status.tsv"

CASES=(
  B3_reference
  B4_energy2
  B5_airGapOF14
  B5_outer3
  B6_adaptiveDt
  B7_outer4
  B8_adaptiveOuter4
  B9_airGapOF14
  B9_topFixedFlux
  B10_airGapOF14
  B11_topFixedFlux_airGapOF14
  B12_topFixedValue_airGapOF14
  B13_prghPressure_airGapOF14
  C3_reference
  C4_energy2
  C5_airGapOF14
  C5_outer3
  C6_adaptiveDt
  C7_outer4
  C8_adaptiveOuter4
  C9_airGapOF14
  C9_topFixedFlux
  C10_airGapOF14
  C11_topFixedFlux_airGapOF14
  C12_topFixedValue_airGapOF14
  C13_prghPressure_airGapOF14
)

mkdir -p "$STATUS_DIR"
printf "case\tstatus\tnote\n" > "$STATUS_FILE"

completed=0

echo "============================================================"
echo "QuickCup full controlled-buoyancy campaign"
echo "Cases: ${#CASES[@]}"
echo "Mode: clean + serial rerun + integrated post-processing"
echo "============================================================"

for CASE in "${CASES[@]}"; do
    CASE_DIR="$CASES_ROOT/$CASE"

    echo
    echo "============================================================"
    echo "[$((completed+1))/${#CASES[@]}] CLEANING: $CASE"
    echo "============================================================"

    if [ ! -f "$CASE_DIR/Allclean" ] || [ ! -f "$CASE_DIR/Allrun" ]; then
        echo "ERROR: missing Allclean or Allrun in $CASE_DIR"
        printf "%s\tFAILED\tmissing_Allclean_or_Allrun\n" "$CASE" >> "$STATUS_FILE"
        exit 2
    fi

    if ! bash "$CASE_DIR/Allclean"; then
        echo "ERROR: Allclean failed for $CASE"
        printf "%s\tFAILED\tAllclean_failed\n" "$CASE" >> "$STATUS_FILE"
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
        echo "Campaign stopped. Fix this case before continuing."
        exit "$rc"
    fi
done

echo
echo "============================================================"
echo "FULL CAMPAIGN COMPLETE"
echo "============================================================"
echo "Completed: $completed / ${#CASES[@]}"
echo "Status:    $STATUS_FILE"
echo
echo "Every successful case was clean-run and post-processed by its Allrun."
