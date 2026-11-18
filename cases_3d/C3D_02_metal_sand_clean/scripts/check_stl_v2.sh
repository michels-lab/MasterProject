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
[[ "$WM_PROJECT_VERSION" == "14" ]] || { echo "Wrong OpenFOAM: require Foundation 14" >&2; exit 2; }
# surfaceCheck can write diagnostic geometry in CWD; isolate all outputs.
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT

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
    # Foundation 14 surfaceCheck often returns 0 even for open surfaces.
    # Therefore the published *text verdict* must satisfy four gates.
    log="$temporary/$name.surfaceCheck.log"
    if ! (cd "$temporary" && surfaceCheck -checkSelfIntersection "$file") > "$log" 2>&1; then
        echo "REJECT: OpenFOAM surfaceCheck failed for $name" >&2
        tail -n 28 "$log" >&2
        exit 5
    fi
    if ! bash "$ROOT/scripts/native_surfacecheck_gate.sh" "$log"; then
        echo "REJECT: Native surfaceCheck geometry gate failed: $name" >&2
        grep -Ei 'Surface is|Number of unconnected parts|Number of zones|self-intersect|FOAM Warning|FOAM FATAL' "$log" >&2 || true
        echo "Inspect native output with: scripts/audit_stl_surfaces_of14.sh" >&2
        exit 5
    fi
    echo "NATIVE STL VERIFIED: $name (closed, 1 component, consistent orientation, no self-intersection)."
done
echo "STL_V2_INPUTS_VERIFIED / units [mm] / NO_MESH / NO_CFD"
echo "Surface geometry passed strict native text gates; physical mutual contact and 3D mesh quality are NOT proven."
