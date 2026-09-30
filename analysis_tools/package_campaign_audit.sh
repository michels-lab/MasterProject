#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES_ROOT="$ROOT/cases_controlled_buoyancy"
OUT_DIR="$ROOT/analysis_results"
STAMP="$(date +%Y%m%d_%H%M%S)"
STAGE="$OUT_DIR/audit_bundle_stage_$STAMP"
ARCHIVE="$OUT_DIR/quickcup_campaign_audit_$STAMP.tar.gz"

CASES=(
  B3_reference B4_energy2 B5_airGapOF14 B5_outer3 B6_adaptiveDt
  B7_outer4 B8_adaptiveOuter4 B9_airGapOF14 B9_topFixedFlux B10_airGapOF14
  B11_topFixedFlux_airGapOF14 B12_topFixedValue_airGapOF14 B13_prghPressure_airGapOF14
  C3_reference C4_energy2 C5_airGapOF14 C5_outer3 C6_adaptiveDt
  C7_outer4 C8_adaptiveOuter4 C9_airGapOF14 C9_topFixedFlux C10_airGapOF14
  C11_topFixedFlux_airGapOF14 C12_topFixedValue_airGapOF14 C13_prghPressure_airGapOF14
)

mkdir -p "$STAGE/cases_controlled_buoyancy" "$STAGE/analysis_results"

if [ -d "$OUT_DIR/full_campaign_run" ]; then
  cp -a "$OUT_DIR/full_campaign_run" "$STAGE/analysis_results/"
fi

for NAME in "${CASES[@]}"; do
  SRC="$CASES_ROOT/$NAME"
  DST="$STAGE/cases_controlled_buoyancy/$NAME"
  mkdir -p "$DST"

  [ -f "$SRC/log.foamMultiRun" ] && cp "$SRC/log.foamMultiRun" "$DST/"
  [ -f "$SRC/log.topSurfaceFlowPostProcess" ] && cp "$SRC/log.topSurfaceFlowPostProcess" "$DST/"
  [ -d "$SRC/logs" ] && cp -a "$SRC/logs" "$DST/"
  [ -d "$SRC/postProcessing" ] && cp -a "$SRC/postProcessing" "$DST/"
done

(
  cd "$STAGE"
  tar -czf "$ARCHIVE" .
)

rm -rf "$STAGE"

echo
echo "AUDIT BUNDLE READY"
echo "$ARCHIVE"
du -h "$ARCHIVE"
echo
echo "Upload this .tar.gz file to ChatGPT. No OpenFOAM solver was executed."
