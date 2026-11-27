"""Native FS-C08 velocity-equivalent diagnostics, not a force/PDE validation."""
from __future__ import annotations
import json
import math
import re
from pathlib import Path

PATTERN = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)=(\([^()]*\)|[^\s]+)")
VECTORS = ("HbyA_m_s", "pressureContribution_m_s", "gravitySurfaceContribution_m_s")
SCALARS = {
    "FS_C08_MOMENTUM_FORCE_SPLIT": ("speed_m_s", "alphaMetal", "maxTemporalFaceCorrection_m_s"),
    "FS_C08_MOMENTUM_CONSISTENCY": ("maxVelocityGap_m_s", "maxDirectPressureSpeed_m_s",
        "maxPureGasVelocityGap_m_s", "maxPureGasSpeed_m_s", "maxInternalFaceNormalGap_m_s"),
    "FS_C08_FRESH_MOMENTUM_DEFECT": ("maxVelocityEquivalentDefect_m_s", "maxPureGasDefect_m_s"),
    "FS_C08_ACCEPTED_EXTREME_CELL": ("alphaGas", "speed_m_s", "p_Pa", "pOld_Pa",
        "T_K", "Told_K", "storage_J_m3", "advectionOut_J_m3",
        "conductionOut_J_m3", "mechanicalWork_J_m3"),
}
STARTUP = {
    "FS_C08_STARTUP_PRESSURE_COMPONENT": ("dt_s", "dpAtMinCell_Pa", "minDp_Pa", "maxDp_Pa", "localResidual"),
    "FS_C08_STARTUP_PRESSURE_ATTRIBUTION": ("dt_s", "fullDpAtMinCell_Pa",
        "sumComponentDpAtMinCell_Pa", "maxResidualDecompositionError", "maxPressureSuperpositionError_Pa"),
    "FS_C08_STARTUP_COMPLIANCE_DIAGNOSTIC": ("dt_s", "bulkModulus_Pa",
        "dpAtOriginalMinCell_Pa", "minDp_Pa", "maxDp_Pa",
        "minLinearTrialPressure_Pa", "maxLinearizedVolumeDefect"),
}

def number(s):
    x=float(s)
    if not math.isfinite(x):
        raise ValueError("nonfinite diagnostic")
    return x

def vector(s):
    if not (s.startswith("(") and s.endswith(")")):
        raise ValueError("invalid vector syntax")
    v=[number(x) for x in s[1:-1].split()]
    if len(v)!=3:
        raise ValueError("invalid vector width")
    return v

def parse(log):
    records=[]
    startup=[]
    issues=[]
    seen=set()
    invalid=set()
    for i,line in enumerate(log.splitlines(),1):
        marker=next((m for m in (*SCALARS,*STARTUP) if m in line),None)
        if marker is None:
            continue
        pairs=PATTERN.findall(line)
        fields=dict(pairs)
        identity=None
        try:
            if len(fields)!=len(pairs):
                raise ValueError("duplicate key")
            if marker in STARTUP:
                values={k:number(fields[k]) for k in STARTUP[marker]}
                if values["dt_s"]<=0:
                    raise ValueError("invalid startup dt")
                # Native startup records have dt, not a physical time marker.
                startup.append(dict(line=i,marker=marker,source=fields.get("source"),
                    minDpCell=fields.get("minDpCell"),**values))
                continue
            t=number(fields["time_s"])
            if t<=0:
                raise ValueError("non-positive time")
            reason=fields.get("reason","")
            if marker=="FS_C08_ACCEPTED_EXTREME_CELL" and reason not in (
                    "maximumSpeed","maximumGasDominatedHeating"):
                raise ValueError("unknown extreme reason")
            identity=(marker,t,reason)
            if identity in seen:
                raise ValueError("duplicate diagnostic")
            seen.add(identity)
            values={k:number(fields[k]) for k in SCALARS[marker]}
            row=dict(line=i,marker=marker,time_s=t,reason=reason,
                     cell=fields.get("cell"),**values)
            if marker=="FS_C08_MOMENTUM_FORCE_SPLIT":
                for key in VECTORS:
                    row[key]=vector(fields[key])
                    row[key+"_norm"]=math.hypot(*row[key])
                summed=[sum(row[k][j] for k in VECTORS) for j in range(3)]
                row["frozen_direct_velocity_norm_m_s"]=math.hypot(*summed)
                row["direct_minus_accepted_speed_m_s"]=math.hypot(*summed)-row["speed_m_s"]
            if marker=="FS_C08_ACCEPTED_EXTREME_CELL":
                row["center_m"]=vector(fields["center_m"])
                row["deltaT_K"]=row["T_K"]-row["Told_K"]
            records.append(row)
        except (KeyError,ValueError,OverflowError) as exc:
            if identity is not None:
                invalid.add(identity)
            issues.append(f"line {i}: {marker}: {exc}")
    records=[r for r in records if (r["marker"],r["time_s"],r["reason"]) not in invalid]
    return {"diagnostic_records":records,"startup_records":startup,"issues":issues,
            "force_or_acceleration_validated":False,"physical_shrinkage_validated":False,
            "scope":"Velocity-equivalent terms, not forces; startup dt is not a timestamp. Records are not accepted-step certificates."}

def write_momentum_diagnostics(log,directory):
    result=parse(log)
    path=directory/"FS_C08_MOMENTUM_DIAGNOSTICS.json"
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return {"json":str(path),"diagnostic_records":len(result["diagnostic_records"]),
            "startup_records":len(result["startup_records"]),"issues":result["issues"],
            "force_or_acceleration_validated":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("log",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    print(json.dumps(write_momentum_diagnostics(a.log.read_text(encoding="utf-8"),a.output),indent=2))
