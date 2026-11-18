#!/usr/bin/env bash
# Pure log-gate for OpenFOAM Foundation 14 surfaceCheck output.
# surfaceCheck returns 0 even if it reports an OPEN or SELF-INTERSECTING surface!
set -euo pipefail
[[ $# -eq 1 && -s "$1" ]] || {
    echo "Usage: native_surfacecheck_gate.sh /absolute/path/log.surfaceCheck" >&2
    exit 2
}
log="$1"
grep -Fq 'Surface is closed. All edges connected to two faces.' "$log" || {
    echo "REJECT: surface is not closed or closure not proven" >&2; exit 5;
}
grep -Eq 'Number of unconnected parts[[:space:]]*:[[:space:]]*1([[:space:]]|$)' "$log" || {
    echo "REJECT: not exactly one connected surface" >&2; exit 5;
}
grep -Eq 'Number of zones \(connected area with consistent normal\)[[:space:]]*:[[:space:]]*1([[:space:]]|$)' "$log" || {
    echo "REJECT: face orientation not consistently connected" >&2; exit 5;
}
grep -Fq 'Surface is not self-intersecting' "$log" || {
    echo "REJECT: self-intersection not excluded by OpenFOAM" >&2; exit 5;
}
if grep -Eq 'Surface is self-intersecting at|Surface is not closed|More than one normal orientation|FOAM FATAL' "$log"; then
    echo "REJECT: diagnostic contains a surface defect" >&2
    exit 5
fi
echo 'SURFACE PASSED: closed / one component / consistent normals / no self intersections'
