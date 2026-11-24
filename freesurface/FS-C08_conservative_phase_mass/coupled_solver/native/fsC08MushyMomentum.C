/* FS-C08: real PIMPLE momentum Darcy sink in partially/fully solid metal.
 * Based on separate CONSERVED phase masses, not relaxed legacy
 * alpha.metal.solid from VoFSolidificationMelting fvModel.
 * OpenFOAM Foundation14 GPL-3.0-or-later, Michel's Lab 2026.
 */
#include "fsC08ConservativeVoF.H"
#include "fvmSup.H"
#include "zeroGradientFvPatchFields.H"
#include <cmath>

Foam::tmp<Foam::fvVectorMatrix>
Foam::solvers::fsC08ConservativeVoF::divDevTau(volVectorField& U)
{
    // The inherited stress and conservative rho/velocity correction remain.
    tmp<fvVectorMatrix> tBase=compressibleVoF::divDevTau(U);

    const scalar Cu=phaseMass_->mushyDarcyCu().value();
    const scalar q=phaseMass_->mushyDarcyQ();
    const auto& aL=phaseMass_->alphaLiquid().primitiveField();
    const auto& aS=phaseMass_->alphaSolid().primitiveField();
    const auto& ml=phaseMass_->liquidMass().primitiveField();
    const auto& ms=phaseMass_->solidMass().primitiveField();
    auto& R=mushyDarcyResistance_.primitiveFieldRef();

    forAll(R,i)
    {
        const scalar aMetal=aL[i]+aS[i];
        if (aMetal<=1e-12)
        {
            R[i]=0;
            continue;
        }
        const scalar fS=aS[i]/aMetal;
        const scalar fL=aL[i]/aMetal;

        // Rate Cu [s^-1] x conserved metal inventory [kg/m3].
        // Conditional fractions avoid damping pure air as if solid metal.
        // In a coherent mushy skeleton this approximates a Darcy sink;
        // q caps the singularity near fL=0.
        R[i]=(ml[i]+ms[i])*Cu*sqr(fS)/(pow3(fL)+q);
        if (!std::isfinite(R[i]) || R[i]<0)
        {
            FatalErrorInFunction
                << "FS-C08 nonphysical Darcy drag in cell " << i
                << " solid fraction=" << fS << " liquid fraction=" << fL
                << " resistance=" << R[i] << exit(FatalError);
        }
    }
    mushyDarcyResistance_.correctBoundaryConditions();

    // The coefficient R is persisted. Actual Darcy dissipation is
    // computed AFTER momentum and pressure correction using FINAL U
    // by postSolve(), not the stale U at matrix assembly.

    // Positive implicit Sp on the momentum LHS => dissipative drag.
    return tBase + fvm::Sp(mushyDarcyResistance_,U);
}
