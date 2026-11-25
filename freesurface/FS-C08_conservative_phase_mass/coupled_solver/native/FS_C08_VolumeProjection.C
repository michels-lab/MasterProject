/* FS-C08 | native FV pressure-volume Newton/Picard building block.
 * This file is deliberately NOT invoked by the legacy split solver yet:
 * the caller must reassemble momentum, energy and gas EOS and iterate
 * before accepting VOF. No standalone projection is a shrinkage result.
 * GPL-3.0-or-later.
 */
#include "FS_C08_VolumeProjection.H"
#include "fvcDiv.H"
#include "fvmLaplacian.H"
#include "fvmSup.H"
#include "fvMatrices.H"
#include <cmath>

namespace Foam { namespace fsC08 {

tmp<volScalarField> trialVolumeResidual
(
    const volScalarField& mL, const volScalarField& mS,
    const volScalarField& mG, const volScalarField& rhoL,
    const volScalarField& rhoS, const volScalarField& rhoG
)
{
    forAll(mL,i)
    {
        if (!std::isfinite(mL[i]) || !std::isfinite(mS[i])
            || !std::isfinite(mG[i]) || mL[i]<0 || mS[i]<0 || mG[i]<0
            || !std::isfinite(rhoL[i]) || rhoL[i]<=0
            || !std::isfinite(rhoS[i]) || rhoS[i]<=0
            || !std::isfinite(rhoG[i]) || rhoG[i]<=0)
        {
            FatalErrorInFunction << "Invalid FS-C08 trial mass/density cell "
                << i << exit(FatalError);
        }
    }
    return mL/rhoL + mS/rhoS + mG/rhoG
         - dimensionedScalar(dimless,1);
}

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
    const label referenceCell
)
{
    const fvMesh& mesh=dp.mesh();
    const dimensionedScalar dt=mesh.time().deltaT();
    if (!std::isfinite(dt.value()) || dt.value()<=0)
        FatalErrorInFunction << "Invalid FS-C08 projection dt" << exit(FatalError);
    forAll(residual,i)
    {
        if (!std::isfinite(residual[i]) || !std::isfinite(mG[i])
            || mG[i]<0 || !std::isfinite(psiG[i]) || psiG[i]<0
            || !std::isfinite(rhoL[i]) || rhoL[i]<=0
            || !std::isfinite(rhoG[i]) || rhoG[i]<=0)
            FatalErrorInFunction << "Invalid FS-C08 pressure Jacobian cell "
                << i << exit(FatalError);
    }
    // Exact linearisation at frozen T, densities and face mobilities:
    // delta(m_i)=-dt div(deltaF_i), deltaF_i=-M_i grad(dp).S
    // delta(mG/rhoG)=delta(mG)/rhoG-mG*psiG*dp/rhoG^2
    // Therefore [ -div(M_L grad)/rhoL -div(M_G grad)/rhoG
    //             + mG psiG/(rhoG^2 dt) ] dp = residual/dt.
    // Row scaling by rho_i is important with unequal phase densities.
    // It can make the combined matrix asymmetric even if each diffusion
    // matrix is symmetric. Use an asymmetric-capable solver.
    if (dp.name()!="pVolumeCorrection.fsC08")
        FatalErrorInFunction << "Use dedicated FS-C08 pressure increment field"
            << exit(FatalError);
    // Foundation fvMatrix cannot row-scale a matrix containing a
    // nonorthogonal faceFluxCorrection. Use a named orthogonal
    // projection operator here; the full momentum/pressure iteration
    // must handle nonorthogonality and re-evaluate the exact residual.
    const word scheme("laplacian(fsC08VolumeMobility,pVolumeCorrection.fsC08)");
    mesh.schemes().setFluxRequired(dp.name());
    fvScalarMatrix liquidEqn(-fvm::laplacian(liquidMobility,dp,scheme));
    fvScalarMatrix gasEqn(-fvm::laplacian(gasMobility,dp,scheme));
    const volScalarField gasCompressibility
    (
        "fsC08VolumeGasCompressibility",
        mG*psiG/(sqr(rhoG)*dt)
    );
    fvScalarMatrix volumeEqn
    (
        liquidEqn/rhoL + gasEqn/rhoG
      + fvm::Sp(gasCompressibility,dp)
     == residual/dt
    );
    // Only supply a reference when the pressure BC and EOS require it.
    // The caller must check closed-domain compatibility; a reference
    // cannot repair a nonzero net expansion in a rigid sealed cavity.
    if (referenceCell>=0)
        volumeEqn.setReference(referenceCell,0);
    volumeEqn.solve();

    // Use the exact assembled per-phase matrix flux, not an unrelated
    // interpolation of grad(dp). These are face mass rates, NOT phi.
    deltaLiquidMassFlux=liquidEqn.flux();
    deltaGasMassFlux=gasEqn.flux();
}

tmp<volScalarField> correctedTrialMass
(
    const volScalarField& candidateMass,
    const surfaceScalarField& deltaMassFlux
)
{
    tmp<volScalarField> result =
        candidateMass-candidateMass.mesh().time().deltaT()
                     *fvc::div(deltaMassFlux);
    const volScalarField& mass=result();
    forAll(mass,i)
    {
        if (!std::isfinite(mass[i]) || mass[i]<0)
            FatalErrorInFunction
                << "FS-C08 pressure increment produced inadmissible trial "
                << "mass cell=" << i << " mass=" << mass[i]
                << "; use a bounded nonlinear flux correction, never clip"
                << exit(FatalError);
    }
    return result;
}

}} // namespace Foam::fsC08
