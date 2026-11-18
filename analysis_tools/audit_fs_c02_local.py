#!/usr/bin/env python3
"""FS-C02 read-only local-result audit; never launches CFD or touches 3D cases.

Scope: provisional rhoConst 6820 metal-air VOF. Global volume from original
postProcessing, a separate final-field alpha check, and Courant logs.
Mass is DERIVED from rhoConst*volume, never independently validated or shrinkage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from run_fs_c02_local import DENSITY, INITIAL_VOLUME, WIDTH, HEIGHT, DEPTH

EXPECTED_CELLS = 80 * 120  # FS-C01 template geometry frozen for FS-C02
CELL_VOLUME = WIDTH * HEIGHT * DEPTH / EXPECTED_CELLS
FINAL_TIME_S = 0.1
VOLUME_FILE = Path("postProcessing/metalVolume/0/volFieldValue.dat")
SCHEMA = "masterproject-fs-c02-metal-air-smoke-v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("FS-C02 AUDIT: " + message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_volume(path: Path) -> list[tuple[float, float]]:
    require(path.is_file() and not path.is_symlink(),
            "original metalVolume time series missing")
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    require(any(re.fullmatch(r"#\s*Time\s+volIntegrate\(alpha\.metal\)\s*", x)
                for x in lines), "incorrect volume function/header (must be alpha.metal)")
    rows = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        cells = s.split()
        require(len(cells) == 2, "volume file needs exactly time and volIntegrate(alpha.metal)")
        try:
            time_s, volume_m3 = map(float, cells)
        except ValueError as error:
            raise ValueError("FS-C02 AUDIT: nonnumeric volume entry") from error
        require(math.isfinite(time_s) and math.isfinite(volume_m3)
                and time_s >= 0 and volume_m3 >= 0, "invalid time or volume")
        require(not rows or time_s > rows[-1][0], "nonmonotonic or duplicate times")
        rows.append((time_s, volume_m3))
    require(len(rows) >= 2, "need at least two volume measurements")
    return rows


def read_alpha(path: Path) -> list[float]:
    require(path.is_file() and not path.is_symlink(), "latest alpha.metal field missing")
    raw = path.read_text(encoding="utf-8", errors="replace")
    require(re.search(r"\bobject\s+alpha\.metal\s*;", raw) is not None,
            "field is not alpha.metal")
    internal = raw.split("boundaryField", 1)[0]
    match = re.search(r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",
                      internal, re.S)
    if match:
        count = int(match.group(1))
        require(count == EXPECTED_CELLS, "unexpected alpha cell count; mesh changed")
        try:
            values = [float(x) for x in match.group(2).split()]
        except ValueError as error:
            raise ValueError("FS-C02 AUDIT: invalid scalar values") from error
        require(len(values) == count, "alpha list does not match declared count")
    else:
        uniform = re.search(r"internalField\s+uniform\s+([+\-0-9.eE]+)\s*;", internal)
        require(uniform is not None, "unsupported/non-ASCII alpha internalField")
        try:
            values = [float(uniform.group(1))] * EXPECTED_CELLS
        except ValueError as error:
            raise ValueError("FS-C02 AUDIT: invalid uniform alpha") from error
    require(all(math.isfinite(x) for x in values), "NaN or infinite alpha cell")
    return values


def latest_field(case: Path, final_time: float) -> tuple[float, Path]:
    options = []
    for child in case.iterdir():
        if not child.is_dir() or child.is_symlink() or child.name == "0":
            continue
        try:
            time = float(child.name)
        except ValueError:
            continue
        if math.isfinite(time) and time > 0:
            options.append((time, child / "alpha.metal"))
    require(bool(options), "no numerical time folders/alpha fields")
    selected = max(options, key=lambda x: x[0])
    require(abs(selected[0] - final_time) <= 5e-5,
            "last saved alpha time differs from volume output time")
    return selected


def log_courant(log: str) -> dict:
    fluid = re.findall(
        r"(?m)^Courant Number mean:\s*([+\-0-9.eE]+)\s+max:\s*([+\-0-9.eE]+)",
        log,
    )
    interface = re.findall(
        r"(?m)^Interface Courant Number mean:\s*([+\-0-9.eE]+)\s+max:\s*([+\-0-9.eE]+)",
        log,
    )
    def vals(rows):
        results = [float(x[1]) for x in rows]
        require(all(math.isfinite(v) and v >= 0 for v in results), "bad Courant data")
        return results
    f, i = vals(fluid), vals(interface)
    return {
        "courant_observations": len(f),
        "max_courant_over_log": max(f) if f else None,
        "last_courant_max": f[-1] if f else None,
        "max_interface_courant_over_log": max(i) if i else None,
        "last_interface_courant_max": i[-1] if i else None,
    }


def audit(run: Path, out: Path, max_drift: float = 0.005) -> dict:
    run, out = run.expanduser().resolve(), out.expanduser().resolve()
    require(0 < max_drift < 1 and math.isfinite(max_drift), "bad volume tolerance")
    case = run / "FS-C02"
    require(case.is_dir() and not case.is_symlink()
            and (run / "FS-C02_RUN_STATUS.json").is_file(),
            "run directory must contain case FS-C02 with its status file")
    require(out != run and run not in out.parents
            and out != case and case not in out.parents,
            "report must be separate from original run/results")
    require(not out.exists(), "refusing overwrite of existing audit output")

    status = json.loads((run / "FS-C02_RUN_STATUS.json").read_text())
    require(status.get("case_id") == "FS-C02"
            and status.get("status") == "SOLVER_FINISHED_PHYSICS_NOT_VALIDATED"
            and status.get("solver_tested_on_real_openfoam") is True,
            "run status is not a completed FS-C02 solver")
    stages = status.get("stages", [])
    require(len(stages) == 3 and
            [s.get("stage") for s in stages] == ["blockMesh", "checkMesh", "foamRun"]
            and all(s.get("returncode") == 0 and s.get("gate_passed") is True
                    for s in stages),
            "missing or failed FS-C02 stage gate")

    manifest_file = case / "FS-C02_MANIFEST.json"
    require(manifest_file.is_file() and not manifest_file.is_symlink(), "manifest missing")
    m = json.loads(manifest_file.read_text())
    physics = m.get("physical_assumptions", {})
    require(m.get("schema") == SCHEMA and m.get("case_id") == "FS-C02"
            and physics.get("contraction") is False
            and physics.get("solidification") is False
            and physics.get("metal_air_vof") is True,
            "not the provisional FS-C02 iron-air case")
    require(math.isclose(m.get("reference_metal_density_kg_m3"), DENSITY)
            and math.isclose(m.get("initial_metal_volume_m3"), INITIAL_VOLUME),
            "unknown metal density or initial geometry")
    thermo = (case / "constant" / "physicalProperties.metal").read_text()
    require(bool(re.search(r"\bequationOfState\s+rhoConst\s*;", thermo))
            and bool(re.search(r"\brho\s+6820\s*;", thermo)),
            "rhoConst metal assumptions changed: mass estimate invalid")
    expected = m.get("generated_input_sha256")
    require(isinstance(expected, dict) and len(expected) == 20,
            "missing SHA256 input inventory")
    for rel, sha in expected.items():
        path = Path(rel)
        require(not path.is_absolute() and ".." not in path.parts
                and path.parts[0] in {"0", "constant", "system"}
                and (case / path).is_file() and not (case / path).is_symlink(),
                "untrusted/modified solver input inventory")
        require(digest(case / path) == sha, "changed FS-C02 solver input: " + rel)

    volume_path = case / VOLUME_FILE
    rows = read_volume(volume_path)
    time_s, final_vol = rows[-1]
    _, first_vol = rows[0]
    last_t, alpha_file = latest_field(case, time_s)
    alphas = read_alpha(alpha_file)
    field_vol = sum(alphas) * CELL_VOLUME
    max_drift_obs = max(abs(v - first_vol)/INITIAL_VOLUME for _,v in rows)
    field_mismatch = abs(final_vol - field_vol)/INITIAL_VOLUME
    courant_file = run / "logs" / "FS-C02_foamRun.log"
    require(courant_file.is_file(), "original FS-C02 solver log missing")
    log = courant_file.read_text(encoding="utf-8", errors="replace")
    cour = log_courant(log)
    flags = []
    if abs(rows[0][0]) > 1e-7:
        flags.append("missing initial time-zero volume")
    if time_s < FINAL_TIME_S-1e-4 or time_s > FINAL_TIME_S+1e-4:
        flags.append("endTime 0.1 s not measured")
    if abs(first_vol-INITIAL_VOLUME)/INITIAL_VOLUME > max_drift:
        flags.append("initial metal volume differs from expected geometry")
    if max_drift_obs > max_drift:
        flags.append("max volume drift exceeds tolerance")
    if field_mismatch > 1e-4:
        flags.append("final integrated alpha field does not match volFieldValue")
    if min(alphas) < -1e-6 or max(alphas) > 1+1e-6:
        flags.append("alpha.metal outside admissible bounds")
    if cour["max_courant_over_log"] is None:
        flags.append("no Courant observations in original solver log")
    elif cour["max_courant_over_log"] > .25 * (1+1e-4):
        flags.append("Courant max exceeds configured maxCo .25")
    if cour["max_interface_courant_over_log"] is None:
        flags.append("no interface Courant observations")
    elif cour["max_interface_courant_over_log"] > .25 * (1+1e-4):
        flags.append("interface Courant exceeds configured maxAlphaCo .25")

    report = {
        "schema": "masterproject-fs-c02-postrun-screen-v1",
        "case_id": "FS-C02",
        "status": "NUMERICAL_SCREEN_PASSED" if not flags else "REVIEW",
        "source_run_directory": str(run),
        "source_case_manifest_sha256": digest(manifest_file),
        "volume_source_sha256": digest(volume_path),
        "alpha_final_source_sha256": digest(alpha_file),
        "solver_log_sha256": digest(courant_file),
        "time_points": len(rows),
        "first_time_s": rows[0][0],
        "last_time_s": time_s,
        "alpha_field_time_s": last_t,
        "first_volume_m3": first_vol,
        "last_volume_m3": final_vol,
        "max_relative_volume_drift": max_drift_obs,
        "max_allowed_relative_volume_drift": max_drift,
        "last_field_integrated_volume_m3": field_vol,
        "field_to_function_volume_mismatch_fraction": field_mismatch,
        "alpha_min": min(alphas),
        "alpha_max": max(alphas),
        "alpha_cells": len(alphas),
        "alpha_interface_cells_strict_0_to_1": sum(0 < x < 1 for x in alphas),
        "density_assumed_rhoConst_kg_m3": DENSITY,
        "initial_mass_reference_kg": DENSITY*INITIAL_VOLUME,
        "last_mass_kg_DERIVED_NOT_MEASURED": DENSITY*final_vol,
        "max_mass_drift_fraction_DERIVED_NOT_INDEPENDENT": max_drift_obs,
        **cour,
        "interface_height_not_measured": True,
        "physical_mass_balance_not_verified": True,
        "melt_solid_fraction_not_modelled": True,
        "solidification_not_modelled": True,
        "shrinkage_not_modelled": True,
        "mold_cht_not_modelled": True,
        "alerts": flags,
    }
    out.mkdir(parents=True)
    (out / "FS-C02_NUMERICAL_SCREEN.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True,
                        help="existing FS-C02 run directory; never modified")
    parser.add_argument("--out", type=Path, required=True,
                        help="NEW report directory outside the run")
    args = parser.parse_args(argv)
    try:
        record = audit(args.run, args.out)
        print("FS-C02 " + record["status"])
        print("Volume drift fraction: " + str(record["max_relative_volume_drift"]))
        print("Final alpha range: " + str(record["alpha_min"]) + " ... "
              + str(record["alpha_max"]))
        print("MASS DERIVED FROM rhoConst, NOT MEASURED. NO SHRINKAGE MODEL.")
        if record["alerts"]:
            print("ALERTS: " + "; ".join(record["alerts"]))
        return 0 if record["status"] == "NUMERICAL_SCREEN_PASSED" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
