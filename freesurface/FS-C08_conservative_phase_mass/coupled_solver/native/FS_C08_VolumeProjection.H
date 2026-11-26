/* FS-C08 pressure-volume closure building block, Foundation14.
 * Experimental implementation. Not yet connected to time integration.
 * GPL-3.0-or-later, Michel's Lab 2026.
 */
#ifndef FS_C08_VolumeProjection_H
#define FS_C08_VolumeProjection_H
#include "fvMesh.H"
#include "volFields.H"
#include "surfaceFields.H"
#include "PtrList.H"

namespace Foam { namespace fsC08 {

// mL/mS/mG are independent trial masses per CELL volume (kg/m3).
// rhoL/rhoS/rhoG are positive intrinsic phase densities (kg/m3).
// The result is dimensionless and may have either sign. This is NOT VOF.
tmp<volScalarField> trialVolumeResidual
(
    const volScalarField& mL, const volScalarField& mS,
    const volScalarField& mG, const volScalarField& rhoL,
    const volScalarField& rhoS, const volScalarField& rhoG
);

// Frozen-coefficient pressure increment. The momentum-derived face
// mobilities are rho_i(face)*w_i(face)*rAUf and must respect BCs,
// mobile fractions and the stationary solid. Caller supplies dp BCs,
// compatible pressure reference, and current gas EOS derivative.
// Outputs are signed corrections to conserved mass fluxes (kg/s).
// Does not alter physical alpha, density, temperature or mass fields.
void solveVolumePressureIncrement
(
    const volScalarField& residual,
    const volScalarField& mG, const volScalarField& rhoL,
    const volScalarField& rhoG, const volScalarField& psiG,
    const surfaceScalarField& liquidMobility,
    const surfaceScalarField& gasMobility,
    volScalarField& dp,
    surfaceScalarField& deltaLiquidMassFlux,
    surfaceScalarField& deltaGasMassFlux,
    const label referenceCell = -1,
    const volScalarField* diagnosticMetalStorage = nullptr
);

// Bound a PREDICTOR mass flux before transport, against the old-time
// available phase inventory. One signed face flux is shared by both cells.
// Do not call this on the converged pressure flux: projection itself
// maintains admissibility and volume closure.
void limitPredictorMassFlux
(
    surfaceScalarField& massFlux,
    const volScalarField& availableMass,
    const char* stage
);

// Apply the SAME signed face flux increment to owner and neighbour.
// New mass is candidateMass - dt*div(deltaMassFlux). No clipping.
// Reject a negative trial before it can enter EOS or energy calculations.
tmp<volScalarField> correctedTrialMass
(
    const volScalarField& candidateMass,
    const surfaceScalarField& deltaMassFlux
);

// Rebuild a trial inventory from the SAME old-time field, never by
// incrementing the previously corrected n+1 state. Source is kg/m3/s;
// a positive source adds phase mass. Gas normally has zero source.
tmp<volScalarField> trialMassFromOldTime
(
    const volScalarField& oldMass,
    const surfaceScalarField& massFlux,
    const volScalarField& massSource
);

// A nonlinear pressure/volume transaction for the fixed-temperature,
// pressure-incompressible metal / linear-in-pressure gas EOS subproblem.
// Inputs mL/mG/pressure/rhoG and fluxes are updated only on success.
// dp must have homogeneous increment BCs consistent with pressure.
// Caller supplies frozen momentum-derived mobilities (NOT arbitrary
// diffusivities). Does not modify VOF, energy, temperature, or U.
// Returns false when the trial cannot be made admissible, without
// clipping mass or relaxing the volume tolerance.
bool projectTrialInventories
(
    volScalarField& mL, const volScalarField& mS,
    volScalarField& mG,
    const volScalarField& rhoL, const volScalarField& rhoS,
    volScalarField& rhoG, const volScalarField& psiG,
    volScalarField& pressure,
    const surfaceScalarField& liquidMobility,
    const surfaceScalarField& gasMobility,
    surfaceScalarField& liquidMassFlux,
    surfaceScalarField& gasMassFlux,
    volScalarField& dp,
    const label referenceCell = -1,
    const PtrList<volScalarField>* startupResidualComponents = nullptr,
    const scalar metalBulkModulusPa = 0
);

}} // namespace Foam::fsC08
#endif
