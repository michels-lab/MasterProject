#!/usr/bin/env python3
"""Case B/3D: strict per-face interface q from native Foundation14 solid model.

Source: isotropicSolidThermophysicalTransport::q = -kappa*snGrad(T).
Pairs conformal mappedWall faces GEOMETRICALLY, never by assumed list index.
Actual native C++ compile/run is mandatory to produce data; synthetic CI is not CFD.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from decimal import Decimal, InvalidOperation
from itertools import product
import hashlib
import json
import math
from pathlib import Path

HEADER = ["time_s", "face_local", "center_x_m", "center_y_m", "center_z_m",
          "area_m2", "normal_x", "normal_y", "normal_z", "q_out_W_m2"]
FACES_PER_PATCH = 12636
CENTER_TOL_M = 1e-7   # GEOMETRIC MATCH TOLERANCE ONLY; NOT THERMAL ACCURACY
AREA_REL_TOL = 0.001  # GEOMETRIC CONSISTENCY ONLY
NORMAL_DOT_MAX = -0.995  # outward face normals must be opposed

# Native F14 extractor prints "%.17g" (binary64 round-trip); the volume
# energy postprocessor serializes numeric times as short JSON floats.
# Only reconcile FLOAT REPRESENTATION noise. No missing/extra times and no
# interpolation, resampling or physical time-grid tolerance is permitted.
TIME_ROUNDTRIP_MAX_ABS_TOL_S = Decimal("1e-12")


def align_native_energy_times(flux_times: set, energy_history: list[dict]) -> tuple[dict, Decimal, Decimal]:
    """Strict one-to-one sorted time match under bounded binary64 formatting noise."""
    if not isinstance(energy_history, list):
        raise ValueError("Native volume-energy history missing")
    energy_rows = {}
    for row in energy_history:
        if not isinstance(row, dict) or type(row.get("time_s")) not in (int, float):
            raise ValueError("Invalid native volume-energy time entry")
        numeric = row["time_s"]
        if not math.isfinite(numeric):
            raise ValueError("Nonfinite native volume-energy time entry")
        t = Decimal(str(numeric))
        if t in energy_rows:
            raise ValueError("Duplicate energy time: cannot pair native flux")
        energy_rows[t] = row
    ft, et = sorted(flux_times), sorted(energy_rows)
    if len(ft) != len(et) or len(ft) < 2:
        raise ValueError(
            f"Native face flux times do not match volumetric energy times: "
            f"flux_samples={len(ft)} energy_samples={len(et)}"
        )
    if any(not t.is_finite() for t in ft):
        raise ValueError("Nonfinite native flux time")
    # A narrower bound relative to the minimum recorded sample interval
    # prevents the tolerance from merging distinct very close time steps.
    gaps = [b-a for times in (ft, et) for a, b in zip(times, times[1:])]
    if not gaps or min(gaps) <= 0:
        raise ValueError("Native time samples not strictly increasing")
    tolerance = min(TIME_ROUNDTRIP_MAX_ABS_TOL_S, min(gaps)/Decimal(10))
    aligned = {}
    max_delta = Decimal(0)
    for flux_time, energy_time in zip(ft, et):
        delta = abs(flux_time-energy_time)
        if delta > tolerance:
            raise ValueError(
                "Native face flux times do not match volumetric energy times: "
                f"flux_t={flux_time} energy_t={energy_time} "
                f"delta_s={delta} permissible_roundtrip_s={tolerance}; "
                "no interpolation or time substitution"
            )
        aligned[flux_time] = energy_rows[energy_time]
        max_delta = max(max_delta, delta)
    return aligned, max_delta, tolerance



def parse_csv(path: Path, expected_faces: int = FACES_PER_PATCH):
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Native q data missing or untrusted: {path}")
    out = defaultdict(dict)
    with path.open(newline="", encoding="utf-8") as stream:
        rdr = csv.DictReader(stream)
        if rdr.fieldnames != HEADER:
            raise ValueError("Native face flux CSV has wrong header; fail closed")
        for row in rdr:
            try:
                t = Decimal(row["time_s"])
                label = int(row["face_local"])
                xyz = tuple(float(row[x]) for x in ("center_x_m","center_y_m","center_z_m"))
                area = float(row["area_m2"])
                n = tuple(float(row[x]) for x in ("normal_x","normal_y","normal_z"))
                q = float(row["q_out_W_m2"])
            except (ValueError, TypeError, InvalidOperation) as exc:
                raise ValueError("Invalid numeric native face row") from exc
            if not t.is_finite() or t < 0 or label < 0:
                raise ValueError("Negative/nonfinite time or face index")
            if label in out[t]:
                raise ValueError(f"Duplicate face {label} at {t}")
            if not all(math.isfinite(x) for x in (*xyz, *n, area, q)) or area <= 0:
                raise ValueError("Nonfinite geometry/flux or invalid face area")
            norm = math.sqrt(sum(x*x for x in n))
            if abs(norm-1) > 1e-8:
                raise ValueError("Native face outward normal not unit length")
            out[t][label] = {"center":xyz,"area":area,"normal":n,"q":q}
    if len(out) < 2:
        raise ValueError("Native interface flux has insufficient temporal samples")
    keys = sorted(out)
    if keys[0] != 0:
        raise ValueError("Native interface flux missing initial t=0 data")
    for t, faces in out.items():
        if len(faces) != expected_faces or set(faces) != set(range(expected_faces)):
            raise ValueError(f"Native patch face coverage invalid at {t}: expected {expected_faces}")
    # A transient thermal simulation cannot change accepted mesh face geometry.
    origin = out[keys[0]]
    for t in keys[1:]:
        for faceid, row in out[t].items():
            first = origin[faceid]
            if row["center"] != first["center"] or row["area"] != first["area"] or row["normal"] != first["normal"]:
                raise ValueError("Moving/reordered native interface mesh: cannot pair")
    return dict(out)


def key_xyz(point: tuple[float, float, float], tol: float = CENTER_TOL_M):
    return tuple(math.floor(x/tol) for x in point)


def face_pairs(metal: dict, mold: dict, tol: float = CENTER_TOL_M):
    """One-to-one geometrical match, 27 spatial bins per metal face, fail ambiguous."""
    if len(metal) != len(mold):
        raise ValueError("Different native interface face counts")
    buckets = defaultdict(list)
    for j, r in mold.items():
        buckets[key_xyz(r["center"],tol)].append(j)
    pairs, claimed = [], set()
    for i in sorted(metal):
        a = metal[i]
        k = key_xyz(a["center"],tol)
        candidates = []
        for offset in product((-1,0,1),repeat=3):
            for j in buckets.get(tuple(k[d]+offset[d] for d in range(3)),()):
                b = mold[j]
                dist = math.sqrt(sum((x-y)**2 for x,y in zip(a["center"],b["center"])))
                if dist <= tol:
                    candidates.append((j,dist))
        if len(candidates) != 1:
            raise ValueError(f"Ambiguous/missing reciprocal native face {i}: candidates={len(candidates)}")
        j,dist = candidates[0]
        if j in claimed:
            raise ValueError(f"Reciprocal native face {j} paired multiple times")
        claimed.add(j)
        b=mold[j]
        if abs(a["area"]-b["area"])/max(a["area"],b["area"]) > AREA_REL_TOL:
            raise ValueError(f"Face-pair area mismatch {i}/{j}")
        dot=sum(u*v for u,v in zip(a["normal"],b["normal"]))
        if dot > NORMAL_DOT_MAX:
            raise ValueError(f"Face-pair normals not opposed {i}/{j}: dot={dot}")
        pairs.append((i,j))
    if len(claimed)!=len(mold):
        raise ValueError("Unmatched native mold interface faces")
    return pairs


def compare(metal, mold, energy: dict, end_time: float, expected_faces: int=FACES_PER_PATCH):
    tm,td=set(metal),set(mold)
    if tm != td:
        raise ValueError("Metal/mold native face-flux time sets differ")
    if abs(float(max(tm))-end_time)>max(1e-10,end_time*1e-7):
        raise ValueError("Native flux did not reach configured endTime")
    first=min(tm)
    pairs=face_pairs(metal[first],mold[first])
    if len(pairs)!=expected_faces:
        raise ValueError("Native paired face count mismatch")
    energy_rows, max_roundtrip_delta_s, time_roundtrip_bound_s = align_native_energy_times(
        tm, energy["history"]
    )
    series=[]
    old=None
    old_native_time=None
    for t in sorted(tm):
        mr=metal[t];dr=mold[t]
        gross=0.;signed_m=0.;signed_d=0.;abs_pair_mismatch=0.
        biggest_face_imbalance=0.
        for i,j in pairs:
            m=mr[i];d=dr[j]
            # Confirm fixed accepted geometry on each side for every written time.
            flux_m=m["q"]*m["area"]
            flux_d=d["q"]*d["area"]
            signed_m+=flux_m
            signed_d+=flux_d
            gross+=0.5*(abs(flux_m)+abs(flux_d))
            mismatch=abs(flux_m+flux_d)
            abs_pair_mismatch+=mismatch
            biggest_face_imbalance=max(biggest_face_imbalance,mismatch)
        err=signed_m+signed_d
        row={
            "time_s":float(t),
            "metal_total_outward_W":signed_m,
            "mold_total_outward_W":signed_d,
            "net_outward_interface_W":err,
            "pairwise_abs_flux_mismatch_W":abs_pair_mismatch,
            "max_abs_single_pair_mismatch_W":biggest_face_imbalance,
            "relative_net_mismatch_over_gross_flux":abs(err)/gross if gross else None,
            "relative_pairwise_mismatch_over_gross_flux":abs_pair_mismatch/gross if gross else None,
            "gross_flux_scale_W":gross
        }
        if old is not None:
            dt=row["time_s"]-old["time_s"]
            if dt<=0:raise ValueError("nonmonotonic native face time")
            # Discrete written-time trapezoidal patch-energy integral is a
            # diagnostic approximation, not an exact finite-volume time integral.
            dm=energy_rows[t]["metal_sensible_energy_J"]-energy_rows[old_native_time]["metal_sensible_energy_J"]
            dd=energy_rows[t]["mold_sensible_energy_J"]-energy_rows[old_native_time]["mold_sensible_energy_J"]
            trapez_m=0.5*(signed_m+old["metal_total_outward_W"])*dt
            trapez_d=0.5*(signed_d+old["mold_total_outward_W"])*dt
            row["metal_energy_change_plus_patch_flux_trapezoid_J"]=dm+trapez_m
            row["mold_energy_change_plus_patch_flux_trapezoid_J"]=dd+trapez_d
            row["interface_flux_integral_sum_trapezoid_J"]=trapez_m+trapez_d
        series.append(row)
        old=row
        old_native_time=t
    return {
        "status":"NATIVE_PATCH_Q_FACE_PAIR_DIAGNOSTICS_NO_ACCEPTANCE_THRESHOLD",
        "patch_names":{"metal":"metal_to_mold","mold":"mold_to_metal"},
        "faces_paired_per_side":len(pairs),
        "source_method":"Foundation14 solid/isotropic q()=-kappa*snGrad(T), evaluated at each saved region time",
        "geometric_match_tolerance_m":CENTER_TOL_M,
        "geometric_area_relative_tolerance":AREA_REL_TOL,
        "geometry_reciprocity_checked":True,
        "time_alignment_method":"one-to-one chronological native flux/volume-energy match; binary64 decimal round-trip only; NO interpolation",
        "max_time_roundtrip_difference_s":float(max_roundtrip_delta_s),
        "max_permitted_time_roundtrip_difference_s":float(time_roundtrip_bound_s),
        "direct_patch_normal_heat_flux_observed":True,
        "patch_flux_continuity_numerically_accepted":False,
        "experimental_validation":False,
        "physical_material_provenance_jmatpro_verified":False,
        "note":"Outputs are native heat-flux diagnostics; acceptance needs convergence, sensitivity and scientific tolerances; trapezoidal time integral is approximate",
        "history":series
    }


def exclusive(path:Path, data:dict):
    content=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if path.exists() or path.is_symlink():
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8")==content:
            return "FACE_Q_ALREADY_REPORTED_IDENTICAL"
        raise FileExistsError(f"Preserving pre-existing flux report: {path}")
    with path.open("x",encoding="utf-8") as handle:
        handle.write(content)
    return "NATIVE_FACE_Q_DIAGNOSTICS_WRITTEN_NO_VALIDATION"


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metal",type=Path,required=True)
    ap.add_argument("--mold",type=Path,required=True)
    ap.add_argument("--energy",type=Path,required=True)
    ap.add_argument("--inputs",type=Path,required=True)
    ap.add_argument("--run-status",type=Path,required=True)
    ap.add_argument("--solver-log",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    # Native solver verification is reused, not reimplemented differently.
    import importlib.util
    driver=Path(__file__).with_name("postprocess_t0_energy.py")
    spec=importlib.util.spec_from_file_location("case_b_energy_post_driver",driver)
    if spec is None or spec.loader is None: raise ValueError("Energy provenance checker missing")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inputbytes=args.inputs.read_bytes()
    module.verify_solver_attempt(args.solver_log,args.run_status,inputbytes)
    cfg=json.loads(inputbytes)
    for path in (args.metal,args.mold,args.energy):
        if path.is_symlink(): raise ValueError("Symlink native evidence not trusted: "+str(path))
    ebytes=args.energy.read_bytes()
    energy=json.loads(ebytes)
    if energy.get("status")!="OBSERVED_NATIVE_VOLUMETRIC_ENERGY_METRICS_NOT_PHYSICAL_VALIDATION":
        raise ValueError("No preceding native volume energy verification")
    if energy.get("input_sha256")!=hashlib.sha256(inputbytes).hexdigest():
        raise ValueError("Prior energy input hash does not match")
    end=float(cfg["simulation"]["endTime_s"])
    m=parse_csv(args.metal)
    d=parse_csv(args.mold)
    report=compare(m,d,energy,end)
    report["source_sha256"]={
       "metal_face_csv":hashlib.sha256(args.metal.read_bytes()).hexdigest(),
       "mold_face_csv":hashlib.sha256(args.mold.read_bytes()).hexdigest(),
       "regional_energy_json":hashlib.sha256(ebytes).hexdigest(),
       "inputs_json":hashlib.sha256(inputbytes).hexdigest(),
       "solver_log":hashlib.sha256(args.solver_log.read_bytes()).hexdigest(),
    }
    print(exclusive(args.out,report))
    print("Paired",report["faces_paired_per_side"],"real native patch faces per side")
    print("NO PHYSICAL ACCEPTANCE OR ENERGY/FLUX CONVERGENCE CLAIMED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
