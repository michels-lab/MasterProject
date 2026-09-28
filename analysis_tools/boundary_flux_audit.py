#!/usr/bin/env python3
"""
Permanent impermeable-boundary / advective-energy audit for controlled B/C cases.

Purpose:
A wall intended to be impermeable (metalTop with U=slip) must not carry a
meaningful solver mass flux or advective energy flux. This diagnostic is the
permanent form of the alert that motivated V9.

OpenFOAM v14 definitions used by the cases:
  energyAdvectiveFlux = fvc::flux(alphaRhoPhi, hs)
  heatFlux             = magSf * q()
  energyFlux           = energyAdvectiveFlux + heatFlux

For the single-phase metal region alpha=1, alphaRhoPhi is the mass flux phi.
Thus each face's advective energy flux has units:
  (kg/s) * (J/kg) = W.

Outputs:
  analysis_results/boundary_flux_audit/case_boundary_flux_summary.csv
  analysis_results/boundary_flux_audit/summary.md

Screening flags are deliberately conservative and are NOT standalone physical
acceptance criteria:
  |integrated top advective energy| > 1e-6 J
  max |sum(phi)_metalTop| > 1e-12 kg/s
or direct phi diagnostic missing.
"""

from __future__ import annotations
import csv
import math
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"boundary_flux_audit"
OUT.mkdir(parents=True,exist_ok=True)

CASE_RE=re.compile(r"^[BC]\d")
E_ADV_SCREEN=1e-6
PHI_SCREEN=1e-12


def numeric_rows(path):
    out=[]
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines():
        s=line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            out.append([float(x) for x in s.split()])
        except ValueError:
            pass
    return out


def trapz(rows,col):
    if len(rows)<2:
        return float("nan")
    return sum(
        0.5*(rows[i][col]+rows[i-1][col])*(rows[i][0]-rows[i-1][0])
        for i in range(1,len(rows))
    )


def read_bc(case_dir):
    p=case_dir/"0"/"metal"/"p_rgh"
    u=case_dir/"0"/"metal"/"U"
    pt=p.read_text(errors="replace") if p.is_file() else ""
    ut=u.read_text(errors="replace") if u.is_file() else ""

    def patch_block(text,name):
        m=re.search(r"\b"+re.escape(name)+r"\s*\{([\s\S]*?)\n\s*\}",text)
        return m.group(1) if m else ""

    pb=patch_block(pt,"metalTop")
    ub=patch_block(ut,"metalTop")
    ptype=re.search(r"\btype\s+([^;]+);",pb)
    utype=re.search(r"\btype\s+([^;]+);",ub)
    return (
        ptype.group(1).strip() if ptype else "",
        utype.group(1).strip() if utype else "",
    )


cases=sorted(
    p for p in BASE.iterdir()
    if p.is_dir() and CASE_RE.match(p.name)
)

rows=[]
for c in cases:
    research=c/"system"/"researchDiagnostics"
    rtext=research.read_text(errors="replace") if research.is_file() else ""
    phi_configured="metalTopPhiSum" in rtext
    energy_configured="metalTopEnergyPower" in rtext and "energyAdvectiveFlux" in rtext

    top_energy=numeric_rows(
        c/"postProcessing"/"metal"/"metalTopEnergyPower"/"0"/"surfaceFieldValue.dat"
    )
    phi_rows=numeric_rows(
        c/"postProcessing"/"metal"/"metalTopPhiSum"/"0"/"surfaceFieldValue.dat"
    )

    Eadv=trapz(top_energy,1) if top_energy else float("nan")
    Ediff=trapz(top_energy,2) if top_energy else float("nan")
    Etot=trapz(top_energy,3) if top_energy and len(top_energy[0])>3 else float("nan")
    adv_fraction=(
        abs(Eadv)/(abs(Eadv)+abs(Ediff))
        if math.isfinite(Eadv) and math.isfinite(Ediff) and abs(Eadv)+abs(Ediff)>0
        else float("nan")
    )

    phi_max=max(abs(r[1]) for r in phi_rows) if phi_rows else float("nan")
    phi_final=phi_rows[-1][1] if phi_rows else float("nan")
    phi_integral=trapz(phi_rows,1) if phi_rows else float("nan")

    pbc,ubc=read_bc(c)

    flags=[]
    if not energy_configured:
        flags.append("TOP_ENERGY_DIAGNOSTIC_MISSING")
    if not phi_configured:
        flags.append("DIRECT_PHI_DIAGNOSTIC_MISSING")
    if math.isfinite(Eadv) and abs(Eadv)>E_ADV_SCREEN:
        flags.append("ADVECTIVE_ENERGY_PRESENT")
    if math.isfinite(phi_max) and phi_max>PHI_SCREEN:
        flags.append("NONZERO_TOP_MASS_FLUX")
    if ubc=="slip" and pbc!="fixedFluxPressure":
        flags.append("SLIP_WITH_NON_FIXEDFLUX_PRESSURE")

    rows.append({
        "case":c.name,
        "metalTop_U_type":ubc,
        "metalTop_p_rgh_type":pbc,
        "energyAdvectiveFlux_configured":energy_configured,
        "metalTopPhiSum_configured":phi_configured,
        "integrated_top_advective_energy_J":Eadv,
        "integrated_top_diffusive_energy_J":Ediff,
        "integrated_top_total_energy_J":Etot,
        "advective_fraction_abs":adv_fraction,
        "max_abs_sum_phi_kg_per_s":phi_max,
        "final_sum_phi_kg_per_s":phi_final,
        "time_integrated_signed_phi_kg":phi_integral,
        "screening_alert":";".join(flags) if flags else "NONE",
    })

if rows:
    with (OUT/"case_boundary_flux_summary.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def fmt(v,n=4):
    return "n/a" if not isinstance(v,(int,float)) or not math.isfinite(v) else f"{v:.{n}g}"

lines=[
    "# Impermeable-boundary / advective-energy audit",
    "",
    "This is the permanent form of the diagnostic that motivated V9.",
    "",
    "For an intended impermeable metalTop, two independent signals are reviewed:",
    "",
    "1. direct solver mass flux: sum(phi) over metalTop;",
    "2. advective sensible-enthalpy power: sum(energyAdvectiveFlux) over metalTop.",
    "",
    "The OpenFOAM v14 native function object computes energyAdvectiveFlux as",
    "fvc::flux(alphaRhoPhi, hs). Therefore a non-zero top advective-energy term",
    "is evidence that solver mass flux is carrying sensible enthalpy across the",
    "boundary; it is not conductive/radiative heat transfer.",
    "",
    "| case | U top | p_rgh top | Eadv top [J] | Ediff top [J] | |Eadv| share | max |sum(phi)| [kg/s] | alert |",
    "|---|---|---|---:|---:|---:|---:|---|",
]
for r in rows:
    lines.append(
        f"| {r['case']} | {r['metalTop_U_type']} | {r['metalTop_p_rgh_type']} | "
        f"{fmt(r['integrated_top_advective_energy_J'])} | "
        f"{fmt(r['integrated_top_diffusive_energy_J'])} | "
        f"{fmt(r['advective_fraction_abs'])} | "
        f"{fmt(r['max_abs_sum_phi_kg_per_s'])} | "
        f"{r['screening_alert']} |"
    )

lines += [
    "",
    "## Permanent review rule",
    "",
    "- An impermeable top is not accepted from U=slip alone.",
    "- Verify direct sum(phi) when available.",
    "- Verify top energyAdvectiveFlux independently.",
    "- Heat loss through heatFlux is allowed: impermeable does not mean adiabatic.",
    "- A non-zero advective term must be investigated before using the case as a physical baseline.",
    "- Historical cases without metalTopPhiSum remain analyzable through their stored energyAdvectiveFlux, but future cases must include both diagnostics.",
    "- Screening thresholds above are alarms only; final interpretation uses magnitudes, signs, boundary orientation, and comparison with diffusive heat transfer.",
    "",
]
(OUT/"summary.md").write_text("\n".join(lines)+"\n")
print((OUT/"summary.md").read_text())
