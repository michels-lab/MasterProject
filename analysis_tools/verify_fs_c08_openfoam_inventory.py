#!/usr/bin/env python3
"""Verify native OpenFOAM14 fsC08NativeInventory log against original FS-C07 data.

This is a READ-ONLY comparison of third-party WSL native utility text against
versioned user-observed 20-snapshot evidence, not a new CFD run. Fails closed:
missing snapshots, duplicate records, wrong saved-cell counts, wrong raw
volume, wrong phase-allocation counts, or missing no-write footer.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "freesurface/FS-C07_thermal_transition/evidence"
    / "FS_C07_PHASE_ALLOCATION_20_NATIVE_STATES_20261123.json"
)
MARKER = "FS_C08_NATIVE_VOLUME_AUDIT "
FOOTER = "FS_C08_NATIVE_BRIDGE_END "
LAST_METAL_M3 = 4.8011038266835194e-5
LAST_SOLID_M3 = 2.403591085462431e-6


def parse_record(line: str) -> dict[str, float]:
    if not line.startswith(MARKER):
        raise ValueError("Not a native volume audit line")
    fields = {}
    for token in line[len(MARKER):].split():
        if "=" not in token:
            raise ValueError("Unparseable native audit token: " + token)
        key, raw = token.split("=", 1)
        if key in fields:
            raise ValueError("Duplicate native audit key: " + key)
        try:
            val = float(raw)
        except ValueError as e:
            raise ValueError("Non-numeric native audit value " + key) from e
        if not math.isfinite(val):
            raise ValueError("Nonfinite native audit value " + key)
        fields[key] = val
    return fields


def verify_native_log(text: str, times: tuple[float, ...]) -> dict:
    if not times or len(times) != len(set(times)) or any(
        not math.isfinite(t) or t <= 0 for t in times
    ):
        raise ValueError("Expected times must be unique positive finite")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    evidence_rows = {round(r["time_s"], 8): r for r in evidence["time_series"]}
    observed = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(MARKER):
            row = parse_record(line)
            for key in (
                "time_s", "cells", "V_metal_raw_m3", "V_solid_raw_m3",
                "V_liquid_difference_raw_m3", "V_solid_excess_m3",
                "max_fraction_excess", "n_significant_excess_gt_1e8",
                "n_core_excess_gt_1e8",
            ):
                if key not in row:
                    raise ValueError("Missing native OpenFOAM metric " + key)
            t = round(row["time_s"], 8)
            if t in observed:
                raise ValueError("Duplicate native timestep audit " + str(t))
            observed[t] = row
    wanted = {round(t, 8) for t in times}
    if set(observed) != wanted:
        raise ValueError(
            "Native audit time coverage differs from requested saved times: "
            f"wanted {sorted(wanted)} got {sorted(observed)}"
        )
    for t in wanted:
        row = observed[t]
        if t not in evidence_rows:
            raise ValueError("No user-observed real FS-C07 evidence for t="+str(t))
        base = evidence_rows[t]
        if row["cells"] != evidence["native_cells_per_time"]:
            raise ValueError(f"Native cell count mismatch at {t}")
        if row["n_significant_excess_gt_1e8"] != base["n_gt_1e8"]:
            raise ValueError(f"VOF solid>metal cell count mismatch at {t}")
        if row["n_core_excess_gt_1e8"] != base["n_core_metal_alpha_ge_0p5"]:
            raise ValueError(f"Native core phase violation mismatch at {t}")
        if not math.isclose(row["V_solid_excess_m3"],
                            base["raw_positive_solid_over_metal_volume_m3"],
                            rel_tol=5e-7, abs_tol=1e-16):
            raise ValueError(f"Native excess integral mismatch at {t}")
        if not math.isclose(row["max_fraction_excess"],
                            base["max_solid_over_metal_fraction"],
                            rel_tol=5e-7, abs_tol=1e-12):
            raise ValueError(f"Native local max fraction excess mismatch at {t}")
        if not math.isclose(
            row["V_metal_raw_m3"],
            row["V_solid_raw_m3"]+row["V_liquid_difference_raw_m3"],
            abs_tol=2e-12, rel_tol=1e-8
        ):
            raise ValueError(f"Native phase volume decomposition mismatch at {t}")
        if t == 1.0:
            if not math.isclose(row["V_metal_raw_m3"], LAST_METAL_M3,
                                rel_tol=1e-7, abs_tol=1e-12):
                raise ValueError("Native final metal volume does not match real FS-C07")
            if not math.isclose(row["V_solid_raw_m3"], LAST_SOLID_M3,
                                rel_tol=1e-7, abs_tol=1e-12):
                raise ValueError("Native final solid volume does not match real FS-C07")
    footers = [line.strip() for line in text.splitlines()
               if line.strip().startswith(FOOTER)]
    if len(footers) != 1:
        raise ValueError("Exactly one FS-C08 native read-only success footer required")
    footer = dict(token.split("=", 1)
                  for token in footers[0][len(FOOTER):].split())
    for key, value in (
        ("read_only", "1"),
        ("solver_reexecuted", "0"),
        ("phase_fields_written", "0"),
        ("physical_shrinkage_validated", "0"),
    ):
        if footer.get(key) != value:
            raise ValueError(f"Native bridge safety footer {key} mismatch")
    return {
        "schema": "masterproject-fs-c08-native-field-integration-check-v1",
        "status": "PASS",
        "saved_times_verified": sorted(wanted),
        "source": "Native OpenFOAM14 stdout cross-checked to verified prior WSL FS-C07 phase evidence",
        "model_integration_scope":
            "read-only mesh/fields and C++17 Gamma=0 ledger only",
        "native_fields_written": False,
        "native_CFD_rerun": False,
        "physical_shrinkage_accepted": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--times", nargs="+", type=float, default=[0.2, 0.4, 1.0])
    args = ap.parse_args(argv)
    try:
        out = verify_native_log(args.log.read_text(encoding="utf-8"),
                                tuple(args.times))
        print(json.dumps(out, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("FS-C08 NATIVE BRIDGE NOT ACCEPTED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
