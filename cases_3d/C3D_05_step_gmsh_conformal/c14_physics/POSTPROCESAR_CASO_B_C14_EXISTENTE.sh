#!/usr/bin/env bash
# ORIGINAL FINISHED C14-B 10s -> offline C14 postprocessing + ParaView.
# No CFD, no mesh, no unit-test suite. Everything written to a separate copy.
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
if [[ "$(printenv WM_PROJECT_VERSION || true)" != "14" ]]; then
    if [[ ! -f /opt/openfoam14/etc/bashrc ]]; then
        echo "Se necesita OpenFOAM Foundation14: /opt/openfoam14/etc/bashrc" >&2
        exit 2
    fi
    set +u
    source /opt/openfoam14/etc/bashrc
    set -u
fi
[[ "$(printenv WM_PROJECT_VERSION || true)" == "14" ]] || {
    echo "La versión activa no es OpenFOAM Foundation14" >&2
    exit 2
}
exec python3 -B "$HERE/POSTPROCESAR_CASO_B_C14_EXISTENTE.py" "$@"
