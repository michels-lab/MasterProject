#!/usr/bin/env python3
"""Independent exact-diff gate: V4 must only move allowed metal nodes/arcs."""
from __future__ import annotations
import argparse
import math
import re
from pathlib import Path

V = re.compile(r"^\s*\(([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\)\s*//\s*(\d+)\s*$")
A = re.compile(r"^\s*arc\s+(\d+)\s+(\d+)\s+\(([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\)\s*//\s*a Y=([-\d.]+)\s*$")
INNER = {89, 90, 93, 94}
OUTER = set(range(84, 100)) - INNER

def assert_close(a: float, b: float, label: str):
    if not math.isclose(a, b, rel_tol=0, abs_tol=6e-7):
        raise ValueError(f"{label}: {a} vs expected {b}")

def verify(source: Path, trial: Path, mode: str, value: float):
    original = source.read_text(encoding="utf-8").splitlines()
    modified = trial.read_text(encoding="utf-8").splitlines()
    if len(original) != len(modified):
        raise ValueError("Changed total line count")
    base_vertex = {}
    base_arcs = {-40.: [], -39.8: []}
    for line in original:
        m = V.fullmatch(line)
        if m:
            base_vertex[int(m.group(4))] = tuple(map(float, m.groups()[:3]))
        arc = A.fullmatch(line)
        if arc and float(arc.group(6)) in base_arcs:
            base_arcs[float(arc.group(6))].append(tuple(map(float, arc.group(3, 4, 5))))
    if len(base_vertex) != 280 or len(base_arcs[-40.]) != 8 or len(base_arcs[-39.8]) != 8:
        raise ValueError("Invalid native V3 baseline")
    edited_nodes = set()
    edited_arcs = 0
    for lineno, (old, new) in enumerate(zip(original, modified), 1):
        if old == new:
            continue
        o, n = V.fullmatch(old), V.fullmatch(new)
        if o and n:
            idx = int(o.group(4))
            if idx != int(n.group(4)):
                raise ValueError(f"Relabeled vertex on line {lineno}")
            oldp = tuple(map(float, o.groups()[:3]))
            newp = tuple(map(float, n.groups()[:3]))
            if mode == "inner_y" and idx in INNER:
                assert_close(newp[0], oldp[0], f"inner X {idx}")
                assert_close(newp[1], -39.8 + value, f"inner Y {idx}")
                assert_close(newp[2], oldp[2], f"inner Z {idx}")
            elif mode == "profile" and idx in OUTER:
                prev = base_vertex[idx - 28]
                assert_close(newp[0], prev[0] + value * (oldp[0] - prev[0]), f"profile X {idx}")
                assert_close(newp[1], oldp[1], f"profile Y {idx}")
                assert_close(newp[2], prev[2] + value * (oldp[2] - prev[2]), f"profile Z {idx}")
            else:
                raise ValueError(f"Unauthorized vertex move: {idx}")
            edited_nodes.add(idx)
            continue
        a, b = A.fullmatch(old), A.fullmatch(new)
        if a and b and mode == "profile" and a.group(1, 2, 6) == b.group(1, 2, 6) and float(a.group(6)) == -39.8:
            idx = len([x for x in original[:lineno] if A.fullmatch(x) and float(A.fullmatch(x).group(6)) == -39.8]) - 1
            if not 0 <= idx < 8:
                raise ValueError(f"Unexpected metal arc index at line {lineno}")
            prev = base_arcs[-40.][idx]
            assert_close(float(b.group(3)), prev[0] + value * (float(a.group(3)) - prev[0]), f"arc X {idx}")
            assert_close(float(b.group(4)), float(a.group(4)), f"arc Y {idx}")
            assert_close(float(b.group(5)), prev[2] + value * (float(a.group(5)) - prev[2]), f"arc Z {idx}")
            edited_arcs += 1
            continue
        raise ValueError(f"Unauthorized changed line {lineno}")
    wanted = INNER if mode == "inner_y" else OUTER
    if edited_nodes != wanted or edited_arcs != (0 if mode == "inner_y" else 8):
        raise ValueError(f"Wrong change contract: {sorted(edited_nodes)}, {edited_arcs} arcs")
    print(f"V4_STATIC_DIFF_OK: {mode} value={value}; {len(edited_nodes)} nodes, {edited_arcs} arcs")
    print("Block connectivity / material zoning / outer mold geometry untouched")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("trial", type=Path)
    p.add_argument("--mode", required=True, choices=["inner_y", "profile"])
    p.add_argument("--value", type=float, required=True)
    args = p.parse_args()
    try:
        verify(args.source, args.trial, args.mode, args.value)
    except (ValueError, OSError) as exc:
        raise SystemExit(f"REJECTED V4 STATIC DIFF: {exc}")
