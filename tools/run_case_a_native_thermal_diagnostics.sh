#!/usr/bin/env bash
# OpenFOAM Foundation 14: isolated, same-policy native startup diagnostics.
set -euo pipefail
umask 077
home="$HOME/OpenFOAM"
mpi="$home/CAMPAIGN_200S_ADAPTIVE_MPI_01"
lockroot="$home/CAMPAIGN_200S_ADAPTIVE_UNCAPPED_01"
out="$home/C14_A_NATIVE_THERMAL_DIAGNOSTICS"
mode="${1:-both}"
case "$mode" in cap|uncapped|both) ;; *) echo "usage: $0 [cap|uncapped|both]" >&2; exit 2;; esac
[[ "${WM_PROJECT_VERSION:-}" == 14 ]] || { echo "Load Foundation 14" >&2; exit 2; }
for exe in foamDictionary decomposePar foamMultiRun mpirun foamLog flock; do
    command -v "$exe" >/dev/null
done
[[ -d "$mpi" && -d "$lockroot" && ! -L "$lockroot" && ! -L "$out" ]] || exit 2
exec 9>"$lockroot/.execution.lock"
flock -n 9 || { echo "Adaptive campaign active; no new run started" >&2; exit 2; }
mkdir -p "$out"
batch=$(mktemp -d "$out/batch-XXXXXXXX")
printf 'Native diagnostics: %s\n' "$batch"
emit() {
    local region=$1 op=$2 fields=$3
    cat <<EOF

granada_${region}_${op}
{
    type            volFieldValue;
    libs            ("libfieldFunctionObjects.so");
    region          $region;
    cellZone        all;
    operation       $op;
    fields          ($fields);
    writeFields     false;
    log             true;
    writeToFile     true;
    executeControl  timeStep;
    executeInterval 1;
    writeControl    timeStep;
    writeInterval   1;
}
EOF
}
run_one() {
    local policy=$1 suffix tag src dest rc fr
    if [[ "$policy" == cap ]]; then suffix=ckuf84dm; tag=0p025; else suffix=fp6has9o; tag=uncapped; fi
    local -a matches
    shopt -s nullglob
    matches=("$mpi"/r8-3s-Co025-dt"$tag"-"$suffix"/C14-3DA-200s)
    shopt -u nullglob
    if (( ${#matches[@]} != 1 )); then
        echo "Original pilot not located: $suffix; no substitution" >&2; return 2
    fi
    src="${matches[0]}"
    [[ -f "$src/log.foamMultiRun" && -f "$src/system/functions" ]] || return 2
    grep -Eq 'Negative initial temperature T0' "$src/log.foamMultiRun" || return 2
    for d in 0 constant system; do
        [[ -d "$src/$d" && ! -L "$src/$d" ]] || return 2
        if [[ -n "$(find "$src/$d" -type l -print -quit)" ]]; then
            echo "Linked input refused: $src/$d" >&2; return 2
        fi
    done
    # Check unchanged original controls with OpenFOAM itself.
    local c="$src/system/controlDict"
    [[ "$(foamDictionary "$c" -entry adjustTimeStep -value)" == yes ]] || return 2
    [[ "$(foamDictionary "$c" -entry deltaT -value)" =~ ^0[.]0010*$ ]] || return 2
    [[ "$(foamDictionary "$c" -entry maxCo -value)" =~ ^0[.]250*$ ]] || return 2
    [[ "$(foamDictionary "$c" -entry endTime -value)" =~ ^3([.]0+)?$ ]] || return 2
    [[ "$(foamDictionary "$src/system/decomposeParDict" -entry numberOfSubdomains -value)" == 8 ]] || return 2
    if [[ "$policy" == cap ]]; then
        [[ "$(foamDictionary "$c" -entry maxDeltaT -value)" =~ ^0[.]0250*$ ]] || return 2
    else
        if foamDictionary "$c" -entry maxDeltaT -value >/dev/null 2>&1; then return 2; fi
    fi
    dest="$batch/$policy"
    mkdir "$dest"
    cp -a --reflink=auto "$src/0" "$src/constant" "$src/system" "$dest/"
    diff -qr "$src/0" "$dest/0"
    diff -qr "$src/constant" "$dest/constant"
    diff -qr "$src/system" "$dest/system"
    printf '%s\n' "$src" > "$dest/SOURCE_CASE.txt"
    # Only diagnostics appended. All original function objects and write cadence remain.
    {
        emit metal min 'T h p_rgh phaseChangeSource:alpha1'
        emit metal max 'T h p_rgh phaseChangeSource:alpha1'
        emit mold min 'T e'
        emit mold max 'T e'
    } >> "$dest/system/functions"
    cmp "$src/system/controlDict" "$dest/system/controlDict"
    cmp "$src/system/fvSolution" "$dest/system/fvSolution"
    cmp "$src/system/metal/fvSolution" "$dest/system/metal/fvSolution"
    cmp "$src/system/mold/fvSolution" "$dest/system/mold/fvSolution"
    foamDictionary "$dest/system/functions" -entry granada_metal_min >/dev/null
    foamDictionary "$dest/system/functions" -entry granada_mold_max >/dev/null
    printf '\n%s: running native OpenFOAM in %s\n' "$policy" "$dest"
    if decomposePar -allRegions -case "$dest" > "$dest/log.decomposePar" 2>&1; then
        :
    else
        echo "Decomposition failed: $dest/log.decomposePar" >&2; return 2
    fi
    # Preserve both failure and success, never declare physical validation.
    set +e
    mpirun -np 8 foamMultiRun -case "$dest" -parallel 2>&1 | tee "$dest/log.foamMultiRun"
    rc=$?
    (cd "$dest" && foamLog log.foamMultiRun > log.foamLog 2>&1)
    fr=$?
    set -e
    printf 'foamMultiRun_pipeline_exit=%s\nfoamLog_exit=%s\n' "$rc" "$fr" > "$dest/NATIVE_EXIT.txt"
    printf '%s: solver pipeline exit=%s, foamLog exit=%s, outputs=%s\n' "$policy" "$rc" "$fr" "$dest"
    return 0
}
# Stop on any preparation failure; a native solver failure is preserved and
# the other policy can still be measured. Do not promote pilots to 200 s.
if [[ "$mode" == cap || "$mode" == both ]]; then run_one cap; fi
if [[ "$mode" == uncapped || "$mode" == both ]]; then run_one uncapped; fi
printf 'Native logs and per-step postProcessing retained: %s\n' "$batch"
