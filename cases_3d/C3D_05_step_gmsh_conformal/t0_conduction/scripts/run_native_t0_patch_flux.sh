#!/usr/bin/env bash
# C3D-05 B Foundation14 bilateral q per face, invoked after native energy audit.
# All build/output artifacts are isolated from MasterProject/source CAD.
set -Eeuo pipefail
set -C  # shell no-clobber logs

if [[ "$#" -ne 4 ]]; then
    echo "Usage: bash run_native_t0_patch_flux.sh CASE INPUTS SOLVER_LOG RUN_STATUS" >&2
    exit 2
fi
CASE="$1"
INPUTS="$2"
LOG="$3"
STATUS="$4"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/../native_flux"
BUILD="$CASE/T0_NATIVE_FLUX_BUILD"
BIN_DIR="$CASE/T0_NATIVE_FLUX_BIN"
BIN="$BIN_DIR/c3d05PatchFlux"
BIN_SHA="$BIN_DIR/c3d05PatchFlux.sha256"
METAL="$CASE/T0_FACE_FLUX_METAL.csv"
MOLD="$CASE/T0_FACE_FLUX_MOLD.csv"
OUTPUT="$CASE/T0_FACE_FLUX_BILATERAL_DIAGNOSTICS.json"
ENERGY="$CASE/T0_NATIVE_ENERGY_HISTORY.json"
SRC_PARTS=(c3d05PatchFlux.C Make/files Make/options)

if [[ "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    echo "BLOCKED: native bilateral heat flux requires Foundation14" >&2
    exit 4
fi
for x in "$CASE" "$INPUTS" "$LOG" "$STATUS" "$ENERGY"; do
    if [[ ! -e "$x" || -L "$x" ]]; then
        echo "BLOCKED: required native evidence absent or symlink: $x" >&2
        exit 4
    fi
done

if [[ ! -e "$BUILD" && ! -L "$BUILD" ]]; then
    cp -a -- "$SRC" "$BUILD"
fi
if [[ -L "$BUILD" || ! -d "$BUILD" ]]; then
    echo "BLOCKED: unsafe native build directory" >&2
    exit 4
fi
for rel in "${SRC_PARTS[@]}"; do
    if ! cmp -s -- "$SRC/$rel" "$BUILD/$rel"; then
        echo "BLOCKED: native source changed since this case build: $rel" >&2
        exit 4
    fi
done

if [[ -e "$METAL" || -e "$MOLD" || -L "$METAL" || -L "$MOLD" ]]; then
    if [[ ! -f "$METAL" || ! -f "$MOLD" ||
          -L "$METAL" || -L "$MOLD" ]]; then
        echo "BLOCKED: previous incomplete/unsafe flux extraction; preserve both" >&2
        exit 2
    fi
    echo "NATIVE_Q_ALREADY_EXTRACTED: reuse both CSVs, verify SHA; no solver/re-extraction."
else
    if ! command -v wmake >/dev/null 2>&1; then
        echo "BLOCKED: OpenFOAM14 wmake unavailable" >&2
        exit 4
    fi
    if [[ -L "$BIN_DIR" || -e "$BIN_DIR" && ! -d "$BIN_DIR" ]]; then
        echo "BLOCKED: unsafe native binary directory" >&2
        exit 4
    fi
    mkdir -p "$BIN_DIR"
    export FOAM_USER_APPBIN="$BIN_DIR"
    if [[ -e "$BIN" || -L "$BIN" ]]; then
        if [[ ! -x "$BIN" || -L "$BIN" || ! -f "$BIN_SHA" ]] ||
           ! sha256sum --check --status "$BIN_SHA"; then
            echo "BLOCKED: pre-existing native executable has invalid SHA" >&2
            exit 4
        fi
    else
        if [[ -e "$CASE/log.wmake.C3D05_T0_flux" ]]; then
            echo "BLOCKED: incomplete prior wmake log retained" >&2
            exit 4
        fi
        echo "=== Build native Foundation14 solid q extractor inside isolated case ==="
        wmake "$BUILD" > "$CASE/log.wmake.C3D05_T0_flux" 2>&1
        if [[ ! -x "$BIN" ]]; then
            echo "BLOCKED: wmake returned but native binary absent; see build log" >&2
            exit 6
        fi
        sha256sum "$BIN" > "$BIN_SHA"
    fi
    if [[ -e "$CASE/log.C3D05_native_bilateral_q" ]]; then
        echo "BLOCKED: prior native extraction log preserved" >&2
        exit 4
    fi
    echo "=== Load BOTH coupledTemperature solid thermos at same time and extract q ==="
    "$BIN" -case "$CASE" -outMetal "$METAL" -outMold "$MOLD" -time '0:' \
        > "$CASE/log.C3D05_native_bilateral_q" 2>&1
fi

echo "=== Match 12636 reciprocal faces, signed direct q and energy integral residual ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/analyze_t0_patch_flux.py" \
    --metal "$METAL" --mold "$MOLD" \
    --energy "$ENERGY" --inputs "$INPUTS" \
    --run-status "$STATUS" --solver-log "$LOG" --out "$OUTPUT"
echo "BILATERAL_NATIVE_Q_DIAGNOSTICS_RECORDED_NOT_EXP_VALIDATED"
