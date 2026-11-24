/*
 * FS-C08 | Phase-resolved internal-energy transport for real OpenFOAM14 CFD.
 *
 * Conserved thermal energy per CELL VOLUME:
 * E = rhoAlpha.liquid*u_l(T) + rhoAlpha.solid*u_s(T)
 *     + alpha.air*rho.air*u.air(p,T)                              [J/m3]
 *
 * The liquid carries its OWN real FV mass flux, the solid is stationary,
 * and the gas uses the native compressibleVoF face mass flux. The
 * material u_l/u_s curves are exact integrals of sourced Cv(T) functions,
 * with u_l(Tref)-u_s(Tref)=L exactly ONCE. NO separate Gamma L source.
 *
 * A nonlinear Picard/Newton linearisation of E(T) solves the true energy
 * inventory, not the old effective Cv + separate latent approximation.
 * Pressure-work/kinetic terms and conduction are inherited from the
 * Foundation14 total-internal-energy equation.
 *
 * NOTES: This is as yet UNCOMPILED on researcher's Foundation14 WSL.
 * Physical validation, full gas continuity, feeding, consistent thermal
 * EOS and p*dV closure still require checks; no shrinkage prediction claim.
 * Modification Copyright 2026 Michel's Lab, GPL-3.0-or-later.
 */
/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) 2022-2023 OpenFOAM Foundation
     \\/     M anipulation  |
-------------------------------------------------------------------------------
License
    This file is part of OpenFOAM.

    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenFOAM is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.

    You should have received a copy of the GNU General Public License
    along with OpenFOAM.  If not, see <http://www.gnu.org/licenses/>.

\*---------------------------------------------------------------------------*/

#include "fsC08ConservativeVoF.H"
#include "fvcMeshPhi.H"
#include "fvcDdt.H"
#include "fvcDiv.H"
#include "fvcInterpolate.H"
#include "fvcSnGrad.H"
#include "fvmSup.H"
#include "fvmLaplacian.H"
#include "zeroGradientFvPatchFields.H"
#include "PstreamReduceOps.H"

#include <cmath>

void Foam::solvers::fsC08ConservativeVoF::thermophysicalPredictor()
{
    // We explicitly transport INTERNAL energies with a pressure-work term.
    // A mixture configured for total enthalpy would require a distinct
    // pressure-work formulation, and MUST NOT be run with this equation.
    if (!mixture.totalInternalEnergy())
    {
        FatalErrorInFunction
            << "FS-C08 u_l(T)/u_s(T) internal-energy transport requires "
            << "totalInternalEnergy true. Refusing an enthalpy-mode "
            << "temperature equation with inconsistent p*dV."
            << exit(FatalError);
    }

    volScalarField& T=mixture_.T();
    T.oldTime();
    alpha2.oldTime();

    const volScalarField& mL=phaseMass_->liquidMass();
    const volScalarField& mS=phaseMass_->solidMass();
    const volScalarField& rhoG=mixture_.rho2();

    // Explicitly retrieve old native phase masses and old gas internal
    // energy. The same oldTime reference is used throughout PIMPLE.
    const auto& mL0=mL.oldTime().primitiveField();
    const auto& mS0=mS.oldTime().primitiveField();
    const auto& TG0=T.oldTime().primitiveField();
    const auto& aG0=alpha2.oldTime().primitiveField();
    const auto& rhoG0=rhoG.oldTime().primitiveField();
    const auto& uG0=mixture_.thermo2().he().oldTime().primitiveField();
    const auto& V=mesh.V();

    const scalar dt=runTime.deltaTValue();
    if (!std::isfinite(dt) || dt<=0)
        FatalErrorInFunction
            << "FS-C08 invalid CFD dt in internal-energy transport"
            << exit(FatalError);

    // The thermal energy reference is defined by u_s(Tref)=0 and
    // u_l(Tref)=latentHeat. This reference has no separate Gamma L.
    volScalarField Eold
    (
        IOobject
        (
            "FS_C08_Eold",runTime.name(),mesh,
            IOobject::NO_READ,IOobject::NO_WRITE
        ),
        mesh,dimensionedScalar(dimEnergy/dimVolume,0),
        zeroGradientFvPatchScalarField::typeName
    );
    auto& E0=Eold.primitiveFieldRef();
    forAll(E0,i)
    {
        scalar l=0,s=0;
        if (mL0[i]>0 || mS0[i]>0)
        {
            l=phaseMass_->liquidInternalEnergy(TG0[i]);
            s=phaseMass_->solidInternalEnergy(TG0[i]);
        }
        E0[i]=mL0[i]*l + mS0[i]*s + aG0[i]*rhoG0[i]*uG0[i];
        if (!std::isfinite(E0[i]))
            FatalErrorInFunction
                << "FS-C08 nonfinite old mixture internal energy cell "
                << i << exit(FatalError);
    }
    Eold.correctBoundaryConditions();

    volScalarField Eguess
    (
        IOobject
        (
            "FS_C08_Eguess",runTime.name(),mesh,
            IOobject::NO_READ,IOobject::NO_WRITE
        ),
        mesh,dimensionedScalar(dimEnergy/dimVolume,0),
        zeroGradientFvPatchScalarField::typeName
    );
    volScalarField CVvol
    (
        IOobject
        (
            "FS_C08_CVvol",runTime.name(),mesh,
            IOobject::NO_READ,IOobject::NO_WRITE
        ),
        mesh,
        dimensionedScalar(dimEnergy/dimVolume/dimTemperature,0),
        zeroGradientFvPatchScalarField::typeName
    );
    volScalarField uLiquid
    (
        IOobject
        (
            "FS_C08_uLiquid",runTime.name(),mesh,
            IOobject::NO_READ,IOobject::NO_WRITE
        ),
        mesh,dimensionedScalar(dimEnergy/dimMass,0),
        zeroGradientFvPatchScalarField::typeName
    );

    // Purely numerical nonlinear solver controls; these are NOT material
    // constants or kinetic coefficients and cannot validate cast iron.
    const label maxEnergyCorrectors=18;
    const scalar energyToleranceK=1e-6;
    scalar lastDeltaT=GREAT;
    bool converged=false;

    for (label corrector=0;corrector<maxEnergyCorrectors;++corrector)
    {
        mixture_.correctThermo();

        const tmp<volScalarField> tGasCv=mixture_.thermo2().Cv();
        const volScalarField& gasCv=tGasCv();
        const auto& ug=mixture_.thermo2().he().primitiveField();
        const auto& gasC=gasCv.primitiveField();
        const auto& aG=alpha2.primitiveField();
        const auto& rg=rhoG.primitiveField();
        const auto& ml=mL.primitiveField();
        const auto& ms=mS.primitiveField();
        const auto& temp=T.primitiveField();

        auto& e=Eguess.primitiveFieldRef();
        auto& c=CVvol.primitiveFieldRef();
        auto& ul=uLiquid.primitiveFieldRef();

        forAll(temp,i)
        {
            // Pure gas has no iron u(T); use the reference solely
            // to construct an inert zero-mass liquid energy face field.
            scalar ul_i=phaseMass_->liquidInternalEnergy
            (
                phaseMass_->energyReferenceT()
            );
            scalar us_i=0;
            scalar cvL=0,cvS=0;
            if (ml[i]>0 || ms[i]>0)
            {
                ul_i=phaseMass_->liquidInternalEnergy(temp[i]);
                us_i=phaseMass_->solidInternalEnergy(temp[i]);
                cvL=phaseMass_->liquidCv(temp[i]);
                cvS=phaseMass_->solidCv(temp[i]);
            }
            ul[i]=ul_i;

            // CURRENT exact internal-energy inventory at Tguess.
            e[i]=ml[i]*ul_i+ms[i]*us_i+aG[i]*rg[i]*ug[i];
            c[i]=ml[i]*cvL+ms[i]*cvS+aG[i]*rg[i]*gasC[i];
            if (!std::isfinite(e[i]) || !std::isfinite(c[i])
                || c[i]<=0)
            {
                FatalErrorInFunction
                    << "FS-C08 nonfinite/nonpositive thermodynamic Cv "
                    << "or energy in cell " << i
                    << exit(FatalError);
            }
        }
        Eguess.correctBoundaryConditions();
        CVvol.correctBoundaryConditions();
        uLiquid.correctBoundaryConditions();

        // Liquid enthalpy at a real metal inflow must be determined by
        // the boundary temperature. Zero-gradient interior values are
        // NOT silently substituted for prescribed inlet temperatures.
        forAll(uLiquid.boundaryField(),patchi)
        {
            const auto& flux=alphaRhoPhi1.boundaryField()[patchi];
            const auto& boundaryT=T.boundaryField()[patchi];
            auto& boundaryU=uLiquid.boundaryFieldRef()[patchi];
            forAll(flux,facei)
            {
                if (mag(flux[facei])>SMALL)
                    boundaryU[facei]=
                        phaseMass_->liquidInternalEnergy
                        (
                            boundaryT[facei]
                        );
            }
        }

        // Same native face flux to owner AND neighbour => exact
        // cancellation of internal advective energy at global level.
        const surfaceScalarField internalEnergyFlux
        (
            "FS_C08_internalEnergyFlux",
            phaseMass_->liquidMassFlux()*fvc::interpolate(uLiquid)
          + alphaRhoPhi2*fvc::interpolate(mixture_.thermo2().he())
        );

        // Retain exactly the FV face energy flux used by TEqn.
        // Pressure may change phi later; recomputation at postSolve
        // would NOT reproduce the equation that was actually solved.
        phaseEnergyPhi_=internalEnergyFlux;

        // Native thermal transport still uses a ONE-PHASE metal k(T).
        // Replace its MOLECULAR metal contribution with real
        // alpha_liquid*k_liquid(T) + alpha_solid*k_solid(T).
        // Preserve the gas molecular transport and upstream turbulent
        // enhancement. Turbulence in the coherent solid requires
        // subsequent closure (not silently called validated).
        volScalarField kappaFsC08
        (
            "kappaEffective.fsC08",
            thermophysicalTransport.kappaEff()
        );
        const tmp<volScalarField> tNativeMetalK=
            mixture_.thermo1().kappa();
        const auto& nativeK=tNativeMetalK().primitiveField();
        const auto& aL=phaseMass_->alphaLiquid().primitiveField();
        const auto& aS=phaseMass_->alphaSolid().primitiveField();
        auto& keff=kappaFsC08.primitiveFieldRef();
        forAll(keff,i)
        {
            if (aL[i]+aS[i]>0)
            {
                keff[i]+=
                    aL[i]*phaseMass_->liquidKappa(temp[i])
                  + aS[i]*phaseMass_->solidKappa(temp[i])
                  - (aL[i]+aS[i])*nativeK[i];
            }
            if (!std::isfinite(keff[i]) || keff[i]<=0)
                FatalErrorInFunction
                    << "FS-C08 nonpositive phase-specific effective "
                    << "conductivity at cell " << i << exit(FatalError);
        }

        // Correct metal conductivity on the REAL mold interface BCs,
        // not only internal cells. This affects CHT heat extraction.
        forAll(kappaFsC08.boundaryField(),patchi)
        {
            auto& kPatch=kappaFsC08.boundaryFieldRef()[patchi];
            const auto& Tpatch=T.boundaryField()[patchi];
            const auto& lPatch=
                phaseMass_->alphaLiquid().boundaryField()[patchi];
            const auto& sPatch=
                phaseMass_->alphaSolid().boundaryField()[patchi];
            const auto& oldK=tNativeMetalK().boundaryField()[patchi];
            forAll(kPatch,facei)
            {
                if (lPatch[facei]+sPatch[facei]>0)
                {
                    kPatch[facei]+=
                        lPatch[facei]
                           *phaseMass_->liquidKappa(Tpatch[facei])
                      + sPatch[facei]
                           *phaseMass_->solidKappa(Tpatch[facei])
                      - (lPatch[facei]+sPatch[facei])*oldK[facei];
                }
                if (!std::isfinite(kPatch[facei]) || kPatch[facei]<=0)
                    FatalErrorInFunction
                        << "FS-C08 invalid mold-interface kappa on patch "
                        << patchi << ", face " << facei
                        << exit(FatalError);
            }
        }

        const scalarField T_before(T.primitiveField());

        // Newton/Picard linearisation of E(T):
        // E(T) ≈ Eguess + CVvol*(T-Tguess).
        // At convergence: ddt(E)+div(F_E)-laplacian(k,T)+W_pK=0.
        //
        // Foundation14 pressure and kinetic-energy work is retained
        // from the native totalInternalEnergy predictor (NOT dropped).
        fvScalarMatrix TEqn
        (
            fvm::Sp(CVvol/runTime.deltaT(),T)
          - fvm::laplacian(kappaFsC08,T)
          + (
                fvc::div(fvc::absolute(phi,U),p)()()
              + (fvc::ddt(rho,K)+fvc::div(rhoPhi,K))()()
              - (U()&(fvModels().source(rho,U)&U)())
              - (contErr1()+contErr2())*K
            )
         ==
            (Eold-Eguess+CVvol*T)/runTime.deltaT()
          - fvc::div(internalEnergyFlux)
        );

        TEqn.relax();
        fvConstraints().constrain(TEqn);
        TEqn.solve();
        fvConstraints().constrain(T);

        // Outward-positive conductive energy flux W on all faces,
        // especially the fluid-mold CHT interface.
        // This uses the same phase conductivity that was assembled in
        // the nonlinear TEqn. q = -k grad(T) dot outward normal.
        phaseHeatPhi_=
            -fvc::interpolate(kappaFsC08)
            *fvc::snGrad(T)*mesh.magSf();

        lastDeltaT=0;
        const auto& Tnew=T.primitiveField();
        forAll(Tnew,i)
        {
            if (!std::isfinite(Tnew[i]) || Tnew[i]<=0)
                FatalErrorInFunction
                    << "FS-C08 invalid energy-corrected T in cell "
                    << i << exit(FatalError);

            lastDeltaT=max(lastDeltaT,mag(Tnew[i]-T_before[i]));
        }
        reduce(lastDeltaT,maxOp<scalar>());
        if (lastDeltaT<=energyToleranceK)
        {
            converged=true;
            break;
        }
    }
    if (!converged)
    {
        FatalErrorInFunction
            << "FS-C08 phase-resolved nonlinear energy predictor "
            << "did not converge after " << maxEnergyCorrectors
            << " correctors. MaxDeltaT=" << lastDeltaT
            << " K. No thermodynamic validation claim."
            << exit(FatalError);
    }

    mixture_.correctThermo();
    mixture_.correct();

    // Energy solve must update rho_l(T), rho_s(T), and thus occupied
    // VOF volume BEFORE native PIMPLE pressure. Never apply Gamma twice.
    phaseMass_->refreshAfterEnergy(T,alpha1);
    alpha1=phaseMass_->alphaMetal();
    alpha2=scalar(1)-alpha1;
    alpha1.correctBoundaryConditions();
    alpha2.correctBoundaryConditions();
    correctInterface();

    alphaRhoPhi1=phaseMass_->liquidMassFlux();
    alphaPhi1=alphaRhoPhi1/
        fvc::interpolate(phaseMass_->liquidDensity());
    alphaPhi2=phi-alphaPhi1;
    alphaRhoPhi2=fvc::interpolate(mixture_.rho2())*alphaPhi2;
    rhoPhi=alphaRhoPhi1+alphaRhoPhi2;
    reconcileMixtureDensity();

    Info<< "FS_C08_NATIVE_PHASE_RESOLVED_INTERNAL_ENERGY"
        << " time_s=" << runTime.value()
        << " nonlinearDeltaT_K=" << lastDeltaT
        << " correctors_converged=1"
        << " phaseInternalEnergiesCvIntegral=1"
        << " singleLatentReferenceOffset=1"
        << " originalVoFSolidificationMeltingMustBeDisabled=1"
        << " globalEnergyBalanceNotYetValidated=1" << nl;
}
// ************************************************************************* //
