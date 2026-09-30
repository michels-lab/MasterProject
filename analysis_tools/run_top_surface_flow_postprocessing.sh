#!/usr/bin/env bash
set -euo pipefail

# Post-process face-wise metalTop flux and the internal velocity line directly
# below metalTop.  This script never runs foamMultiRun and never changes the
# physical solution.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DICT="$SCRIPT_DIR/topSurfaceFlowPostProcessing"

if ! command -v foamPostProcess >/dev/null 2>&1; then
    echo "ERROR: foamPostProcess is not available in this shell."
    echo "Source your OpenFOAM Foundation v14 environment first, then rerun."
    exit 2
fi

if [ "$#" -eq 0 ]; then
    set -- \
      "$REPO_ROOT/cases_controlled_buoyancy/B11_topFixedFlux_airGapOF14" \
      "$REPO_ROOT/cases_controlled_buoyancy/B13_prghPressure_airGapOF14"
fi

for CASE in "$@"; do
    CASE="$(cd "$CASE" && pwd)"

    echo
    echo "================================================================="
    echo "Top-flow post-processing: $CASE"
    echo "================================================================="

    if [ ! -d "$CASE/constant/metal/polyMesh" ]; then
        echo "ERROR: metal mesh not found in $CASE/constant/metal/polyMesh"
        echo "This case must already have been meshed/run locally."
        exit 3
    fi

    # Exact spatial flux visualization requires the solved surface field phi.
    # Check the latest canonical 10 s output first.
    if [ ! -f "$CASE/10/metal/phi" ] && [ ! -f "$CASE/10/metal/phi.gz" ]; then
        echo "ERROR: $CASE/10/metal/phi is missing."
        echo "The existing integrated postProcessing sum(phi) is not enough"
        echo "to reconstruct the exact face-wise top flux retrospectively."
        echo "Do NOT rerun yet. Send this message back for the fallback route."
        exit 4
    fi

    rm -rf \
      "$CASE/postProcessing/topPatchFaceFields" \
      "$CASE/postProcessing/topPhiNet" \
      "$CASE/postProcessing/topPhiAbsolute" \
      "$CASE/postProcessing/topPhiMinimum" \
      "$CASE/postProcessing/topPhiMaximum" \
      "$CASE/postProcessing/nearTopInternalLine"

    foamPostProcess \
        -case "$CASE" \
        -region metal \
        -dict "$DICT" \
        -time '0.1:10' \
        -fields '(U T p_rgh rho phi phaseChangeSource:alpha1)' \
        2>&1 | tee "$CASE/log.topSurfaceFlowPostProcess"

    echo
    echo "Created:"
    echo "  postProcessing/topPatchFaceFields/   <- face-by-face metalTop data"
    echo "  postProcessing/topPhiNet/            <- net sum(phi)"
    echo "  postProcessing/topPhiAbsolute/       <- sum(abs(phi_i))"
    echo "  postProcessing/topPhiMinimum/        <- strongest negative face flux"
    echo "  postProcessing/topPhiMaximum/        <- strongest positive face flux"
    echo "  postProcessing/nearTopInternalLine/  <- U,T,p_rgh,rho,alphaL below top"
    echo "  log.topSurfaceFlowPostProcess"
done

echo
echo "DONE. No solver rerun was performed."
