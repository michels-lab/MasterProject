#!/usr/bin/env python3
"""FS-C06 read-only density/phase-volume *screen*, never a shrinkage solver.

Requires authentic native FS-C06 phase-volume report AND a user-supplied,
hash-traceable constant-density input. No density defaults or assumptions
are silently copied from C14 or provisional FS-C05 thermophysics.

Conditional fixed-M reference: V*(fs) = M0/(rho_s*fs + rho_l*(1-fs)).
Here fs = measured *volumetric* solid fraction, NOT a mass fraction.
No measured boundary mass flux, coupled rho(T,fs), or graphitization
constitutive law is available, so this is NOT validated shrinkage/feeding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys


SCHEMA = "masterproject-fs-c06-density-screen-v1"
DENSITY_SCHEMA = "masterproject-fs-c06-density-input-v1"
NATIVE_STATUS = "FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE"
HEX256 = re.compile(r"[0-9a-fA-F]{64}\Z")


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("FS-C06 DENSITY SCREEN: " + why)


def finite_positive(value: object, label: str) -> float:
    require(type(value) in (int, float), label + " must be numeric")
    v = float(value)
    require(math.isfinite(v) and v > 0, label + " must be finite and positive")
    return v


def read_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), "missing/linked JSON: " + str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    require(type(data) is dict, "JSON root must be object")
    return data


def sha256(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), "missing/linked original provenance file")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_density_law(source_json: Path, source_file: Path) -> dict:
    law = read_json(source_json)
    require(law.get("schema") == DENSITY_SCHEMA, "density schema mismatch")
    require(isinstance(law.get("material_id"), str) and law["material_id"].strip(),
            "missing material/composition identifier")
    require(isinstance(law.get("source_reference"), str)
            and law["source_reference"].strip(), "missing density source reference")
    require(law.get("source_kind") in ("jmatpro_export", "laboratory_measurement"),
            "source_kind must identify JMatPro export or laboratory measurement")
    expected = law.get("source_file_sha256")
    require(isinstance(expected, str) and HEX256.fullmatch(expected) is not None,
            "source_file_sha256 absent/invalid")
    actual = sha256(source_file)
    require(expected.lower() == actual, "original density source hash mismatch")
    rho_l = finite_positive(law.get("rho_liquid_kg_m3"), "liquid density")
    rho_s = finite_positive(law.get("rho_solid_kg_m3"), "solid density")
    t_ref = finite_positive(law.get("density_reference_temperature_K"),
                            "reference temperature")
    require(law.get("graphitization_handling") in
            ("not_modelled", "effective_density_declared"),
            "graphitization handling must be explicit")
    return {"material_id": law["material_id"],
            "source_kind": law["source_kind"],
            "source_reference": law["source_reference"],
            "source_file_sha256": actual,
            "density_input_json_sha256": sha256(source_json),
            "rho_liquid_kg_m3": rho_l, "rho_solid_kg_m3": rho_s,
            "density_reference_temperature_K": t_ref,
            "graphitization_handling": law["graphitization_handling"],
            "constant_density_screen_only": True,
            "density_temperature_range_verified": False,
            "scientific_calibration_independently_verified": False}


def check_native_report(data: dict) -> tuple[float, list[dict]]:
    require(data.get("status") == NATIVE_STATUS,
            "requires an accepted native FS-C06 two-step run")
    require(data.get("native_cfd_executed") is True
            and data.get("model_loaded_native") is True
            and data.get("solid_fraction_fields_measured") is True,
            "cannot screen synthetic/staged solver reports")
    require(data.get("model_field_expected") == "alpha.metal.solid",
            "solid field provenance missing")
    evidence = data.get("native_fraction_diagnostics")
    require(type(evidence) is dict
            and evidence.get("native_solid_fraction_observed") is True
            and evidence.get("volumes_from_native_fluid_mesh") is True,
            "requires real volume-weighted mesh-derived inventory")
    v0 = finite_positive(evidence.get("initial_metal_vof_volume_m3"),
                         "initial metal volume")
    snapshots = evidence.get("snapshots")
    require(type(snapshots) is list and len(snapshots) == 2,
            "expected exactly two native snapshots")
    previous_time = 0.0
    for snap in snapshots:
        require(type(snap) is dict, "snapshot not an object")
        t = finite_positive(snap.get("time_s"), "snapshot time")
        require(t > previous_time, "snapshots missing time ordering")
        previous_time = t
        require(snap.get("cell_volume_weighted_not_cell_sum") is True
                and snap.get("solid_fraction_within_metal_vof") is True
                and snap.get("temperature_field_for_solidification") == "T.metal",
                "phase volume or phase-temperature evidence incomplete")
        for key in ("alpha_metal_sha256", "alpha_metal_solid_sha256",
                    "temperature_sha256"):
            require(isinstance(snap.get(key), str)
                    and HEX256.fullmatch(snap[key]) is not None,
                    "missing native field fingerprint: " + key)
        vm = finite_positive(snap.get("metal_vof_volume_m3"), "metal VO(F) volume")
        vs = snap.get("metal_solid_volume_m3")
        vl = snap.get("metal_liquid_volume_m3")
        require(type(vs) in (int, float) and type(vl) in (int, float),
                "missing solid/liquid volume inventory")
        require(all(math.isfinite(float(x)) and float(x) >= 0 for x in (vs, vl)),
                "unphysical phase volume")
        require(abs((vs + vl) - vm) <= 1e-9 * max(vm, v0),
                "solid + liquid volume does not recover metal VOF")
        require(isinstance(snap.get("metal_T_mean_K_alpha_volume_weighted"),
                           (float, int))
                and math.isfinite(snap["metal_T_mean_K_alpha_volume_weighted"])
                and snap["metal_T_mean_K_alpha_volume_weighted"] > 0,
                "missing physical phase temperature")
    return v0, snapshots


def screen_inventories(initial_metal_volume_m3: float, snapshots: list[dict],
                       density: dict) -> list[dict]:
    v0 = finite_positive(initial_metal_volume_m3, "initial volume")
    rho_l = finite_positive(density["rho_liquid_kg_m3"], "rho_liquid")
    rho_s = finite_positive(density["rho_solid_kg_m3"], "rho_solid")
    # Valid ONLY under the explicitly hypothetical initially all-liquid,
    # fixed mass, no feeding, no boundary metal flux assumptions.
    initial_liquid_mass_proxy = v0 * rho_l
    results = []
    for snap in snapshots:
        vm, vs, vl = (float(snap[k]) for k in
                      ("metal_vof_volume_m3", "metal_solid_volume_m3",
                       "metal_liquid_volume_m3"))
        require(vm > 0 and vs >= 0 and vl >= 0
                and abs(vs+vl-vm) <= 1e-9 * max(v0, vm),
                "incompatible phase inventories")
        fs_vol = vs/vm
        effective_rho = rho_s*fs_vol + rho_l*(1-fs_vol)
        fixed_mass_volume = initial_liquid_mass_proxy/effective_rho
        proxy_mass = rho_s*vs + rho_l*vl
        results.append({
            "time_s": snap["time_s"],
            "native_solid_volume_fraction_of_metal": fs_vol,
            "native_observed_metal_vof_volume_m3": vm,
            "inferred_metal_mass_kg_constant_density_proxy": proxy_mass,
            "inferred_metal_mass_proxy_change_from_initial_kg":
                proxy_mass-initial_liquid_mass_proxy,
            "inferred_metal_mass_proxy_relative_change":
                (proxy_mass-initial_liquid_mass_proxy)/initial_liquid_mass_proxy,
            "closed_fixed_mass_hypothesis_volume_m3": fixed_mass_volume,
            "closed_fixed_mass_signed_contraction_relative_initial":
                (v0-fixed_mass_volume)/v0,
            "native_vof_minus_fixed_mass_hypothesis_volume_m3":
                vm-fixed_mass_volume,
            "field_sha256": {
                "alpha.metal": snap["alpha_metal_sha256"],
                "alpha.metal.solid": snap["alpha_metal_solid_sha256"],
                "T.metal": snap["temperature_sha256"],
            },
            "metal_phase_temperature_mean_K": snap[
                "metal_T_mean_K_alpha_volume_weighted"],
            "measured_boundary_metal_mass_flux_kg_s": None,
            "measured_surface_displacement_m": None,
            "metal_mass_conservation_verified": False,
            "physical_volumetric_shrinkage_verified": False,
            "feeding_verified": False,
        })
    return results


def audit(native_report: Path, density_json: Path, density_source: Path,
          out: Path) -> dict:
    native_report, density_json, density_source, out = [
        p.expanduser().resolve() for p in
        (native_report, density_json, density_source, out)
    ]
    require(out not in (native_report, density_json, density_source)
            and not out.exists(), "refusing overwrite of source/report")
    case = read_json(native_report)
    v0, snaps = check_native_report(case)
    density = read_density_law(density_json, density_source)
    results = screen_inventories(v0, snaps, density)
    output = {
        "schema": SCHEMA,
        "status": "CONDITIONAL_DENSITY_SCREEN_NOT_MASS_OR_SHRINKAGE_VALIDATION",
        "origin_fs_c06_report_sha256": sha256(native_report),
        "initial_metal_vof_volume_m3": v0,
        "density_source": density,
        "snapshots": results,
        "assumptions": {
            "initially_all_liquid": True,
            "closed_fixed_initial_metal_mass_hypothesis_only": True,
            "density_law_is_constant_reference_value_not_rho_T_fs": True,
            "no_feeding_or_mass_flux_data": True,
            "graphitization_not_independently_verified": True,
            "no_cfd_or_foam_command_executed_by_this_tool": True,
        },
        "density_coupled_into_solver": False,
        "experimental_validation": False,
        "mass_conservation_verified": False,
        "volumetric_shrinkage_verified": False,
        "next_gate": "Implement physically backed rho(T,fs), metal/air boundary mass flux, free-surface displacement, graphite expansion, energy closure and QuickCup validation."
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create; original report and simulation case are never modified.
    with out.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-report", type=Path, required=True)
    parser.add_argument("--density-json", type=Path, required=True)
    parser.add_argument("--density-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.native_report, args.density_json,
                       args.density_source, args.out)
        print(result["status"])
        print("NO CFD, NO VERIFIED SHRINKAGE/FEEDING/MASS BALANCE.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("FS-C06 DENSITY SCREEN BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
