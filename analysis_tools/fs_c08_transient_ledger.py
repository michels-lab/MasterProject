"""Export native FS-C08 accepted-state ledgers, including partial runs.
No physical energy-validation claim. Values originate exclusively in CFD logs.
"""
from __future__ import annotations
import csv
import json
import math
import re
from pathlib import Path

MARKERS = {
    "FS_C08_ACCEPTED_STATE_LEDGER": "state",
    "FS_C08_LOCAL_ENERGY_LEDGER": "energy",
    "FS_C08_REAL_CFD_MASS_BUDGET": "budget",
    "FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY": "pressure",
}
REQUIRED = {
    "state": ("dt_s", "liquidMass_kg", "solidMass_kg", "independentGasMass_kg",
              "liquidVolume_m3", "solidVolume_m3", "gasVolume_m3", "domainVolume_m3",
              "previousMetalVolume_m3", "deltaMetalVolume_m3", "phaseVolumeRate_m3_s",
              "thermalVolumeRate_m3_s", "Tmin_K", "Tmax_K", "pMin_Pa", "pMax_Pa", "maxU_m_s"),
    "energy": ("maxAbsCellResidual_J_m3", "sumAbsCellResidual_J", "sumAbsCellTerms_J",
               "maxCellRelativeResidual"),
    "budget": ("liquidSolidMetalMass_kg", "previousMetalMass_kg", "nativeGasInventory_kg",
               "previousGasInventory_kg", "metalMassResidual_kg", "gasContinuityDefect_kg",
               "phaseResolvedInternalEnergy_J", "previousInternalEnergy_J",
               "totalInternalEnergyEquationBalance_J"),
    "pressure": ("gasEOSMismatch", "pressureVolumeEnergyIterationConverged"),
}

def extract(log: str) -> tuple[list[dict], list[str]]:
    by_time = {}
    issues = []
    for line in log.splitlines():
        for marker, kind in MARKERS.items():
            if marker not in line:
                continue
            entries = dict(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=([^\s]+)", line))
            try:
                t = float(entries["time_s"])
                values = {key: float(entries[key]) for key in REQUIRED[kind]}
                if t <= 0 or not math.isfinite(t) or not all(map(math.isfinite, values.values())):
                    raise ValueError("invalid numeric ledger")
            except (KeyError, ValueError) as exc:
                issues.append(f"{kind}: {exc}")
                continue
            row = by_time.setdefault(t, {"time_s": t, "kinds": set()})
            if kind in row["kinds"]:
                issues.append(f"duplicate {kind} at {t:g}")
            row["kinds"].add(kind)
            row.update(values)
    result = []
    prev = None
    for t, row in sorted(by_time.items()):
        missing = set(REQUIRED) - row.pop("kinds")
        row["all_native_ledgers_present"] = not missing
        if missing:
            issues.append(f"time {t:g}: missing {sorted(missing)}")
        else:
            metal_v = row["liquidVolume_m3"] + row["solidVolume_m3"]
            row["metalVolume_m3"] = metal_v
            row["solidMassFraction"] = row["solidMass_kg"] / max(1e-300, row["liquidMass_kg"] + row["solidMass_kg"])
            row["volumeClosure_m3"] = metal_v + row["gasVolume_m3"] - row["domainVolume_m3"]
            row["metalInventoryAgreement_kg"] = row["liquidMass_kg"] + row["solidMass_kg"] - row["liquidSolidMetalMass_kg"]
            row["gasInventoryAgreement_kg"] = row["independentGasMass_kg"] - row["nativeGasInventory_kg"]
            row["localEnergyRelativeL1"] = row["sumAbsCellResidual_J"] / max(1e-300, row["sumAbsCellTerms_J"])
            if prev is not None:
                row["metalHistoryMismatch_kg"] = row["previousMetalMass_kg"] - prev["liquidSolidMetalMass_kg"]
                row["gasHistoryMismatch_kg"] = row["previousGasInventory_kg"] - prev["nativeGasInventory_kg"]
                row["energyHistoryMismatch_J"] = row["previousInternalEnergy_J"] - prev["phaseResolvedInternalEnergy_J"]
                row["volumeHistoryMismatch_m3"] = row["previousMetalVolume_m3"] - prev["metalVolume_m3"]
            prev = row
        result.append(row)
    return result, issues

def write_transient_ledger(log: str, directory: Path) -> dict:
    rows, issues = extract(log)
    path = directory / "FS_C08_TRANSIENT_LEDGER.csv"
    columns = ["time_s"] + sorted({key for row in rows for key in row} - {"time_s"})
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    complete = [row for row in rows if row["all_native_ledgers_present"]]
    summary = {
        "csv": str(path),
        "recorded_times": len(rows),
        "complete_native_ledger_times": len(complete),
        "issues": issues,
        "last_complete_state": complete[-1] if complete else None,
        "global_energy_verified": False,
        "physical_shrinkage_validated": False,
    }
    (directory / "FS_C08_TRANSIENT_LEDGER.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = write_transient_ledger(
        args.log.read_text(encoding="utf-8", errors="replace"), args.output)
    print(json.dumps(report, indent=2, allow_nan=False))
