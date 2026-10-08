#!/usr/bin/env python3
"""Read-only configuration auditor: NOT a runtime or physics validation."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases_controlled_buoyancy"
OBJECTS = {
    "functions": ("temperatureProbe", "topFlow"),
    "researchDiagnostics": ("vorticityField", "flowTopology", "energyAdvectiveFlux",
        "heatFlux", "energyFlux", "metalTopPhiSum", "metalTopEnergyPower",
        "metalMoldEnergyPower", "metalBoundaryEnergyPower",
        "metalSensibleEnthalpy", "metalMeanLiquidFraction", "temperatureGradient",
        "densityGradient", "temperatureTimeDerivative",
        "liquidFractionTimeDerivative", "solidificationRate",
        "latentHeatField", "latentHeatRateDensity", "cellCourantNumber",
        "solidificationMeltingMomentumDiagnostics"),
    "lineProfiles": ("horizontalProfiles", "verticalProfiles"),
    "momentumPostProcessing": ("momentumMean", "momentumMax",
        "momentumHorizontalProfiles", "momentumVerticalProfiles")
}
DECLARATION = re.compile(r"(?m)^([A-Za-z][A-Za-z0-9_]*)\s*\n\s*\{\s*\n\s*type\s+([^\s;]+)\s*;")

def audit(case_name):
    case = CASES / case_name
    item = {"case":case_name, "configured_objects":{}, "errors":[], "warnings":[]}
    for filename, required in OBJECTS.items():
        path = case / "system" / filename
        if not path.is_file():
            item["errors"].append(f"Missing system/{filename}")
            continue
        data = path.read_text(encoding="utf-8")
        found = dict(DECLARATION.findall(data))
        item["configured_objects"][filename] = found
        for name in required:
            if name not in found:
                item["errors"].append(f"Missing {name} in {filename}")
        if filename == "functions":
            if "writeFields     true;" not in data or "operation       none;" not in data:
                item["errors"].append("topFlow per-face export configuration must be checked")
            for include in ('#include "researchDiagnostics"', '#include "lineProfiles"'):
                if include not in data:
                    item["errors"].append(f"Missing functions include {include}")
        if filename == "researchDiagnostics":
            if not re.search(r"solidificationMeltingMomentumDiagnostics\s*\n\{\s*\n\s*type\s+coded;",data):
                item["errors"].append("coded momentum diagnostic missing")
            mat = case / "constant/metal/fvModels"
            if mat.is_file():
                a = re.search(r"(?m)^\s*L\s+([0-9.eE+-]+)\s*;",mat.read_text())
                b = re.search(r"latentHeatField\s*\n\{[\s\S]*?\bvalue\s+([0-9.eE+-]+)\s*;",data)
                if a and b and abs(float(a.group(1)) - float(b.group(1))) > 1e-6:
                    item["errors"].append("Latent heat differs between fvModels and diagnostics")
                elif not a or not b:
                    item["warnings"].append("Latent heat could not be cross-checked")
    guide = ROOT / "POSTPROCESSING_FIELD_GUIDE_ES.md"
    if not guide.is_file():
        item["errors"].append("Postprocessing field guide missing")
    else:
        docs = guide.read_text(encoding="utf-8")
        documented = set()
        for declared in item["configured_objects"].values():
            for name in declared:
                if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", docs):
                    documented.add(name)
                else:
                    item["errors"].append(f"Undocumented function object: {name}")
        item["documented_function_objects"] = len(documented)
    control = case / "system/controlDict"
    if control.is_file():
        t = control.read_text()
        if "application     foamMultiRun;" not in t:
            item["warnings"].append("Confirm exact solver application and configuration")
    item["warnings"] += [
        "Checking dictionary declarations does not prove the functions executed.",
        "Net sum(phi) can hide cancelling face-wise flux: inspect topFlow.",
        "energyFlux includes energyAdvectiveFlux and heatFlux; do not double count.",
        "ddt fields depend on solver time history and must not be fabricated retrospectively."
    ]
    return item

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--strict", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    items = [audit(n) for n in ("B14_topFixedFlux_explicitRef", "C14_topFixedFlux_explicitRef")]
    errors = [f"{x['case']}: {e}" for x in items for e in x["errors"]]
    for item in items:
        print(item["case"], "| objects:",sum(map(len,item["configured_objects"].values())))
        for issue in item["errors"]: print("ERROR:",issue)
        for warning in item["warnings"]: print("NOTE:",warning)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"time_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"V14 config-only", "items":items, "errors":errors},indent=2)+"\n")
    print("Static configuration:", "FAIL" if errors else "PASS")
    return int(bool(args.strict and errors))

if __name__ == "__main__":
    raise SystemExit(main())
