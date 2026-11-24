#!/usr/bin/env python3
"""FS-C08 conservative finite-volume reference (NO OpenFOAM CFD solver).

Exact finite-volume bookkeeping of liquid-metal, solid-metal and gas mass;
conservative donor-cell advection, equal/opposite phase-change Γ, sensible
and latent enthalpy, tabulated T-dependent metal density and heat capacity,
closed-cell gas pressure from ideal-gas EOS and volume displacement.

Gamma is an explicitly supplied closure, NOT calibrated or inferred from C14.
Internal/BC fluxes are also inputs, NOT solved from velocity/pressure.
Tests contain explicitly SYNTHETIC values; no JMatPro data is invented.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path
from typing import Any


def finite_positive(value: float, name: str, *, zero: bool = False) -> float:
    if not isinstance(value, (float, int)) or not math.isfinite(value) or (value < 0 if zero else value <= 0):
        raise ValueError(f"{name} must be finite and {'non-negative' if zero else 'positive'}")
    return float(value)


@dataclass(frozen=True)
class Curve:
    """Piecewise linear, no extrapolation. Tabulated SI property vs K."""
    points: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("Property curve requires >=2 T,value pairs")
        prev = -math.inf
        for t, y in self.points:
            finite_positive(t, "property temperature K")
            finite_positive(y, "property value")
            if t <= prev:
                raise ValueError("Property temperature knots must strictly increase")
            prev = t

    @property
    def lo(self) -> float:
        return self.points[0][0]

    @property
    def hi(self) -> float:
        return self.points[-1][0]

    def at(self, T: float) -> float:
        if not math.isfinite(T) or T < self.lo or T > self.hi:
            raise ValueError(f"Temperature {T}K outside property curve [{self.lo}, {self.hi}]K; no extrapolation")
        for (t0,v0),(t1,v1) in zip(self.points, self.points[1:]):
            if t0 <= T <= t1:
                return v0+(v1-v0)*(T-t0)/(t1-t0)
        raise AssertionError("Unreachable piecewise interpolation")

    def integral(self, T0: float, T1: float) -> float:
        """Exact trapezoidal integral of piecewise LINEAR cp(T): J/kg."""
        if T0 == T1:
            self.at(T0)
            return 0.0
        if T1 < T0:
            return -self.integral(T1,T0)
        self.at(T0)
        self.at(T1)
        knots=[T0]+[t for t,_ in self.points if T0<t<T1]+[T1]
        return math.fsum((b-a)*(self.at(a)+self.at(b))/2 for a,b in zip(knots,knots[1:]))


@dataclass(frozen=True)
class Thermo:
    rho_liquid: Curve             # kg / m^3
    rho_solid: Curve              # kg / m^3
    cp_liquid: Curve              # J / kg / K
    cp_solid: Curve               # J / kg / K
    cp_gas: Curve                 # J / kg / K
    latent_liquid_minus_solid_J_kg: float
    gas_R_J_kg_K: float
    T_reference_K: float
    provenance: str

    def __post_init__(self) -> None:
        finite_positive(self.latent_liquid_minus_solid_J_kg,"latent enthalpy J/kg")
        finite_positive(self.gas_R_J_kg_K,"gas R J/(kg K)")
        if not self.provenance or not isinstance(self.provenance,str):
            raise ValueError("Explicit material property provenance required")
        lo=max(c.lo for c in self.curves)
        hi=min(c.hi for c in self.curves)
        if lo>=hi:
            raise ValueError("All phase property curves must overlap in temperature")
        if not lo<=self.T_reference_K<=hi:
            raise ValueError("T_reference outside common curve temperature support")

    @property
    def curves(self) -> tuple[Curve,...]:
        return (self.rho_liquid,self.rho_solid,self.cp_liquid,self.cp_solid,self.cp_gas)

    @property
    def common_min_K(self) -> float:
        return max(c.lo for c in self.curves)

    @property
    def common_max_K(self) -> float:
        return min(c.hi for c in self.curves)

    def phase_h(self,phase:str,T:float) -> float:
        if phase=="liquid":
            return self.cp_liquid.integral(self.T_reference_K,T)+self.latent_liquid_minus_solid_J_kg
        if phase=="solid":
            return self.cp_solid.integral(self.T_reference_K,T)
        if phase=="gas":
            return self.cp_gas.integral(self.T_reference_K,T)
        raise ValueError("Unknown phase (liquid/solid/gas): "+str(phase))

    def density(self,phase:str,T:float) -> float:
        if phase=="liquid":return self.rho_liquid.at(T)
        if phase=="solid":return self.rho_solid.at(T)
        raise ValueError("Gas density is not a fixed curve; use gas EOS")


PHASES=("liquid","solid","gas")


@dataclass(frozen=True)
class Cell:
    V_m3: float
    m_liquid_kg: float
    m_solid_kg: float
    m_gas_kg: float
    T_K: float

    def __post_init__(self) -> None:
        finite_positive(self.V_m3,"cell V m3")
        for p in PHASES:
            finite_positive(getattr(self,f"m_{p}_kg"),f"cell {p} kg",zero=True)
        finite_positive(self.T_K,"cell T K")
        if self.m_liquid_kg+self.m_solid_kg+self.m_gas_kg<=0:
            raise ValueError("Empty mass cell; no internal energy or EOS closure")

    def mass(self,phase:str) -> float:
        if phase not in PHASES:raise ValueError("Unsupported phase")
        return getattr(self,f"m_{phase}_kg")


@dataclass(frozen=True)
class Face:
    left:int
    right:int
    liquid_kg_s:float=0.0
    solid_kg_s:float=0.0
    gas_kg_s:float=0.0
    heat_W:float=0.0            # positive left->right


@dataclass(frozen=True)
class Boundary:
    cell:int
    phase:str
    outward_kg_s:float         # positive leaves domain
    inflow_T_K:float|None=None  # necessary if outward_kg_s < 0


@dataclass(frozen=True)
class Step:
    dt_s:float
    gamma_kg_m3_s:tuple[float,...]    # + liquid -> solid, - melting
    faces:tuple[Face,...]=()
    boundaries:tuple[Boundary,...]=()
    external_heat_W:tuple[float,...]=()   # + heat entering domain per cell


@dataclass(frozen=True)
class CellDiagnostics:
    T_K:float
    V_liquid_m3:float
    V_solid_m3:float
    V_gas_m3:float
    pressure_gas_Pa:float|None
    E_J:float


def energy(cell:Cell,th:Thermo) -> float:
    return math.fsum(cell.mass(p)*th.phase_h(p,cell.T_K) for p in PHASES)


def geometry(cell:Cell,th:Thermo,*,vol_tolerance:float=1e-12) -> CellDiagnostics:
    Vliq=cell.m_liquid_kg/th.density("liquid",cell.T_K)
    Vsol=cell.m_solid_kg/th.density("solid",cell.T_K)
    Vair=cell.V_m3-Vliq-Vsol
    if Vair < -vol_tolerance*max(cell.V_m3,1e-15):
        raise ValueError(f"Volume overfill: metal {Vliq+Vsol} > cell {cell.V_m3}")
    if Vair<0:Vair=0.0  # only floating-point residual for diagnostic, no phase mass clipped
    if Vair==0 and cell.m_gas_kg>0:
        raise ValueError("Gas mass trapped at zero gas volume; pressure is undefined")
    pressure=(cell.m_gas_kg*th.gas_R_J_kg_K*cell.T_K/Vair if Vair>0 else None)
    return CellDiagnostics(cell.T_K,Vliq,Vsol,Vair,pressure,energy(cell,th))


def recover_T(masses:dict[str,float], target_E:float,th:Thermo, *, max_iter:int=110)->float:
    """Find T at a conserved total enthalpy; cp(T)>0 gives monotone E."""
    def E(T:float)->float:
        return math.fsum(masses[p]*th.phase_h(p,T) for p in PHASES)
    t0,t1=th.common_min_K,th.common_max_K
    e0,e1=E(t0),E(t1)
    tol=1e-10*max(1.0,abs(target_E),abs(e0),abs(e1))
    if target_E<e0-tol or target_E>e1+tol:
        raise ValueError("Enthalpy outside tabulated cp(T) temperature range")
    if abs(target_E-e0)<=tol:return t0
    if abs(target_E-e1)<=tol:return t1
    for _ in range(max_iter):
        t=(t0+t1)/2
        if E(t)<target_E:t0=t
        else:t1=t
    return (t0+t1)/2


def advance(cells:tuple[Cell,...],th:Thermo,step:Step)->dict[str,Any]:
    """Conservative explicit FV reference, not a discretized OpenFOAM solve.

    Outer BC mass flux positive outward. Face flux positive left->right.
    Convection uses upstream cell's phase enthalpy; heat positive into cell.
    Γ is mass/(cell volume*time). Solid may move if face solid_kg_s input.
    Report fails on phase negativity, metal overfill or invalid property range.
    """
    if not cells:
        raise ValueError("At least one finite-volume cell required")
    finite_positive(step.dt_s,"dt_s")
    n=len(cells)
    if len(step.gamma_kg_m3_s)!=n:
        raise ValueError("One Gamma for each native finite volume cell required")
    if step.external_heat_W and len(step.external_heat_W)!=n:
        raise ValueError("External heat vector length mismatch")
    for c in cells:geometry(c,th)
    dmass={p:[0.0]*n for p in PHASES}
    denergy=[step.dt_s*(step.external_heat_W[i] if step.external_heat_W else 0.0) for i in range(n)]
    for value in (*step.gamma_kg_m3_s, *[f.heat_W for f in step.faces],
                  *step.external_heat_W):
        if not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError("Gamma/heat must be finite")
    boundary_phase_masses={p:0.0 for p in PHASES}
    boundary_energy_out=0.0
    for f in step.faces:
        if not 0<=f.left<n or not 0<=f.right<n or f.left==f.right:
            raise ValueError("Internal face has invalid distinct cell indices")
        for p in PHASES:
            flow=getattr(f,f"{p}_kg_s")
            if not math.isfinite(flow):raise ValueError("Nonfinite face mass flux")
            moved=flow*step.dt_s
            dmass[p][f.left]-=moved
            dmass[p][f.right]+=moved
            donor=f.left if flow>=0 else f.right
            h=moved*th.phase_h(p,cells[donor].T_K)
            denergy[f.left]-=h
            denergy[f.right]+=h
        if not math.isfinite(f.heat_W):raise ValueError("Nonfinite internal heat flux")
        denergy[f.left]-=f.heat_W*step.dt_s
        denergy[f.right]+=f.heat_W*step.dt_s
    for b in step.boundaries:
        if not 0<=b.cell<n or b.phase not in PHASES or not math.isfinite(b.outward_kg_s):
            raise ValueError("Invalid boundary cell, phase or flux")
        massout=b.outward_kg_s*step.dt_s
        dmass[b.phase][b.cell]-=massout
        boundary_phase_masses[b.phase]+=massout
        if massout<0:
            if b.inflow_T_K is None:
                raise ValueError("Boundary inflow requires explicit incoming phase temperature K")
            donor_T=b.inflow_T_K
        else:
            donor_T=cells[b.cell].T_K
        phase_h=th.phase_h(b.phase,donor_T)
        denergy[b.cell]-=massout*phase_h
        boundary_energy_out+=massout*phase_h
    changed=[]
    diagnostics=[]
    transferred_mass=[]
    phase_residuals={p:[] for p in PHASES}
    for i,c in enumerate(cells):
        g=step.gamma_kg_m3_s[i]
        # Gamma per unit total finite-volume cell, not per phase volume.
        converted=g*c.V_m3*step.dt_s
        transferred_mass.append(converted)
        dmass["liquid"][i]-=converted
        dmass["solid"][i]+=converted
        final={p:c.mass(p)+dmass[p][i] for p in PHASES}
        for p in PHASES:
            scale=max(1.0,c.mass(p),abs(dmass[p][i]))
            if final[p] < -1e-12*scale:
                raise ValueError(f"Negative {p} mass in cell {i}; shrink dt/flux/Gamma")
            if final[p]<0:
                # Round-off remainders are rejected instead of silently
                # manufacturing a compensating mass or energy source.
                raise ValueError(f"Slightly negative {p} mass in cell {i}; no clipping")
            phase_residuals[p].append(final[p]-c.mass(p)-dmass[p][i])
        E_after=energy(c,th)+denergy[i]
        T_after=recover_T(final,E_after,th)
        new=Cell(c.V_m3,final["liquid"],final["solid"],final["gas"],T_after)
        diag=geometry(new,th)
        changed.append(new)
        diagnostics.append(diag)
    heat_external=step.dt_s*math.fsum(step.external_heat_W) if step.external_heat_W else 0.0
    Ebefore=math.fsum(energy(c,th) for c in cells)
    Eafter=math.fsum(d.E_J for d in diagnostics)
    mbefore={p:math.fsum(c.mass(p) for c in cells) for p in PHASES}
    mafter={p:math.fsum(c.mass(p) for c in changed) for p in PHASES}
    converted_all=math.fsum(transferred_mass)
    phase_residual={
        "liquid":mafter["liquid"]-mbefore["liquid"]+boundary_phase_masses["liquid"]+converted_all,
        "solid":mafter["solid"]-mbefore["solid"]+boundary_phase_masses["solid"]-converted_all,
        "gas":mafter["gas"]-mbefore["gas"]+boundary_phase_masses["gas"],
    }
    metal_residual=(mafter["liquid"]+mafter["solid"]-
                    mbefore["liquid"]-mbefore["solid"]+
                    boundary_phase_masses["liquid"]+boundary_phase_masses["solid"])
    energy_residual=Eafter-Ebefore-heat_external+boundary_energy_out
    metal_V_before=math.fsum(geometry(c,th).V_liquid_m3+geometry(c,th).V_solid_m3 for c in cells)
    metal_V_after=math.fsum(d.V_liquid_m3+d.V_solid_m3 for d in diagnostics)
    shrinkage_geometry_delta=metal_V_after-metal_V_before
    gross_conversion_volume_at_initial_T=math.fsum(
        exchanged*(1/th.rho_solid.at(c.T_K)-1/th.rho_liquid.at(c.T_K))
        for exchanged,c in zip(transferred_mass,cells)
    )
    return {
        "cells":changed,"diagnostics":diagnostics,
        "audit":{
            "phase_mass_initial_kg":mbefore,"phase_mass_final_kg":mafter,
            "outward_boundary_mass_kg":boundary_phase_masses,
            "solidification_mass_liquid_to_solid_kg":converted_all,
            "phase_mass_residual_kg":phase_residual,
            "metal_mass_residual_kg":metal_residual,
            "global_energy_initial_J":Ebefore,
            "global_energy_final_J":Eafter,
            "global_external_heat_input_J":heat_external,
            "global_boundary_advected_energy_out_J":boundary_energy_out,
            "global_energy_residual_J":energy_residual,
            "metal_volume_before_m3":metal_V_before,
            "metal_volume_after_m3":metal_V_after,
            "geometric_metal_volume_delta_m3":shrinkage_geometry_delta,
            "constant_initial_T_conversion_only_volume_delta_m3":gross_conversion_volume_at_initial_T,
            "pressure_velocity_and_interface_not_solved":True,
            "gamma_closure_not_derived":True,
            "material_properties_require_external_traced_input":True,
            "is_full_OpenFOAM_3D_CFD_solver":False,
        }
    }


def parse_curve(obj:Any,name:str)->Curve:
    if not isinstance(obj,list):raise ValueError(f"{name}: expected [[T_K,value],...] list")
    return Curve(tuple(tuple(map(float,p)) for p in obj))


def load_scenario(path:Path)->tuple[Thermo,tuple[Cell,...],Step,dict]:
    doc=json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema")!="masterproject-fs-c08-conservative-control-volume-v1":
        raise ValueError("Unsupported FS-C08 scenario schema")
    if doc.get("provenance") in (None, "", "JMatPro"):
        raise ValueError("Material provenance must be explicit and not pretend JMatPro")
    if doc.get("purpose") not in ("SYNTHETIC_TEST_ONLY","MEASURED_RESEARCH_INPUT"):
        raise ValueError("Scenario purpose must be explicitly synthetic or measured")
    t=doc["thermo"]
    thermo=Thermo(
        rho_liquid=parse_curve(t["rho_liquid_kg_m3"],"rho_liquid"),
        rho_solid=parse_curve(t["rho_solid_kg_m3"],"rho_solid"),
        cp_liquid=parse_curve(t["cp_liquid_J_kg_K"],"cp_liquid"),
        cp_solid=parse_curve(t["cp_solid_J_kg_K"],"cp_solid"),
        cp_gas=parse_curve(t["cp_gas_J_kg_K"],"cp_gas"),
        latent_liquid_minus_solid_J_kg=float(t["latent_liquid_minus_solid_J_kg"]),
        gas_R_J_kg_K=float(t["gas_R_J_kg_K"]),
        T_reference_K=float(t["T_reference_K"]),
        provenance=doc["provenance"],
    )
    cells=tuple(Cell(**c) for c in doc["cells"])
    st=doc["step"]
    step=Step(
        dt_s=float(st["dt_s"]),
        gamma_kg_m3_s=tuple(map(float,st["gamma_kg_m3_s"])),
        faces=tuple(Face(**a) for a in st.get("faces",[])),
        boundaries=tuple(Boundary(**a) for a in st.get("boundaries",[])),
        external_heat_W=tuple(map(float,st.get("external_heat_W",[]))),
    )
    return thermo,cells,step,doc


def printable(result:dict[str,Any],doc:dict)->dict[str,Any]:
    return {
        "schema":"masterproject-fs-c08-control-volume-result-v1",
        "case_purpose":doc["purpose"],
        "material_provenance":doc["provenance"],
        "result_cells":[vars(c) for c in result["cells"]],
        "result_eos_and_volumes":[vars(d) for d in result["diagnostics"]],
        "audit":result["audit"],
        "physical_3d_shrinkage_validated":False,
        "openfoam_14_solver_executed":False,
    }


def main(argv=None)->int:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("scenario",type=Path,help="Explicit synthetic or measured FS-C08 input JSON")
    args=a.parse_args(argv)
    try:
        thermo,cells,step,doc=load_scenario(args.scenario)
        print(json.dumps(printable(advance(cells,thermo,step),doc),indent=2,allow_nan=False))
        return 0
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
        a.exit(2,"FS-C08 CONSERVATIVE REFERENCE BLOCKED: "+str(e)+"\n")


if __name__=="__main__":
    raise SystemExit(main())
