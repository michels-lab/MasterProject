#!/usr/bin/env python3
"""Locate saved native FS-C07 alpha.solid > alpha.metal violations in the
34,368 cell split-fluid mesh. Forensic, read-only, NO CFD, NO clipping.

Tests the *hypothesis* that over-allocation is restricted to VOF interface
cells. Reports each alpha.metal magnitude band separately and true native
fluid cell indices and mesh 8-vertex coordinate averages; never infers
that interface confinement is proven until those counts are actually read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import (
    FLUID_CELLS, METRE_COORD_SCALE, read_mesh, cell_volume_m3,
)
from stage_fs_c06_vof_solidification import (
    MODEL_FIELD, read_native_solid_fraction, read_native_metal_temperature,
)
from inspect_existing_fs_c07 import inspect, native_time_dirs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metal_bin(a: float) -> str:
    if a < 0:
        return "alpha_metal_negative"
    if a == 0:
        return "alpha_metal_exactly_zero"
    if a < 1e-6:
        return "alpha_metal_0_to_1e-6"
    if a < 1e-3:
        return "alpha_metal_1e-6_to_1e-3"
    if a < 0.5:
        return "alpha_metal_1e-3_to_0p5"
    if a <= 1:
        return "alpha_metal_ge_0p5"
    return "alpha_metal_above_one"


BINS = tuple(metal_bin(a) for a in (
    -1, 0, 1e-10, 1e-5, 0.1, 0.5, 1.1,
))


def cell_vertex_average_m(mesh: dict, cell: int) -> tuple[float, float, float]:
    vertices = mesh["cell_nodes"][cell]
    if len(vertices) != 8:
        raise ValueError("Expected real 8-node native hexahedral cell")
    return tuple(
        sum(mesh["points"][i][d] / METRE_COORD_SCALE for i in vertices) / 8
        for d in range(3)
    )


def locate(
    volumes: list[float], metal: list[float], solid: list[float],
    T: list[float], mesh: dict, tol: float = 1e-8,
) -> dict:
    if not (len(volumes) == len(metal) == len(solid) == len(T)
            == len(mesh["cell_nodes"]) > 0):
        raise ValueError("Native arrays must have matching cell counts")
    if not math.isfinite(tol) or tol <= 0:
        raise ValueError("Invalid absolute allocation threshold")
    if (any(not math.isfinite(v) or v <= 0 for v in volumes)
        or any(not math.isfinite(v) for v in metal + solid + T)):
        raise ValueError("Invalid mesh volume or nonfinite native fields")
    groups = {name: {"count_gt_tolerance": 0,
                     "count_positive_any": 0,
                     "excess_integral_m3": 0.,
                     "max_local_excess": 0.,
                     "worst_cell": None}
              for name in BINS}
    bad_cells = []
    all_positive_volume = 0.
    for i, (v, a, s, temp) in enumerate(zip(volumes, metal, solid, T)):
        delta = s - a
        if delta <= 0:
            continue
        b = groups[metal_bin(a)]
        b["count_positive_any"] += 1
        excess = v*delta
        all_positive_volume += excess
        b["excess_integral_m3"] += excess
        if delta > b["max_local_excess"]:
            b["max_local_excess"] = delta
            b["worst_cell"] = i
        if delta > tol:
            b["count_gt_tolerance"] += 1
            bad_cells.append({
                "native_fluid_cell": i,
                "alpha_metal": a,
                "alpha_metal_solid": s,
                "excess_fraction": delta,
                "cell_volume_m3": v,
                "excess_integral_m3": excess,
                "T_metal_K": temp,
            })
    for name, g in groups.items():
        g["excess_integral_m3"] = float(g["excess_integral_m3"])
    by_volume = sorted(bad_cells,
                       key=lambda row: row["excess_integral_m3"],
                       reverse=True)
    by_fraction = sorted(bad_cells,
                         key=lambda row: row["excess_fraction"],
                         reverse=True)
    for row in by_fraction[:8] + by_volume[:8]:
        row["8_vertex_average_xyz_m"] = list(cell_vertex_average_m(
            mesh, row["native_fluid_cell"]))
    measured = sum(g["count_gt_tolerance"] for g in groups.values())
    total_excess = sum(g["excess_integral_m3"] for g in groups.values())
    if not math.isclose(total_excess, all_positive_volume,
                        abs_tol=1e-17, rel_tol=1e-12):
        raise ValueError("Violation grouped volume sum inconsistent")
    return {
        "total_native_cells": len(metal),
        "overlap_constraint": "alpha.metal.solid > alpha.metal",
        "absolute_fraction_tolerance": tol,
        "cells_above_tolerance": measured,
        "positive_excess_integral_m3_all_cells": all_positive_volume,
        "positive_excess_integral_mm3_all_cells": all_positive_volume*1e9,
        "bin_by_actual_native_alpha_metal": groups,
        "top_8_by_local_excess": by_fraction[:8],
        "top_8_by_integrated_excess": by_volume[:8],
        "all_significant_solid_excess_outside_metal_core_alpha_ge_0p5": (
            measured > 0
            and groups["alpha_metal_ge_0p5"]["count_gt_tolerance"] == 0
            and groups["alpha_metal_above_one"]["count_gt_tolerance"] == 0
        ),
        "important_limitation": (
            "alpha.metal<0.5 identifies non-core VOF cells, NOT automatically "
            "the geometrically resolved free-surface location. Inspect "
            "native mesh coordinates before drawing spatial conclusions."
        ),
        "native_field_edited": False,
        "solver_executed": False,
        "physical_shrinkage_validated": False,
    }


def evaluate(case: Path, selected_times: tuple[float, ...]) -> dict:
    base = inspect(case)
    case = Path(base["case"])
    if base["solver_end_marker_in_recent_log_tail"] is not True:
        raise ValueError("Native solver not proven ended; diagnose source first")
    mesh = read_mesh(case / "constant/fluid/polyMesh", FLUID_CELLS)
    volumes = [cell_volume_m3(mesh, i) for i in range(FLUID_CELLS)]
    available = native_time_dirs(case)
    results = []
    for req in selected_times:
        matching = [p for t, p in available if abs(t-req) <= 1e-9]
        if len(matching) != 1:
            raise ValueError(f"Requested true native saved time {req}s absent")
        fluid = matching[0] / "fluid"
        names = ["alpha.metal", MODEL_FIELD, "T.metal"]
        files = [fluid / name for name in names]
        if not all(p.is_file() and not p.is_symlink() for p in files):
            raise ValueError("Required saved native fluid phase fields absent")
        a = read_alpha(files[0], expected_cells=FLUID_CELLS)
        s = read_native_solid_fraction(files[1], expected_cells=FLUID_CELLS)
        T = read_native_metal_temperature(files[2], expected_cells=FLUID_CELLS)
        result = locate(volumes, a, s, T, mesh)
        result["time_s"] = req
        result["native_field_sha256"] = {
            p.name: sha256(p) for p in files
        }
        results.append(result)
    return {
        "schema": "masterproject-fs-c07-nonclipping-phase-location-v1",
        "case": str(case),
        "actual_saved_times_s": list(selected_times),
        "results": results,
        "case_modified": False,
        "solver_rerun": False,
        "next_scientific_gate": (
            "Determine whether native correction order lets transported "
            "VOF alpha.metal become smaller than alpha.metal.solid at the "
            "save instant; then implement physically conservative phase "
            "transport rather than adjusting archived fields."
        ),
    }


def complete_saved_native_times(case: Path) -> tuple[float, ...]:
    """Discover true saved phase states, not function-object-only time folders."""
    case = case.expanduser().resolve()
    times = tuple(
        t for t, p in native_time_dirs(case)
        if t > 0 and all(
            (p / "fluid" / name).is_file()
            and not (p / "fluid" / name).is_symlink()
            for name in ("alpha.metal", MODEL_FIELD, "T.metal")
        )
    )
    if len(times) != 20 or not math.isclose(times[-1], 1.0, abs_tol=1e-9):
        raise ValueError(
            "Expected exactly 20 native saved FS-C07 1s phase snapshots; "
            "preserve case and inspect actual time directories"
        )
    return times


def compact_result(report: dict) -> dict:
    """20 native state summary with zero numerical invention or clipping."""
    results = report["results"]
    if not results:
        raise ValueError("No native phase-location results to summarize")
    def count(r: dict, group: str) -> int:
        return r["bin_by_actual_native_alpha_metal"][group][
            "count_gt_tolerance"
        ]
    core = [count(r, "alpha_metal_ge_0p5") for r in results]
    total_violations = sum(r["cells_above_tolerance"] for r in results)
    rows = []
    for r in results:
        bins = r["bin_by_actual_native_alpha_metal"]
        counted = sum(g["count_gt_tolerance"] for g in bins.values())
        if counted != r["cells_above_tolerance"]:
            raise ValueError(
                "Native alpha.metal bins do not reproduce actual significant "
                "solid>metal cell count at time " + str(r["time_s"])
            )
        rows.append({
            "time_s": r["time_s"],
            "total_native_cells": r["total_native_cells"],
            "cells_with_solid_excess_gt_1e8": r["cells_above_tolerance"],
            "cells_alpha_negative_or_zero_gt_1e8":
                count(r, "alpha_metal_negative")
                + count(r, "alpha_metal_exactly_zero"),
            "cells_alpha_lt_1e6_gt_1e8":
                count(r, "alpha_metal_0_to_1e-6"),
            "cells_alpha_1e6_to_1e3_gt_1e8":
                count(r, "alpha_metal_1e-6_to_1e-3"),
            "cells_alpha_1e3_to_0p5_gt_1e8":
                count(r, "alpha_metal_1e-3_to_0p5"),
            "cells_core_alpha_ge_0p5_gt_1e8":
                count(r, "alpha_metal_ge_0p5"),
            "integrated_unphysical_excess_m3":
                r["positive_excess_integral_m3_all_cells"],
            "max_fraction_excess": (
                r["top_8_by_local_excess"][0]["excess_fraction"]
                if r["top_8_by_local_excess"] else None
            ),
        })
    peak = max(results,
               key=lambda r: r["positive_excess_integral_m3_all_cells"])
    result = dict(report)
    result["results"] = rows
    result["all_20_states_have_zero_core_cell_excess_above_threshold"] = (
        len(results) == 20 and all(v == 0 for v in core)
    )
    result["max_core_cells_exceeding_threshold_any_state"] = max(core)
    result["total_cell_time_incidences_above_threshold"] = total_violations
    result["peak_integrated_excess_time_s"] = peak["time_s"]
    result["peak_integrated_excess_m3"] = (
        peak["positive_excess_integral_m3_all_cells"]
    )
    result["peak_case_top_8_by_fraction"] = peak["top_8_by_local_excess"]
    result["not_a_geometric_interface_classification"] = True
    result["no_global_phase_boundedness_claim"] = True
    result["no_new_native_solver_run"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--times", type=float, nargs="+",
                        default=[0.2, 0.4, 1.0],
                        help="Existing native saved times (default 0.2 0.4 1.0)")
    parser.add_argument("--all-saved", action="store_true",
                        help="Inspect every one of 20 actual 0.05..1.0s snapshots")
    parser.add_argument("--compact", action="store_true",
                        help="Print 20-state summary and worst-case cells")
    args = parser.parse_args()
    if not args.all_saved and any(
        not math.isfinite(x) or x <= 0 for x in args.times
    ):
        parser.error("Requested saved times must be finite positive")
    try:
        times = (complete_saved_native_times(args.case)
                 if args.all_saved else tuple(args.times))
        result = evaluate(args.case, times)
        if args.compact:
            result = compact_result(result)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("FS-C07 NATIVE GEOMETRY FORENSIC BLOCKED:", exc, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
