#!/usr/bin/env python3
"""Native Foundation14 Case B T0 energy history from both regional temperature fields.

Runs foamPostProcess with region-specific volFieldValue (all cells, volAverage T,
reported volume), then computes E(t)=sum_rhoCvV*Tavg from REAL native output.
No CFD is launched, no mesh is changed, no energy/flux validation is invented.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

REGIONS = ("metal", "mold")
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
NAME = {"metal": "caseBT0MetalVolumeTemperature", "mold": "caseBT0MoldVolumeTemperature"}
# Input mesh/FO volume comparison tolerance (0.5%), NOT energy closure tolerance.
MESH_VOLUME_CONSISTENCY_TOL = 0.005


def functions_dict(region: str) -> str:
    """OpenFOAM14 foamPostProcess -dict reads functionObject entries directly."""
    if region not in REGIONS:
        raise ValueError("unexpected region")
    return f"""/* C3D-05/B -- FOUNDATION14 T0 diagnostics only.
 * volFieldValue API: src/functionObjects/field/fieldValues/volFieldValue
 * Invoked by foamPostProcess -region {region} -dict system/T0_energy_{region}.
 */
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object functions;
}}
{NAME[region]}
{{
    type volFieldValue;
    libs ("libfieldFunctionObjects.so");
    region {region};
    cellZone all;
    operation volAverage;
    writeVolume true;
    writeFields false;
    fields (T);
}}
"""


def read_volume_average(path: Path) -> list[dict]:
    """Require exact native volFieldValue header and finite, increasing time."""
    if not path.is_file() or path.is_symlink():
        raise ValueError("missing or untrusted OpenFOAM volFieldValue data: " + str(path))
    lines = path.read_text(encoding="utf-8").splitlines()
    headers = [line[1:].strip().split() for line in lines if line.lstrip().startswith("#")]
    if not any(row[:3] == ["Time", "Volume", "volAverage(T)"] for row in headers):
        raise ValueError("native volFieldValue header not found (expected Time Volume volAverage(T))")
    rows = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        values = line.split()
        if len(values) != 3:
            raise ValueError("ambiguous native output row: " + line[:120])
        try:
            t = Decimal(values[0])
            vol = float(values[1])
            temp = float(values[2])
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid numeric native output row") from exc
        if not t.is_finite() or t < 0 or not all(math.isfinite(x) and x > 0 for x in (vol, temp)):
            raise ValueError("nonfinite, negative-time or nonpositive native temperature/volume")
        if t in seen or (rows and t <= rows[-1]["time_decimal"]):
            raise ValueError("non-increasing or duplicate native time")
        seen.add(t)
        rows.append({"time_decimal": t, "volume_m3": vol, "T_volume_average_K": temp})
    if not rows:
        raise ValueError("native volFieldValue has no numerical data")
    return rows


def inspect_outputs(case: Path, region: str) -> tuple[Path, list[dict]]:
    """Find unique object-name data under postProcessing; do not assume time folder."""
    if region not in REGIONS:
        raise ValueError("unexpected region")
    pp = case / "postProcessing"
    paths = [p for p in pp.glob(f"**/{NAME[region]}/**/volFieldValue.dat") if p.is_file()]
    # Some Foundation layouts place output under object-name first; others
    # use a region prefix. Each object name is globally unique in this case.
    paths += [p for p in pp.glob("**/volFieldValue.dat")
              if NAME[region] in p.parts and p not in paths]
    paths = list(dict.fromkeys(paths))
    if len(paths) != 1:
        raise ValueError(f"{region}: expected 1 native postProcessing/volFieldValue.dat for {NAME[region]}, got {len(paths)}")
    return paths[0], read_volume_average(paths[0])


def prepare_dict(case: Path, region: str) -> Path:
    path = case / "system" / f"T0_energy_{region}"
    text = functions_dict(region)
    if path.exists() or path.is_symlink():
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8") == text:
            return path
        raise FileExistsError("Nonmatching native postprocessing dictionary preserved: " + str(path))
    with path.open("x", encoding="utf-8") as f:
        f.write(text)
    return path


def native_postprocess(case: Path, region: str) -> tuple[Path, list[dict]]:
    """Never rerun native postprocess if the expected output already exists."""
    try:
        return inspect_outputs(case, region)
    except ValueError as exc:
        # Existing unexpected/broken output is preserved, not silently replaced.
        pp = case / "postProcessing"
        if pp.exists() and any(NAME[region] in p.parts for p in pp.rglob("*")):
            raise ValueError(f"{region}: prior postProcessing data exists but failed validation: {exc}") from exc
    prepare_dict(case, region)
    if shutil.which("foamPostProcess") is None:
        raise RuntimeError("Foundation14 foamPostProcess executable unavailable")
    log = case / f"log.foamPostProcess.T0_{region}"
    if log.exists() or log.is_symlink():
        raise FileExistsError("Prior native postprocessing log preserved: " + str(log))
    command = [
        "foamPostProcess", "-case", str(case), "-region", region,
        "-dict", f"system/T0_energy_{region}", "-time", "0:",
    ]
    with log.open("x", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=case, stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Native foamPostProcess region={region} exit={result.returncode}; see {log}")
    return inspect_outputs(case, region)


def compute_energy_history(
    metal: list[dict], mold: list[dict], reference: dict, input_cfg: dict
) -> dict:
    """No arbitrary energy PASS threshold: quantify closure and effective transfer."""
    by_region = {}
    for region, rows in (("metal", metal), ("mold", mold)):
        if not rows:
            raise ValueError("no native temperatures for " + region)
        capacity = reference["regions"][region]["thermal_capacity_J_per_K"]
        expected_vol = reference["regions"][region]["volume_m3"]
        if not math.isfinite(capacity) or capacity <= 0:
            raise ValueError("bad reference capacity")
        for row in rows:
            mismatch = abs(row["volume_m3"] - expected_vol) / expected_vol
            if mismatch > MESH_VOLUME_CONSISTENCY_TOL:
                raise ValueError(f"{region}: native volume differs from accepted checkMesh by {mismatch:.3%}")
        by_region[region] = {row["time_decimal"]: row for row in rows}
    times_metal, times_mold = set(by_region["metal"]), set(by_region["mold"])
    if times_metal != times_mold:
        raise ValueError("metal and mold native write-time sets differ; refuse energy pairing")
    times = sorted(times_metal)
    if len(times) < 2 or times[0] != 0:
        raise ValueError("expected native time-zero and at least two temperature samples")
    # Initial uniform scalar fields are explicitly prescribed for the C14
    # diagnostic. Reject a wrong first saved state instead of interpreting
    # subsequent drift against a reference that was never established.
    for region in ("metal", "mold"):
        expected_start = float(input_cfg[region]["T_initial_K"])
        measured_start = by_region[region][times[0]]["T_volume_average_K"]
        tolerance = max(1e-3, abs(expected_start)*1e-6)
        if abs(measured_start-expected_start) > tolerance:
            raise ValueError(
                f"{region}: time-zero native T={measured_start:.9g} K does not "
                f"match prescribed initial {expected_start:.9g} K "
                f"(field write tolerance {tolerance:g} K)"
            )
    initial = reference["total_initial_sensible_energy_relative_to_zero_K_J"]
    scale = reference["initial_hot_to_cold_energy_scale_J"]
    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("invalid nonzero internal-exchange energy scale")
    series = []
    previous = None
    for time in times:
        met = by_region["metal"][time]
        mol = by_region["mold"][time]
        em = reference["regions"]["metal"]["thermal_capacity_J_per_K"] * met["T_volume_average_K"]
        eo = reference["regions"]["mold"]["thermal_capacity_J_per_K"] * mol["T_volume_average_K"]
        total = em + eo
        entry = {
            "time_s": float(time),
            "metal_T_volAverage_K": met["T_volume_average_K"],
            "mold_T_volAverage_K": mol["T_volume_average_K"],
            "metal_sensible_energy_J": em,
            "mold_sensible_energy_J": eo,
            "total_sensible_energy_J": total,
            "closure_error_J": total - initial,
            "abs_closure_error_over_initial_exchange_scale": abs(total-initial)/scale,
        }
        if previous is not None:
            dt = entry["time_s"] - previous["time_s"]
            if dt <= 0:
                raise ValueError("no strictly increasing times")
            # Closed two-solid: ideally metal energy lost = mold energy gained.
            # These are net internal energy rates, NOT measured patch-face flux.
            entry["effective_metal_energy_loss_rate_W"] = -(em-previous["metal_sensible_energy_J"])/dt
            entry["effective_mold_energy_gain_rate_W"] = (eo-previous["mold_sensible_energy_J"])/dt
            entry["pair_net_energy_rate_residual_W"] = (total-previous["total_sensible_energy_J"])/dt
        previous = entry
        series.append(entry)
    end_time = float(input_cfg["simulation"]["endTime_s"])
    last = series[-1]["time_s"]
    if abs(last - end_time) > max(1e-10, 1e-7*end_time):
        raise ValueError(f"postprocessed time ends at {last}, expected {end_time}")
    max_fraction = max(e["abs_closure_error_over_initial_exchange_scale"] for e in series)
    # Metadata describe what was OBSERVED; do not claim a numerical acceptance.
    return {
        "status": "OBSERVED_NATIVE_VOLUMETRIC_ENERGY_METRICS_NOT_PHYSICAL_VALIDATION",
        "samples": len(series),
        "last_time_s": last,
        "initial_time_native_observed": bool(times and times[0] == 0),
        "max_abs_energy_closure_relative_to_initial_exchange": max_fraction,
        "mesh_volume_consistency_tolerance_used": MESH_VOLUME_CONSISTENCY_TOL,
        "energy_closure_physically_or_numerically_accepted": False,
        "direct_coupled_face_heat_flux_verified": False,
        "surface_flux_continuity_verified": False,
        "scientific_status": "C14 NUMERICAL reference ONLY, no mesh/time sensitivity or experimental validation",
        "definitions": {
            "E_region": "rhoConst * CvConst * checkMesh_region_V * foamPostProcess volAverage(T)",
            "energy_scale": "rho_metal Cv_metal V_metal*(T_metal_initial-T_equilibrium_closed)",
            "interfacial_heat_rate": "Effective energy transfer inferred from cell-volume integrals; not measured patch heat flux",
        },
        "history": series,
    }


def verify_solver_attempt(log: Path, status_file: Path, input_bytes: bytes):
    """Resume ONLY a completed native run tied to exactly these log and input bytes."""
    if log.is_symlink() or status_file.is_symlink():
        raise ValueError("symlink run artifacts not accepted")
    status = json.loads(status_file.read_text(encoding="utf-8"))
    if status.get("numerical_run_completed") is not True:
        raise ValueError("native solver run not verified complete")
    if status.get("input_sha256") != hashlib.sha256(input_bytes).hexdigest():
        raise ValueError("solver input checksum does not match current data")
    if status.get("log_sha256") != hashlib.sha256(log.read_bytes()).hexdigest():
        raise ValueError("solver log bytes differ from previous audited attempt")
    if status.get("scope") != "C14_ARCHIVED_NUMERICAL_TWO_SOLID_T0_ONLY":
        raise ValueError("wrong solver scientific scope")
    return status


def save_exclusive(path: Path, report: dict):
    data = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path.exists() or path.is_symlink():
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8") == data:
            return "ALREADY_REPORTED_IDENTICAL"
        raise FileExistsError("Previous energy observations preserved: " + str(path))
    with path.open("x", encoding="utf-8") as f:
        f.write(data)
    return "NATIVE_ENERGY_OBSERVATIONS_WRITTEN_NO_PHYSICAL_VALIDATION"


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--case", type=Path, required=True)
    cli.add_argument("--inputs", type=Path, required=True)
    cli.add_argument("--reference", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--native", action="store_true", help="Invoke Foundation14 foamPostProcess for both regions")
    cli.add_argument("--run-status", type=Path, required=True)
    cli.add_argument("--solver-log", type=Path, required=True)
    args = cli.parse_args()
    source_case = args.case.expanduser().resolve()
    inputs = args.inputs.read_bytes()
    cfg = json.loads(inputs)
    verify_solver_attempt(args.solver_log, args.run_status, inputs)
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    if hashlib.sha256(inputs).hexdigest() != reference["input_file_sha256"]:
        raise ValueError("Native energy analysis blocked: reference inputs SHA differs")
    # Exact documented archived case; arbitrary C14-looking labels are not enough.
    import importlib.util
    file = Path(__file__).with_name("c14_numerical_reference.py")
    spec = importlib.util.spec_from_file_location("c3d05_c14_energy_ref", file)
    if spec is None or spec.loader is None:
        raise ValueError("C14 reference verifier missing")
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    issues = bridge.validate_reference(cfg)
    if issues:
        raise ValueError("C14 numeric reference invalid: " + "; ".join(issues))
    fields = {}
    for region in REGIONS:
        file, entries = native_postprocess(source_case, region) if args.native else inspect_outputs(source_case, region)
        fields[region] = (file, entries)
    out = compute_energy_history(fields["metal"][1], fields["mold"][1], reference, cfg)
    out["input_sha256"] = hashlib.sha256(inputs).hexdigest()
    out["original_reference_sha256"] = hashlib.sha256(args.reference.read_bytes()).hexdigest()
    out["native_field_value_provenance"] = {
        r: {"file": str(fields[r][0]), "sha256": hashlib.sha256(fields[r][0].read_bytes()).hexdigest()}
        for r in REGIONS
    }
    print(save_exclusive(args.out, out), "samples", out["samples"])
    print("MAX observed closure discrepancy / initial exchange =",
          out["max_abs_energy_closure_relative_to_initial_exchange"])
    print("No direct interfacial face flux or experimental validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
