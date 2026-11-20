#!/usr/bin/env bash
# C3D-05 Case B native Foundation14 heat flux, all 12,636 bilateral face pairs.
# Transactional output publication: do not expose partly written CSV as evidence.
# Runs ONLY after an audited, completed numerical solver and energy postprocess.
set -Eeuo pipefail
set -C   # Fail rather than clobber a prior log

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
ENERGY="$CASE/T0_NATIVE_ENERGY_HISTORY.json"
PUBLISHED="$CASE/T0_NATIVE_FACE_FLUX"
REQUIRED_SOURCE=(c3d05PatchFlux.C Make/files Make/options)
REQUIRED_DATA=(metal.csv mold.csv bilateral_diagnostics.json log.c3d05PatchFlux manifest.sha256)

if [[ "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    echo "BLOCKED_FOUNDATION14: source /opt/openfoam14/etc/bashrc, then execute the full Granada command" >&2
    exit 4
fi
for item in "$CASE" "$INPUTS" "$LOG" "$STATUS" "$ENERGY"; do
    if [[ ! -e "$item" || -L "$item" ]]; then
        echo "BLOCKED_EVIDENCE: missing or symlink native source: $item" >&2
        exit 4
    fi
done
if [[ -L "$PUBLISHED" || -e "$PUBLISHED" && ! -d "$PUBLISHED" ]]; then
    echo "BLOCKED_OUTPUT: invalid prior native face-flux directory" >&2
    exit 4
fi

# Never rebuild inside the tracked checkout, and never quietly substitute code
# for a prior build already tied to this numerical attempt.
if [[ ! -e "$BUILD" && ! -L "$BUILD" ]]; then
    cp -a -- "$SRC" "$BUILD"
fi
if [[ -L "$BUILD" || ! -d "$BUILD" ]]; then
    echo "BLOCKED_BUILD: unsafe native source copy" >&2
    exit 4
fi
for relative in "${REQUIRED_SOURCE[@]}"; do
    if [[ ! -f "$BUILD/$relative" || -L "$BUILD/$relative" ]] ||
       ! cmp -s -- "$SRC/$relative" "$BUILD/$relative"; then
        echo "BLOCKED_BUILD_DRIFT: preserved native source differs: $relative" >&2
        exit 4
    fi
done

# If completed evidence exists, verify ALL hashes and rerun ONLY the independent
# Python report check. No solver, native extractor, or wmake is invoked.
if [[ -d "$PUBLISHED" ]]; then
    for file in "${REQUIRED_DATA[@]}"; do
        if [[ ! -f "$PUBLISHED/$file" || -L "$PUBLISHED/$file" ]]; then
            echo "BLOCKED_PARTIAL_PUBLISHED_OUTPUT: $file" >&2
            exit 4
        fi
    done
    ( cd "$PUBLISHED" && sha256sum --check --status manifest.sha256 )
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/analyze_t0_patch_flux.py" \
        --metal "$PUBLISHED/metal.csv" --mold "$PUBLISHED/mold.csv" \
        --energy "$ENERGY" --inputs "$INPUTS" \
        --run-status "$STATUS" --solver-log "$LOG" \
        --out "$PUBLISHED/bilateral_diagnostics.json"
    echo "NATIVE_FACE_FLUX_VERIFIED_REUSED: no solver, wmake or CSV overwritten"
    exit 0
fi

if ! command -v wmake >/dev/null 2>&1; then
    echo "BLOCKED_WMAKE: Foundation14 compiler tool unavailable" >&2
    exit 4
fi
if [[ -L "$BIN_DIR" || -e "$BIN_DIR" && ! -d "$BIN_DIR" ]]; then
    echo "BLOCKED_BIN: unsafe binary output directory" >&2
    exit 4
fi
mkdir -p "$BIN_DIR"
export FOAM_USER_APPBIN="$BIN_DIR"
if [[ -e "$BIN" || -L "$BIN" ]]; then
    if [[ ! -x "$BIN" || -L "$BIN" || ! -f "$BIN_SHA" ]] ||
       ! sha256sum --check --status "$BIN_SHA"; then
        echo "BLOCKED_BIN_DRIFT: existing native binary checksum invalid" >&2
        exit 4
    fi
else
    if [[ -e "$CASE/log.wmake.C3D05_T0_flux" ]]; then
        echo "BLOCKED_BUILD_ATTEMPT: prior log preserved, cannot overwrite" >&2
        exit 4
    fi
    echo "=== Foundation14 native compile: isolated C++ source, no CFD ==="
    wmake "$BUILD" > "$CASE/log.wmake.C3D05_T0_flux" 2>&1
    if [[ ! -x "$BIN" ]]; then
        echo "BLOCKED_BUILD: no executable produced; see log" >&2
        exit 6
    fi
    sha256sum "$BIN" > "$BIN_SHA"
fi

# Write EVERYTHING into a private stage. Failed native extraction or malformed
# data leave prior accepted evidence intact; partial CSV never becomes canonical.
STAGE="$(mktemp -d "$CASE/.T0_NATIVE_FACE_FLUX_STAGING.XXXXXXXX")"
echo "=== Native bilateral mappedWall flux 12,636 faces per region ==="
echo "STAGE=$STAGE"
"$BIN" -case "$CASE" -outMetal "$STAGE/metal.csv" -outMold "$STAGE/mold.csv" -time '0:' \
    > "$STAGE/log.c3d05PatchFlux" 2>&1

echo "=== Validate native CSV coverage, paired geometry and signed heat transfer ==="
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HERE/analyze_t0_patch_flux.py" \
    --metal "$STAGE/metal.csv" --mold "$STAGE/mold.csv" \
    --energy "$ENERGY" --inputs "$INPUTS" \
    --run-status "$STATUS" --solver-log "$LOG" \
    --out "$STAGE/bilateral_diagnostics.json"

( cd "$STAGE" &&
  sha256sum metal.csv mold.csv bilateral_diagnostics.json log.c3d05PatchFlux > manifest.sha256 )
if [[ -e "$PUBLISHED" || -L "$PUBLISHED" ]]; then
    echo "BLOCKED_RACE: prior completed flux report appeared; stage preserved at $STAGE" >&2
    exit 4
fi
# A single directory rename publishes all mutually consistent evidence at once.
mv -T -- "$STAGE" "$PUBLISHED"
echo "NATIVE_BILATERAL_FACE_Q_PUBLISHED_NO_PHYSICAL_VALIDATION: $PUBLISHED"
