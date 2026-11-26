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
#include "FS_C08_VolumeProjection.H"
#include "fvcMeshPhi.H"
#include "fvcDdt.H"
#include "fvcDiv.H"
#include "fvc.H"
#include "fvcSnGrad.H"
#include "fvmSup.H"
#include "fvmLaplacian.H"
#include "harmonic.H"
#include "upwind.H"
#include "IOdictionary.H"
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
    const IOdictionary numerics
    (
        IOobject("fsC08Numerics",runTime.constant(),mesh,
                 IOobject::READ_IF_PRESENT,IOobject::NO_WRITE,false)
    );
    const word energyDonor=numerics.found("energyDonorMode")
        ? numerics.lookup<word>("energyDonorMode") : word("legacy");
    if (energyDonor!="legacy" && energyDonor!="oldGas"
        && energyDonor!="currentLiquid" && energyDonor!="oldGasCurrentLiquid")
        FatalErrorInFunction << "FS-C08 unknown energyDonorMode " << energyDonor
            << exit(FatalError);
    const bool oldGas=energyDonor=="oldGas" || energyDonor=="oldGasCurrentLiquid";
    const bool currentLiquid=energyDonor=="currentLiquid" || energyDonor=="oldGasCurrentLiquid";
    const volScalarField& gasEnergyOld=mixture_.thermo2().he().oldTime();

    const volScalarField& mL=phaseMass_->liquidMass();
    const volScalarField& mS=phaseMass_->solidMass();
    const volScalarField& rhoG=mixture_.rho2();

    // Explicitly retrieve old native phase masses and old gas internal
    // energy. The same oldTime reference is used throughout PIMPLE.
    // The previous accepted energy inventory is persisted at t=n.
    // Native phase thermo oldTime fields may be lazily created during
    // correction; do not mix snapshots from different EOS states.
    const auto& acceptedE0=phaseInternalEnergy_.oldTime().primitiveField();

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
        E0[i]=acceptedE0[i];
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
    const scalar linearTolerance=numerics.found("energyLinearTolerance")
        ? numerics.lookup<scalar>("energyLinearTolerance") : scalar(0);
    if (!std::isfinite(linearTolerance) || linearTolerance<0 || linearTolerance>1)
        FatalErrorInFunction << "Invalid FS-C08 energyLinearTolerance" << exit(FatalError);
    const bool residualControlled=linearTolerance>0;
    const label maxEnergyCorrectors=residualControlled ? 36 : 18;
    scalar lastResidualEquivalentK=GREAT;
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
        // Gas trial inventory is an independent conserved predictor;
        // native rhoG is still the EOS field used by the pressure block.
        const auto& mg=gasMassTrial_.primitiveField();
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
            // Advective energy belongs to the transported liquid,
            // not the post-freezing inventory in the receiver. Use the
            // old donor temperature for explicit first-order transport;
            // a cell with no old metal uses its current mixture T
            // if the pressure flux establishes a through-flow.
            const scalar oldMetal= mL.oldTime()[i]+mS.oldTime()[i];
            ul[i]=phaseMass_->liquidInternalEnergy
                (!currentLiquid && oldMetal>0 ? T.oldTime()[i] : temp[i]);

            // CURRENT exact internal-energy inventory at Tguess.
            e[i]=ml[i]*ul_i+ms[i]*us_i+mg[i]*ug[i];
            c[i]=ml[i]*cvL+ms[i]*cvS+mg[i]*gasC[i];
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

        // Donor-consistent signed mass-energy flux: do not average a
        // hot liquid donor with a cold gas receiver or an inert energy
        // reference at the interface. Same flux to owner/neighbour => exact
        // cancellation of internal advective energy at global level.
        const surfaceScalarField liquidEnergyFlux
        (
            "fsC08LiquidEnergyFlux",
            phaseMass_->liquidMassFlux()
                *upwind<scalar>(mesh,phaseMass_->liquidMassFlux()).interpolate(uLiquid)
        );
        surfaceScalarField gasEnergyFlux
        (
            "fsC08GasEnergyFlux",
            alphaRhoPhi2
                *upwind<scalar>(mesh,alphaRhoPhi2).interpolate(mixture_.thermo2().he())
        );
        if (oldGas)
        {
            const surfaceScalarField explicitGasFlux
            (
                "fsC08OldDonorGasEnergyFlux",
                alphaRhoPhi2
                    *upwind<scalar>(mesh,alphaRhoPhi2).interpolate(gasEnergyOld)
            );
            gasEnergyFlux.primitiveFieldRef()=explicitGasFlux.primitiveField();
            // Outflow uses old donor energy; imposed inflow retains
            // the actual current boundary thermodynamic state.
            forAll(gasEnergyFlux.boundaryField(),patchi)
                forAll(gasEnergyFlux.boundaryField()[patchi],facei)
                    if (alphaRhoPhi2.boundaryField()[patchi][facei]>=0)
                        gasEnergyFlux.boundaryFieldRef()[patchi][facei]=
                            explicitGasFlux.boundaryField()[patchi][facei];
        }
        const surfaceScalarField internalEnergyFlux
        (
            "FS_C08_internalEnergyFlux", liquidEnergyFlux+gasEnergyFlux
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
        const tmp<volScalarField> tNativeGasK=mixture_.thermo2().kappa();
        const auto& nativeGasK=tNativeGasK().primitiveField();
        scalar maxNativeEddyK=0;
        label maxEddyCell=-1;
        forAll(nativeK,i)
        {
            const scalar molecular=alpha1[i]*nativeK[i]+alpha2[i]*nativeGasK[i];
            const scalar eddy=kappaFsC08[i]-molecular;
            if (eddy>maxNativeEddyK)
            {
                maxNativeEddyK=eddy;
                maxEddyCell=i;
            }
        }
        if (corrector==0)
        {
            Info<< "FS_C08_THERMAL_TRANSPORT_SPLIT"
                << " maxNativeEddyK_W_mK=" << maxNativeEddyK
                << " cell=" << maxEddyCell;
            if (maxEddyCell>=0)
                Info<< " nativeMetalK_W_mK=" << nativeK[maxEddyCell]
                    << " nativeGasK_W_mK=" << nativeGasK[maxEddyCell]
                    << " nativeKeff_W_mK=" << kappaFsC08[maxEddyCell]
                    << " alphaMetal=" << alpha1[maxEddyCell];
            Info<< nl;
        }
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

        // A discontinuity in conductivity is a series thermal resistance,
        // not a parallel arithmetic average across a metal/air face.
        // Use the distance-weighted harmonic interpolation for internal
        // faces; keep physical patch conductivities supplied by CHT.
        surfaceScalarField kappaFace
        (
            "fsC08HarmonicFaceKappa",
            harmonic(mesh).interpolate(kappaFsC08)
        );
        forAll(kappaFace.boundaryField(),patchi)
            if (!mesh.boundary()[patchi].coupled())
                kappaFace.boundaryFieldRef()[patchi]=
                    kappaFsC08.boundaryField()[patchi];

        const scalarField T_before(T.primitiveField());

        // Newton/Picard linearisation of E(T):
        // E(T) ≈ Eguess + CVvol*(T-Tguess).
        // At convergence: ddt(E)+div(F_E)-laplacian(k,T)+W_pK=0.
        //
        // IMPORTANT: this is the EXACT volumetric mechanical-work
        // density assembled in the native internal-energy equation.
        // Retaining it lets the later postSolve budget account for
        // pressure and kinetic-energy work with its actual sign.
        // The Darcy resistance already changes K; it is NOT inserted
        // a second time as an artificial Gamma/Darcy heat source.
        mechanicalWorkDensity_.primitiveFieldRef() =
              fvc::div(fvc::absolute(phi,U),p)()()
            + (fvc::ddt(rho,K)+fvc::div(rhoPhi,K))()()
            - (U()&(fvModels().source(rho,U)&U)())
            - (contErr1()+contErr2())*K;
        mechanicalWorkDensity_.correctBoundaryConditions();

        // Retain the actual assembled conductive matrix to recover its
        // signed face flux, including the explicit non-orthogonal term.
        // Use the inherited named temperature Laplacian discretisation.
        mesh.schemes().setFluxRequired(T.name());
        fvScalarMatrix heatEqn
        (
            -fvm::laplacian
            (
                kappaFace,T,"laplacian(kappaEffective.fsC08,T)"
            )
        );
        fvScalarMatrix TEqn
        (
            fvm::Sp(CVvol/runTime.deltaT(),T)
          + heatEqn
          + mechanicalWorkDensity_
         ==
            (Eold-Eguess+CVvol*T)/runTime.deltaT()
          - fvc::div(internalEnergyFlux)
        );

        TEqn.relax();
        fvConstraints().constrain(TEqn);
        if (residualControlled)
        {
            dictionary controls(mesh.solution().solverDict(T.name()));
            controls.set("tolerance",linearTolerance);
            controls.set("relTol",scalar(0));
            controls.set("minIter",label(1));
            TEqn.solve(controls);
        }
        else
            TEqn.solve();
        fvConstraints().constrain(T);

        // Outward-positive conductive energy flux W on all faces,
        // especially the fluid-mold CHT interface.
        // This uses the same phase conductivity that was assembled in
        // the nonlinear TEqn. q = -k grad(T) dot outward normal.
        phaseHeatPhi_=heatEqn.flux();

        // Separate conductive, advective and mechanical contributions
        // in the cell with the largest thermal change. This is an
        // equation-level audit, not a claim of global CHT conservation.
        const tmp<volScalarField> tHeatDiv=fvc::div(phaseHeatPhi_);
        const tmp<volScalarField> tEnergyDiv=fvc::div(internalEnergyFlux);
        const volScalarField& heatDiv=tHeatDiv();
        const volScalarField& energyDiv=tEnergyDiv();
        label worstThermalCell=-1;
        scalar worstThermalChange=0;
        forAll(T_before,i)
        {
            const scalar change=mag(T[i]-T.oldTime()[i]);
            if (change>worstThermalChange)
            {
                worstThermalChange=change;
                worstThermalCell=i;
            }
        }
        if (worstThermalCell>=0 && worstThermalChange>1)
        {
            const label i=worstThermalCell;
            const tmp<volScalarField> liquidDiv=fvc::div(liquidEnergyFlux);
            const tmp<volScalarField> gasDiv=fvc::div(gasEnergyFlux);
            Info<< "FS_C08_PHASE_ENERGY_SPLIT"
                << " time_s=" << runTime.value()
                << " mode=" << energyDonor
                << " cell=" << i
                << " alphaGasGeometry=" << alpha2[i]
                << " liquidMass_kg_m3=" << mL[i]
                << " solidMass_kg_m3=" << mS[i]
                << " gasMass_kg_m3=" << gasMassTrial_[i]
                << " oldGasSpecificEnergy_J_kg=" << gasEnergyOld[i]
                << " currentGasSpecificEnergy_J_kg=" << ug[i]
                << " liquidAdvectionOut_J_m3=" << dt*liquidDiv()[i]
                << " gasAdvectionOut_J_m3=" << dt*gasDiv()[i]
                << " conductionOut_J_m3=" << dt*heatDiv[i]
                << " mechanicalWork_J_m3=" << dt*mechanicalWorkDensity_[i]
                << " diagnosticOnly=1" << nl;
            const scalar storageLinear=
                (Eguess[i]-Eold[i]+CVvol[i]*(T[i]-T_before[i]))/dt;
            Info<< "FS_C08_CELL_THERMAL_BUDGET"
                << " cell=" << i
                << " corrector=" << corrector
                << " center_m=" << mesh.C()[i]
                << " cellVolume_m3=" << mesh.V()[i]
                << " Told_K=" << T.oldTime()[i]
                << " Tguess_K=" << T_before[i]
                << " Tnew_K=" << T[i]
                << " gasMass_kg_m3=" << gasMassTrial_[i]
                << " CvVol_J_m3K=" << CVvol[i]
                << " kCell_W_mK=" << kappaFsC08[i]
                << " storage_W_m3=" << storageLinear
                << " conductionOut_W_m3=" << heatDiv[i]
                << " advectionOut_W_m3=" << energyDiv[i]
                << " mechanicalWork_W_m3=" << mechanicalWorkDensity_[i]
                << " linearBalance_W_m3="
                << storageLinear+heatDiv[i]+energyDiv[i]+mechanicalWorkDensity_[i]
                << nl;
        }

        // Audit the actual nonlinear inventory at updated T, with the
        // same mass and cached face fluxes as this energy solve.
        // A small temperature change alone is not evidence of balance.
        mixture_.correctThermo();
        const auto& newUg=mixture_.thermo2().he().primitiveField();
        scalar absBalance=0,absTerms=0;
        lastResidualEquivalentK=0;
        forAll(T_before,i)
        {
            scalar updatedEnergy=gasMassTrial_[i]*newUg[i];
            if (mL[i]+mS[i]>0)
                updatedEnergy+=mL[i]*phaseMass_->liquidInternalEnergy(T[i])
                    +mS[i]*phaseMass_->solidInternalEnergy(T[i]);
            const scalar storage=updatedEnergy-Eold[i];
            const scalar advection=dt*energyDiv[i];
            const scalar conduction=dt*heatDiv[i];
            const scalar work=dt*mechanicalWorkDensity_[i];
            const scalar imbalance=mag(storage+advection+conduction+work);
            if (!std::isfinite(imbalance))
                FatalErrorInFunction << "Nonfinite FS-C08 thermal residual" << exit(FatalError);
            absBalance+=mesh.V()[i]*imbalance;
            absTerms+=mesh.V()[i]*(mag(storage)+mag(advection)+mag(conduction)+mag(work));
            lastResidualEquivalentK=max(lastResidualEquivalentK,imbalance/CVvol[i]);
        }
        reduce(lastResidualEquivalentK,maxOp<scalar>());
        reduce(absBalance,sumOp<scalar>());
        reduce(absTerms,sumOp<scalar>());
        Info<< "FS_C08_THERMAL_RESIDUAL_CONTROL time_s=" << runTime.value()
            << " corrector=" << corrector
            << " linearTolerance=" << linearTolerance
            << " maxResidualEquivalent_K=" << lastResidualEquivalentK
            << " absBalance_J=" << absBalance
            << " relativeL1=" << absBalance/max(scalar(VSMALL),absTerms)
            << " residualGateEnabled=" << residualControlled << nl;
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
        if (lastDeltaT<=energyToleranceK
            && (!residualControlled || lastResidualEquivalentK<=energyToleranceK))
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
            << " K, residualEquivalentK=" << lastResidualEquivalentK
            << ". No thermodynamic validation claim."
            << exit(FatalError);
    }

    mixture_.correctThermo();
    mixture_.correct();

    // Energy solve must update rho_l(T), rho_s(T), and thus occupied
    // VOF volume BEFORE native PIMPLE pressure. Never apply Gamma twice.
    phaseMass_->refreshTrialProperties(T,alpha1);
    const tmp<volScalarField> volumeResidual=fsC08::trialVolumeResidual
    (
        phaseMass_->liquidMass(),phaseMass_->solidMass(),gasMassTrial_,
        phaseMass_->liquidDensity(),phaseMass_->solidDensity(),rhoG
    );
    scalar maxVolumeDefect=0;
    label worstCell=-1;
    forAll(volumeResidual(),i)
        if (mag(volumeResidual()[i])>maxVolumeDefect)
        {
            maxVolumeDefect=mag(volumeResidual()[i]);
            worstCell=i;
        }
    if (worstCell>=0 && maxVolumeDefect>1e-8)
    {
        const label i=worstCell;
        Info<< "FS_C08_TRIAL_VOLUME_COMPONENTS"
            << " cell=" << i
            << " signedResidual=" << volumeResidual()[i]
            << " Told_K=" << T.oldTime()[i]
            << " center_m=" << mesh.C()[i]
            << " cellVolume_m3=" << mesh.V()[i]
            << " T_K=" << T[i] << " p_Pa=" << p[i]
            << " mGasOld=" << gasMassTrial_.oldTime()[i]
            << " mGasTrial=" << gasMassTrial_[i]
            << " rhoGas=" << rhoG[i]
            << " alphaGasGeometry=" << alpha2[i]
            << " alphaGasFromMass=" << gasMassTrial_[i]/rhoG[i]
            << " alphaLiquidFromMass=" << mL[i]/phaseMass_->liquidDensity()[i]
            << " alphaSolidFromMass=" << mS[i]/phaseMass_->solidDensity()[i]
            << nl;
    }
    reduce(maxVolumeDefect,maxOp<scalar>());
    Info<< "FS_C08_THREE_PHASE_TRIAL_VOLUME"
        << " time_s=" << runTime.value()
        << " maxAbsResidual=" << maxVolumeDefect
        << " acceptedPhysicalState=0" << nl;

    // Do not accept overfilled trial geometry here. This same energy
    // predictor is called again from the coupled pressure corrector
    // using the corrected phase mass fluxes and independent inventories.
    reconcileMixtureDensity();
    updatePhaseInternalEnergy();

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
