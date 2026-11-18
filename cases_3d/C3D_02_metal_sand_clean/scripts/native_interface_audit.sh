#!/usr/bin/env bash
# Read-only inspection of splitMeshRegions patches (OpenFOAM Foundation 14).
# Does not change polyMesh, STL, C14 material fields or CHT settings.
set -euo pipefail
[[ $# -eq 1 && "$1" == /* ]] || { echo "Usage: native_interface_audit.sh /absolute/case" >&2; exit 2; }
CASE="$1"
[[ -d "$CASE" ]] || { echo "Missing case: $CASE" >&2; exit 2; }

for region in metal mold; do
    boundary="$CASE/constant/$region/polyMesh/boundary"
    echo
    echo "REGION $region: $boundary"
    if [[ ! -s "$boundary" ]]; then
        echo "MISSING REGION BOUNDARY"
        continue
    fi
    # Native OpenFOAM boundary file is a FoamFile header followed by
    # a patch count and a parenthesized list, not an ordinary dictionary.
    # Read patch declarations, type, nFaces and both historical and newer
    # mapping vocabulary without modifying anything.
    awk '
        !inList && /^[[:space:]]*\([[:space:]]*$/ { inList=1; next }
        !inList { next }
        inList && !active && /^[[:space:]]*\)[[:space:]]*$/ { exit }
        !active && $1 ~ /^[A-Za-z_][A-Za-z0-9_]*$/ && NF == 1 {
            candidate=$1; next
        }
        !active && $1=="{" && candidate!="" {
            active=1; name=candidate; candidate=""
            type="missing"; faces="missing"
            nr="-"; np="-"; sr="-"; sp="-"
            next
        }
        active && $1=="}" {
            printf "PATCH name=%s type=%s nFaces=%s neighbourRegion=%s neighbourPatch=%s sampleRegion=%s samplePatch=%s\n", name, type, faces, nr, np, sr, sp
            active=0; next
        }
        active && $1=="type"            { type=$2; sub(/;$/, "", type) }
        active && $1=="nFaces"          { faces=$2; sub(/;$/, "", faces) }
        active && $1=="neighbourRegion" { nr=$2; sub(/;$/, "", nr) }
        active && $1=="neighbourPatch"  { np=$2; sub(/;$/, "", np) }
        active && $1=="sampleRegion"    { sr=$2; sub(/;$/, "", sr) }
        active && $1=="samplePatch"     { sp=$2; sub(/;$/, "", sp) }
    ' "$boundary"
done
echo
echo "Interpretation: no listed metal_to_mold / mold_to_metal means no named"
echo "interface in this split output. Patch named but type != mappedWall"
echo "is a separate issue; never retype a patch without verifying matching"
echo "physical faces and the OpenFOAM Foundation 14 coupling contract."
