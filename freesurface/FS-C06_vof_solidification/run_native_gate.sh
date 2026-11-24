#!/usr/bin/env bash
# FS-C06: isolated OpenFOAM Foundation 14 native smoke + mesh geometry/topology gate.
# Does NOT establish physical shrinkage, feeding or experimental validation.
# Usage: bash freesurface/FS-C06_vof_solidification/run_native_gate.sh /absolute/FS-C05-case
set -Eeuo pipefail

die() { printf 'FS-C06 BLOCKED: %s\n' "$*" >&2; exit 2; }
[[ $# -eq 1 ]] || die "Provide one accepted FS-C05 source case"
[[ -d "$1" ]] || die "FS-C05 source directory not found: $1"
[[ "${WM_PROJECT_VERSION:-}" == "14" ]] || die "Source OpenFOAM Foundation 14 before running"
for binary in foamMultiRun foamDictionary checkMesh python3; do
    command -v "$binary" >/dev/null 2>&1 || die "Missing prerequisite: $binary"
done
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
source_case="$(cd "$1" && pwd -P)"
[[ "$source_case" != "$repo" && "$source_case" != "$repo/"* ]] || die "Use an independent FS-C05 delivered case"
[[ -f "$source_case/constant/fluid/fvModels" ]] || die "Source missing fluid fvModels"
[[ -f "$source_case/system/controlDict" ]] || die "Source missing controlDict"

# The existing stager verifies source provenance and C14 reference, writes into
# a NEW delivery and runs actual Foundation14 foamMultiRun (two 1e-7 s steps).
# Never write into the source or mistake these two steps for solidification.
set +e
output="$(cd "$repo" && python3 analysis_tools/stage_fs_c06_vof_solidification.py --source "$source_case" --native 2>&1)"
rc=$?
set -e
printf '%s\n' "$output"
[[ "$rc" -eq 0 ]] || die "Native run failed; preserve the printed isolated evidence path"
case_dir="$(printf '%s\n' "$output" | sed -n 's/^ISOLATED CASE: //p' | tail -n 1)"
[[ -n "$case_dir" && -d "$case_dir" && "$case_dir" != "$source_case" ]] || die "No isolated delivery"
[[ -f "$case_dir/FS_C06_REPORT.json" ]] || die "Native report missing"
[[ -f "$case_dir/log.FS_C06_foamMultiRun" ]] || die "Native solver log missing"
cmp -s "$repo/freesurface/FS-C06_vof_solidification/native/system/controlDict" "$case_dir/system/controlDict" || die "Native controlDict changed during stage/run"
cmp -s "$repo/freesurface/FS-C06_vof_solidification/native/system/functions" "$case_dir/system/functions" || die "Foundation14 native system/functions missing or altered"
cmp -s "$repo/freesurface/FS-C06_vof_solidification/native/constant/fluid/fvModels" "$case_dir/constant/fluid/fvModels" || die "Native fvModels changed during stage/run"

# An ordinary solver PASS without native postProcessing data is NOT acceptance.
# Foundation 14 reads system/functions independently of controlDict.
[[ -d "$case_dir/postProcessing" ]] || die "No postProcessing outputs: functions may not have been loaded"
for name in FS_C06_metalVoFVolume FS_C06_solidMetalVolume FS_C06_mixtureMass \
            FS_C06_atmosphereMassFlux FS_C06_atmosphereTopMassFlux \
            FS_C06_atmosphereSidesMassFlux FS_C06_atmosphereLowerSidesMassFlux \
            FS_C06_fluidToMoldMassFlux FS_C06_wallHeatFluxFluid FS_C06_wallHeatFluxMold; do
    data="$(find "$case_dir/postProcessing" -type f -path "*/$name/*" -name '*.dat' -size +0c -print -quit)"
    [[ -n "$data" ]] || die "Missing native monitor .dat ($name). Solver passed but diagnostic gate FAILS."
done
printf '%s\n' 'FS-C06 FUNCTION OBJECTS: 10/10 native monitor files observed (values not yet validated)'

# The source runner already checks native phase fields; additionally require
# *native* mesh geometry/topology acceptance for BOTH regions.
for region in fluid mold; do
    [[ -d "$case_dir/constant/$region/polyMesh" ]] || die "Missing mesh for $region"
    log="$case_dir/log.FS_C06_checkMesh_$region"
    if ! checkMesh -case "$case_dir" -region "$region" -allGeometry -allTopology > "$log" 2>&1; then
        die "Native checkMesh failed in $region ($log)"
    fi
    grep -q 'Mesh OK' "$log" || die "Native checkMesh did not accept $region ($log)"
done

python3 - "$case_dir/FS_C06_REPORT.json" <<'PY'
import json
import sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text())
required = {
    "status": "FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE",
    "native_cfd_executed": True,
    "model_loaded_native": True,
    "solid_fraction_fields_measured": True,
    "volumetric_shrinkage_implemented": False,
    "feeding_implemented": False,
    "mass_energy_validated": False,
}
for key, expected in required.items():
    if report.get(key) != expected:
        raise SystemExit("FS-C06 BLOCKED: unexpected native report field " + key)
print("FS-C06 NATIVE GATE PASS: Foundation14 model fields and both checkMesh regions")
print("PHYSICAL ACCEPTANCE: OPEN; no shrinkage, feeding or global mass-energy balance")
PY
printf 'ISOLATED NATIVE EVIDENCE: %s\n' "$case_dir"
