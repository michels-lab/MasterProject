#!/usr/bin/env bash
set -u -o pipefail

# Batch retrospective post-processing of face-wise metalTop flow.
#
# Default behavior:
#   - auto-detect every current B*/C* case in cases_controlled_buoyancy/
#   - process cases that already contain solved time directories + phi
#   - skip cases that cannot be reconstructed exactly
#   - NEVER run foamMultiRun
#
# Optional behavior:
#   pass one or more case directories explicitly to process only those cases.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES_ROOT="$REPO_ROOT/cases_controlled_buoyancy"
DICT="$SCRIPT_DIR/topSurfaceFlowPostProcessing"
STATUS_DIR="$REPO_ROOT/analysis_results/top_surface_flow_batch"
STATUS_FILE="$STATUS_DIR/status.tsv"

if ! command -v foamPostProcess >/dev/null 2>&1; then
    echo "ERROR: foamPostProcess is not available in this shell."
    echo "Source your OpenFOAM Foundation v14 environment first, then rerun."
    exit 2
fi

mkdir -p "$STATUS_DIR"
printf "case\tstatus\tlatest_phi_time\tnote\n" > "$STATUS_FILE"

if [ "$#" -gt 0 ]; then
    CASES=("$@")
else
    mapfile -t CASES < <(
        find "$CASES_ROOT" -mindepth 1 -maxdepth 1 -type d \
            \( -name 'B[0-9]*' -o -name 'C[0-9]*' \) \
            -print | sort -V
    )
fi

if [ "${#CASES[@]}" -eq 0 ]; then
    echo "ERROR: no B*/C* cases found."
    exit 3
fi

processed=0
skipped=0
failed=0

for CASE_INPUT in "${CASES[@]}"; do
    if [ ! -d "$CASE_INPUT" ]; then
        echo "SKIP: case directory not found: $CASE_INPUT"
        printf "%s\tSKIPPED\t\tnot_found\n" "$CASE_INPUT" >> "$STATUS_FILE"
        skipped=$((skipped+1))
        continue
    fi

    CASE="$(cd "$CASE_INPUT" && pwd)"
    NAME="$(basename "$CASE")"

    echo
    echo "================================================================="
    echo "Top-flow post-processing: $NAME"
    echo "================================================================="

    if [ ! -d "$CASE/constant/metal/polyMesh" ]; then
        echo "SKIP: metal mesh not found."
        printf "%s\tSKIPPED\t\tmetal_mesh_missing\n" "$NAME" >> "$STATUS_FILE"
        skipped=$((skipped+1))
        continue
    fi

    # Find all solved time directories that contain the exact solver surface
    # field phi.  The latest one is reported for traceability.
    mapfile -t PHI_TIMES < <(
        find "$CASE" -mindepth 2 -maxdepth 3 -type f \
            \( -path '*/metal/phi' -o -path '*/metal/phi.gz' \) -print |
        sed -E 's#^.*/([^/]+)/metal/phi(\.gz)?$#\1#' |
        awk '/^[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$/' |
        sort -g -u
    )

    if [ "${#PHI_TIMES[@]}" -eq 0 ]; then
        echo "SKIP: no solved time contains metal/phi."
        echo "      Existing integrated sums cannot reconstruct exact face-wise flux."
        printf "%s\tSKIPPED\t\tphi_not_saved_in_time_directories\n" "$NAME" >> "$STATUS_FILE"
        skipped=$((skipped+1))
        continue
    fi

    LATEST_PHI_TIME="${PHI_TIMES[${#PHI_TIMES[@]}-1]}"
    echo "Latest time with exact metal/phi: $LATEST_PHI_TIME s"

    rm -rf \
      "$CASE/postProcessing/topPatchFaceFields" \
      "$CASE/postProcessing/topPhiNet" \
      "$CASE/postProcessing/topPhiAbsolute" \
      "$CASE/postProcessing/topPhiMinimum" \
      "$CASE/postProcessing/topPhiMaximum" \
      "$CASE/postProcessing/nearTopInternalLine"

    if foamPostProcess \
        -case "$CASE" \
        -region metal \
        -dict "$DICT" \
        -time '0:' \
        -fields '(U T p_rgh rho phi phaseChangeSource:alpha1)' \
        2>&1 | tee "$CASE/log.topSurfaceFlowPostProcess"
    then
        echo "OK: $NAME"
        printf "%s\tPROCESSED\t%s\tok\n" "$NAME" "$LATEST_PHI_TIME" >> "$STATUS_FILE"
        processed=$((processed+1))
    else
        echo "FAILED: foamPostProcess returned an error for $NAME"
        printf "%s\tFAILED\t%s\tsee_log.topSurfaceFlowPostProcess\n" "$NAME" "$LATEST_PHI_TIME" >> "$STATUS_FILE"
        failed=$((failed+1))
    fi
done

echo
echo "================================================================="
echo "BATCH SUMMARY"
echo "================================================================="
echo "Processed: $processed"
echo "Skipped:   $skipped"
echo "Failed:    $failed"
echo "Status:    $STATUS_FILE"
echo
echo "No foamMultiRun execution was performed."

# Do not hide partial failures from the user, but allow skipped cases because
# missing historical phi cannot be reconstructed without rerunning them.
if [ "$failed" -gt 0 ]; then
    exit 5
fi
