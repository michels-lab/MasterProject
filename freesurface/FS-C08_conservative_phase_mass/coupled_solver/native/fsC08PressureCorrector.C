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
    fvVectorMatrix& UEqn=tUEqn.ref();
    setrAU(UEqn);
    const surfaceScalarField rAUf("fsC08MomentumMobility",fvc::interpolate(rAU()));
    const volVectorField HbyA(constrainHbyA(rAU()*UEqn.H(),U,p_rgh));
    surfaceScalarField phiHbyA
    (
        "fsC08MomentumPredictorFlux",
        fvc::flux(HbyA)+fvc::interpolate(rho*rAU())*fvc::ddtCorr(U,phi,Uf)
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
        "fsC08CoupledGasAtN",alpha2.oldTime()*mixture_.rho2().oldTime()
    );
    const volScalarField gasSource
    (
        "fsC08CoupledGasSource",
        (gasMassTrial_-gasMassOld)/dt+fvc::div(alphaRhoPhi2)
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
    fl+=fvc::interpolate(phaseMass_->liquidDensity())*donorWL*baselineDeltaPhi;
    fg+=fvc::interpolate(mixture_.rho2())*donorWG*baselineDeltaPhi;
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

    const scalar volumeTolerance=1e-12;
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
        forAll(mesh.boundary(),patchi)
            if (incrementTypes[patchi]=="fixedValue")
                liquidMobility.boundaryFieldRef()[patchi]=scalar(0);

        volScalarField projectedL("fsC08ProjectedL",phaseMass_->liquidMass());
        volScalarField projectedG("fsC08ProjectedG",gasMassTrial_);
        volScalarField projectedRhoG("fsC08ProjectedRhoG",rG);
        volScalarField projectedP("fsC08ProjectedP",p);
        if (!fsC08::projectTrialInventories
            (projectedL,mS,projectedG,rL,rS,projectedRhoG,
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
        scalar maxVolume=0,maxDT=0,maxReplay=0,maxOverfill=0;
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
        }
        reduce(maxVolume,maxOp<scalar>());
        reduce(maxDT,maxOp<scalar>());
        reduce(maxReplay,maxOp<scalar>());
        reduce(maxOverfill,maxOp<scalar>());
        Info<< "FS_C08_COUPLED_VOLUME_ENERGY_ITER"
            << " time_s=" << runTime.value()
            << " corrector=" << iter+1
            << " maxVolumeResidual=" << maxVolume
            << " maxDeltaT_K=" << maxDT
            << " maxPhaseReplayRelative=" << maxReplay
            << " maxMetalOverfill=" << maxOverfill << nl;
        if (maxVolume<=volumeTolerance && maxDT<=temperatureTolerance
            && maxReplay<=phaseReplayTolerance && maxOverfill<=0)
        {
            phaseMass_->acceptTrialFractions(T);
            alpha1=phaseMass_->alphaMetal();
            alpha2=scalar(1)-alpha1;
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
    vDot=fvc::ddt(alpha1)()()+fvc::div(alphaPhi1)()()
        -alpha1()*fvc::div(phi)()();
    fvc::correctUf(Uf,U,fvc::absolute(phi,U),MRF);
    p_rgh=p-rho*buoyancy.gh-buoyancy.pRef;
    p_rgh.correctBoundaryConditions();
    Info<< "FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY"
        << " time_s=" << runTime.value()
        << " gasEOSMismatch=" << gasMismatch
        << " pressureVolumeEnergyIterationConverged=1"
        << " independentGasTrialMass=1"
        << " frozenMomentumMatrixApproximation=1"
        << " physicalShrinkageValidated=0" << nl;
    clearrAU();
    tUEqn.clear();
}
// ************************************************************************* //
