#!/usr/bin/env bash
# Foundation v14 surfaceCheck must be judged by textual findings, not exit=0.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/native_surfacecheck_gate.sh"
bash -n "$GATE"
bash -n "$ROOT/scripts/check_stl_v2.sh"
bash -n "$ROOT/scripts/audit_stl_surfaces_of14.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/good" <<'EOF'
Statistics:
Surface is closed. All edges connected to two faces.
Number of unconnected parts : 1
Number of zones (connected area with consistent normal) : 1
Checking self-intersection.
Surface is not self-intersecting
End
EOF
bash "$GATE" "$tmp/good" > /dev/null
sed 's/Surface is closed. All edges connected to two faces./Surface is not closed since not all edges connected to two faces:/g' "$tmp/good" > "$tmp/open"
if bash "$GATE" "$tmp/open" >/dev/null 2>&1; then
    echo "GATE BUG: open surface was approved" >&2; exit 1;
fi
sed 's/Surface is not self-intersecting/Surface is self-intersecting at 11 locations./g' "$tmp/good" > "$tmp/intersect"
if bash "$GATE" "$tmp/intersect" >/dev/null 2>&1; then
    echo "GATE BUG: self-intersecting surface was approved" >&2; exit 1;
fi
sed 's/Number of unconnected parts : 1/Number of unconnected parts : 2/g' "$tmp/good" > "$tmp/split"
if bash "$GATE" "$tmp/split" >/dev/null 2>&1; then
    echo "GATE BUG: disconnected STL surface was approved" >&2; exit 1;
fi
sed 's/Number of zones (connected area with consistent normal) : 1/Number of zones (connected area with consistent normal) : 3/g' "$tmp/good" > "$tmp/winding"
if bash "$GATE" "$tmp/winding" >/dev/null 2>&1; then
    echo "GATE BUG: inconsistent orientation was approved" >&2; exit 1;
fi
echo "OK: text gate rejects open, intersecting, disconnected and inconsistent STL (even with exit=0)."
