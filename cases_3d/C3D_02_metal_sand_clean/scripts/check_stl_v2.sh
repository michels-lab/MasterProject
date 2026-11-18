#!/usr/bin/env bash
# Validate the two final SolidWorks binary STL files before 3D OpenFOAM meshing.
# Works on repository copies, never modifies either STL, previous mesh or physics.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GEO="$ROOT/constant/geometry"
[[ -r /opt/openfoam14/etc/bashrc ]] || {
    echo "ERROR: OpenFOAM Foundation 14 is not available" >&2; exit 2;
}
set +u
source /opt/openfoam14/etc/bashrc
set -u
command -v surfaceCheck >/dev/null || { echo "Missing surfaceCheck" >&2; exit 2; }

for row in \
  "metal_v2.stl f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf" \
  "mold_v2.stl ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32"; do
    read -r name expected <<< "$row"
    file="$GEO/$name"
    [[ -s "$file" ]] || {
        echo "MISSING: $file" >&2
        echo "Upload the verified SolidWorks v2 STL before using the mesh candidate." >&2
        exit 3
    }
    actual="$(sha256sum "$file" | cut -d' ' -f1)"
    [[ "$actual" == "$expected" ]] || {
        echo "ERROR: SHA-256 mismatch for $name. No candidate mesh permitted." >&2
        exit 4
    }
    echo "SHA-256 VERIFIED: $name"
    # Surface checking uses OpenFOAM and only reads STL files.
    if ! surfaceCheck -checkSelfIntersection "$file" > /dev/null; then
        echo "ERROR: OpenFOAM surfaceCheck failed on $name" >&2
        exit 5
    fi
    echo "surfaceCheck completed: $name (inspect full output if investigating quality)."
done
echo "STL_V2_INPUTS_VERIFIED / units [mm] / NO_MESH / NO_CFD"
echo "Closed geometry and physical contact must still be inspected via OpenFOAM logs."
