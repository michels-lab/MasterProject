#!/usr/bin/env bash
# Case B C3D-05: ONE native Foundation14 milestone for EXACT archived C14
# metal fluid + mold solid, with solidificationMeltingSource on accepted HEX8.
# Never deletes/modifies accepted STEP/Gmsh mesh or prior C14 T0 numeric run.
set -Eeuo pipefail

if [[ "${1:-}" != "--preflight" && "${1:-}" != "--materialize" && "${1:-}" != "--run-full" ]] || [[ "$#" -ne 1 ]]; then
    echo "Usage: bash run_case_b_c14_native.sh {--preflight|--materialize|--run-full}" >&2
    exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HWLOC_COMPONENTS=-gl
if [[ ! -f /opt/openfoam14/etc/bashrc ]]; then
    echo "BLOCKED_FOUNDATION14: /opt/openfoam14/etc/bashrc missing; no mesh/model touched" >&2
    exit 4
fi
# OpenFOAM Foundation14's official bashrc probes ZSH_NAME and other optional
# variables without default expansions. Running it under our set -u triggers
# "ZSH_NAME: unbound variable" before ANY native case or CFD exists.
# Temporarily disable nounset ONLY while sourcing this trusted system script.
# Restore strict guards for the rest of this runner.
set +u
# shellcheck disable=SC1091
source /opt/openfoam14/etc/bashrc
set -u
if [[ "${WM_PROJECT_VERSION:-}" != "14" ]]; then
    echo "BLOCKED_FOUNDATION14: sourced environment is not Foundation14" >&2
    exit 4
fi
exec python3 -B "$HERE/stage_c14_3d_case_b.py" "$1"
