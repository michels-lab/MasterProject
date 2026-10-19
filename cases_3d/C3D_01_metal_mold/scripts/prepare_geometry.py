#!/usr/bin/env python3
"""C3D-01: convert ORIGINAL aligned SolidWorks binary STL coordinates from mm to m.

Converts triangle vertices only: normals, triangulation, winding, shared origin,
and face attributes stay unchanged. Source files are never modified.
Requires the exact two validated STL exports recorded in geometry_reference.json.
Does not execute OpenFOAM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


def convert_binary_stl_mm_to_m(source: bytes) -> bytes:
    if len(source) < 84:
        raise ValueError("STL truncated: missing 84-byte binary header")
    count, = struct.unpack_from("<I", source, 80)
    if count == 0 or len(source) != 84 + count * 50:
        raise ValueError("Expected closed binary STL byte layout (84 + 50*N)")
    output = bytearray(source)
    for i in range(count):
        record = 84 + 50*i
        for axis in range(9):  # nine vertex floats, NOT three normal floats
            address = record + 12 + axis*4
            x, = struct.unpack_from("<f", source, address)
            if not (-1e10 < x < 1e10):
                raise ValueError(f"Non-finite/unreasonable coordinate: triangle {i}")
            struct.pack_into("<f", output, address, x*0.001)
    return bytes(output)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mold", type=Path, required=True, help="QuickCup.STL (mm; aligned export)")
    parser.add_argument("--metal", type=Path, required=True, help="metal.STL (mm; aligned export)")
    args = parser.parse_args()
    case = Path(__file__).resolve().parents[1]
    root = case.parents[1]
    meta = json.loads((case/"geometry_reference.json").read_text(encoding="utf-8"))
    dst = case/"constant"/"triSurface"
    targets = {"mold":dst/"mold.stl", "metal":dst/"metal.stl"}
    if any(p.exists() for p in targets.values()):
        raise SystemExit("ERROR: target STL already exists; refusing to overwrite it.")

    with tempfile.TemporaryDirectory(prefix="c3d01-stl-") as temp:
        temporary = Path(temp)
        for name, src in (("mold",args.mold),("metal",args.metal)):
            raw = src.read_bytes()
            actual = sha(raw)
            expected = meta[name]["original_sha256"]
            if actual != expected:
                raise ValueError(
                    f"{name}: original SolidWorks STL SHA-256 does not match this "
                    f"validated C3D-01 export. Found {actual}; expected {expected}. "
                    "Check that you chose the corrected coordinate-preserving export."
                )
            converted = convert_binary_stl_mm_to_m(raw)
            (temporary/(name+".stl")).write_bytes(converted)
            print(f"{name}: {len(converted)} bytes, SHA-256 after scaling {sha(converted)}")

        # Validate BOTH converted surfaces and interior seeds before publishing either.
        cmd = [sys.executable, str(root/"analysis_tools"/"preflight_c3d_stl.py"),
               "--stl-dir",str(temporary),
               "--manifest",str(case/"geometry_reference.json"),
               "--json",str(temporary/"preflight.json")]
        result = subprocess.run(cmd,check=False)
        if result.returncode:
            raise RuntimeError("STL geometry preflight failed. No output files published.")
        dst.mkdir(parents=True,exist_ok=True)
        # Atomic replacement within the same filesystem, only after full validation.
        for name,target in targets.items():
            source = temporary/(name+".stl")
            target.write_bytes(source.read_bytes())
        (case/"geometry_preflight_runtime.json").write_text(
            (temporary/"preflight.json").read_text(encoding="utf-8"),encoding="utf-8")
    print("Geometry prepared in METRES. CAD originals unchanged. NO OpenFOAM solver run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
