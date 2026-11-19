#!/usr/bin/env python3
"""Independent proof of exact scope of a C3D-04 V3 candidate (read-only).

The original V2 and V3 polyMesh model must differ ONLY at four inner-grid
corner vertices in section Y=-39.8 mm and 108 sand radial grading lines.
Does not change geometry, run OpenFOAM or approve mesh quality.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

CORNER_IDS = {89, 90, 93, 94}
VERTEX = re.compile(
    r"^(\s*)\(([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\)(\s*//\s*(\d+)\s*)$"
)
RING = re.compile(
    r"^(.*\s+mold\s+\([\d\s]+\)\s+simpleGrading\s+)"
    r"\(([\d.]+) 1 1\)(\s*//\s*slab=(\d+) ring (\d+)\s*)$"
)


def verify(original: Path, trial: Path, delta: float, grading: float) -> None:
    a = original.read_text(encoding="utf-8").splitlines()
    b = trial.read_text(encoding="utf-8").splitlines()
    if len(a) != len(b):
        raise ValueError("File line count changed unexpectedly")
    touched_corners = set()
    touched_rings = set()
    for line_num, (old, new) in enumerate(zip(a, b), 1):
        if old == new:
            continue
        av = VERTEX.fullmatch(old)
        bv = VERTEX.fullmatch(new)
        if av and bv:
            ident = int(av.group(6))
            if (ident not in CORNER_IDS or ident != int(bv.group(6))
                    or ident in touched_corners):
                raise ValueError(f"Unauthorized modified vertex at line {line_num}")
            if float(av.group(3)) != -39.8 or float(bv.group(3)) != -39.8:
                raise ValueError(f"Modified section Y at line {line_num}")
            if av.group(1) != bv.group(1) or av.group(5) != bv.group(5):
                raise ValueError(f"Changed vertex formatting or metadata at line {line_num}")
            for x in (2, 4):
                original_value = float(av.group(x))
                expected = original_value + (delta if original_value < 25.9 else -delta)
                if not math.isclose(float(bv.group(x)), expected, abs_tol=6e-7):
                    raise ValueError(f"Unexpected vertex move at line {line_num}")
            touched_corners.add(ident)
            continue
        ar = RING.fullmatch(old)
        br = RING.fullmatch(new)
        if ar and br:
            key = (int(ar.group(4)), int(ar.group(5)))
            if key in touched_rings or key != (int(br.group(4)), int(br.group(5))):
                raise ValueError(f"Sand ring mismatch at line {line_num}")
            if ar.group(1) != br.group(1) or ar.group(3) != br.group(3):
                raise ValueError(f"Unexpected ring metadata change at line {line_num}")
            if float(ar.group(2)) != 1.5 or not math.isclose(
                float(br.group(2)), grading, abs_tol=5e-4
            ):
                raise ValueError(f"Unauthorized grading at line {line_num}")
            touched_rings.add(key)
            continue
        raise ValueError(f"Unauthorized edit at line {line_num}")

    if delta != 0 and touched_corners != CORNER_IDS:
        raise ValueError(f"Expected 4 interior vertex moves: {sorted(touched_corners)}")
    if delta == 0 and touched_corners:
        raise ValueError("Zero delta should make no corner changes")
    expected_rings = {(slab, ring) for slab in range(9) for ring in range(12)}
    if touched_rings != expected_rings:
        raise ValueError(f"Expected 108 radial ring edits; got {len(touched_rings)}")
    print(
        f"V3_STATIC_DIFF_OK: {len(touched_corners)} interior corner vertices; "
        f"{len(touched_rings)} radial sand blocks; all other geometry unchanged"
    )
    print(f"PARAMETERS: internalCornerDelta={delta} mm, sandRadialGrading={grading}")
    print("STATIC_ONLY: no native OpenFOAM or CFD executed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("trial", type=Path)
    parser.add_argument("--delta", type=float, required=True)
    parser.add_argument("--grading", type=float, required=True)
    args = parser.parse_args()
    try:
        verify(args.original, args.trial, args.delta, args.grading)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"REJECTED: {exc}")


if __name__ == "__main__":
    main()
