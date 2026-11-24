#!/usr/bin/env python3
"""Fail-closed numeric verifier for FS-C08 genuine-fvMesh SYNTHETIC shadow step.

Confirms nonzero Gamma, owner-neighbour connectivity, all 3 phase flows,
per-step total metal/gas conservation and one-count latent enthalpy conservation.
This is not a validation of cast-iron shrinkage, liquid feeding, VOF or pressure.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

MARKER = "FS_C08_NATIVE_SHADOW_STEP "
FOOTER = "FS_C08_NATIVE_SHADOW_END "


def numeric_line(line: str) -> dict[str, float]:
    result = {}
    for item in line.split():
        if "=" not in item:
            raise ValueError("Malformed native shadow step token: " + item)
        k, v = item.split("=", 1)
        if k in result:
            raise ValueError("Duplicate native shadow key: " + k)
        value = float(v)
        if not math.isfinite(value):
            raise ValueError("Nonfinite native shadow metric: " + k)
        result[k] = value
    return result


def verify_shadow_stdout(stdout: str) -> dict:
    rows = [
        line.strip()[len(MARKER):]
        for line in stdout.splitlines()
        if line.strip().startswith(MARKER)
    ]
    ends = [
        line.strip()[len(FOOTER):]
        for line in stdout.splitlines()
        if line.strip().startswith(FOOTER)
    ]
    if len(rows) != 1 or len(ends) != 1:
        raise ValueError("Exactly one native shadow metric and safety footer required")
    row = numeric_line(rows[0])
    flags = numeric_line(ends[0])
    mandatory = (
        "cells", "internal_faces", "face_index", "owner", "neighbour",
        "dt_s", "GammaOwner_kg_m3_s", "GammaNeighbour_kg_m3_s",
        "flowL_kg_s", "flowS_kg_s", "flowG_kg_s",
        "initial_metal_kg", "final_metal_kg",
        "initial_gas_kg", "final_gas_kg",
        "initial_enthalpy_J", "final_enthalpy_J",
        "gamma_transferred_kg", "delta_metal_volume_m3",
        "metal_mass_residual_kg", "gas_mass_residual_kg",
        "enthalpy_residual_J", "owner_T_final_K",
        "neighbour_T_final_K",
    )
    for key in mandatory:
        if key not in row:
            raise ValueError("Missing native shadow field: "+key)
    required_flags = {
        "synthetic_only": 1,
        "nonzero_gamma": 1,
        "native_fvmesh_owner_neighbour": 1,
        "three_phase_internal_flux": 1,
        "closed_domain_no_boundary_flux": 1,
        "original_fields_written": 0,
        "OpenFOAM_CFD_pressure_solved": 0,
        "OpenFOAM_CFD_velocity_solved": 0,
        "physical_3d_shrinkage_validated": 0,
    }
    for key, required in required_flags.items():
        if flags.get(key) != required:
            raise ValueError(f"Native shadow footer {key} invalid")
    if row["cells"] != 34368:
        raise ValueError("Wrong FS-C07 native mesh cell count")
    if row["internal_faces"] <= 0:
        raise ValueError("Real native internal face needed")
    if not (0 <= row["face_index"] < row["internal_faces"]):
        raise ValueError("Native internal face index invalid")
    if not (0 <= row["owner"] < row["cells"] and
            0 <= row["neighbour"] < row["cells"] and
            row["owner"] != row["neighbour"]):
        raise ValueError("Native owner/neighbour invalid")
    if row["dt_s"] <= 0:
        raise ValueError("Time step not positive")
    if not (row["GammaOwner_kg_m3_s"] > 0 and
            row["GammaNeighbour_kg_m3_s"] < 0):
        raise ValueError("Nonzero opposite-sign local Gamma needed")
    for phase in ("flowL_kg_s", "flowS_kg_s", "flowG_kg_s"):
        if row[phase] == 0:
            raise ValueError("All three phase internal face flows required")
    for k in ("initial_metal_kg", "final_metal_kg",
              "initial_gas_kg", "final_gas_kg", "initial_enthalpy_J",
              "final_enthalpy_J", "owner_T_final_K",
              "neighbour_T_final_K"):
        if row[k] <= 0:
            raise ValueError("Nonpositive mass/energy/temperature: "+k)
    if row["gamma_transferred_kg"] == 0:
        raise ValueError("Gamma source integrated to zero: no net conversion")
    checks = (
        ("metal", "initial_metal_kg", "final_metal_kg", "metal_mass_residual_kg"),
        ("gas", "initial_gas_kg", "final_gas_kg", "gas_mass_residual_kg"),
        ("enthalpy", "initial_enthalpy_J", "final_enthalpy_J",
         "enthalpy_residual_J"),
    )
    for name, initial, final, residual in checks:
        scale = max(1.0, abs(row[initial]), abs(row[final]))
        if abs(row[final] - row[initial]) > 1e-10*scale:
            raise ValueError(name+" global conservation failed")
        if abs(row[residual]) > 1e-10*scale:
            raise ValueError(name+" reported residual too large")
        if not math.isclose(
            row[residual], row[final]-row[initial],
            rel_tol=1e-9, abs_tol=1e-10*scale
        ):
            raise ValueError(name+" reported mass/energy residual inconsistent")
    return {
        "schema": "masterproject-fs-c08-native-shadow-parity-v1",
        "status": "PASS",
        "mesh_cells": int(row["cells"]),
        "internal_faces": int(row["internal_faces"]),
        "owner": int(row["owner"]),
        "neighbour": int(row["neighbour"]),
        "nonzero_source_gamma_owner_kg_m3_s": row["GammaOwner_kg_m3_s"],
        "nonzero_source_gamma_neighbour_kg_m3_s": row["GammaNeighbour_kg_m3_s"],
        "phase_face_flows_kg_s": {
            "liquid": row["flowL_kg_s"], "solid": row["flowS_kg_s"],
            "gas": row["flowG_kg_s"],
        },
        "net_liquid_to_solid_kg": row["gamma_transferred_kg"],
        "metal_mass_residual_kg": row["metal_mass_residual_kg"],
        "gas_mass_residual_kg": row["gas_mass_residual_kg"],
        "enthalpy_residual_J": row["enthalpy_residual_J"],
        "metal_geometric_volume_change_m3":
            row["delta_metal_volume_m3"],
        "simulation_scope":
            "one explicit conservative synthetic FV step on real native fvMesh",
        "real_FC07_state_fields_used": False,
        "physical_shrinkage_validated": False,
        "pressure_velocity_free_surface_solved": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        print(json.dumps(
            verify_shadow_stdout(args.log.read_text(encoding="utf-8")),
            indent=2,allow_nan=False
        ))
        return 0
    except (ValueError, OSError) as err:
        print("FS-C08 NATIVE SHADOW NOT ACCEPTED:",err,file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
