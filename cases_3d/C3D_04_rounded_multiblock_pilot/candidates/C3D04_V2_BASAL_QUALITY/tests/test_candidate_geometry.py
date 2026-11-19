#!/usr/bin/env python3
"""Verify C3D-04 V2 changes ONLY intended internal grid and radial grading.

Native blockMesh and checkMesh are still mandatory. This runs read-only.
"""
from __future__ import annotations
import math
import re
import sys
from pathlib import Path

INDEX_Y = {
    89: -39.8, 90: -39.8, 93: -39.8, 94: -39.8,
    117: -39.5, 118: -39.5, 121: -39.5, 122: -39.5,
    145: -39.0, 146: -39.0, 149: -39.0, 150: -39.0,
}
VERTEX_RE = re.compile(
    r"^\s*\(\s*([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\s*\)\s*//\s*(\d+)\s*$"
)
RING_RE = re.compile(
    r"^\s*hex\s+\([\d\s]+\)\s+mold\s+\([\d\s]+\)\s+"
    r"simpleGrading\s+\(([\d.]+) 1 1\)\s+// slab=(\d+) ring (\d+)\s*$"
)


def verify(original: Path, candidate: Path) -> None:
    old_lines = original.read_text(encoding="utf-8").splitlines()
    new_lines = candidate.read_text(encoding="utf-8").splitlines()
    if len(old_lines) != len(new_lines):
        raise ValueError("Candidate changed number of dictionary lines")
    changed = set()
    altered_ring = set()
    original_rings = set()
    for line_number, (old, new) in enumerate(zip(old_lines, new_lines), start=1):
        old_ring = RING_RE.fullmatch(old)
        if old_ring:
            if float(old_ring.group(1)) != 1.0:
                raise ValueError("Source mold ring radial grading not 1.0")
            original_rings.add((int(old_ring.group(2)), int(old_ring.group(3))))
        if old == new:
            if old_ring:
                raise ValueError(f"Missing expected mold ring grading change: {line_number}")
            continue
        a = VERTEX_RE.fullmatch(old)
        b = VERTEX_RE.fullmatch(new)
        if a and b:
            i = int(a.group(4))
            if i != int(b.group(4)) or i not in INDEX_Y or i in changed:
                raise ValueError(f"Unexpected modified vertex: {line_number}")
            y = INDEX_Y[i]
            if abs(float(a.group(2)) - y) > 1e-8 or float(b.group(2)) != float(a.group(2)):
                raise ValueError(f"Altered Y station: {i}")
            t = (y + 40.0) / 1.5
            smooth = t * t * (3.0 - 2.0 * t)
            left = 13.76 + (11.8 - 13.76) * smooth
            right = 51.8 - left
            for k in (1, 3):
                expected = left if float(a.group(k)) < 25.9 else right
                if not math.isclose(float(b.group(k)), expected, abs_tol=6e-7):
                    raise ValueError(f"Unexpected smoothed vertex {i} axis {k}")
            changed.add(i)
            continue
        new_ring = RING_RE.fullmatch(new)
        if old_ring and new_ring:
            old_key = (int(old_ring.group(2)), int(old_ring.group(3)))
            new_key = (int(new_ring.group(2)), int(new_ring.group(3)))
            if old_key != new_key or float(new_ring.group(1)) != 1.5:
                raise ValueError(f"Unexpected mold grading change on line {line_number}")
            altered_ring.add(old_key)
            continue
        raise ValueError(f"Unauthorized dictionary edit at line {line_number}")

    if changed != set(INDEX_Y):
        raise ValueError(f"Expected 12 adjusted vertices, got {sorted(changed)}")
    if len(original_rings) != 108 or altered_ring != original_rings:
        raise ValueError(
            f"Expected grading in all 108 ring blocks; got {len(altered_ring)}"
        )
    print("C3D04_V2_STATIC_DIFF_OK: 12 interior metal-grid vertices smoothed")
    print("C3D04_V2_STATIC_DIFF_OK: 108 mold ring blocks radial grading 1.0 -> 1.5")
    print("C3D04_V2_STATIC_DIFF_OK: no other changed blockMeshDict lines")
    print("STATIC_ONLY: neither checkMesh nor CFD was executed")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: test_candidate_geometry.py originalDict candidateDict")
    try:
        verify(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"REJECTED: {error}")
