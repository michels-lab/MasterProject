/* FS-C08 | Extension of real Foundation14 compressibleVoF fluid module.
 * Explicitly separates phase-mass continuity from old VoFSolidificationMelting.
 * No calibration inferred, no shadow or post-processing time step.
 * Copyright 2026 Michel's Lab, GPL-3.0-or-later.
 */
#ifndef fsC08ConservativeVoF_H
#define fsC08ConservativeVoF_H

#include "compressibleVoF.H"
#include "FS_C08_PhaseMassTransport.H"

namespace Foam
{
namespace solvers
{

class fsC08ConservativeVoF : public compressibleVoF
{
    autoPtr<fsC08::PhaseMassTransport> phaseMass_;

    // Independent trial gas mass per cell volume. Until the pressure
    // projection is connected, this is NOT an accepted restart field.
    volScalarField gasMassTrial_;

    // Persistent effective metal density from actual conserved phase masses.
    // Must own oldTime() for the native compressible pressure ddt terms.
    volScalarField rhoMetalEffective_;

    // Persisted conservative thermal inventory [J/m3], built from
    // m_l*u_l(T) + m_s*u_s(T) + m_g*u_g(p,T).
    volScalarField phaseInternalEnergy_;

    // Signed per-face thermal/internal energy flux [W] used in the
    // ACTUAL energy solve (not reconstructed from post-pressure phi).
    surfaceScalarField phaseEnergyPhi_;

    // Signed outward conductive heat flux [W] at native fluid FV faces.
    // At fluid-mold wall: positive value = heat leaving fluid to mold.
    surfaceScalarField phaseHeatPhi_;

    // Signed physical mechanical-work density used by the exact
    // finite-volume internal-energy predictor [W/m3].
    volScalarField mechanicalWorkDensity_;

    // Positive Darcy kinetic-energy dissipation [W/m3], diagnostic
    // only: existing native ddt(rho,K) already converts that kinetic
    // energy into thermal energy in the TOTAL-energy conservation.
    // Adding this again as a heat source would double-count it.
    // Darcy coefficient from the last native momentum matrix [kg/(m3 s)].
    // Retain it to compute dissipation with final pressure-corrected U.
    volScalarField mushyDarcyResistance_;
    volScalarField mushyDarcyDissipation_;

    // Restore mixture mass from actual liquid+solid inventories, not
    // alpha.metal * rho_liquid alone. Gas remains native compressibleVoF.
    void reconcileMixtureDensity();
    void updatePhaseInternalEnergy();

protected:
    virtual void prePredictor() override;
    // Actual mushy-zone momentum resistance derived from conserved solid.
    virtual tmp<fvVectorMatrix> divDevTau(volVectorField& U) override;
    virtual void pressureCorrector() override;
    virtual void thermophysicalPredictor() override;

    // Called after ALL PIMPLE iterations: audit completed CFD step.
    virtual void postSolve() override;

public:
    TypeName("fsC08ConservativeVoF");

    explicit fsC08ConservativeVoF(fvMesh& mesh);
    virtual ~fsC08ConservativeVoF();

    // Publicly exposes no synthetic trigger; invoked by foamMultiRun PIMPLE.
};

} // namespace solvers
} // namespace Foam

#endif
