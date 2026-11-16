#!/usr/bin/env python3
"""C3D-02: read-only spatial audit of checkMesh's four VTK defect surfaces.

No OpenFOAM/VTK Python package needed. Supports legacy VTK ASCII and binary
POINTS blocks. Counts are VTK *surface vertices*, NOT bad volume cells.
The exact bad-cell counts come from the existing checkMesh logs.
"""
from __future__ import annotations

import argparse
from collections import deque
import math
import re
import struct
import sys
import tempfile
from pathlib import Path
from typing import Iterator

AXIAL_MM = (-65.5, -49.125, -32.75, -16.375, 0.0)
FILES = (
    ("hierro", "concaveCells", "metal"),
    ("arena", "concaveCells", "mold"),
    ("arena", "underdeterminedCells", "mold"),
    ("arena", "twoInternalFacesCells", "mold"),
)


def vtk_points(path: Path) -> Iterator[tuple[float, float, float]]:
    """Iterate geometry POINTS from a legacy .vtk without altering the file."""
    with path.open("rb") as handle:
        first = handle.readline()
        if not first.lstrip().lower().startswith(b"# vtk datafile"):
            raise ValueError("El archivo no tiene encabezado legacy VTK")
        handle.readline()  # title
        mode = handle.readline().strip().upper()
        if mode not in (b"ASCII", b"BINARY"):
            raise ValueError("VTK no declara modo ASCII/BINARY reconocible")
        handle.readline()  # DATASET ...
        while True:
            line = handle.readline()
            if not line:
                raise ValueError("No se encontro bloque POINTS en VTK")
            m = re.match(rb"^\s*POINTS\s+(\d+)\s+(float|double)\s*$", line, re.I)
            if m:
                n = int(m.group(1))
                data_type = m.group(2).lower()
                break
        if not 0 < n <= 20_000_000:
            raise ValueError("Numero de puntos VTK invalido o inusualmente grande")
        if mode == b"BINARY":
            width = 4 if data_type == b"float" else 8
            blob = handle.read(n * 3 * width)
            if len(blob) != n * 3 * width:
                raise ValueError("Archivo VTK binario incompleto")
            unpack = ">fff" if width == 4 else ">ddd"
            for x, y, z in struct.iter_unpack(unpack, blob):
                if not all(math.isfinite(v) for v in (x, y, z)):
                    raise ValueError("VTK contiene coordenadas no finitas")
                yield x, y, z
        else:
            buf: deque[str] = deque()
            seen = 0
            for raw in handle:
                try:
                    buf.extend(raw.decode("ascii").split())
                except UnicodeDecodeError as exc:
                    raise ValueError("Bloque POINTS ASCII ilegible") from exc
                while len(buf) >= 3 and seen < n:
                    x, y, z = (float(buf.popleft()), float(buf.pop(0)), float(buf.pop(0)))
                    if not all(math.isfinite(v) for v in (x, y, z)):
                        raise ValueError("VTK contiene coordenadas no finitas")
                    yield x, y, z
                    seen += 1
                if seen == n:
                    break
            if seen != n:
                raise ValueError("Archivo VTK ASCII incompleto")


def summary(path: Path, keep_points: bool = False) -> dict:
    low = [float("inf")] * 3
    high = [-float("inf")] * 3
    weighted_sum = [0.0] * 3
    counts = [0] * 4
    outside_y = 0
    n = 0
    selected = [] if keep_points else None
    for p in vtk_points(path):
        n += 1
        if selected is not None:
            selected.append(p)
        for k, val in enumerate(p):
            low[k] = min(low[k], val)
            high[k] = max(high[k], val)
            weighted_sum[k] += val
        y_mm = p[1] * 1000
        if AXIAL_MM[0] - 0.001 <= y_mm <= AXIAL_MM[-1] + 0.001:
            index = min(3, max(0, int((y_mm - AXIAL_MM[0]) / 16.375)))
            counts[index] += 1
        else:
            outside_y += 1
    if n == 0:
        raise ValueError("VTK no contiene puntos")
    return {
        "count": n,
        "low": low,
        "high": high,
        "mean": [s / n for s in weighted_sum],
        "bins": counts,
        "outside_y": outside_y,
        "points": selected,
    }


def bbox_gap(a: dict, b: dict) -> float:
    distances = [
        max(0.0, a["low"][i] - b["high"][i], b["low"][i] - a["high"][i])
        for i in range(3)
    ]
    return math.sqrt(sum(x * x for x in distances))


def nearest_gap(a: dict, b: dict) -> float:
    return min(
        math.dist(x, y) for x in a["points"] for y in b["points"]
    )


def self_test() -> None:
    fixture = b"# vtk DataFile Version 3.0\nsynthetic\nASCII\nDATASET POLYDATA\nPOINTS 2 float\n0 -0.0655 0\n0.0518 0 0.0518\nPOLYGONS 0 0\n"
    binary = (
        b"# vtk DataFile Version 3.0\nsynthetic\nBINARY\nDATASET POLYDATA\nPOINTS 2 float\n"
        + struct.pack(">ffffff", 0, -0.0655, 0, 0.0518, 0, 0.0518)
        + b"\nPOLYGONS 0 0\n"
    )
    with tempfile.TemporaryDirectory() as td:
        paths = [Path(td) / "ascii.vtk", Path(td) / "binary.vtk"]
        for path, data in zip(paths, (fixture, binary)):
            path.write_bytes(data)
            result = summary(path, keep_points=True)
            assert result["count"] == 2
            assert math.isclose(result["high"][0], 0.0518, rel_tol=1e-5)
            assert math.isclose(result["low"][1], -0.0655, rel_tol=1e-5)
            assert result["bins"][0] == 1 and result["bins"][3] == 1
            assert bbox_gap(result, result) == 0
            assert nearest_gap(result, result) == 0
    print("OK: parser VTK legacy ASCII y binario, rangos y distancias.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        type=Path,
        default=Path.home() / "OpenFOAM/C3D02_materials/quality_evidence_01",
        help="Carpeta de evidencia previa (solo lectura)",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    base = args.base.expanduser().resolve(strict=True)
    cache: dict[tuple[str, str], dict] = {}
    for mat, label, folder in FILES:
        file = base / folder / "postProcessing/checkMesh/constant" / (label + ".vtk")
        if not file.is_file():
            print("ERROR: falta", file, file=sys.stderr)
            return 2
    print("=== C3D-02: DISTRIBUCION DE VERTICES VTK DE DEFECTOS ===")
    print("Malla fuente de evidencia (no modificada):", base)
    print("Interpretacion: VERTICES de superficies VTK, NO centros de celda ni numero de celdas.")

    for mat, label, folder in FILES:
        file = base / folder / "postProcessing/checkMesh/constant" / (label + ".vtk")
        try:
            record = summary(file, keep_points=(folder == "mold" and label != "concaveCells"))
        except (ValueError, OSError, OverflowError) as exc:
            print("ERROR al leer", file, ":", exc, file=sys.stderr)
            return 3
        cache[folder, label] = record
        low, high, center = (
            [x * 1000 for x in record[key]] for key in ("low", "high", "mean")
        )
        print(f"\n--- {mat}: {label} ---")
        print(f"VTK: {file}")
        print(f"Puntos de superficie VTK: {record['count']:,d}")
        for axis, k in zip("xyz", range(3)):
            print(f"  {axis} en mm: {low[k]:.3f} a {high[k]:.3f}; centroide de vertices {center[k]:.3f}")
        print("Distribucion axial Y de VERTICES (bins fijos del molde, no celdas):")
        for i, n in enumerate(record["bins"]):
            print(
                f"  Y {AXIAL_MM[i]:8.3f} .. {AXIAL_MM[i+1]:7.3f} mm : "
                f"{n:8d} vertices ({100*n/record['count']:5.1f}%)"
            )
        if record["outside_y"]:
            print(f"  Fuera de Y nominal: {record['outside_y']} vertices.")

    a = cache["mold", "underdeterminedCells"]
    b = cache["mold", "twoInternalFacesCells"]
    print("\n=== COMPARACION DE LOS DOS DEFECTOS PUNTUALES EN ARENA ===")
    print(f"Separacion de cajas espaciales: {bbox_gap(a,b)*1000:.5f} mm")
    print(f"Distancia minima entre vertices exportados: {nearest_gap(a,b)*1000:.5f} mm")
    print("Si las regiones se solapan, NO prueba por si solo que sea la misma celda.")
    print("\nPASO SIGUIENTE: revisar en ParaView los VTK junto a la superficie del CAD.")
    print("No se cambiaron mallas ni STLs, ni se ejecutaron utilidades CFD.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
