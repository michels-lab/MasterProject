#!/usr/bin/env bash
# Pure Bash/awk regression using actual OpenFOAM 14 log formatting.
# Does not run OpenFOAM or alter a 3D case.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/native_checkmesh_report.sh"
dir="$(mktemp -d)"
trap 'rm -rf "$dir"' EXIT
mkdir -p "$dir/base" "$dir/candidate"

cat > "$dir/base/log.checkMesh.metal" <<'LOG'
    cells:            85350
    Number of regions: 1 (OK).
    Min volume = 3.62642e-11. Max volume = 8.33744e-09.  Total volume = 4.79793e-05.  Cell volumes OK.
 ***Cells with small determinant (< 0.001) found, number of cells: 3
 ***Concave cells (using face planes) found, number of cells: 4834
Failed 2 mesh checks.
End
LOG

cat > "$dir/base/log.checkMesh.mold" <<'LOG'
    cells:            274788
    Number of regions: 1 (OK).
    Min volume = 3.01694e-11. Max volume = 9.9632e-09.  Total volume = 0.000103389.  Cell volumes OK.
 ***Error in face tets: 1 faces with low quality or negative volume decomposition tets.
 ***Cells with small determinant (< 0.001) found, number of cells: 1
 ***Concave cells (using face planes) found, number of cells: 14951
Failed 3 mesh checks.
End
LOG

sed -e 's/3.62642e-11/3.54062e-11/' -e 's/4834/5004/' \
    "$dir/base/log.checkMesh.metal" > "$dir/candidate/log.checkMesh.metal"
sed -e 's/3.01694e-11/2.8263e-11/' -e 's/14951/15079/' \
    "$dir/base/log.checkMesh.mold" > "$dir/candidate/log.checkMesh.mold"

[[ "$(foam_checkmesh_total_volume "$dir/base/log.checkMesh.metal")" == "4.79793e-05" ]]
[[ "$(foam_checkmesh_total_volume "$dir/base/log.checkMesh.mold")" == "0.000103389" ]]
foam_write_mesh_comparison "$dir/base" "$dir/candidate" "$dir/corrected.tsv"
grep -Fq $'BASELINE\tmetal\t85350\t4.79793e-05\t4834\t3\t0\t2\t0' "$dir/corrected.tsv"
grep -Fq $'CANDIDATE\tmetal\t85350\t4.79793e-05\t5004\t3\t0\t2\t0' "$dir/corrected.tsv"
grep -Fq $'BASELINE\tmold\t274788\t0.000103389\t14951\t1\t1\t3\t0' "$dir/corrected.tsv"
grep -Fq $'CANDIDATE\tmold\t274788\t0.000103389\t15079\t1\t1\t3\t0' "$dir/corrected.tsv"
if grep -Fq $'3.62642e-11' "$dir/corrected.tsv"; then
    echo "ERROR: cell minimum volume substituted for material total volume" >&2
    exit 1
fi
bash -n "$ROOT/Allmesh"
echo "OK: checkMesh Total volume is parsed and all four comparison rows match the supplied logs."
