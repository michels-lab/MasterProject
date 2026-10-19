#!/usr/bin/env python3
"""C3D-01: verify and stage original aligned SolidWorks STL in native mm.

OpenFOAM Foundation v14 reads these surfaces using geometry.units [mm].
The exact STL binary content and original CAD coordinates remain unchanged.
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


def validate_binary_stl(source: bytes) -> int:
    """Validate the binary STL layout without modifying a single byte."""
    if len(source) < 84:
        raise ValueError("STL truncated: missing 84-byte binary header")
    count, = struct.unpack_from("<I", source, 80)
    if count == 0 or len(source) != 84 + count*50:
        raise ValueError("Expected binary STL 84 + 50*N bytes")
    return count


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
    dst = case/"constant"/"geometry"
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
            triangles = validate_binary_stl(raw)
            (temporary/(name+".stl")).write_bytes(raw)  # source bytes, never transformed
            print(f"{name}: {triangles} triangles; native units [mm]; SHA-256 {actual}")

        # Validate BOTH converted surfaces and interior seeds before publishing either.
        cmd = [sys.executable, str(root/"analysis_tools"/"preflight_c3d_stl.py"),
               "--stl-dir",str(temporary), "--stl-units","mm",
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
    print("Geometry copied UNCHANGED in millimetres. OpenFOAM14 uses geometry.units [mm]. No solver run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
