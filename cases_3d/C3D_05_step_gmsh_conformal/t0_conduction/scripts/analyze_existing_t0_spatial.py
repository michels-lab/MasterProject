#!/usr/bin/env python3
"""Case B C3D-05: read-only spatial interface flux postrun from REAL archived C14 T0.

Reads SHA-verified original native face CSV, regional-energy evidence and solver
audit; does NOT run foamMultiRun, alter the HEX8 mesh, invent JMatPro properties,
or claim convergence/experimental validation. Outputs an independent, immutable
axial q distribution plus last-time face-centre point cloud for ParaView.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import tempfile


HERE = Path(__file__).resolve().parent
OUTPUT_FILES = ("AXIAL_INTERFACE_Q_BY_TIME.csv", "FINAL_INTERFACE_FACE_CENTERS.csv",
                "T0_SPATIAL_INTERPRETATION.json")
AXIAL_HEADER = ("time_s", "band", "y_lo_mm", "y_hi_mm", "paired_faces",
                "paired_area_m2", "metal_outward_W", "mold_outward_W",
                "net_outward_W", "pairwise_abs_mismatch_W",
                "metal_area_mean_q_W_m2", "mold_area_mean_q_W_m2",
                "max_abs_metal_q_W_m2")
FACE_HEADER = ("time_s", "metal_face", "mold_face", "x_mm", "y_mm", "z_mm",
               "area_m2", "metal_outward_q_W_m2", "mold_outward_q_W_m2",
               "pairwise_abs_mismatch_W")
SCHEMA = "C3D05_B_NATIVE_Q_SPATIAL_BANDS_V1"


def load_code(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Missing source module: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or unsafe original evidence: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    sha(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON evidence object: " + str(path))
    return data


def relative_aggregate_ok(actual: float, expected: float, flux_scale: float) -> bool:
    """Only test reproducibility of sums, NOT physical heat-flux accuracy."""
    return math.isfinite(actual) and math.isfinite(expected) and (
        abs(actual - expected) <= 1e-9 * max(1.0, flux_scale)
    )


def spatialize(metal: dict, mold: dict, original: dict, paired: list,
               bands: int = 12) -> tuple[dict, list, list]:
    """Pure binning of native q by vertical Y; same preverified geometric pairs."""
    if type(bands) is not int or not 2 <= bands <= 200:
        raise ValueError("Band count must be an integer from 2 to 200")
    mt, dt = sorted(metal), sorted(mold)
    if mt != dt or len(mt) < 2 or mt[0] != 0:
        raise ValueError("Two-region native time samples invalid")
    rows = original.get("history")
    if not isinstance(rows, list) or len(rows) != len(mt):
        raise ValueError("Published native flux diagnostic time count differs")
    # Native %.17g versus JSON float: exact order and representation-only deltas.
    def aligned_time(t, row):
        if type(row.get("time_s")) not in (float, int):
            raise ValueError("Invalid native q timestamp")
        dt_s = abs(t - Decimal(str(row["time_s"])))
        if dt_s > Decimal("1e-12"):
            raise ValueError("Published flux diagnostics are not time aligned")
    for t, row in zip(mt, rows):
        aligned_time(t, row)
    if set(metal[mt[0]]) != {i for i, _ in paired}:
        raise ValueError("Face pair coverage incomplete")
    if set(mold[mt[0]]) != {j for _, j in paired}:
        raise ValueError("Mold face pair coverage incomplete")
    base = metal[mt[0]]
    low = min(v["center"][1] for v in base.values())
    high = max(v["center"][1] for v in base.values())
    if not all(math.isfinite(x) for x in (low, high)) or high <= low:
        raise ValueError("Cannot produce axial bands without a finite Y span")
    dy = (high-low)/bands
    members = [[] for _ in range(bands)]
    for i, j in paired:
        y = base[i]["center"][1]
        idx = min(bands - 1, max(0, int((y-low)/dy)))
        members[idx].append((i, j))
    output_bands, final_points = [], []
    per_t = []
    for it, t in enumerate(mt):
        m, d = metal[t], mold[t]
        observed = rows[it]
        all_m, all_d, all_pair, all_gross = [], [], [], []
        for b, pairs in enumerate(members):
            areas, powers_m, powers_d, mismatches, max_q = [], [], [], [], []
            for i, j in pairs:
                a, z = m[i], d[j]
                area = a["area"]
                wm = area * a["q"]
                wd = z["area"] * z["q"]
                areas.append(area)
                powers_m.append(wm)
                powers_d.append(wd)
                mismatches.append(abs(wm + wd))
                max_q.append(abs(a["q"]))
                if it == len(mt)-1:
                    x, y, zz = a["center"]
                    final_points.append((float(t), i, j, x*1000, y*1000,
                                         zz*1000, area, a["q"], z["q"],
                                         abs(wm+wd)))
            am, wm, wd = (math.fsum(areas), math.fsum(powers_m),
                          math.fsum(powers_d))
            local_mismatch = math.fsum(mismatches)
            all_m.extend(powers_m)
            all_d.extend(powers_d)
            all_pair.extend(mismatches)
            all_gross.extend(.5*(abs(x)+abs(y))
                             for x, y in zip(powers_m, powers_d))
            output_bands.append((float(t), b, (low+b*dy)*1000,
                                 (low+(b+1)*dy)*1000, len(pairs), am,
                                 wm, wd, wm+wd, local_mismatch,
                                 wm/am if am else None,
                                 wd/am if am else None,
                                 max(max_q) if max_q else None))
        gm, gd, gp, gross = (math.fsum(all_m), math.fsum(all_d),
                             math.fsum(all_pair), math.fsum(all_gross))
        for label, actual, expected in (
            ("metal_W", gm, observed.get("metal_total_outward_W")),
            ("mold_W", gd, observed.get("mold_total_outward_W")),
            ("pair_abs_mismatch_W", gp,
             observed.get("pairwise_abs_flux_mismatch_W")),
        ):
            if type(expected) not in (float, int) or not relative_aggregate_ok(
                    actual, float(expected), gross):
                raise ValueError(f"Spatial power sum is inconsistent with native q: {label} at t={t}")
        per_t.append({
            "time_s": float(t),
            "metal_outward_W": gm,
            "mold_outward_W": gd,
            "pairwise_abs_mismatch_W": gp,
            "gross_interface_power_scale_W": gross,
            "signed_net_interface_W": gm+gd,
            "max_band_abs_metal_q_W_m2": max(
                (x[12] for x in output_bands[-bands:] if x[12] is not None),
                default=0.0),
        })
    result = {
        "schema": SCHEMA,
        "status": "C14_REAL_NATIVE_INTERFACE_SPATIAL_DIAGNOSTICS_NO_PHYSICAL_VALIDATION",
        "case": "C3D_05_step_gmsh_conformal",
        "source_scope": "Two solids, archived C14 constant-property 0.1 s numerical T0; not casting physics",
        "axial_coordinate": "y", "axial_unit": "mm",
        "face_coordinate": "centre of native conformal metal interface face",
        "axial_band_count": bands,
        "axial_bounds_m": [low, high],
        "face_pairs_per_sample": len(paired),
        "temporal_samples": len(mt),
        "time_series": per_t,
        "limits": [
            "Outward normals define signs; metal/mold q are opposite orientations",
            "Face centres are point-cloud coordinates, NOT a reconstructed volume mesh",
            "Contact conservation does not prove thermal accuracy or grid independence",
            "High nonorthogonality, JMatPro, QuickCup and latent heat unvalidated",
            "Only the original C14 two-solid thermal reference was examined",
        ],
        "physically_accepted": False,
        "experimental_validation": False,
    }
    return result, output_bands, final_points


def verify_sources(case: Path, inputs: Path):
    """Reuse existing authoritative chain rather than trusting CSV alone."""
    if not case.is_dir() or case.is_symlink() or inputs.is_symlink():
        raise ValueError("Original case and C14 inputs must be safe directories/files")
    final = load_code(HERE/"finalize_t0_granada.py", "case_b_c14_final_for_spatial")
    fx = load_code(HERE/"analyze_t0_patch_flux.py", "case_b_c14_face_for_spatial")
    reviewed = case/"T0_NUMERICAL_RUN_STATUS_REVIEWED.json"
    status = reviewed if reviewed.is_file() and not reviewed.is_symlink() else None
    expected = final.summarize(case, inputs, status)
    existing = load_json(case/"T0_GRANADA_EVIDENCE_SUMMARY.json")
    if expected != existing:
        raise ValueError("Immutable C14 summary differs from freshly checked native SHA evidence")
    fluxdir = case/"T0_NATIVE_FACE_FLUX"
    flux = load_json(fluxdir/"bilateral_diagnostics.json")
    if flux.get("faces_paired_per_side") != 12636:
        raise ValueError("Source is not the real 12,636-pair accepted geometry")
    metal_path, mold_path = fluxdir/"metal.csv", fluxdir/"mold.csv"
    m = fx.parse_csv(metal_path)
    d = fx.parse_csv(mold_path)
    fx.align_native_energy_times(set(m), load_json(
        case/"T0_NATIVE_ENERGY_HISTORY.json")["history"])
    paired = fx.face_pairs(m[min(m)], d[min(d)])
    evidence = {
        "original_case_summary_sha256": sha(case/"T0_GRANADA_EVIDENCE_SUMMARY.json"),
        "original_native_flux_report_sha256": sha(fluxdir/"bilateral_diagnostics.json"),
        "original_metal_csv_sha256": sha(metal_path),
        "original_mold_csv_sha256": sha(mold_path),
        "original_regional_energy_sha256": sha(case/"T0_NATIVE_ENERGY_HISTORY.json"),
        "original_numerical_inputs_sha256": sha(inputs),
        "original_solver_log_sha256": sha(case/"log.foamMultiRun.C14_NUMERICAL_T0"),
    }
    return m, d, flux, paired, evidence


def write_table(path: Path, header: tuple, rows: list) -> None:
    with path.open("x", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def save_new(out: Path, report: dict, band_rows: list, face_rows: list):
    if out.is_symlink():
        raise ValueError("Refuse symlink spatial output")
    if out.exists():
        if not out.is_dir() or (out/"T0_SPATIAL_INTERPRETATION.json").is_symlink():
            raise ValueError("Unsafe prior spatial output")
        previous = load_json(out/"T0_SPATIAL_INTERPRETATION.json")
        if previous != report:
            raise FileExistsError("Existing spatial report differs: preserve prior result")
        manifest = load_json(out/"MANIFEST_SHA256.json")
        names = set(OUTPUT_FILES)
        if set(manifest) != names or any(
                manifest[name] != sha(out/name) for name in OUTPUT_FILES):
            raise ValueError("Existing spatial outputs differ from their immutable SHA manifest")
        return "SPATIAL_ALREADY_PRESENT_SHA_VERIFIED_NO_RECOMPUTE"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.parent.is_symlink():
        raise ValueError("Unsafe output parent")
    staging = Path(tempfile.mkdtemp(prefix=".C3D05_B_SPATIAL_STAGING_", dir=out.parent))
    # Preserve any failed stage for forensic review, never overwrite user data.
    write_table(staging/OUTPUT_FILES[0], AXIAL_HEADER, band_rows)
    write_table(staging/OUTPUT_FILES[1], FACE_HEADER, face_rows)
    (staging/OUTPUT_FILES[2]).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n",
        encoding="utf-8")
    manifest = {name: sha(staging/name) for name in OUTPUT_FILES}
    (staging/"MANIFEST_SHA256.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    if out.exists() or out.is_symlink():
        raise FileExistsError("Spatial destination appeared during analysis; stage preserved")
    os.rename(staging, out)
    return "C3D05_B_SPATIAL_NATIVE_Q_PUBLISHED_NOT_PHYSICALLY_ACCEPTED"


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--case", type=Path,
        default=Path.home()/"OpenFOAM/C3D05_T0_C14_SHK_01")
    cli.add_argument("--inputs", type=Path,
        default=Path.home()/"OpenFOAM/C3D05_T0_C14_NUMERICAL_INPUTS.json")
    cli.add_argument("--out", type=Path,
        default=Path.home()/"OpenFOAM/C3D05_B_T0_SPATIAL_DIAGNOSTICS_01")
    cli.add_argument("--bands", type=int, default=12)
    args = cli.parse_args()
    m, d, native, paired, evidence = verify_sources(
        args.case.expanduser().resolve(), args.inputs.expanduser().resolve())
    report, bands, face_points = spatialize(m, d, native, paired, args.bands)
    report["source_sha256"] = evidence
    print(save_new(args.out.expanduser(), report, bands, face_points))
    print("NATIVE_REAL_C3D05_HEX8_Q: faces_per_time=", len(paired),
          "times=", report["temporal_samples"],
          "vertical_bands=", report["axial_band_count"])
    for t in report["time_series"]:
        print("time_s=", t["time_s"], "metal_outward_W=", t["metal_outward_W"],
              "mold_outward_W=", t["mold_outward_W"],
              "peak_abs_interface_q_W_m2=", t["max_band_abs_metal_q_W_m2"])
    print("NO_SOLVER_NO_MESH_CHANGE_NO_JMATPRO_NO_EXPERIMENTAL_ACCEPTANCE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
