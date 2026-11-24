#!/usr/bin/env python3
"""Foundation14 C3D04-A OFFLINE postProcessing recovery in a NEW physical copy.

The actual WSL C14 full-functions postProcess died at "Field rho not found
in database" while the bare-mode registry lacked thermo/transport models.
Foundation v14 explicitly supports "-region metal -solver fluid" for
postProcessing with model fields. This runner always splits the ORIGINAL C14
diagnostic definitions into independent dependency-isolated passes so failure
of any optional object cannot block native energy/primitives/phase/profiles.

Only POST-PROCESSING on a new copy: NEVER foamMultiRun, Allrun, remesh, re-solve,
checkout/reset, write to old workcopy, or update the research source.
The source C14 physical dictionaries, mesh and 101 original states are copied
unaltered. Original time-step derivatives ddt(phaseChange:alpha1) and ddt(T)
cannot be recovered retrospectively from 0.1-second saved states.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

import run_c14_3d_complete_postprocess as old
import stage_c14_3d_case_a as stage
import c14_3d_native_energy_closure as energy
import audit_existing_native_c14_stage07 as forensic

ROOT = Path(__file__).resolve().parent
C14 = old.C14
OUTPUT = "C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_02"
REPORT = "C3D04_A_C14_SOLVER_BACKED_RECOVERY_REPORT.json"
PAIRS = {
    "core": (
        ("functions", "temperatureProbe"),
        ("functions", "topFlow"),
        ("researchDiagnostics", "metalTopPhiSum"),
        ("researchDiagnostics", "metalSensibleEnthalpy"),
    ),
    "energy": (
        ("researchDiagnostics", "energyAdvectiveFlux"),
        ("researchDiagnostics", "heatFlux"),
        ("researchDiagnostics", "energyFlux"),
        ("researchDiagnostics", "metalTopEnergyPower"),
        ("researchDiagnostics", "metalMoldEnergyPower"),
        ("researchDiagnostics", "metalBoundaryEnergyPower"),
    ),
    "phase": (
        ("researchDiagnostics", "metalMeanLiquidFraction"),
    ),
    "flow": (
        ("researchDiagnostics", "vorticityField"),
        ("researchDiagnostics", "flowTopology"),
        ("researchDiagnostics", "temperatureGradient"),
        ("researchDiagnostics", "temperatureGradientMagnitude"),
        ("researchDiagnostics", "densityGradient"),
        ("researchDiagnostics", "densityGradientMagnitude"),
        ("researchDiagnostics", "cellCourantNumber"),
        ("researchDiagnostics", "metalMaxCourant"),
        ("researchDiagnostics", "metalMaxThermalGradient"),
        ("researchDiagnostics", "metalMaxDensityGradient"),
    ),
    "profiles": (
        ("lineProfiles", "horizontalProfiles"),
        ("lineProfiles", "verticalProfiles"),
    ),
    "momentum": (
        ("researchDiagnostics", "solidificationMeltingMomentumDiagnostics"),
        ("momentumPostProcessing", "momentumMean"),
        ("momentumPostProcessing", "momentumMax"),
        ("momentumPostProcessing", "momentumHorizontalProfiles"),
        ("momentumPostProcessing", "momentumVerticalProfiles"),
    ),
}
TASK_ORDER = ("core", "energy", "phase", "flow", "profiles", "momentum")


class Blocked(ValueError):
    pass


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise Blocked("C3D04_A_NATIVE_RECOVERY_BLOCKED: " + reason)


def file_ok(p: Path) -> bool:
    return p.is_file() and not p.is_symlink()


def sha(path: Path) -> str:
    need(file_ok(path), "expected regular file missing or symlinked: " + str(path))
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


def read_json(path: Path) -> dict:
    need(file_ok(path), "JSON evidence missing: " + str(path))
    item = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(item, dict), "JSON evidence not an object: " + str(path))
    return item


def selected_source_block(content: str, name: str) -> str:
    """Copy an ORIGINAL C14 object byte-equivalent; never edit model params."""
    m = re.search(r"(?m)^[ \t]*" + re.escape(name) + r"[ \t]*\r?\n?[ \t]*\{", content)
    need(m is not None, "C14 diagnostic function not found: " + name)
    at = content.index("{", m.start())
    end = old.balanced(content, at)
    return content[m.start():end + 1].strip() + "\n"


def strip_profile_unsupported_fields(block: str) -> str:
    """Only in OFFLINE sample dictionary, not original C14 physics/objects.

    Restores primitive profiles at 101 saved times. The original ddt/T phase
    rate/derived-field profiles cannot be fabricated from 0.1s snapshots.
    """
    fields = re.compile(r"\bfields\s*\((.*?)\)\s*;", re.S)
    new = ("fields\n    (\n        U\n        T\n        p_rgh\n"
           "        phaseChangeSource:alpha1\n    );")
    changed, count = fields.subn(new, block, count=1)
    need(count == 1, "original C14 profile has no unique fields block")
    return changed


def assembled_dict(copy: Path, group: str) -> tuple[Path, list[dict]]:
    need(group in PAIRS, "unrecognized C14 group")
    records = []
    blocks = []
    for filename, name in PAIRS[group]:
        source = copy / "system" / filename
        need(file_ok(source), "copied C14 source dictionary absent: " + str(source))
        content = source.read_text(encoding="utf-8")
        b = selected_source_block(content, name)
        if group == "profiles":
            b = strip_profile_unsupported_fields(b)
        records.append({
            "object": name, "original_C14_dictionary": filename,
            "original_adapted_source_sha256": sha(source),
            "offline_geometry_or_field_filter": group == "profiles",
        })
        blocks.append(b)
    p = copy / "system" / ("stage07Offline_" + group)
    need(not p.exists() and not p.is_symlink(),
         "new physical copy unexpectedly already contains generated group " + group)
    p.write_text(
        "FoamFile\n{\n    format ascii;\n    class dictionary;\n"
        "    location \"system\";\n    object stage07Offline_" + group + ";\n}\n\n"
        + "\n".join(blocks), encoding="utf-8",
    )
    return p, records


def original_case_gate(case: Path, failed: Path, recovery: Path,
                       forensic_dir: Path, out: Path) -> dict:
    """All source/target safety checks BEFORE a potentially large copytree."""
    case = case.expanduser().resolve()
    failed = failed.expanduser().resolve()
    recovery = recovery.expanduser().resolve()
    forensic_dir = forensic_dir.expanduser().resolve()
    out = out.expanduser().absolute()
    input_dirs = [case, failed, recovery, forensic_dir, C14.resolve(),
                  ROOT.parents[2].resolve()]
    need(case.is_dir() and failed.is_dir() and recovery.is_dir()
         and forensic_dir.is_dir(), "real 10s CFD or archived prior evidence absent")
    need(not out.exists() and not out.is_symlink(),
         "new isolated copy output occupied; NEVER overwrite previous CFD or postprocessing")
    need(all(out != p and p not in out.parents and out not in p.parents
             for p in input_dirs),
         "new output overlaps original CFD, failed copy or repository")
    need(out.parent.is_dir(), "new workcopy parent does not exist")
    need(not any(p.is_symlink() for p in case.rglob("*")),
         "original CFD source contains symlinks; refuse implicit external file copy")
    orig_control = C14 / "system/controlDict"
    source_control = case / "system/controlDict"
    failed_control = failed / "system/controlDict"
    need(sha(orig_control) == sha(source_control) == sha(failed_control),
         "C14 original, actual source or prior failed controlDict changed")
    original_log = sha(case / "log.foamMultiRun")
    need(sha(failed / "log.foamMultiRun") == original_log,
         "failed copy native solver log differs from original CFD")
    prior = read_json(recovery / "C3D04_A_STAGE07_RECOVERY_REPORT.json")
    need(prior.get("schema") == "C3D04_A_C14_3D_STAGE07_EXISTING_EVIDENCE_V1"
         and prior.get("case_A_source_run_read_only") == str(case)
         and prior.get("source_sha256", {}).get("source_CFD_log_sha256") == original_log,
         "previous real 101-state recovery does not match this CFD case")
    failure = read_json(
        forensic_dir / "C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json"
    )
    need(failure.get("schema") == "C3D04_A_STAGE07_NATIVE_FAILURE_FORENSICS_V1"
         and failure.get("original_10s_case_read_only") == str(case)
         and failure.get("existing_native_workcopy_read_only") == str(failed),
         "native failure evidence belongs to another case/workcopy")
    sid = failure.get("evidence_sha256", {}).get("source_model_sha", {})
    need(sid.get("authentic_10s_solver_log_sha256") == original_log,
         "native failure forensic report SHA contradicts original C14 solver")
    need(failure.get("native_commands_verified") is False
         and "c14_functions" in failure.get("native_failed_commands", []),
         "source failure is not the verified C14 functions rho-registry blocker")
    need(file_ok(case/"10/metal/T") and file_ok(case/"10/metal/U")
         and file_ok(case/"10/metal/phaseChangeSource:alpha1"),
         "original genuine C14 terminal 10-second state is missing")
    mesh_cells = stage.region_cells(case,"metal",stage.EXPECTED["metal"])
    original_has_zone = stage.audit_existing_zone(
        case/"constant/metal/polyMesh/cellZones",mesh_cells["nCells"])
    return {
        "case": str(case), "failed_workcopy": str(failed),
        "recovery_report_sha256": sha(recovery/"C3D04_A_STAGE07_RECOVERY_REPORT.json"),
        "forensic_report_sha256":
            sha(forensic_dir/"C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json"),
        "original_C14_controlDict_sha256": sha(orig_control),
        "original_10s_solver_log_sha256": original_log,
        "prior_failed_copy_solver_log_sha256": sha(failed/"log.foamMultiRun"),
        "original_final_alpha1_sha256": sha(case/"10/metal/phaseChangeSource:alpha1"),
        "native_metal_mesh_cell_count": mesh_cells["nCells"],
        "original_CFD_contains_full_metal_cellZone": original_has_zone,
    }



def verify_or_add_metal_zone_in_new_copy(case: Path, copy: Path) -> dict:
    """Repair only zone lookup metadata, not mesh connectivity or physical model.

    Real WSL copy _02 showed FOAM FATAL IO ERROR: Cannot find cellZone metal;
    C14 source's solidificationMeltingSource references an all-metal cellZone.
    This function must NEVER run against an existing/occupied copy.
    """
    case = case.expanduser().resolve()
    copy = copy.expanduser().absolute()
    need(copy.is_dir() and not copy.is_symlink(),
         "new workcopy is not a regular directory")
    need(case != copy and case not in copy.parents and copy not in case.parents,
         "no changes inside original research CFD case")
    real = stage.region_cells(case, "metal", stage.EXPECTED["metal"])
    copied = stage.region_cells(copy, "metal", stage.EXPECTED["metal"])
    n = real["nCells"]
    need(copied["nCells"] == n, "copy metal region cell count differs")
    for name in stage.MESH:
        rel = Path("constant/metal/polyMesh") / name
        need(sha(case / rel) == sha(copy / rel),
             "source and copy mesh geometry/connectivity differ: " + name)
    original_zone = case / "constant/metal/polyMesh/cellZones"
    copied_zone = copy / "constant/metal/polyMesh/cellZones"
    if stage.audit_existing_zone(original_zone, n):
        need(file_ok(copied_zone), "original C14 metal zone missing in clone")
        need(sha(original_zone) == sha(copied_zone),
             "new clone changed pre-existing C14 full metal zone")
        return {
            "status": "SOURCE_FULL_METAL_CELLZONE_PRESENT_PRESERVED",
            "metal_cells": n,
            "copy_cellZones_sha256": sha(copied_zone),
            "added_to_copy_only": False,
            "geometry_connectivity_unchanged": True,
        }
    need(not copied_zone.exists() and not copied_zone.is_symlink(),
         "missing source metal cellZone but clone contains unexpected zone")
    copied_zone.write_text(stage.whole_region_zone(n), encoding="utf-8")
    need(stage.audit_existing_zone(copied_zone, n),
         "new metal zone is not all real native cells")
    need(not original_zone.exists() and not original_zone.is_symlink(),
         "original C14 mesh source zone unexpectedly changed")
    return {
        "status": "FULL_METAL_CELLZONE_CREATED_ONLY_IN_FRESH_COPY",
        "metal_cells": n,
        "copy_cellZones_sha256": sha(copied_zone),
        "added_to_copy_only": True,
        "original_CFD_cellZones_created": False,
        "geometry_connectivity_unchanged": True,
    }


def fatal_openfoam_log(log: Path, limit: int = 5) -> dict:
    """Native F14 can exit 0 while writing FOAM FATAL IO ERROR several times."""
    need(file_ok(log), "native subprocess log missing: " + str(log))
    pattern = re.compile(r"\bFOAM\s+FATAL(?:\s+IO)?\s+ERROR\b|\bFOAM aborting\b", re.I)
    found = []
    count = 0
    with log.open(encoding="utf-8", errors="replace") as stream:
        for line_no, line in enumerate(stream, 1):
            if pattern.search(line):
                count += 1
                if len(found) < limit:
                    found.append({"line": line_no, "text": line.strip()[:240]})
    return {
        "foam_fatal_present": count > 0,
        "foam_fatal_occurrence_count": count,
        "first_foam_fatal_markers": found,
    }



def native_group(copy: Path, group: str, dictionary: Path) -> dict:
    # Foundation14 user guide: -solver fluid reconstructs thermo/transport
    # model registry for rho,h and energyFlux; does not advance fluid solver.
    if group in ("core", "energy", "flow", "momentum"):
        args = ["foamPostProcess","-region","metal","-solver","fluid",
                "-dict","system/" + dictionary.name,"-time","0:"]
    else:
        # Without -solver, foamPostProcess reads these explicitly saved
        # primitive fields. Phase/object profiles must not rely on thermo.
        required = ("(phaseChangeSource:alpha1)" if group == "phase" else
                    "(U T p_rgh phaseChangeSource:alpha1)")
        args = ["foamPostProcess","-region","metal","-fields",required,
                "-dict","system/" + dictionary.name,"-time","0:"]
    executed = old.run_native(copy,"solverBacked_"+group,args)
    log = copy/executed["log"]
    errors = forensic.error_excerpt(log, limit=8)
    fatal = fatal_openfoam_log(log)
    # OpenFOAM may report FOAM FATAL IO with OS exit code 0.
    semantically_passed = executed["exit_code"] == 0 and not fatal["foam_fatal_present"]
    return {
        **executed, "group": group, "passed": semantically_passed,
        "os_exit_code_zero": executed["exit_code"] == 0,
        **fatal,
        "read_model": "fluid_solver_registry_no_FV_solve"
                      if group in ("core","energy","flow","momentum")
                      else "only_explicit_saved_fields",
        "log_sha256": errors["sha256"],
        "log_signatures": errors["error_signatures"],
        "log_last_24_lines": errors.get("tail_last_24_lines",[]),
    }


def saved_native_power_table(path: Path) -> tuple[list[str], list[dict[str, float]]]:
    """Strict 101 states or complete 100 intervals excluding 0s startup.

    Source C14 native functionObjects may not write an initialized t=0 table.
    0.1..10.0 is not the same dataset as 0..10.0; document the distinction.
    No extrapolation or fabricated initial power.
    """
    need(file_ok(path), "missing native face-power table " + str(path))
    header = None
    data = []
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith("# Time"):
                need(header is None, "duplicate native table header " + str(path))
                header = line[1:].split()
            elif not line.strip() or line.lstrip().startswith("#"):
                continue
            else:
                need(header is not None, "native power data before header")
                parts = line.split()
                need(len(parts) == len(header), "native power columns do not match header")
                try:
                    values = [float(x) for x in parts]
                except ValueError as exc:
                    raise Blocked("native power table contains nonnumeric entries") from exc
                need(all(math.isfinite(x) for x in values),
                     "native power table includes nonfinite values")
                data.append(dict(zip(header, values)))
    need(header is not None and "Time" in header and "sum(energyFlux)" in header,
         "native face table lacks Time/sum(energyFlux) columns")
    n = len(data)
    need(n in (100, 101),
         "native face-power time-series has " + str(n) +
         " rows; need all saved times 0..10 or 0.1..10")
    first = 0.0 if n == 101 else 0.1
    need(all(math.isclose(row["Time"],first+i*0.1,abs_tol=1e-8,rel_tol=0)
             for i,row in enumerate(data)),
         "native face-power times not exact consecutive saved 0.1s states")
    return header, data


def native_surface_table_coverage(copy: Path) -> dict:
    """Show real row counts even if incomplete, never invent times."""
    output = {}
    for family in ("metalTopEnergyPower","metalMoldEnergyPower",
                   "metalBoundaryEnergyPower"):
        path=copy/"postProcessing/metal"/family/"0/surfaceFieldValue.dat"
        if not file_ok(path):
            output[family]={"present":False}
            continue
        data_lines = []
        with path.open(encoding="utf-8",errors="replace") as stream:
            for ln in stream:
                if ln.strip() and not ln.lstrip().startswith("#"):
                    data_lines.append(ln.strip())
        first = data_lines[0].split()[0] if data_lines else None
        last = data_lines[-1].split()[0] if data_lines else None
        output[family]={"present":True,"sha256":sha(path),
                        "numeric_data_row_count":len(data_lines),
                        "first_recorded_time_text":first,
                        "last_recorded_time_text":last}
    return output


def primitive_profile_coverage(copy: Path) -> dict:
    """Original 3D sample locations: 80 finite points per saved final profile."""
    all_profiles = old.profile_coverage(copy)
    names = ("horizontalProfiles/line_y10mm",
             "horizontalProfiles/line_y20mm",
             "horizontalProfiles/line_y30mm",
             "verticalProfiles/line_x20mm")
    return {name:all_profiles[name] for name in names}


def surface_energy_summary(copy: Path) -> dict:
    """Face-power reconciliation is not metal+mold energy conservation."""
    base = copy/"postProcessing/metal"
    names = {
        "top":"metalTopEnergyPower",
        "contact":"metalMoldEnergyPower",
        "total":"metalBoundaryEnergyPower",
    }
    tables={}
    try:
        for key, family in names.items():
            _,rows = saved_native_power_table(
                base/family/"0"/"surfaceFieldValue.dat")
            tables[key]=rows
        first_times = [r["Time"] for r in tables["top"]]
        need(all(len(tables[k])==len(first_times)
                 and all(math.isclose(r["Time"], t, abs_tol=1e-8, rel_tol=0)
                         for r,t in zip(tables[k],first_times))
                 for k in names),
             "three native face-power time axes are inconsistent")
    except (Blocked, ValueError, OSError, KeyError) as err:
        return {
            "status":"NATIVE_SURFACE_POWER_TABLES_MISSING_OR_INCOMPATIBLE",
            "reason":str(err)[:900],
            "native_time_series":native_surface_table_coverage(copy),
            "nominal_metal_surface_power_reconciled":False,
            "global_energy_conservation_verified":False,
        }
    discrepancy=[]
    for i in range(len(first_times)):
        top=tables["top"][i]["sum(energyFlux)"]
        interface=tables["contact"][i]["sum(energyFlux)"]
        total=tables["total"][i]["sum(energyFlux)"]
        err=total-top-interface
        scale=max(1,abs(total),abs(top)+abs(interface))
        discrepancy.append(abs(err)/scale)
    final={k:tables[k][-1]["sum(energyFlux)"] for k in names}
    return {
        "status":"NATIVE_METAL_SURFACE_POWER_SAVED_STATES_DIAGNOSTIC",
        "saved_times_count":len(first_times),
        "first_saved_time_s":first_times[0],
        "last_saved_time_s":first_times[-1],
        "t0_native_power_available":math.isclose(first_times[0],0,abs_tol=1e-9),
        "t0_native_flux_fabricated":False,
        "final_energy_power_out_W":final,
        "maximum_relative_top_plus_contact_vs_total_discrepancy":max(discrepancy),
        "nominal_metal_surface_power_reconciled":max(discrepancy)<5e-5,
        "native_time_series":native_surface_table_coverage(copy),
        "energy_flux_direction":"outward positive (original C14 native surfaceFieldValue convention)",
        "global_energy_conservation_verified":False,
        "mold_side_flux_compared":False,
        "phase_change_source_discretization_verified":False,
    }


def inspect_occupied_copy(case: Path, copy: Path,
                          recovery: Path, forensic_dir: Path) -> dict:
    """Read-only classification. An existing copy is NEVER an overwrite target.

    Determine whether the existing six-pass output has a complete, source-
    matched final report or is a partial/in-progress evidence directory.
    Never conclude that an unfinished attempt is safe to resume or replace:
    another WSL foamPostProcess process may still be using that directory.
    """
    case = case.expanduser().resolve()
    copy = copy.expanduser().absolute()
    need(copy.is_dir() and not copy.is_symlink(),
         "occupied output is not a regular directory; refuse reading symlink")
    result = {
        "status": "EXISTING_COPY_PARTIAL_OR_POSSIBLY_ACTIVE_PRESERVED",
        "copy": str(copy),
        "mode": "READ_ONLY_INSPECTION",
        "solver_rerun": False,
        "copy_modified": False,
        "original_CFD_modified": False,
        "can_prove_other_process_not_running": False,
        "native_validation_verified": False,
        "global_energy_conservation_verified": False,
        "per_group_logs": {},
    }
    real_c14 = C14 / "system/controlDict"
    actual_ctrl = case / "system/controlDict"
    copy_ctrl = copy / "system/controlDict"
    for key, p in (("copy_original_controlDict", copy_ctrl),
                   ("copy_solver_log", copy / "log.foamMultiRun")):
        result[key + "_exists"] = file_ok(p)
    if file_ok(real_c14) and file_ok(actual_ctrl) and file_ok(copy_ctrl):
        result["source_C14_controlDict_matches"] = (
            sha(real_c14) == sha(actual_ctrl) == sha(copy_ctrl)
        )
    else:
        result["source_C14_controlDict_matches"] = False
    log_source = case / "log.foamMultiRun"
    copy_log = copy / "log.foamMultiRun"
    if file_ok(log_source) and file_ok(copy_log):
        result["copy_10s_solver_log_SHA_matches"] = sha(log_source) == sha(copy_log)
    else:
        result["copy_10s_solver_log_SHA_matches"] = False
    for group in TASK_ORDER:
        logfile = copy / ("log.C14_3D_postprocess_solverBacked_" + group)
        if file_ok(logfile):
            evidence = forensic.error_excerpt(logfile, limit=4)
            result["per_group_logs"][group] = {
                "present": True,
                "sha256": evidence["sha256"],
                "error_signatures": evidence["error_signatures"],
                "tail_last_24_lines": evidence.get("tail_last_24_lines", [])[-8:],
            }
        else:
            result["per_group_logs"][group] = {"present": False}
    report_file = copy / REPORT
    result["final_report_present"] = file_ok(report_file)
    if not file_ok(report_file):
        result["reason"] = (
            "There is no final six-group report. This may be a previous "
            "interrupted run OR a currently running foamPostProcess. Do not "
            "delete it, assume failure, resume it, or use it as a new target."
        )
        return result
    try:
        prior = read_json(report_file)
    except (OSError, ValueError, TypeError) as exc:
        result["reason"] = "Final report unreadable/incomplete: " + str(exc)[:500]
        return result
    result["report"] = str(report_file)
    result["report_sha256"] = sha(report_file)
    identity = prior.get("source_authentication")
    groups = prior.get("native_groups")
    if (prior.get("schema") !=
            "C3D04_A_C14_F14_SOLVER_BACKED_OFFLINE_RECOVERY_V1"
        or not isinstance(identity, dict)
        or not isinstance(groups, list)
        or prior.get("isolated_new_workcopy") != str(copy)
        or identity.get("case") != str(case)):
        result["reason"] = "Final report has unexpected schema/case/copy identity."
        return result
    current = {
        "original_10s_solver_log_sha256":
            sha(log_source) if file_ok(log_source) else None,
        "original_C14_controlDict_sha256":
            sha(real_c14) if file_ok(real_c14) else None,
        "recovery_report_sha256":
            sha(recovery / "C3D04_A_STAGE07_RECOVERY_REPORT.json")
            if file_ok(recovery / "C3D04_A_STAGE07_RECOVERY_REPORT.json") else None,
        "forensic_report_sha256":
            sha(forensic_dir / "C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json")
            if file_ok(forensic_dir / "C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json")
            else None,
    }
    need_keys = tuple(current)
    if (not result["source_C14_controlDict_matches"] or
        not result["copy_10s_solver_log_SHA_matches"] or
        not all(current[k] and identity.get(k) == current[k] for k in need_keys)):
        result["reason"] = "The completed report's authenticated original source/hash provenance differs."
        return result
    seen = set()
    for item in groups:
        if not isinstance(item, dict):
            result["reason"] = "Malformed native group completion record."
            return result
        group = item.get("group")
        if group not in TASK_ORDER or group in seen:
            result["reason"] = "Duplicate or unexpected native group."
            return result
        seen.add(group)
        native_log = result["per_group_logs"][group]
        exit_code = item.get("exit_code")
        # Earlier V1 reports recorded OS return code only. New six-group
        # reports persist the fatal-log semantic gate as well. Authenticate
        # the matching log before accepting either version.
        has_new_semantics = isinstance(item.get("foam_fatal_present"), bool)
        expected_pass = (exit_code == 0) if isinstance(exit_code, int) else False
        actual_fatal = fatal_openfoam_log(
            copy / ("log.C14_3D_postprocess_solverBacked_" + group)
        ) if native_log.get("present") else {"foam_fatal_present": False}
        if has_new_semantics:
            expected_pass = expected_pass and not actual_fatal["foam_fatal_present"]
        if (not native_log.get("present") or
            item.get("log_sha256") != native_log.get("sha256") or
            not isinstance(exit_code, int) or isinstance(exit_code, bool) or
            (has_new_semantics and
             item["foam_fatal_present"] is not actual_fatal["foam_fatal_present"]) or
            item.get("passed") is not expected_pass or
            item.get("log") !=
                "log.C14_3D_postprocess_solverBacked_" + group):
            result["reason"] = (
                "Native group exit/log provenance missing or changed: " + group
            )
            return result
    if seen != set(TASK_ORDER):
        result["reason"] = "Only some native groups were recorded in final report."
        return result
    declared_passed = [x["group"] for x in groups if x["passed"]]
    declared_failed = [x["group"] for x in groups if not x["passed"]]
    if (prior.get("native_groups_passed") != declared_passed or
        prior.get("native_groups_failed") != declared_failed):
        result["reason"] = "Native passed/failed rollups contradict recorded group status."
        return result
    semantic = {}
    for item in groups:
        group = item["group"]
        signal = fatal_openfoam_log(
            copy / ("log.C14_3D_postprocess_solverBacked_" + group))
        semantic[group] = {
            "original_report_passed": item["passed"],
            "os_exit_code": item["exit_code"],
            "semantically_passed": item["exit_code"] == 0 and not signal["foam_fatal_present"],
            **signal,
        }
    groups_passed = [g for g in TASK_ORDER if semantic[g]["semantically_passed"]]
    groups_failed = [g for g in TASK_ORDER if not semantic[g]["semantically_passed"]]
    false_positive = any(
        x["original_report_passed"] and not x["semantically_passed"]
        for x in semantic.values()
    )
    profile_check=primitive_profile_coverage(copy)
    valid_profiles=[k for k,v in profile_check.items() if v.get("status")=="PASS"]
    profile_coverage_complete=(len(valid_profiles)==len(profile_check)==4)
    power_coverage=native_surface_table_coverage(copy)
    power_series_count=[v.get("numeric_data_row_count",0)
                        for v in power_coverage.values()]
    power_series_complete=(len(power_series_count)==3 and
                           all(count in (100,101) for count in power_series_count)
                           and len(set(power_series_count))==1)
    result.update({
        "read_only_existing_native_surface_table_coverage":power_coverage,
        "read_only_existing_primitive_profile_coverage":profile_check,
        "primitive_80point_profiles_valid_count":len(valid_profiles),
        "primitive_80point_profiles_requested_count":len(profile_check),
        "primitive_80point_profiles_complete":profile_coverage_complete,
        "energy_native_three_face_power_series_100_or_101_rows_present":
            power_series_complete,
        "stage07_native_scientific_data_complete":(
            profile_coverage_complete and power_series_complete and
            all(semantic[g]["semantically_passed"] for g in TASK_ORDER)),
        "native_group_pass_only_certifies_no_FOAM_FATAL_not_field_completeness":True,
        "status": (
            "EXISTING_COMPLETE_REPORT_WITH_NATIVE_FATALS_PRESERVED"
            if false_positive else
            "EXISTING_COMPLETE_NATIVE_POSTPROCESS_REPORT_REUSED_NO_NEW_RUN"
        ),
        "original_report_groups_passed_by_exit_code_only": declared_passed,
        "semantic_group_results": semantic,
        "prior_report_false_positive_success_detected": false_positive,
        "final_report_sha_verified": True,
        "native_groups_passed": groups_passed,
        "native_groups_failed": groups_failed,
        "surface_energy": prior.get("surface_energy"),
        "native_validation_verified": False,
        "reason": (
            "The original six-log and report SHA identities match. "
            "Native FOAM FATAL markers override any exit-code-only PASS; "
            "no source/workcopy changes or CFD occurred. "
            "This is NOT physical/global energy validation."
        ),
    })
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    p.add_argument("--failed-copy",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01")
    p.add_argument("--recovery",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01")
    p.add_argument("--forensic",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_NATIVE_STAGE07_FORENSICS_01")
    p.add_argument("--out",type=Path,default=Path.home()/("OpenFOAM/"+OUTPUT))
    opt=p.parse_args()
    source=opt.case.expanduser().resolve()
    out=opt.out.expanduser().absolute()
    try:
        if out.exists() or out.is_symlink():
            observed = inspect_occupied_copy(
                source,out,opt.recovery,opt.forensic)
            print(json.dumps(observed, indent=2, ensure_ascii=False))
            # A partial/in-progress output must NOT be called a completed run.
            return 0 if observed["status"].startswith("EXISTING_COMPLETE") else 3
        identity = original_case_gate(
            source,opt.failed_copy,opt.recovery,opt.forensic,out)
        # Any failure from this point forward touches only the new copy.
        shutil.copytree(source,out,symlinks=False)
        zone_meta=verify_or_add_metal_zone_in_new_copy(source,out)
        prior=out/"postProcessing"
        if prior.exists():
            need(not (out/"_original_postProcessing_preserved").exists(),
                 "new copy already contains reserved postprocessing archive")
            prior.rename(out/"_original_postProcessing_preserved")
        centres=old.cell_centres(out)
        geometry=old.sample_geometry(centres)
        original_fo_hashes=old.adapt_diagnostic_files(out,geometry)
        need(sha(out/"system/controlDict")==
             identity["original_C14_controlDict_sha256"],
             "C14 original controlDict changed during isolated copying")
        need(sha(out/"log.foamMultiRun") ==
             identity["original_10s_solver_log_sha256"],
             "C14 original solver log changed during isolated copying")
        steps=[]
        dict_audit={}
        for group in TASK_ORDER:
            dictionary, provenance = assembled_dict(out,group)
            dict_audit[group]={
                "path":str(dictionary.relative_to(out)),
                "sha256":sha(dictionary),"objects":provenance}
            # A failed stage never blocks other independent stage executions.
            steps.append(native_group(out,group,dictionary))
        energy_result=surface_energy_summary(out)
        final={
            "schema":"C3D04_A_C14_F14_SOLVER_BACKED_OFFLINE_RECOVERY_V1",
            "date_utc":datetime.now(timezone.utc).isoformat(),
            "source_authentication":identity,
            "original_C14_postprocess_source_hashes":original_fo_hashes,
            "isolated_new_workcopy":str(out),
            "geometry_sampling":geometry,
            "metal_cellZone_copy_only_recovery":zone_meta,
            "group_dictionary_SHA256":dict_audit,
            "native_groups":steps,
            "native_groups_passed":[s["group"] for s in steps if s["passed"]],
            "native_groups_failed":[s["group"] for s in steps if not s["passed"]],
            "surface_energy":energy_result,
            "native_surface_table_coverage":native_surface_table_coverage(out),
            "primitive_profile_coverage_at_10s":primitive_profile_coverage(out),
            "native_energy_group_without_fatal":
                any(x["group"]=="energy" and x["passed"] for x in steps),
            "original_solver_reexecuted":False,
            "original_CFD_mesh_changed":False,
            "new_copy_cellZone_metadata_added":zone_meta["added_to_copy_only"],
            "new_copy_mesh_geometry_connectivity_changed":False,
            "original_C14_physics_or_controlDict_changed":False,
            "other_A_old_workcopy_B_FS_modified":False,
            "in_run_ddt_fields_recovered":False,
            "in_run_0_001s_probe_10001_history_recovered":False,
            "full_C14_2D_parity_verified":False,
            "global_energy_conservation_verified":False,
            "quickcup_validated":False,
            "milestones_completed":"6/10","stage":"07/10",
            "scientific_limits":[
                "Foundation14 -solver fluid constructs fluid thermo/transport model for native postprocessing without advancing the CFD solver.",
                "Source C14 phase and cooling rates computed as ddt during the original 0.001s runtime cannot be reconstructed from 0.1s snapshots.",
                "Postprocessing only of pre-existing fields, not a CFD/mesh/time-step or experimental validation.",
                "Native face energy sums alone cannot validate global metal+mold heat balance or original latent source accounting.",
                "The offline profiles deliberately include only original primitive fields, not unavailable ddt/derived fields.",
                "Any coded/momentum group failure is isolated and remains visibly incomplete; no original C14 model terms were changed.",
            ],
        }
        target=out/REPORT
        target.write_text(json.dumps(final,indent=2,ensure_ascii=False)+"\n",
                          encoding="utf-8")
        print(json.dumps({
            "status":"NATIVE_SOLVER_BACKED_OFFLINE_ATTEMPT_PRESERVED",
            "new_copy":str(out),"solver_rerun":False,
            "groups_passed":final["native_groups_passed"],
            "groups_failed":final["native_groups_failed"],
            "original_C14_metal_cellZone":zone_meta,
            "failed_group_last_24_lines":{
                s["group"]:s["log_last_24_lines"] for s in steps if not s["passed"]},
            "native_energy_power":energy_result,
            "scientific_validation":False,
            "stage":"07/10","milestones_done":"6/10",
            "report":str(target),
        },indent=2,ensure_ascii=False))
        return 0  # Audit outcome: per-group PASS/FAIL is always in report.
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("C3D04_A_SOLVER_BACKED_RECOVERY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
