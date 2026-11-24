/* FS-C08: C++17 explicit finite-volume phase-mass and enthalpy step.
 * Uses the already verified ConservativePhaseExchange.H per control volume.
 * Internal face mass flows exactly cancel across their two neighbouring cells.
 * ALL thermophysical values and face rates are supplied by the caller.
 * No pressure-velocity solve, density(T), physical kinetics or moving interface.
 */
#ifndef MASTERPROJECT_FS_C08_CONSERVATIVE_PHASE_NETWORK_H
#define MASTERPROJECT_FS_C08_CONSERVATIVE_PHASE_NETWORK_H

#include "ConservativePhaseExchange.H"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>
#include <vector>

namespace MichelMasterProject::FS_C08
{
struct FVCell
{
    CellProps geometry;
    Masses mass;
    double T_K;
};

struct EnthalpyProperties
{
    double cpLiquid_J_kg_K;
    double cpSolid_J_kg_K;
    double cpGas_J_kg_K;
    double latentLiquidMinusSolid_J_kg;
    double Tref_K;
};

struct InternalMassFace
{
    std::size_t owner;
    std::size_t neighbour;
    OutwardMassFlux flowOwnerToNeighbour_kg_s;
    double heatOwnerToNeighbour_W=0.0;
};

struct NetworkStep
{
    double dt_s;
    std::vector<double> gamma_kg_m3_s;
    std::vector<InternalMassFace> internalFaces;
    std::vector<double> externalHeat_W;
};

struct NetworkResult
{
    std::vector<FVCell> next;
    double initialMetalMass_kg=0.0;
    double finalMetalMass_kg=0.0;
    double initialGasMass_kg=0.0;
    double finalGasMass_kg=0.0;
    double initialEnthalpy_J=0.0;
    double finalEnthalpy_J=0.0;
    double externalHeat_J=0.0;
    double totalGammaTransfer_kg=0.0;
    double metalVolumeChange_m3=0.0;
    double metalMassResidual_kg=0.0;
    double gasMassResidual_kg=0.0;
    double enthalpyResidual_J=0.0;
    double maxCellMassResidual_kg=0.0;
    double maxCellEnthalpyResidual_J=0.0;
};

inline void checkFinite(const double x, const char* name)
{
    if (!std::isfinite(x))
        throw std::domain_error(std::string(name)+" must be finite");
}

inline void validateEnthalpy(const EnthalpyProperties& p)
{
    for (const double x : {p.cpLiquid_J_kg_K, p.cpSolid_J_kg_K,
                            p.cpGas_J_kg_K})
    {
        if (!std::isfinite(x) || x<=0)
            throw std::domain_error("All three phase cp must be positive");
    }
    if (!std::isfinite(p.Tref_K) || p.Tref_K<=0 ||
        !std::isfinite(p.latentLiquidMinusSolid_J_kg) ||
        p.latentLiquidMinusSolid_J_kg<0)
        throw std::domain_error("Invalid enthalpy reference or latent heat");
}

inline double phaseSpecificEnthalpy(const EnthalpyProperties& p,
                                    const std::size_t phase, double T)
{
    checkFinite(T,"temperature");
    if (T<=0) throw std::domain_error("Temperature must be in Kelvin > 0");
    const double dT=T-p.Tref_K;
    if (phase==0) return p.cpLiquid_J_kg_K*dT+
                         p.latentLiquidMinusSolid_J_kg;
    if (phase==1) return p.cpSolid_J_kg_K*dT;
    if (phase==2) return p.cpGas_J_kg_K*dT;
    throw std::domain_error("Unknown phase index");
}

inline double cellEnthalpy(const FVCell& c,const EnthalpyProperties& p)
{
    return c.mass.liquid_kg*phaseSpecificEnthalpy(p,0,c.T_K)+
           c.mass.solid_kg*phaseSpecificEnthalpy(p,1,c.T_K)+
           c.mass.gas_kg*phaseSpecificEnthalpy(p,2,c.T_K);
}

inline NetworkResult advanceNetwork(
    const std::vector<FVCell>& cells,
    const EnthalpyProperties& thermo,
    const NetworkStep& step)
{
    validateEnthalpy(thermo);
    if (cells.empty()) throw std::domain_error("No finite-volume cells");
    if (!std::isfinite(step.dt_s) || step.dt_s<=0)
        throw std::domain_error("Network time step must be positive");
    const std::size_t n=cells.size();
    if (step.gamma_kg_m3_s.size()!=n ||
        (!step.externalHeat_W.empty() && step.externalHeat_W.size()!=n))
        throw std::domain_error("One Gamma and optional heat source per cell required");
    std::vector<OutwardMassFlux> outward(n);
    std::vector<double> outwardEnthalpy_W(n,0.0);
    NetworkResult result;
    result.next.reserve(n);
    for (std::size_t i=0;i<n;++i)
    {
        checkFinite(cells[i].T_K,"cell temperature");
        if (cells[i].T_K<=0) throw std::domain_error("T must be positive Kelvin");
        checkFinite(step.gamma_kg_m3_s[i],"Gamma cell");
        if (!step.externalHeat_W.empty())
            checkFinite(step.externalHeat_W[i],"external heat source");
        // Reuse the tested C++17 single-cell invariants at zero Gamma.
        (void)exchange(cells[i].mass,cells[i].geometry,step.dt_s,0.0,{});
        result.initialMetalMass_kg+=cells[i].mass.liquid_kg+
                                    cells[i].mass.solid_kg;
        result.initialGasMass_kg+=cells[i].mass.gas_kg;
        result.initialEnthalpy_J+=cellEnthalpy(cells[i],thermo);
    }
    for (const InternalMassFace& face : step.internalFaces)
    {
        if (face.owner>=n || face.neighbour>=n || face.owner==face.neighbour)
            throw std::domain_error("Invalid owner-neighbour internal face");
        const double f[3]={face.flowOwnerToNeighbour_kg_s.liquid_kg_s,
                           face.flowOwnerToNeighbour_kg_s.solid_kg_s,
                           face.flowOwnerToNeighbour_kg_s.gas_kg_s};
        double enthalpy_W=face.heatOwnerToNeighbour_W;
        checkFinite(enthalpy_W,"internal heat rate");
        for (std::size_t phase=0;phase<3;++phase)
        {
            checkFinite(f[phase],"phase mass flow on internal face");
            const FVCell& donor=(f[phase]>=0)?cells[face.owner]:
                                                 cells[face.neighbour];
            enthalpy_W+=f[phase]*
                       phaseSpecificEnthalpy(thermo,phase,donor.T_K);
        }
        OutwardMassFlux& a=outward[face.owner];
        OutwardMassFlux& b=outward[face.neighbour];
        a.liquid_kg_s+=f[0]; b.liquid_kg_s-=f[0];
        a.solid_kg_s+=f[1]; b.solid_kg_s-=f[1];
        a.gas_kg_s+=f[2]; b.gas_kg_s-=f[2];
        outwardEnthalpy_W[face.owner]+=enthalpy_W;
        outwardEnthalpy_W[face.neighbour]-=enthalpy_W;
    }
    for (std::size_t i=0;i<n;++i)
    {
        const auto update=exchange(
            cells[i].mass,cells[i].geometry,step.dt_s,
            step.gamma_kg_m3_s[i],outward[i]
        );
        const Masses& m=update.next;
        const double heatW=step.externalHeat_W.empty()?0.0:
                                                  step.externalHeat_W[i];
        const double targetH=cellEnthalpy(cells[i],thermo)+
                             step.dt_s*(heatW-outwardEnthalpy_W[i]);
        const double cpMass=m.liquid_kg*thermo.cpLiquid_J_kg_K+
                            m.solid_kg*thermo.cpSolid_J_kg_K+
                            m.gas_kg*thermo.cpGas_J_kg_K;
        if (!std::isfinite(cpMass) || cpMass<=0)
            throw std::domain_error("No remaining phase heat capacity");
        const double Tnew=thermo.Tref_K+
                 (targetH-m.liquid_kg*thermo.latentLiquidMinusSolid_J_kg)/
                 cpMass;
        if (!std::isfinite(Tnew) || Tnew<=0)
            throw std::domain_error("Energy closure produces invalid temperature");
        const FVCell next{cells[i].geometry,m,Tnew};
        const double localHResidual=cellEnthalpy(next,thermo)-targetH;
        result.next.push_back(next);
        result.finalMetalMass_kg+=m.liquid_kg+m.solid_kg;
        result.finalGasMass_kg+=m.gas_kg;
        result.finalEnthalpy_J+=cellEnthalpy(next,thermo);
        result.externalHeat_J+=heatW*step.dt_s;
        result.totalGammaTransfer_kg+=update.transferred_liquid_to_solid_kg;
        result.metalVolumeChange_m3+=update.metalVolumeChange_m3;
        result.maxCellMassResidual_kg=std::max(
            result.maxCellMassResidual_kg,std::abs(update.metalMassResidual_kg));
        result.maxCellEnthalpyResidual_J=std::max(
            result.maxCellEnthalpyResidual_J,std::abs(localHResidual));
    }
    result.metalMassResidual_kg=
        result.finalMetalMass_kg-result.initialMetalMass_kg;
    result.gasMassResidual_kg=
        result.finalGasMass_kg-result.initialGasMass_kg;
    result.enthalpyResidual_J=result.finalEnthalpy_J-
                               result.initialEnthalpy_J-
                               result.externalHeat_J;
    return result;
}
} // namespace MichelMasterProject::FS_C08
#endif
