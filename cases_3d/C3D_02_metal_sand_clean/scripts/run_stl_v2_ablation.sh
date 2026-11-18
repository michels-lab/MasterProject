#!/usr/bin/env bash
# Controlled geometry ablation: change one STL at a time. Native OpenFOAM 14.
# Existing cases and source STLs are never overwritten; no CFD.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT="$HOME/OpenFOAM/C3D02_STL_V2_ABLATION_REPORT.txt"
[[ ! -e "$REPORT" ]] || {
    echo "Existing report preserved: $REPORT" >&2
    echo "Use existing candidate cases or archive the report intentionally." >&2
    exit 2
}
mkdir -p "$HOME/OpenFOAM"
exec > >(tee "$REPORT") 2>&1
echo "C3D-02 / native OpenFOAM 14 / single-STL variable isolation"
echo "Sources: original metal.stl, original mold_repaired.stl, approved v2 STL"
echo "Physics C14, geometry units [mm], snappy settings identical in all cases."
echo "No solver run. No source or historical case overwrite."
echo
for trial in metal mold; do
    if [[ "$trial" == metal ]]; then
        variant="--v2-metal-only"
        CASE="$HOME/OpenFOAM/c3d-better-v2-metal-only"
    else
        variant="--v2-mold-only"
        CASE="$HOME/OpenFOAM/c3d-better-v2-mold-only"
    fi
    echo "===== $trial only ====="
    if [[ -e "$CASE" || -L "$CASE" ]]; then
        echo "Existing case preserved; refusing automatic repeat: $CASE"
    else
        echo "Launching isolated native trial: $variant"
        if bash "$ROOT/Allmesh" "$variant"; then
            echo "ALLMESH_RETURN=0"
        else
            code=$?
            echo "ALLMESH_RETURN=$code (inspect native logs; rejection is evidence)"
        fi
    fi
    echo "Case: $CASE"
    if [[ -s "$CASE/NATIVE_BUILD_STATUS.txt" ]]; then
        cat "$CASE/NATIVE_BUILD_STATUS.txt"
    fi
    if [[ -s "$CASE/STL_V2_SOURCE_MAP.txt" ]]; then
        cat "$CASE/STL_V2_SOURCE_MAP.txt"
    fi
    if [[ -s "$CASE/log.splitMeshRegions" ]]; then
        echo "Native regions after splitMeshRegions:"
        # Show the native table, without inventing missing data.
        grep -A 5 -m1 -E 'Region[[:space:]]+nCells[[:space:]]+cellZone' "$CASE/log.splitMeshRegions" || true
        echo "Native inter-region interfaces:"
        grep -A 5 -m1 -E 'Interface[[:space:]]+Owner Region[[:space:]]+Neighbour Region' "$CASE/log.splitMeshRegions" || true
        echo "Summary:"
        awk '
            $1=="metal" && $3=="metal" { metal=$2 }
            $1=="mold" && $3=="mold" { mold=$2 }
            $1=="exterior" && $3=="<none>" { exterior=$2 }
            END {
                printf "metal_cells=%s mold_cells=%s exterior_cells=%s\n", metal?metal:"UNKNOWN", mold?mold:"UNKNOWN", exterior?exterior:"UNKNOWN"
            }
        ' "$CASE/log.splitMeshRegions"
        if grep -q 'metal_to_mold' "$CASE/log.splitMeshRegions"; then
            echo "Metal-mold interface string FOUND in native split log."
        else
            echo "Metal-mold interface MISSING from native split log."
        fi
    else
        echo "No completed splitMeshRegions log; inspect pre-split failure."
        if [[ -s "$CASE/log.snappyHexMesh" ]]; then
            tail -n 22 "$CASE/log.snappyHexMesh"
        fi
    fi
    echo
done
echo "Baseline (already measured): metal 85350 / mold 274788, reciprocal mappedWall 27501 faces."
echo "SolidWorks v2 pair (already measured): metal 4 / mold 4 / exterior 589813, NO metal-to-mold."
echo "Interpretation must depend on BOTH fresh trials; do not infer final mesh acceptance."
echo "Report: $REPORT"
echo "No CFD. All STL files and mesh evidence preserved."
