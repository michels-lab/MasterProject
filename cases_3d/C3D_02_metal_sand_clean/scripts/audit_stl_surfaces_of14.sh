#!/usr/bin/env bash
# Native Foundation 14 STL geometry audit (all 4 STL surfaces); NO MESH/CFD.
# A zero exit status from surfaceCheck is NOT evidence of closed geometry.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GEO="$ROOT/constant/geometry"
OUT="$HOME/OpenFOAM/C3D02_STL_SURFACE_AUDIT_OF14"
[[ ! -e "$OUT" && ! -L "$OUT" ]] || {
    echo "Preserving existing surface evidence: $OUT" >&2
    exit 2
}
[[ -r /opt/openfoam14/etc/bashrc ]] || {
    echo "OpenFOAM Foundation 14 not found" >&2; exit 2;
}
set +u
source /opt/openfoam14/etc/bashrc
set -u
[[ "$WM_PROJECT_VERSION" == "14" ]] || {
    echo "OpenFOAM is not Foundation 14" >&2; exit 2;
}
command -v surfaceCheck >/dev/null || {
    echo "Missing native surfaceCheck" >&2; exit 2;
}
mkdir -p "$OUT"
summary="$OUT/STL_SURFACE_RESULTS.tsv"
printf '%s\n' 'stl	exit_code	closed	parts_1	normals_1	no_self_intersection	status' > "$summary"
bad=0
for name in metal.stl mold_repaired.stl metal_v2.stl mold_v2.stl; do
    sourceFile="$GEO/$name"
    [[ -s "$sourceFile" ]] || { echo "MISSING: $sourceFile" >&2; bad=1; continue; }
    trial="$OUT/$(basename "$name" .stl)"
    mkdir -p "$trial"
    # OpenFOAM surfaceCheck can write OBJ/problemFaces to CWD; isolate them.
    set +e
    (cd "$trial" && surfaceCheck -checkSelfIntersection "$sourceFile") > "$trial/log.surfaceCheck" 2>&1
    rc=$?
    set -e
    log="$trial/log.surfaceCheck"
    closed=0
    parts=0
    normals=0
    noSelf=0
    grep -Fq "Surface is closed. All edges connected to two faces." "$log" && closed=1
    grep -Eq 'Number of unconnected parts[[:space:]]*:[[:space:]]*1([[:space:]]|$)' "$log" && parts=1
    grep -Eq 'Number of zones \(connected area with consistent normal\)[[:space:]]*:[[:space:]]*1([[:space:]]|$)' "$log" && normals=1
    grep -Fq 'Surface is not self-intersecting' "$log" && noSelf=1
    status=REJECT
    if (( rc==0 && closed && parts && normals && noSelf )); then status=PASS; else bad=1; fi
    printf '%s\t%d\t%d\t%d\t%d\t%d\t%s\n' "$name" "$rc" "$closed" "$parts" "$normals" "$noSelf" "$status" | tee -a "$summary"
    echo "---- $name: surfaceCheck Foundation 14 (summary) ----"
    grep -Ei 'Surface is|Number of unconnected parts|Number of zones \(connected area|not self-intersecting|self-intersecting at|connected to one face|connected to >2 faces|FOAM Warning|FOAM FATAL|Error' "$log" | tail -n 35 || true
    echo "Full native log: $log"
done
echo
cat "$summary"
echo "All four source STLs unchanged; outputs preserved at $OUT"
echo "Native surfaceCheck did not generate or modify any 3D mesh or C14 physical property."
if (( bad )); then
    echo "NATIVE STL SURFACE AUDIT REJECTED: examine logs BEFORE editing snappyHexMeshDict." >&2
    exit 5
fi
echo "NATIVE STL SURFACE AUDIT PASSED; pairing/contact and volumetric mesh are still unverified."
