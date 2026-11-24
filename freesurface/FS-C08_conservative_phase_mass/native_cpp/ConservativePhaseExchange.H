/* FS-C08: stand-alone C++17 conservative phase-mass exchange kernel.
 * This is NOT an OpenFOAM-14 solver or fvModel. No pressure or energy solved.
 * Gamma (kg/m3/s) comes from an external thermodynamic closure.
 * All inputs use SI. Positive flux is mass OUT of the finite-volume cell.
 * Never clip phase fractions, discard negative masses or invent density.
 */
#ifndef MASTERPROJECT_FS_C08_CONSERVATIVE_PHASE_EXCHANGE_H
#define MASTERPROJECT_FS_C08_CONSERVATIVE_PHASE_EXCHANGE_H

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

namespace MichelMasterProject::FS_C08
{
struct Masses
{
    double liquid_kg;
    double solid_kg;
    double gas_kg;
};
struct CellProps
{
    double cellVolume_m3;
    double rhoLiquid_kg_m3;
    double rhoSolid_kg_m3;
};
struct OutwardMassFlux
{
    double liquid_kg_s=0;
    double solid_kg_s=0;
    double gas_kg_s=0;
};
struct Result
{
    Masses next;
    double transferred_liquid_to_solid_kg;
    double liquidVolume_m3;
    double solidVolume_m3;
    double gasVoidVolume_m3;
    double metalVolumeChange_m3;
    double conversionOnlyVolumeChange_m3;
    double metalMassResidual_kg;
};

inline void validateNonnegative(const double x, const char* name)
{
    if (!std::isfinite(x) || x < 0)
        throw std::domain_error(std::string(name) + " must be finite and >=0");
}

inline Result exchange(
    const Masses& current,
    const CellProps& props,
    const double deltaT_s,
    const double Gamma_kg_m3_s,
    const OutwardMassFlux& outwardFlux)
{
    validateNonnegative(current.liquid_kg, "current liquid mass");
    validateNonnegative(current.solid_kg, "current solid mass");
    validateNonnegative(current.gas_kg, "current gas mass");
    if (!std::isfinite(props.cellVolume_m3) || props.cellVolume_m3<=0 ||
        !std::isfinite(props.rhoLiquid_kg_m3) || props.rhoLiquid_kg_m3<=0 ||
        !std::isfinite(props.rhoSolid_kg_m3) || props.rhoSolid_kg_m3<=0 ||
        !std::isfinite(deltaT_s) || deltaT_s<=0 ||
        !std::isfinite(Gamma_kg_m3_s) ||
        !std::isfinite(outwardFlux.liquid_kg_s) ||
        !std::isfinite(outwardFlux.solid_kg_s) ||
        !std::isfinite(outwardFlux.gas_kg_s))
        throw std::domain_error("Invalid density, volume, dt, Gamma or flux");

    const double initialMetalVolume =
        current.liquid_kg/props.rhoLiquid_kg_m3+
        current.solid_kg/props.rhoSolid_kg_m3;
    if (initialMetalVolume>props.cellVolume_m3*(1+1.e-12))
        throw std::domain_error("Initial metal phases overfill control volume");

    const double dM=Gamma_kg_m3_s*props.cellVolume_m3*deltaT_s;
    Masses next{
        current.liquid_kg-outwardFlux.liquid_kg_s*deltaT_s-dM,
        current.solid_kg -outwardFlux.solid_kg_s*deltaT_s +dM,
        current.gas_kg   -outwardFlux.gas_kg_s*deltaT_s
    };
    validateNonnegative(next.liquid_kg, "updated liquid mass");
    validateNonnegative(next.solid_kg, "updated solid mass");
    validateNonnegative(next.gas_kg, "updated gas mass");

    const double vl=next.liquid_kg/props.rhoLiquid_kg_m3;
    const double vs=next.solid_kg/props.rhoSolid_kg_m3;
    if (vl+vs>props.cellVolume_m3*(1+1.e-12))
        throw std::domain_error("Updated metal phases overfill control volume");
    double vg=props.cellVolume_m3-vl-vs;
    if (vg<0) vg=0; // rounding of geometric void only; no phase mass changed
    if (vg==0 && next.gas_kg>0)
        throw std::domain_error("Gas mass trapped in zero void; pressure undefined");

    const double metalMassResidual =
        (next.liquid_kg+next.solid_kg)-(current.liquid_kg+current.solid_kg)
        +deltaT_s*(outwardFlux.liquid_kg_s+outwardFlux.solid_kg_s);
    return {next,dM,vl,vs,vg,vl+vs-initialMetalVolume,
        dM*(1/props.rhoSolid_kg_m3-1/props.rhoLiquid_kg_m3),
        metalMassResidual};
}
} // namespace MichelMasterProject::FS_C08
#endif
