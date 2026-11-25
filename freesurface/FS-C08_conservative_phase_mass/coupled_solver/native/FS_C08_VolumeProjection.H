/* FS-C08 pressure-volume closure building block, Foundation14.
 * Experimental implementation. Not yet connected to time integration.
 * GPL-3.0-or-later, Michel's Lab 2026.
 */
#ifndef FS_C08_VolumeProjection_H
#define FS_C08_VolumeProjection_H
#include "fvMesh.H"
#include "volFields.H"
#include "surfaceFields.H"

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
    const label referenceCell = -1
);

// Apply the SAME signed face flux increment to owner and neighbour.
// New mass is candidateMass - dt*div(deltaMassFlux). No clipping.
// Reject a negative trial before it can enter EOS or energy calculations.
tmp<volScalarField> correctedTrialMass
(
    const volScalarField& candidateMass,
    const surfaceScalarField& deltaMassFlux
);

}} // namespace Foam::fsC08
#endif
