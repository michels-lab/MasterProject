#!/usr/bin/env bash
# FS-C06: read already-written OpenFOAM Foundation 14 function-object .dat files.
# Does NOT execute foamMultiRun, alter cases or infer conservation closure.
# Accepts paths such as postProcessing/fluid/FS_C06_.../0/file.dat.
set -Eeuo pipefail

die() { printf 'FS-C06 READ BLOCKED: %s\n' "$*" >&2; exit 2; }
[[ $# -eq 1 ]] || die "Usage: bash read_native_monitors.sh /absolute/FS-C06-isolated-case"
[[ -d "$1" ]] || die "Case directory not found: $1"
case_dir="$(cd "$1" && pwd -P)"
post="$case_dir/postProcessing"
[[ -d "$post" ]] || die "postProcessing directory absent: $post"
[[ -f "$case_dir/FS_C06_REPORT.json" ]] || die "FS_C06_REPORT.json absent in selected case"

monitors=(
    FS_C06_metalVoFVolume
    FS_C06_solidMetalVolume
    FS_C06_mixtureMass
    FS_C06_atmosphereMassFlux
    FS_C06_atmosphereTopMassFlux
    FS_C06_atmosphereSidesMassFlux
    FS_C06_atmosphereLowerSidesMassFlux
    FS_C06_fluidToMoldMassFlux
    FS_C06_wallHeatFluxFluid
    FS_C06_wallHeatFluxMold
)

printf 'FS-C06 RAW NATIVE MONITOR READ (NO CFD): %s\n' "$case_dir"
printf 'PATH DISCOVERY: recursive; accepts region-specific postProcessing layout.\n'
found=0
for name in "${monitors[@]}"; do
    printf '\n========== %s ==========\n' "$name"
    # Match exactly the same path rule as the accepted native gate.
    # Do not assume /postProcessing/FS_C06_name exists at the top level.
    mapfile -d '' -t files < <(find "$post" -type f \
        -path "*/$name/*" -name '*.dat' -size +0c -print0)
    if (( ${#files[@]} == 0 )); then
        printf 'MISSING .dat for %s\n' "$name" >&2
        continue
    fi
    found=$((found + 1))
    for file in "${files[@]}"; do
        printf 'FILE: %s\n' "${file#"$case_dir"/}"
        printf 'SHA256: '
        sha256sum "$file" | awk '{print $1}'
        printf '%s\n' 'HEADER:'
        awk '/^[[:space:]]*#/ { if (n++ < 12) print }' "$file"
        printf '%s\n' 'DATA LAST UP TO 4 ROWS:'
        # Preserve original multicolumn rows without inferring units or signs.
        awk 'NF && $1 !~ /^#/ { a[(n++ % 4)] = $0 } END {
            start = n > 4 ? n - 4 : 0;
            for (i = start; i < n; i++) print a[i % 4];
            if (n == 0) print "NO NUMERICAL ROWS FOUND";
        }' "$file"
    done
done
printf '\nFS-C06 MONITOR PATHS WITH NONEMPTY .dat: %s/10\n' "$found"
(( found == ${#monitors[@]} )) || die "One or more expected monitor paths are absent"
printf '%s\n' 'NOTE: file existence is not numerical mass/energy closure or physical shrinkage.'
