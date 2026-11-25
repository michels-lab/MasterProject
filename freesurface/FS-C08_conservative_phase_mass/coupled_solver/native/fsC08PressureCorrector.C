/* FS-C08 adaptation from OpenFOAM Foundation14 pressureCorrector.C.
 * Changes: native conserved liquid+solid effective metal density, native
 * liquid-only metal mass flux, and density sync after pressure.
 * Pressure is NOT yet experimentally calibrated; thermo psi remains that
 * of liquid, and energy coupling will be part of the same dedicated module.
 * Upstream OpenFOAM Foundation GPL v3 license/copyright retained below.
 */
/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) 2022-2026 OpenFOAM Foundation
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
#include "PstreamReduceOps.H"
#include "upwind.H"
#include "harmonic.H"
#include "IOdictionary.H"
#include "zeroGradientFvPatchFields.H"
#include "fixedValueFvPatchFields.H"
#include <cmath>
#include "constrainHbyA.H"
#include "constrainPressure.H"
#include "adjustPhi.H"
#include "fvcMeshPhi.H"
#include "fvcFlux.H"
#include "fvcDdt.H"
#include "fvcSnGrad.H"
#include "fvcReconstruct.H"
#include "fvmDiv.H"
#include "fvmSup.H"
#include "fvmLaplacian.H"

// * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * * //

void Foam::solvers::fsC08ConservativeVoF::pressureCorrector()
{
    // Experimental serial, static, vented casting closure. The original
    // PISO pressure equation must NOT be applied again after projection.
    if (Pstream::parRun() || pimple.transonic() || mesh.moving())
        FatalErrorInFunction
            << "FS-C08 coupled volume path requires static serial non-transonic case"
            << exit(FatalError);

    volScalarField& T=mixture_.T();
    volScalarField& p_rgh=p_rgh_;
    volVectorField& U=U_;
    surfaceScalarField& phi=phi_;
    const dimensionedScalar dt=runTime.deltaT();

    // Freeze the real momentum matrix during the inner nonlinear closure.
    reconcileMixtureDensity();
    // Controlled numerical comparison, not a material property.
    // Keep the ten-step passing arithmetic reference as the default.
    const IOdictionary numerics
    (
        IOobject("fsC08Numerics",runTime.constant(),mesh,
                 IOobject::READ_IF_PRESENT,IOobject::NO_WRITE)
    );
    const word faceMobility=numerics.found("momentumFaceMobility")
        ? numerics.lookup<word>("momentumFaceMobility") : word("linear");
    if (faceMobility!="linear" && faceMobility!="harmonic")
        FatalErrorInFunction << "FS-C08 unknown momentumFaceMobility "
            << faceMobility << exit(FatalError);
    const word momentumCoupling=numerics.found("momentumMatrixCoupling")
        ? numerics.lookup<word>("momentumMatrixCoupling") : word("legacy");
    if (momentumCoupling!="legacy" && momentumCoupling!="refreshBeforePressure")
        FatalErrorInFunction << "FS-C08 unknown momentumMatrixCoupling "
            << momentumCoupling << exit(FatalError);
    const word phaseMobility=numerics.found("phasePressureMobility")
        ? numerics.lookup<word>("phasePressureMobility") : word("separate");
    if (phaseMobility!="separate" && phaseMobility!="phaseWeighted")
        FatalErrorInFunction << "FS-C08 unknown phasePressureMobility "
            << phaseMobility << exit(FatalError);
    if (phaseMobility=="phaseWeighted" && faceMobility!="linear")
        FatalErrorInFunction << "FS-C08 phaseWeighted comparison requires linear face mobility"
            << exit(FatalError);
    const word fluxMode=numerics.found("momentumFluxMode")
        ? numerics.lookup<word>("momentumFluxMode") : word("incremental");
    if (fluxMode!="incremental" && fluxMode!="totalUpwind"
        && fluxMode!="incrementalNoDdtCorr" && fluxMode!="totalUpwindNoDdtCorr")
        FatalErrorInFunction << "FS-C08 unknown momentumFluxMode " << fluxMode
            << exit(FatalError);
    const bool totalUpwind=fluxMode=="totalUpwind" || fluxMode=="totalUpwindNoDdtCorr";
    const bool noDdtCorr=fluxMode=="incrementalNoDdtCorr" || fluxMode=="totalUpwindNoDdtCorr";
    // Native PIMPLE assembles UEqn before the thermal predictor. FS-C08
    // changes the independent densities during that predictor. Rebuild
    // UEqn from the updated inventory and conservative fluxes once,
    // before constructing the pressure Schur complement.
    // No separate momentum solve or change to old-time inventories.
    if (momentumCoupling=="refreshBeforePressure")
    {
        if (pimple.momentumPredictor())
            FatalErrorInFunction << "FS-C08 refresh experiment requires momentumPredictor no"
                << exit(FatalError);
        // Update only internal reduced pressure here. fixedFluxPressure
        // requires constrainPressure() to install the CURRENT time-index
        // normal gradient before any boundary evaluation. The matrix
        // assembly (momentumPredictor no) does not solve for U.
        p_rgh.primitiveFieldRef()=
            p.primitiveField()-rho.primitiveField()*buoyancy.gh.primitiveField()
            -buoyancy.pRef.value();
        Info<< "FS_C08_MOMENTUM_REFRESH_BEGIN time_s=" << runTime.value()
            << " pressureBoundaryEvaluationDeferred=1" << nl;
        compressibleVoF::momentumPredictor();
        Info<< "FS_C08_MOMENTUM_REFRESH_ASSEMBLED time_s=" << runTime.value() << nl;
    }
    fvVectorMatrix& UEqn=tUEqn.ref();
    setrAU(UEqn);
    surfaceScalarField rAUf("fsC08MomentumMobility",fvc::interpolate(rAU()));
    if (faceMobility=="harmonic")
    {
        const tmp<surfaceScalarField> tHarmonic=harmonic(mesh).interpolate(rAU());
        // Only change internal face interpolation, preserving BC mobilities.
        rAUf.primitiveFieldRef()=tHarmonic().primitiveField();
    }
    forAll(rAUf,i)
        if (!std::isfinite(rAUf[i]) || rAUf[i]<=0)
            FatalErrorInFunction << "FS-C08 invalid face momentum mobility "
                << i << exit(FatalError);
    const volVectorField HbyA(constrainHbyA(rAU()*UEqn.H(),U,p_rgh));
    surfaceScalarField temporalFluxCorrection
    (
        "fsC08TemporalFluxCorrection",
        fvc::interpolate(rho*rAU())*fvc::ddtCorr(U,phi,Uf)
    );
    if (noDdtCorr)
        temporalFluxCorrection=dimensionedScalar(temporalFluxCorrection.dimensions(),0);
    surfaceScalarField phiHbyA
    (
        "fsC08MomentumPredictorFlux",
        fvc::flux(HbyA)+temporalFluxCorrection
    );
    MRF.makeRelative(phiHbyA);
    const surfaceScalarField phig
    (
        "fsC08GravitySurfaceFlux",
        (surfaceTensionForce()-buoyancy.ghf*fvc::snGrad(rho))
        *rAUf*mesh.magSf()
    );
    phiHbyA+=phig;
    constrainPressure(p_rgh,U,phiHbyA,rAUf,MRF);
    if (momentumCoupling=="refreshBeforePressure")
    {
        p_rgh.correctBoundaryConditions();
        Info<< "FS_C08_MOMENTUM_REFRESH_PRESSURE_BC_READY time_s="
            << runTime.value() << nl;
    }
    fvc::makeRelative(phiHbyA,U);

    // Homogeneous pressure increment BCs. Reject unknown boundary types.
    wordList incrementTypes(mesh.boundary().size(),"zeroGradient");
    label pressureAnchors=0;
    forAll(mesh.boundary(),patchi)
    {
        const word meshType=mesh.boundary()[patchi].type();
        const auto& bc=p_rgh.boundaryField()[patchi];
        if (mesh.boundary()[patchi].coupled())
            FatalErrorInFunction << "FS-C08 unsupported coupled pressure patch "
                << mesh.boundary()[patchi].name() << exit(FatalError);
        if (meshType=="empty" || meshType=="symmetry"
            || meshType=="symmetryPlane" || meshType=="wedge")
            incrementTypes[patchi]=meshType;
        else if (bc.fixesValue())
        {
            incrementTypes[patchi]="fixedValue";
            ++pressureAnchors;
        }
        else if (bc.type()!="zeroGradient" && bc.type()!="fixedFluxPressure")
            FatalErrorInFunction << "FS-C08 unsupported increment BC "
                << bc.type() << " on " << mesh.boundary()[patchi].name()
                << exit(FatalError);
    }
    if (!pressureAnchors)
        FatalErrorInFunction << "FS-C08 first coupled candidate requires "
            << "prescribed-pressure vent" << exit(FatalError);
    volScalarField dp
    (
        IOobject("pVolumeCorrection.fsC08",runTime.name(),mesh,
                 IOobject::NO_READ,IOobject::NO_WRITE),
        mesh,dimensionedScalar(p.dimensions(),0),incrementTypes
    );
    const volScalarField gasMassOld
    (
        "fsC08CoupledGasAtN",gasMassTrial_.oldTime()
    );
    const volScalarField gasSource
    (
        "fsC08CoupledGasSource",
        (fvModels().source(alpha2,mixture_.rho2())&mixture_.rho2())
    );
    const surfaceScalarField predictedPhi
    (
        "fsC08PredictedVolumeFlux",
        phiHbyA-rAUf*fvc::snGrad(p_rgh)*mesh.magSf()
    );
    const surfaceScalarField baselineDeltaPhi
    (
        "fsC08MomentumFluxIncrement",predictedPhi-phi
    );
    // Provisional superficial velocity: mobile volume is split between
    // liquid and gas, stationary solid enters via Darcy resistance.
    volScalarField wL
    (
        IOobject("fsC08LiquidMobileWeight",runTime.name(),mesh,
                 IOobject::NO_READ,IOobject::NO_WRITE),
        mesh,dimensionedScalar(dimless,0),"zeroGradient"
    );
    volScalarField wG
    (
        IOobject("fsC08GasMobileWeight",runTime.name(),mesh,
                 IOobject::NO_READ,IOobject::NO_WRITE),
        mesh,dimensionedScalar(dimless,0),"zeroGradient"
    );
    const auto updateWeights=[&]()
    {
        const auto& ml=phaseMass_->liquidMass().primitiveField();
        const auto& rl=phaseMass_->liquidDensity().primitiveField();
        const auto& mg=gasMassTrial_.primitiveField();
        const auto& rg=mixture_.rho2().primitiveField();
        forAll(ml,i)
        {
            const scalar l=ml[i]/rl[i], g=mg[i]/rg[i];
            const scalar mobile=l+g;
            wL[i]=mobile>0 ? l/mobile : 0;
            wG[i]=mobile>0 ? g/mobile : 0;
        }
        wL.correctBoundaryConditions();
        wG.correctBoundaryConditions();
        forAll(mesh.boundary(),patchi)
            if (incrementTypes[patchi]=="fixedValue")
            {
                wL.boundaryFieldRef()[patchi]=scalar(0);
                wG.boundaryFieldRef()[patchi]=scalar(1);
            }
    };
    updateWeights();
    surfaceScalarField fl("fsC08CoupledLiquidFlux",alphaRhoPhi1);
    surfaceScalarField fg("fsC08CoupledGasFlux",alphaRhoPhi2);
    const surfaceScalarField donorWL
    (
        "fsC08MomentumDonorL",
        upwind<scalar>(mesh,baselineDeltaPhi).interpolate(wL)
    );
    const surfaceScalarField donorWG
    (
        "fsC08MomentumDonorG",
        upwind<scalar>(mesh,baselineDeltaPhi).interpolate(wG)
    );
    if (totalUpwind)
    {
        // Diagnostic alternative: replace the incremental split with a
        // signed total predictor split, using the same mobile weights.
        // This deliberately removes the MULES compression contribution
        // from this predictor only; it is NOT a production VOF scheme.
        fl=fvc::interpolate(phaseMass_->liquidDensity())
            *upwind<scalar>(mesh,predictedPhi).interpolate(wL)*predictedPhi;
        fg=fvc::interpolate(mixture_.rho2())
            *upwind<scalar>(mesh,predictedPhi).interpolate(wG)*predictedPhi;
    }
    else
    {
        fl+=fvc::interpolate(phaseMass_->liquidDensity())*donorWL*baselineDeltaPhi;
        fg+=fvc::interpolate(mixture_.rho2())*donorWG*baselineDeltaPhi;
    }
    const surfaceScalarField rhoGFace
    (
        "fsC08VentedGasDensity",fvc::interpolate(mixture_.rho2())
    );
    forAll(mesh.boundary(),patchi)
        if (incrementTypes[patchi]=="fixedValue")
        {
            // For this geometry vents are gas-only, not metal feed/spill.
            forAll(fl.boundaryField()[patchi],facei)
                if (mag(fl.boundaryField()[patchi][facei])>SMALL)
                    FatalErrorInFunction << "FS-C08 unexpected metal flux at gas vent "
                        << mesh.boundary()[patchi].name() << exit(FatalError);
            fg.boundaryFieldRef()[patchi]=rhoGFace.boundaryField()[patchi]
                *predictedPhi.boundaryField()[patchi];
        }

    // The combined momentum predictor is not a converged pressure
    // flux. Its total signed transfer must also be admissible before
    // replaying from time n. Recompute pressure after this restriction.
    const volScalarField gasAvailable
    (
        "fsC08GasMomentumAvailable",gasMassOld+dt*gasSource
    );
    fsC08::limitPredictorMassFlux
        (fl,phaseMass_->liquidMass().oldTime(),"liquidMomentum");
    fsC08::limitPredictorMassFlux(fg,gasAvailable,"gasMomentum");

    const scalar volumeTolerance=1e-12;
    const scalar localMassTolerance=1e-10;
    const scalar temperatureTolerance=1e-6;
    const scalar phaseReplayTolerance=1e-10;
    const label maxCoupledCorrectors=30;
    bool converged=false;
    for (label iter=0;iter<maxCoupledCorrectors;++iter)
    {
        phaseMass_->replayTrialFromFlux(T,alpha1,fl);
        gasMassTrial_=fsC08::trialMassFromOldTime(gasMassOld,fg,gasSource);
        gasMassTrial_.correctBoundaryConditions();
        phaseMass_->refreshTrialProperties(T,alpha1);
        const volScalarField& rL=phaseMass_->liquidDensity();
        const volScalarField& rS=phaseMass_->solidDensity();
        const volScalarField& mS=phaseMass_->solidMass();
        const volScalarField& rG=mixture_.rho2();
        const tmp<volScalarField> initialResidual=fsC08::trialVolumeResidual
            (phaseMass_->liquidMass(),mS,gasMassTrial_,rL,rS,rG);
        updateWeights();
        surfaceScalarField liquidMobility
        (
            "fsC08LiquidPressureMobility",
            fvc::interpolate(rL)*fvc::interpolate(wL)*rAUf
        );
        surfaceScalarField gasMobility
        (
            "fsC08GasPressureMobility",
            fvc::interpolate(rG)*fvc::interpolate(wG)*rAUf
        );
        // Interpolate the product of conditional mobile-phase weight
        // and cell inverse momentum diagonal, instead of multiplying
        // two independently interpolated quantities. With a large
        // density contrast, the separate product couples a metal
        // weight to the much larger mobility of the neighbouring gas.
        // For linear interpolation and wL+wG=1, the sum of the two
        // volume mobilities remains interpolate(rAU). This is a
        // controlled discretisation experiment, not a phase-slip model.
        const surfaceScalarField weightedL
        (
            "fsC08WeightedLiquidMobility",
            fvc::interpolate(rL)*fvc::interpolate(wL*rAU())
        );
        const surfaceScalarField weightedG
        (
            "fsC08WeightedGasMobility",
            fvc::interpolate(rG)*fvc::interpolate(wG*rAU())
        );
        scalar maxCrossPhaseRatio=0,maxSumGap=0;
        label interfaceFace=-1;
        const auto& owner=mesh.owner();
        const auto& neighbour=mesh.neighbour();
        const surfaceScalarField weightedVolumeL
        (
            "fsC08WeightedLiquidVolumeMobility",
            fvc::interpolate(wL*rAU())
        );
        const surfaceScalarField weightedVolumeG
        (
            "fsC08WeightedGasVolumeMobility",
            fvc::interpolate(wG*rAU())
        );
        forAll(neighbour,facei)
        {
            // Reporting only: select strong phase-contrast faces.
            // No phase inventory or transport is thresholded.
            if (mag(wL[owner[facei]]-wL[neighbour[facei]])>0.5
                && weightedL[facei]>0)
            {
                const scalar ratio=liquidMobility[facei]/weightedL[facei];
                if (std::isfinite(ratio) && ratio>maxCrossPhaseRatio)
                {
                    maxCrossPhaseRatio=ratio;
                    interfaceFace=facei;
                }
            }
            if (rAUf[facei]>0)
                maxSumGap=max(maxSumGap,mag
                (
                    (weightedVolumeL[facei]+weightedVolumeG[facei])
                    /rAUf[facei]-1
                ));
        }
        if (phaseMobility=="phaseWeighted")
        {
            // Keep existing boundary mobilities, including gas-only vent.
            liquidMobility.primitiveFieldRef()=weightedL.primitiveField();
            gasMobility.primitiveFieldRef()=weightedG.primitiveField();
        }
        Info<< "FS_C08_PHASE_PRESSURE_MOBILITY"
            << " time_s=" << runTime.value() << " corrector=" << iter
            << " mode=" << phaseMobility
            << " maxSeparateToWeightedLiquidRatio=" << maxCrossPhaseRatio
            << " interfaceFace=" << interfaceFace
            << " maxWeightedVolumeMobilitySumGap=" << maxSumGap << nl;
        forAll(mesh.boundary(),patchi)
            if (incrementTypes[patchi]=="fixedValue")
                liquidMobility.boundaryFieldRef()[patchi]=scalar(0);

        // The pressure unknown changes transported liquid mass BEFORE
        // equilibrium phase conversion, not the post-conversion mobile
        // liquid. At fixed T, total metal M has volume M*((1-fs)/rhoL
        // +fs/rhoS). The old stationary solid remains an invariant in
        // this transport split; after projection the exact equilibrium
        // partition is replayed from n. A reduction of incoming liquid
        // is allowed even if that incoming liquid has since frozen.
        if (phaseMass_->phaseChangeClosure()!="equilibrium")
            FatalErrorInFunction
                << "FS-C08 equilibrium volume Jacobian requires equilibrium "
                << "phase closure; kinetic derivative not implemented"
                << exit(FatalError);
        volScalarField rhoEq("fsC08EquilibriumPressureDensity",rL);
        forAll(T,i)
            rhoEq[i]=phaseMass_->equilibriumDensity(T[i]);
        rhoEq.correctBoundaryConditions();
        const volScalarField& oldSolid=phaseMass_->solidMass().oldTime();
        volScalarField projectedL
        (
            "fsC08ProjectedTransportedLiquid",
            phaseMass_->liquidMass().oldTime()-dt*fvc::div(fl)
        );
        volScalarField projectedG("fsC08ProjectedG",gasMassTrial_);
        volScalarField projectedRhoG("fsC08ProjectedRhoG",rG);
        volScalarField projectedP("fsC08ProjectedP",p);
        scalar maxEquilibriumMismatch=0;
        forAll(T,i)
        {
            const scalar v=(projectedL[i]+oldSolid[i])/rhoEq[i]
                +projectedG[i]/rG[i]-1;
            maxEquilibriumMismatch=max(maxEquilibriumMismatch,
                mag(v-initialResidual()[i]));
        }
        Info<< "FS_C08_EQUILIBRIUM_PRESSURE_INVENTORY"
            << " corrector=" << iter
            << " maxPrePostConversionVolumeMismatch=" << maxEquilibriumMismatch
            << " minTransportedLiquid=" << min(projectedL).value() << nl;
        if (maxEquilibriumMismatch>volumeTolerance)
            FatalErrorInFunction << "FS-C08 equilibrium pressure inventory mismatch"
                << exit(FatalError);
        if (!fsC08::projectTrialInventories
            (projectedL,oldSolid,projectedG,rhoEq,rhoEq,projectedRhoG,
             mixture_.thermo2().psi(),projectedP,liquidMobility,
             gasMobility,fl,fg,dp))
            FatalErrorInFunction << "FS-C08 pressure projection rejected "
                << "at corrector " << iter << "; no accepted time step"
                << exit(FatalError);

        p=projectedP;
        fvConstraints().constrain(p);
        p.correctBoundaryConditions();
        mixture_.correctThermo();
        mixture_.correct();
        // Recalculate Gamma once from time n and the corrected flux.
        phaseMass_->replayTrialFromFlux(T,alpha1,fl);
        gasMassTrial_=fsC08::trialMassFromOldTime(gasMassOld,fg,gasSource);
        gasMassTrial_.correctBoundaryConditions();
        phaseMass_->refreshTrialProperties(T,alpha1);
        const tmp<volScalarField> replayedVolume=fsC08::trialVolumeResidual
        (
            phaseMass_->liquidMass(),phaseMass_->solidMass(),gasMassTrial_,
            phaseMass_->liquidDensity(),phaseMass_->solidDensity(),mixture_.rho2()
        );
        scalar fixedTReplayDefect=0;
        forAll(T,i)
            fixedTReplayDefect=max(fixedTReplayDefect,mag(replayedVolume()[i]));
        Info<< "FS_C08_FIXED_T_EQUILIBRIUM_REPLAY"
            << " corrector=" << iter
            << " maxResidual=" << fixedTReplayDefect << nl;
        if (fixedTReplayDefect>2*volumeTolerance)
            FatalErrorInFunction
                << "FS-C08 projected inventory and equilibrium replay disagree"
                << exit(FatalError);

        alphaRhoPhi1=phaseMass_->liquidMassFlux();
        alphaRhoPhi2=fg;
        alphaPhi1=alphaRhoPhi1/fvc::interpolate(phaseMass_->liquidDensity());
        alphaPhi2=alphaRhoPhi2/fvc::interpolate(mixture_.rho2());
        phi=alphaPhi1+alphaPhi2;
        rhoPhi=alphaRhoPhi1+alphaRhoPhi2;
        reconcileMixtureDensity();
        // Reconstruct the velocity with exactly the corrected face volume
        // flux; do not overwrite it with a second native pressure solve.
        U=HbyA+rAU()*fvc::reconstruct((phi-phiHbyA+phig)/rAUf);
        U.correctBoundaryConditions();
        fvConstraints().constrain(U);
        K=0.5*magSqr(U);
        p_rgh=p-rho*buoyancy.gh-buoyancy.pRef;
        p_rgh.correctBoundaryConditions();
        contErr1=(fvc::ddt(phaseMass_->liquidMass())()()
                 +fvc::ddt(phaseMass_->solidMass())()()
                 +fvc::div(alphaRhoPhi1)()());
        contErr2=(((gasMassTrial_-gasMassOld)/dt)()()
                 +fvc::div(alphaRhoPhi2)()()-gasSource());

        // Solve the actual energy equation again with corrected fluxes.
        const scalarField temperatureBefore(T.primitiveField());
        const scalarField liquidBefore(phaseMass_->liquidMass().primitiveField());
        const scalarField solidBefore(phaseMass_->solidMass().primitiveField());
        thermophysicalPredictor();
        phaseMass_->replayTrialFromFlux(T,alpha1,fl);
        phaseMass_->refreshTrialProperties(T,alpha1);
        const tmp<volScalarField> residual=fsC08::trialVolumeResidual
            (
                phaseMass_->liquidMass(),phaseMass_->solidMass(),gasMassTrial_,
                phaseMass_->liquidDensity(),phaseMass_->solidDensity(),mixture_.rho2()
            );
        // Local FV continuity audit in kg/m3 over this actual time step.
        // Global cancellation cannot hide a cell-level conservation defect.
        const volScalarField lDefect
        (
            "fsC08LocalLiquidDefect",
            phaseMass_->liquidMass()-phaseMass_->liquidMass().oldTime()
          + dt*(fvc::div(fl)+phaseMass_->gamma())
        );
        const volScalarField sDefect
        (
            "fsC08LocalSolidDefect",
            phaseMass_->solidMass()-phaseMass_->solidMass().oldTime()
          - dt*phaseMass_->gamma()
        );
        const volScalarField gDefect
        (
            "fsC08LocalGasDefect",
            gasMassTrial_-gasMassOld+dt*(fvc::div(fg)-gasSource)
        );
        scalar maxVolume=0,maxDT=0,maxReplay=0,maxOverfill=0;
        scalar maxLocalMetal=0,maxLocalGas=0;
        forAll(temperatureBefore,i)
        {
            maxVolume=max(maxVolume,mag(residual()[i]));
            maxDT=max(maxDT,mag(T[i]-temperatureBefore[i]));
            const scalar scale=max(scalar(1),liquidBefore[i]+solidBefore[i]);
            maxReplay=max(maxReplay,
                (mag(phaseMass_->liquidMass()[i]-liquidBefore[i])
                +mag(phaseMass_->solidMass()[i]-solidBefore[i]))/scale);
            const scalar occupied=phaseMass_->liquidMass()[i]/phaseMass_->liquidDensity()[i]
                                +phaseMass_->solidMass()[i]/phaseMass_->solidDensity()[i];
            maxOverfill=max(maxOverfill,occupied-scalar(1));
            const scalar scaleMetal=max(scalar(1),
                phaseMass_->liquidMass().oldTime()[i]+phaseMass_->solidMass().oldTime()[i]);
            const scalar scaleGas=max(scalar(1),max(gasMassOld[i],gasMassTrial_[i]));
            maxLocalMetal=max(maxLocalMetal,(mag(lDefect[i])+mag(sDefect[i]))/scaleMetal);
            maxLocalGas=max(maxLocalGas,mag(gDefect[i])/scaleGas);
        }
        reduce(maxVolume,maxOp<scalar>());
        reduce(maxDT,maxOp<scalar>());
        reduce(maxReplay,maxOp<scalar>());
        reduce(maxOverfill,maxOp<scalar>());
        reduce(maxLocalMetal,maxOp<scalar>());
        reduce(maxLocalGas,maxOp<scalar>());
        Info<< "FS_C08_COUPLED_VOLUME_ENERGY_ITER"
            << " time_s=" << runTime.value()
            << " corrector=" << iter+1
            << " maxVolumeResidual=" << maxVolume
            << " maxDeltaT_K=" << maxDT
            << " maxPhaseReplayRelative=" << maxReplay
            << " maxMetalOverfill=" << maxOverfill
            << " maxLocalMetalContinuity=" << maxLocalMetal
            << " maxLocalGasContinuity=" << maxLocalGas << nl;
        if (maxVolume<=volumeTolerance && maxDT<=temperatureTolerance
            && maxReplay<=phaseReplayTolerance && maxOverfill<=volumeTolerance
            && maxLocalMetal<=localMassTolerance && maxLocalGas<=localMassTolerance)
        {
            phaseMass_->acceptTrialFractions(T);
            // Only roundoff-level closure mismatch remains. The native
            // VOF pair must sum to exactly one. Normalize the geometry
            // by the total volume, NEVER the independent mass fields.
            // Reject larger corrections before this operation.
            scalar geometryCorrection=0;
            forAll(gasMassTrial_,i)
            {
                const scalar am=phaseMass_->alphaMetal()[i];
                const scalar ag=gasMassTrial_[i]/mixture_.rho2()[i];
                const scalar total=am+ag;
                if (!std::isfinite(total) || total<=0
                    || mag(total-scalar(1))>volumeTolerance
                    || am<0 || ag<0)
                    FatalErrorInFunction << "FS-C08 inadmissible accepted geometry "
                        << i << exit(FatalError);
                alpha1[i]=am/total;
                alpha2[i]=scalar(1)-alpha1[i];
                geometryCorrection=max(geometryCorrection,mag(alpha1[i]-am));
            }
            reduce(geometryCorrection,maxOp<scalar>());
            Info<< "FS_C08_NATIVE_VOF_ROUNDOFF_CLOSURE maxCorrection="
                << geometryCorrection << " conservedMassModified=0" << nl;
            alpha1.correctBoundaryConditions();
            alpha2.correctBoundaryConditions();
            correctInterface();
            mixture_.correct();
            reconcileMixtureDensity();
            updatePhaseInternalEnergy();
            converged=true;
            break;
        }
    }
    if (!converged)
        FatalErrorInFunction << "FS-C08 pressure-volume/energy iteration limit; "
            << "no mass clipping or accepted unconverged state" << exit(FatalError);

    // Independent gas inventory must agree with the actual EOS/VOF.
    scalar gasMismatch=0;
    forAll(gasMassTrial_,i)
        gasMismatch=max(gasMismatch,
            mag(alpha2[i]*mixture_.rho2()[i]-gasMassTrial_[i])
            /max(scalar(1),mixture_.rho2()[i]));
    reduce(gasMismatch,maxOp<scalar>());
    if (gasMismatch>2*volumeTolerance)
        FatalErrorInFunction << "FS-C08 accepted gas EOS mismatch " << gasMismatch
            << exit(FatalError);
    alphaRhoPhi1=phaseMass_->liquidMassFlux();
    alphaRhoPhi2=fg;
    alphaPhi1=alphaRhoPhi1/fvc::interpolate(phaseMass_->liquidDensity());
    alphaPhi2=alphaRhoPhi2/fvc::interpolate(mixture_.rho2());
    phi=alphaPhi1+alphaPhi2;
    rhoPhi=alphaRhoPhi1+alphaRhoPhi2;
    U=HbyA+rAU()*fvc::reconstruct((phi-phiHbyA+phig)/rAUf);
    U.correctBoundaryConditions();
    fvConstraints().constrain(U);
    K=0.5*magSqr(U);
    vDot=fvc::ddt(alpha1)()()+fvc::div(alphaPhi1)()()
        -alpha1()*fvc::div(phi)()();
    fvc::correctUf(Uf,U,fvc::absolute(phi,U),MRF);
    p_rgh=p-rho*buoyancy.gh-buoyancy.pRef;
    p_rgh.correctBoundaryConditions();
    // Audit numerical transport across the original metal/air support.
    // No threshold or deletion of trace inventories is used.
    scalar intoInitiallyGasKg=0,metalInInitiallyGasKg=0,counterflowVolume=0;
    label counterflowFaces=0;
    const auto& own=mesh.owner();
    const auto& nei=mesh.neighbour();
    const auto& oldL=phaseMass_->liquidMass().oldTime();
    const auto& oldS=phaseMass_->solidMass().oldTime();
    forAll(nei,facei)
    {
        const scalar q=alphaRhoPhi1[facei];
        const label receiver=q>=0 ? nei[facei] : own[facei];
        if (oldL[receiver]==0 && oldS[receiver]==0)
            intoInitiallyGasKg+=dt.value()*mag(q);
        const scalar qL=alphaPhi1[facei],qG=alphaPhi2[facei];
        if ((qL>0 && qG<0) || (qL<0 && qG>0))
        {
            ++counterflowFaces;
            counterflowVolume+=dt.value()*min(mag(qL),mag(qG));
        }
    }
    forAll(oldL,i)
        if (oldL[i]==0 && oldS[i]==0)
            metalInInitiallyGasKg+=mesh.V()[i]*
                (phaseMass_->liquidMass()[i]+phaseMass_->solidMass()[i]);
    Info<< "FS_C08_INTERFACE_TRANSPORT_AUDIT"
        << " time_s=" << runTime.value() << " fluxMode=" << fluxMode
        << " grossMetalTransferIntoPreviouslyGasCells_kg=" << intoInitiallyGasKg
        << " retainedMetalInPreviouslyGasCells_kg=" << metalInInitiallyGasKg
        << " counterflowFaces=" << counterflowFaces
        << " counterflowVolume_m3=" << counterflowVolume
        << " diagnosticOnly=1" << nl;
    // An independent comparison: the accepted conservative flux
    // reconstruction versus the frozen matrix's direct pressure-gradient
    // velocity. Neither diagnostic overwrites the accepted solution.
    const volVectorField pressureGradientU
    (
        "fsC08PressureGradientVelocity",
        HbyA+rAU()*fvc::reconstruct
        (
            phig/rAUf-fvc::snGrad(p_rgh)*mesh.magSf()
        )
    );
    const surfaceScalarField fluxFromU("fsC08FluxFromAcceptedU",fvc::flux(U));
    const volVectorField pressureContribution
    (
        "fsC08PressureContribution",
        -rAU()*fvc::reconstruct(fvc::snGrad(p_rgh)*mesh.magSf())
    );
    const volVectorField gravitySurfaceContribution
    (
        "fsC08GravitySurfaceContribution",
        rAU()*fvc::reconstruct(phig/rAUf)
    );
    label fastest=-1;
    scalar maxSpeed=-1;
    forAll(U,i)
        if (mag(U[i])>maxSpeed)
        {
            fastest=i;
            maxSpeed=mag(U[i]);
        }
    scalar maxTemporalNormal=0;
    forAll(temporalFluxCorrection,facei)
        maxTemporalNormal=max(maxTemporalNormal,
            mag(temporalFluxCorrection[facei])/mesh.magSf()[facei]);
    if (fastest>=0)
    {
        const label i=fastest;
        Info<< "FS_C08_MOMENTUM_FORCE_SPLIT"
            << " time_s=" << runTime.value()
            << " matrixCoupling=" << momentumCoupling
            << " cell=" << i << " alphaMetal=" << alpha1[i]
            << " speed_m_s=" << maxSpeed
            << " HbyA_m_s=" << HbyA[i]
            << " pressureContribution_m_s=" << pressureContribution[i]
            << " gravitySurfaceContribution_m_s=" << gravitySurfaceContribution[i]
            << " maxTemporalFaceCorrection_m_s=" << maxTemporalNormal
            << " diagnosticOnly=1" << nl;
    }
    scalar maxVelocityGap=0,maxPressureVelocity=0,maxFaceGap=0;
    scalar maxPureGasGap=0,maxPureGasSpeed=0;
    label gapCell=-1,faceGapId=-1;
    forAll(U,i)
    {
        const scalar gap=mag(U[i]-pressureGradientU[i]);
        maxPressureVelocity=max(maxPressureVelocity,mag(pressureGradientU[i]));
        if (gap>maxVelocityGap)
        {
            maxVelocityGap=gap;
            gapCell=i;
        }
        if (phaseMass_->liquidMass()[i]==0 && phaseMass_->solidMass()[i]==0)
        {
            maxPureGasGap=max(maxPureGasGap,gap);
            maxPureGasSpeed=max(maxPureGasSpeed,mag(U[i]));
        }
    }
    forAll(phi,facei)
    {
        const scalar gap=mag(phi[facei]-fluxFromU[facei])/mesh.magSf()[facei];
        if (gap>maxFaceGap)
        {
            maxFaceGap=gap;
            faceGapId=facei;
        }
    }
    Info<< "FS_C08_MOMENTUM_CONSISTENCY"
        << " time_s=" << runTime.value()
        << " faceMobility=" << faceMobility
        << " maxVelocityGap_m_s=" << maxVelocityGap
        << " maxDirectPressureSpeed_m_s=" << maxPressureVelocity
        << " maxPureGasVelocityGap_m_s=" << maxPureGasGap
        << " maxPureGasSpeed_m_s=" << maxPureGasSpeed
        << " maxInternalFaceNormalGap_m_s=" << maxFaceGap
        << " face=" << faceGapId << " cell=" << gapCell;
    if (gapCell>=0)
        Info<< " center_m=" << mesh.C()[gapCell]
            << " reconstructedU=" << U[gapCell]
            << " pressureGradientU=" << pressureGradientU[gapCell]
            << " alphaMetal=" << alpha1[gapCell]
            << " rho_kg_m3=" << rho[gapCell];
    Info<< " diagnosticOnly=1" << nl;
    Info<< "FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY"
        << " time_s=" << runTime.value()
        << " gasEOSMismatch=" << gasMismatch
        << " pressureVolumeEnergyIterationConverged=1"
        << " independentGasTrialMass=1"
        << " frozenMomentumMatrixApproximation=1"
        << " physicalShrinkageValidated=0" << nl;
    // Audit the accepted velocity against a freshly assembled native
    // matrix, without solving or changing U. This measures a velocity-
    // equivalent algebraic defect, not a validated full momentum PDE
    // residual (the single-velocity and interface force model remain).
    if (!pimple.momentumPredictor())
    {
        compressibleVoF::momentumPredictor();
        setrAU(tUEqn.ref());
        const volVectorField freshHbyA
        (
            "fsC08FreshHbyA",
            constrainHbyA(rAU()*tUEqn.ref().H(),U,p_rgh)
        );
        const volVectorField freshTarget
        (
            "fsC08FreshMomentumTarget",
            freshHbyA+rAU()*fvc::reconstruct
            (
                (surfaceTensionForce()-buoyancy.ghf*fvc::snGrad(rho)
                 -fvc::snGrad(p_rgh))*mesh.magSf()
            )
        );
        scalar maxDefect=0,maxGasDefect=0;
        label worst=-1;
        forAll(U,i)
        {
            const scalar defect=mag(U[i]-freshTarget[i]);
            if (defect>maxDefect) {maxDefect=defect; worst=i;}
            if (phaseMass_->liquidMass()[i]==0 && phaseMass_->solidMass()[i]==0)
                maxGasDefect=max(maxGasDefect,defect);
        }
        Info<< "FS_C08_FRESH_MOMENTUM_DEFECT"
            << " time_s=" << runTime.value()
            << " matrixCoupling=" << momentumCoupling
            << " maxVelocityEquivalentDefect_m_s=" << maxDefect
            << " maxPureGasDefect_m_s=" << maxGasDefect
            << " cell=" << worst << " diagnosticOnly=1" << nl;
    }
    clearrAU();
    tUEqn.clear();
}
// ************************************************************************* //
