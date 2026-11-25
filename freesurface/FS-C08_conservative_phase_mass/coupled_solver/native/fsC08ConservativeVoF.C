/* FS-C08 | physically distinct native CFD phase mass equations.
 * GPL-3.0-or-later. Does not modify installed OpenFOAM14.
 */
#include "fsC08ConservativeVoF.H"
#include "FS_C08_VolumeProjection.H"
#include "addToRunTimeSelectionTable.H"
#include "fvcDdt.H"
#include "fvcDiv.H"
#include "fvc.H"
#include "zeroGradientFvPatchFields.H"
#include "PstreamReduceOps.H"
#include <cmath>

namespace Foam
{
namespace solvers
{
    defineTypeNameAndDebug(fsC08ConservativeVoF,0);
    addToRunTimeSelectionTable(solver,fsC08ConservativeVoF,fvMesh);
}

solvers::fsC08ConservativeVoF::fsC08ConservativeVoF(fvMesh& mesh)
:
    compressibleVoF(mesh),
    phaseMass_
    (
        new fsC08::PhaseMassTransport(mesh,alpha1,mixture_.T())
    ),
    gasMassTrial_
    (
        IOobject
        (
            "rhoAlpha.airTrial.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::AUTO_WRITE
        ),
        alpha2*mixture_.rho2()
    ),
    rhoMetalEffective_
    (
        IOobject
        (
            "rhoMetalEffective.fsC08",mesh.time().name(),mesh,
            IOobject::READ_IF_PRESENT,IOobject::AUTO_WRITE
        ),
        mesh,dimensionedScalar(dimDensity,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    phaseInternalEnergy_
    (
        IOobject
        (
            "internalEnergy.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::AUTO_WRITE
        ),
        mesh,dimensionedScalar(dimEnergy/dimVolume,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    phaseEnergyPhi_
    (
        IOobject
        (
            "energyFlux.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::NO_WRITE
        ),
        mesh,dimensionedScalar(dimPower,0)
    ),
    phaseHeatPhi_
    (
        IOobject
        (
            "heatFlux.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::NO_WRITE
        ),
        mesh,dimensionedScalar(dimPower,0)
    ),
    mechanicalWorkDensity_
    (
        IOobject
        (
            "mechanicalWorkDensity.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::AUTO_WRITE
        ),
        mesh,dimensionedScalar(dimPower/dimVolume,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    mushyDarcyResistance_
    (
        IOobject
        (
            "mushyDarcyResistance.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::AUTO_WRITE
        ),
        mesh,dimensionedScalar(dimDensity/dimTime,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    mushyDarcyDissipation_
    (
        IOobject
        (
            "mushyDarcyDissipation.fsC08",mesh.time().name(),mesh,
            IOobject::NO_READ,IOobject::AUTO_WRITE
        ),
        mesh,dimensionedScalar(dimPower/dimVolume,0),
        zeroGradientFvPatchScalarField::typeName
    )
{
    // This first native phase-mass/energy formulation assumes the
    // FS-C07 STATIC Eulerian fluid mesh. Using volume V(n+1) for
    // masses at n on a moving/changing mesh would break the GCL and
    // silently corrupt both mass and internal-energy ledgers.
    if (mesh.moving() || mesh.topoChanging())
    {
        FatalErrorInFunction
            << "FS-C08 current CFD phase mass + energy equations "
            << "are for stationary non-topology-changing fvMesh only. "
            << "Moving mesh requires conservative V(n)/V(n+1) "
            << "geometric conservation and remapping."
            << exit(FatalError);
    }

    // The density curves rhoLiquid(T), rhoSolid(T) have no pressure
    // argument. Thus, within this first EOS closure, metal psi MUST
    // be zero (pressure-incompressible). Gas retains its native
    // compressible EOS. Never combine independent rho(T) with nonzero
    // liquid psi(p,T) in the same pressure equation.
    if (!mixture_.thermo1().incompressible())
    {
        FatalErrorInFunction
            << "FS-C08 rhoLiquidT(T) and rhoSolidT(T) require a "
            << "pressure-incompressible METAL thermo package in this "
            << "implementation. The gas may remain compressible. "
            << "Nonzero metal psi would violate the chosen equation "
            << "of state; use a fully p,T-dependent phase EOS first."
            << exit(FatalError);
    }

    // Phase energies now have exactly ONE latent offset in u_l(T).
    // The old VoFSolidificationMelting source L*ddt(rho,alphaSolid)
    // would double-count it. The stand-alone total-energy equation
    // does NOT incorporate arbitrary legacy fluid fvModel heat sources:
    // reject them instead of silently violating the first law.
    if
    (
        fvModels().addsSupToField(mixture_.thermo1().he().name())
     || fvModels().addsSupToField(mixture_.thermo2().he().name())
    )
    {
        FatalErrorInFunction
            << "FS-C08 rejects inherited fvModel fluid energy sources. "
            << "Disable legacy VoFSolidificationMelting and supply heat "
            << "via the native conjugate conduction term. Latent heat "
            << "is already in u_liquid(Tref)-u_solid(Tref)."
            << exit(FatalError);
    }

    // Establish one thermodynamically consistent t=0 state AFTER the
    // base constructor has initialized pressure/buoyancy. Never rebuild
    // conserved gas mass from mutable native thermo oldTime fields later.
    mixture_.correctThermo();
    mixture_.correct();
    gasMassTrial_=alpha2*mixture_.rho2();
    gasMassTrial_.correctBoundaryConditions();
    gasMassTrial_.oldTime();
    // Foundation14 creates alpha2 as 1-alpha1 without AUTO_WRITE.
    // FS-C08 requires both native geometry fields in every saved state
    // for independent inspection of the conservative gas inventory.
    mixture_.alpha2().writeOpt()=IOobject::AUTO_WRITE;
    mixture_.T().oldTime();
    reconcileMixtureDensity();
    rhoMetalEffective_.oldTime();
    scalar initialGasMass=0, initialVolumeDefect=0;
    const auto& cellVolumes=mesh.V();
    forAll(gasMassTrial_,i)
    {
        initialGasMass+=gasMassTrial_[i]*cellVolumes[i];
        const scalar occupied=
              phaseMass_->liquidMass()[i]/phaseMass_->liquidDensity()[i]
            + phaseMass_->solidMass()[i]/phaseMass_->solidDensity()[i]
            + gasMassTrial_[i]/mixture_.rho2()[i];
        if (!std::isfinite(occupied))
            FatalErrorInFunction << "FS-C08 nonfinite initial phase volume "
                << i << exit(FatalError);
        initialVolumeDefect=max(initialVolumeDefect,mag(occupied-1));
    }
    reduce(initialGasMass,sumOp<scalar>());
    reduce(initialVolumeDefect,maxOp<scalar>());
    Info<< "FS_C08_INITIAL_GAS_INVENTORY"
        << " mass_kg=" << initialGasMass
        << " maxInitialVolumeDefect=" << initialVolumeDefect
        << " rhoMin=" << min(mixture_.rho2()).value()
        << " rhoMax=" << max(mixture_.rho2()).value()
        << " Tmin=" << min(mixture_.T()).value()
        << " Tmax=" << max(mixture_.T()).value() << nl;
    if (initialVolumeDefect>1e-12)
        FatalErrorInFunction << "FS-C08 initial gas/metal volume inconsistent"
            << exit(FatalError);
    updatePhaseInternalEnergy();
    phaseInternalEnergy_.oldTime();
    Info<< "FS_C08_COUPLED_SOLVER_MODULE_INSTALLED "
        << "materialId=" << phaseMass_->materialId()
        << " source=" << phaseMass_->propertySource()
        << " (not experimentally validated)" << nl;
}

solvers::fsC08ConservativeVoF::~fsC08ConservativeVoF()
{}

void solvers::fsC08ConservativeVoF::reconcileMixtureDensity()
{
    // Base compressibleVoF uses rho1*alphaMetal+rho2*alphaAir; that
    // is WRONG with rhoSolid != rhoLiquid. The actual metal mass is
    // rhoAlpha.liquid + rhoAlpha.solid, both kg/m3.
    volScalarField& mixtureDensity = const_cast<volScalarField&>(rho);
    const auto& ml=phaseMass_->liquidMass().primitiveField();
    const auto& ms=phaseMass_->solidMass().primitiveField();
    const auto& rL=phaseMass_->liquidDensity().primitiveField();
    const auto& rS=phaseMass_->solidDensity().primitiveField();
    auto& rMetal=rhoMetalEffective_.primitiveFieldRef();
    forAll(rMetal,i)
    {
        const scalar trialVolume=ml[i]/rL[i]+ms[i]/rS[i];
        rMetal[i]=trialVolume>0 ? (ml[i]+ms[i])/trialVolume : rL[i];
    }
    rhoMetalEffective_.correctBoundaryConditions();
    mixtureDensity =
        phaseMass_->liquidMass()
      + phaseMass_->solidMass()
      + gasMassTrial_;
    mixtureDensity.correctBoundaryConditions();
}

void solvers::fsC08ConservativeVoF::updatePhaseInternalEnergy()
{
    // Post-processing field in J/m3, carried forward across timesteps.
    // Uses the EXACT same thermodynamic reference as the nonlinear
    // energy PDE. Gas internal energy comes from native compressible EOS.
    const auto& ml=phaseMass_->liquidMass().primitiveField();
    const auto& ms=phaseMass_->solidMass().primitiveField();
    const auto& T=mixture_.T().primitiveField();
    const auto& gasMass=gasMassTrial_.primitiveField();
    const auto& uGas=mixture_.thermo2().he().primitiveField();
    auto& energy=phaseInternalEnergy_.primitiveFieldRef();

    forAll(energy,i)
    {
        scalar liquid=0,solid=0;
        if (ml[i]>0 || ms[i]>0)
        {
            liquid=phaseMass_->liquidInternalEnergy(T[i]);
            solid=phaseMass_->solidInternalEnergy(T[i]);
        }
        energy[i]=
            ml[i]*liquid
          + ms[i]*solid
          + gasMass[i]*uGas[i];
        if (!std::isfinite(energy[i]))
        {
            FatalErrorInFunction
                << "FS-C08 nonfinite conserved internal-energy inventory "
                << "in cell " << i << exit(FatalError);
        }
    }
    phaseInternalEnergy_.correctBoundaryConditions();
}


void solvers::fsC08ConservativeVoF::prePredictor()
{
    // Snapshot the old physical gas inventory before base MULES can
    // change alpha. Replaying an outer corrector always starts at n.
    const volScalarField gasMassOld
    (
        "fsC08GasMassAtN",
        gasMassTrial_.oldTime()
    );
    // MULES provides a real, all-face metal VOF flux from evolving U.
    compressibleVoF::prePredictor();

    // Preserve native gas volume flux before liquid-only transport
    // changes the metal flux. Do not turn a withheld liquid/solid flux
    // into a fictitious gas flux through a metal cell.
    const surfaceScalarField nativeGasPhi("fsC08NativeGasPredictorPhi",phi-alphaPhi1);
    // Actual finite-volume continuity for liquid and stationary solid.
    phaseMass_->solve(mixture_.T(),alpha1,alphaPhi1);

    // Keep native bounded MULES geometry as provisional geometry.
    // The independent trial masses are not yet admissible VOF.
    // Publish phaseMass alpha only after pressure/volume closure.

    // Flow of solid skeleton is zero. Only liquid carries metal mass.
    alphaRhoPhi1 = phaseMass_->liquidMassFlux();
    alphaPhi1 =
        alphaRhoPhi1/fvc::interpolate(phaseMass_->liquidDensity());
    alphaPhi2 = nativeGasPhi;
    alphaRhoPhi2 = fvc::interpolate(mixture_.rho2())*alphaPhi2;

    // Predict gas mass from the actual old inventory and signed FV gas
    // mass flux, not from a provisional complement of alpha.metal.
    const volScalarField gasSource
    (
        "fsC08GasTrialMassSource",
        (fvModels().source(alpha2,mixture_.rho2())&mixture_.rho2())
    );
    const volScalarField gasAvailable
    (
        "fsC08GasPredictorAvailable",gasMassOld+runTime.deltaT()*gasSource
    );
    fsC08::limitPredictorMassFlux(alphaRhoPhi2,gasAvailable,"gasMULES");
    alphaPhi2=alphaRhoPhi2/fvc::interpolate(mixture_.rho2());
    phi_=alphaPhi1+alphaPhi2;
    rhoPhi=alphaRhoPhi1+alphaRhoPhi2;
    gasMassTrial_=fsC08::trialMassFromOldTime
    (
        gasMassOld,alphaRhoPhi2,gasSource
    );
    forAll(gasMassTrial_,i)
    {
        if (!std::isfinite(gasMassTrial_[i]) || gasMassTrial_[i]<0)
            FatalErrorInFunction
                << "FS-C08 inadmissible gas trial mass cell=" << i
                << "; no clipping" << exit(FatalError);
    }
    gasMassTrial_.correctBoundaryConditions();

    const tmp<volScalarField> preEnergyResidual=fsC08::trialVolumeResidual
    (
        phaseMass_->liquidMass(),phaseMass_->solidMass(),gasMassTrial_,
        phaseMass_->liquidDensity(),phaseMass_->solidDensity(),mixture_.rho2()
    );
    scalar maxPreEnergyDefect=0;
    forAll(preEnergyResidual(),i)
        maxPreEnergyDefect=max(maxPreEnergyDefect,mag(preEnergyResidual()[i]));
    reduce(maxPreEnergyDefect,maxOp<scalar>());
    Info<< "FS_C08_PRE_ENERGY_VOLUME"
        << " time_s=" << runTime.value()
        << " maxAbsResidual=" << maxPreEnergyDefect << nl;

    // Per-phase mass continuity errors are now from physical inventory.
    contErr1 =
    (
        fvc::ddt(phaseMass_->liquidMass())()()
      + fvc::ddt(phaseMass_->solidMass())()()
      + fvc::div(alphaRhoPhi1)()()
    );
    contErr2 =
    (
        ((gasMassTrial_-gasMassOld)/runTime.deltaT())()()
      + fvc::div(alphaRhoPhi2)()()
      - gasSource()
    );

    mixture_.correct();
    reconcileMixtureDensity();

}

// Audit AFTER the actual gas EOS, pressure corrector and energy solve.
void solvers::fsC08ConservativeVoF::postSolve()
{
    compressibleVoF::postSolve();

    // Snapshot the stored accepted internal energy before this postSolve
    // reconstruction. The difference audits postSolve consistency;
    // it is NOT an isolated pressure-work measurement.
    const scalarField energyBeforePressure
    (
        phaseInternalEnergy_.primitiveField()
    );

    // Ensure the base postSolve did not overwrite the accepted gas closure.
    scalar postSolveGasMismatch=0;
    forAll(gasMassTrial_,i)
        postSolveGasMismatch=max(postSolveGasMismatch,
            mag(gasMassTrial_[i]-alpha2[i]*mixture_.rho2()[i])
            /max(scalar(1),mixture_.rho2()[i]));
    reduce(postSolveGasMismatch,maxOp<scalar>());
    if (postSolveGasMismatch>2e-12)
        FatalErrorInFunction
            << "FS-C08 postSolve changed accepted gas inventory "
            << postSolveGasMismatch << exit(FatalError);
    // Now include the actual corrected gas p/rho/u state.
    updatePhaseInternalEnergy();
    // Darcy dissipation must use the velocity AFTER the final native
    // momentum/pressure correction. The old predictor U used when
    // assembling fvm::Sp(R,U) would misstate physical energy loss.
    const auto& R=mushyDarcyResistance_.primitiveField();
    const auto& finalU=U.primitiveField();
    auto& dragHeat=mushyDarcyDissipation_.primitiveFieldRef();
    forAll(dragHeat,i)
    {
        dragHeat[i]=R[i]*magSqr(finalU[i]);
        if (!std::isfinite(dragHeat[i]) || dragHeat[i]<0)
            FatalErrorInFunction
                << "FS-C08 nonfinite final PIMPLE Darcy dissipation cell "
                << i << exit(FatalError);
    }
    mushyDarcyDissipation_.correctBoundaryConditions();

    // Runtime budget from REAL CFD state, all fluid cells and all
    // fluid boundary patches. Gamma cancels in total metal mass.
    // This is a physical conservation metric, NOT a synthetic test.
    const auto& V=mesh.V();
    const auto& l=phaseMass_->liquidMass().primitiveField();
    const auto& s=phaseMass_->solidMass().primitiveField();
    const auto& l0=phaseMass_->liquidMass().oldTime().primitiveField();
    const auto& s0=phaseMass_->solidMass().oldTime().primitiveField();
    const auto& rGas=mixture_.rho2().primitiveField();
    const auto& aGas=alpha2.primitiveField();
    const auto& gas0=gasMassTrial_.oldTime().primitiveField();
    scalar M0=0, M=0, Mgas=0, Mgas0=0;
    scalar E0=0,E=0,mechanicalWork_W=0,darcyDissipation_W=0;
    scalar postPressureEnergyJump_J=0;
    const auto& workDensity=mechanicalWorkDensity_.primitiveField();
    const auto& darcyHeat=mushyDarcyDissipation_.primitiveField();
    const auto& u=phaseInternalEnergy_.primitiveField();
    const auto& u0=phaseInternalEnergy_.oldTime().primitiveField();
    forAll(V,i)
    {
        M0+=V[i]*(l0[i]+s0[i]);
        M+=V[i]*(l[i]+s[i]);
        Mgas+=V[i]*aGas[i]*rGas[i];
        Mgas0+=V[i]*gas0[i];
        E+=V[i]*u[i];
        E0+=V[i]*u0[i];
        postPressureEnergyJump_J+=
            V[i]*(u[i]-energyBeforePressure[i]);
        mechanicalWork_W+=V[i]*workDensity[i];
        darcyDissipation_W+=V[i]*darcyHeat[i];
    }
    reduce(M0,sumOp<scalar>());
    reduce(M,sumOp<scalar>());
    reduce(Mgas,sumOp<scalar>());
    reduce(Mgas0,sumOp<scalar>());
    reduce(E0,sumOp<scalar>());
    reduce(E,sumOp<scalar>());
    reduce(postPressureEnergyJump_J,sumOp<scalar>());
    reduce(mechanicalWork_W,sumOp<scalar>());
    reduce(darcyDissipation_W,sumOp<scalar>());

    scalar boundaryMassRate=0;
    const auto& patches=phaseMass_->liquidMassFlux().boundaryField();
    forAll(patches,patchi)
    {
        const auto& patchFlux=patches[patchi];
        forAll(patchFlux,facei)
        {
            boundaryMassRate+=patchFlux[facei];
        }
    }
    reduce(boundaryMassRate,sumOp<scalar>());

    // Native air flux is from two-phase mixture. Here it is audited
    // after pressure correction, rather than being mistaken for a
    // separately solved three-phase gas continuity equation.
    scalar gasBoundaryOut=0;
    const auto& gasPatches=alphaRhoPhi2.boundaryField();
    forAll(gasPatches,patchi)
    {
        const auto& gasFlux=gasPatches[patchi];
        forAll(gasFlux,facei) gasBoundaryOut+=gasFlux[facei];
    }
    reduce(gasBoundaryOut,sumOp<scalar>());

    // Energy crossing ACTUAL fluid boundary faces. This is not yet a
    // closed total-energy residual, since wall heat and mechanical
    // work must also enter with correct signs.
    scalar liquidEnergyOut_W=0;
    scalar gasEnergyOut_W=0;
    const auto& liquidBoundary=
        phaseMass_->liquidMassFlux().boundaryField();
    const auto& gasBoundary=alphaRhoPhi2.boundaryField();
    const auto& temperatureBoundary=mixture_.T().boundaryField();
    const auto& gasEnergyBoundary=
        mixture_.thermo2().he().boundaryField();
    forAll(liquidBoundary,patchi)
    {
        forAll(liquidBoundary[patchi],facei)
        {
            const scalar fL=liquidBoundary[patchi][facei];
            if (mag(fL)>SMALL)
            {
                // Check real boundary phase temperature against sourced
                // material curves; no imaginary inlet energy at air T.
                liquidEnergyOut_W+=fL*
                    phaseMass_->liquidInternalEnergy
                    (
                        temperatureBoundary[patchi][facei]
                    );
            }
            gasEnergyOut_W+=
                gasBoundary[patchi][facei]
               *gasEnergyBoundary[patchi][facei];
        }
    }
    reduce(liquidEnergyOut_W,sumOp<scalar>());
    reduce(gasEnergyOut_W,sumOp<scalar>());

    // These are the face fluxes from the ACTUAL last energy
    // linear solve, not fluxes reconstructed later after p correction.
    // Sign convention is outward from fluid patch into mold/ambient.
    scalar energyAdvectionOut_W=0;
    scalar conductionOut_W=0;
    const auto& energyPatches=phaseEnergyPhi_.boundaryField();
    const auto& heatPatches=phaseHeatPhi_.boundaryField();
    forAll(energyPatches,patchi)
    {
        const auto& energyPatch=energyPatches[patchi];
        const auto& heatPatch=heatPatches[patchi];
        forAll(energyPatch,facei)
        {
            energyAdvectionOut_W+=energyPatch[facei];
            conductionOut_W+=heatPatch[facei];
        }
    }
    reduce(energyAdvectionOut_W,sumOp<scalar>());
    reduce(conductionOut_W,sumOp<scalar>());

    // Actual open-face metal feeding and mold/ambient heat extraction
    // MUST remain distinguishable. A single global outflow can cancel
    // feeding and discharge from different boundaries. These labels
    // use the actual region mesh patch names; no patch is classified
    // as "inlet", "mold" or "vent" without the case geometry.
    scalar totalMetalIn_kg_s=0;
    scalar totalMetalOut_kg_s=0;
    forAll(mesh.boundary(),patchi)
    {
        scalar metalInto_kg_s=0,metalOut_kg_s=0;
        scalar gasOut_kg_s=0,heatOut_W=0,energyOut_W=0;
        const auto& patchMetal=liquidBoundary[patchi];
        const auto& patchGas=gasBoundary[patchi];
        const auto& patchHeat=heatPatches[patchi];
        const auto& patchEnergy=energyPatches[patchi];
        forAll(patchMetal,facei)
        {
            const scalar mflux=patchMetal[facei];
            metalInto_kg_s+=max(-mflux,scalar(0));
            metalOut_kg_s+=max(mflux,scalar(0));
            gasOut_kg_s+=patchGas[facei];
            heatOut_W+=patchHeat[facei];
            energyOut_W+=patchEnergy[facei];
        }
        reduce(metalInto_kg_s,sumOp<scalar>());
        reduce(metalOut_kg_s,sumOp<scalar>());
        reduce(gasOut_kg_s,sumOp<scalar>());
        reduce(heatOut_W,sumOp<scalar>());
        reduce(energyOut_W,sumOp<scalar>());

        totalMetalIn_kg_s+=metalInto_kg_s;
        totalMetalOut_kg_s+=metalOut_kg_s;

        Info<< "FS_C08_REAL_CFD_PATCH_BUDGET"
            << " time_s=" << runTime.value()
            << " patch=" << mesh.boundary()[patchi].name()
            << " liquidMetalIn_kg_s=" << metalInto_kg_s
            << " liquidMetalOut_kg_s=" << metalOut_kg_s
            << " signedGasOut_kg_s=" << gasOut_kg_s
            << " signedCHTHeatOut_W=" << heatOut_W
            << " energySolverAdvectedOut_W=" << energyOut_W
            << " physicalFeedingNotYetValidated=1" << nl;
    }
    Info<< "FS_C08_REAL_CFD_METAL_FEEDING_SUMMARY"
        << " time_s=" << runTime.value()
        << " allBoundaryLiquidMetalIn_kg_s=" << totalMetalIn_kg_s
        << " allBoundaryLiquidMetalOut_kg_s=" << totalMetalOut_kg_s
        << " shrinkageFeedingPhysicsNotYetValidated=1" << nl;

    const scalar dt=runTime.deltaTValue();

    // Independent accepted-state observables for transient investigation.
    // These do not change the equations or convert an energy diagnostic
    // into an acceptance claim. Integrate actual conserved phase masses
    // and intrinsic densities, not thresholded interface cells.
    scalar liquidKg=0,solidKg=0,liquidV=0,solidV=0,gasV=0;
    scalar oldMetalV=0,phaseRate=0,thermalRate=0,domainV=0,independentGasKg=0;
    scalar maxLocalEnergy=0,absLocalEnergy=0,energyScale=0,maxU=0;
    scalar maxLocalEnergyRelative=0;
    label worstEnergyCell=-1;
    const tmp<volScalarField> tAdvDiv=fvc::div(phaseEnergyPhi_);
    const tmp<volScalarField> tHeatDiv=fvc::div(phaseHeatPhi_);
    const auto& advDiv=tAdvDiv().primitiveField();
    const auto& heatDiv=tHeatDiv().primitiveField();
    const auto& rL=phaseMass_->liquidDensity().primitiveField();
    const auto& rS=phaseMass_->solidDensity().primitiveField();
    const auto& aOld=alpha1.oldTime().primitiveField();
    const auto& phaseSource=phaseMass_->phaseVolumeSource().primitiveField();
    const auto& thermalSource=phaseMass_->thermalVolumeSource().primitiveField();
    forAll(V,i)
    {
        domainV+=V[i];
        liquidKg+=V[i]*l[i];
        solidKg+=V[i]*s[i];
        liquidV+=V[i]*l[i]/rL[i];
        solidV+=V[i]*s[i]/rS[i];
        independentGasKg+=V[i]*gasMassTrial_[i];
        gasV+=V[i]*gasMassTrial_[i]/rGas[i];
        oldMetalV+=V[i]*aOld[i];
        phaseRate+=V[i]*phaseSource[i];
        thermalRate+=V[i]*thermalSource[i];
        maxU=max(maxU,mag(finalU[i]));
        const scalar storage=u[i]-u0[i];
        const scalar advection=dt*advDiv[i];
        const scalar conduction=dt*heatDiv[i];
        const scalar work=dt*workDensity[i];
        const scalar defect=mag(storage+advection+conduction+work);
        const scalar scale=mag(storage)+mag(advection)+mag(conduction)+mag(work);
        if (!std::isfinite(defect) || !std::isfinite(scale))
            FatalErrorInFunction << "FS-C08 nonfinite local energy ledger cell=" << i
                << exit(FatalError);
        absLocalEnergy+=V[i]*defect;
        energyScale+=V[i]*scale;
        maxLocalEnergyRelative=max(maxLocalEnergyRelative,
            defect/max(scalar(1),scale));
        if (defect>maxLocalEnergy)
        {
            maxLocalEnergy=defect;
            worstEnergyCell=i;
        }
    }
    // The coupled solver explicitly rejects parallel execution.
    Info<< "FS_C08_ACCEPTED_STATE_LEDGER"
        << " time_s=" << runTime.value() << " dt_s=" << dt
        << " liquidMass_kg=" << liquidKg << " solidMass_kg=" << solidKg
        << " independentGasMass_kg=" << independentGasKg
        << " liquidVolume_m3=" << liquidV << " solidVolume_m3=" << solidV
        << " gasVolume_m3=" << gasV << " domainVolume_m3=" << domainV
        << " previousMetalVolume_m3=" << oldMetalV
        << " deltaMetalVolume_m3=" << liquidV+solidV-oldMetalV
        << " phaseVolumeRate_m3_s=" << phaseRate
        << " thermalVolumeRate_m3_s=" << thermalRate
        << " Tmin_K=" << min(mixture_.T()).value()
        << " Tmax_K=" << max(mixture_.T()).value()
        << " pMin_Pa=" << min(p).value() << " pMax_Pa=" << max(p).value()
        << " maxU_m_s=" << maxU << nl;
    Info<< "FS_C08_LOCAL_ENERGY_LEDGER"
        << " time_s=" << runTime.value()
        << " maxAbsCellResidual_J_m3=" << maxLocalEnergy
        << " worstCell=" << worstEnergyCell
        << " sumAbsCellResidual_J=" << absLocalEnergy
        << " sumAbsCellTerms_J=" << energyScale
        << " maxCellRelativeResidual=" << maxLocalEnergyRelative
        << " energyValidationPending=1" << nl;

    const scalar metalResidual=M-M0+dt*boundaryMassRate;
    const scalar gasContinuityDefect=Mgas-Mgas0+dt*gasBoundaryOut;
    // This numerical tolerance is dimensionless and independent of
    // the material. A pressure/VOF update that destroys gas inventory
    // must NOT be reported as a valid shrinkage calculation.
    const scalar gasRelativeTolerance=1e-6;
    const scalar gasTolerance_kg=
        gasRelativeTolerance*max(SMALL,max(Mgas,Mgas0));
    Info<< "FS_C08_REAL_CFD_MASS_BUDGET"
        << " time_s=" << runTime.value()
        << " liquidSolidMetalMass_kg=" << M
        << " previousMetalMass_kg=" << M0
        << " phaseResolvedInternalEnergy_J=" << E
        << " previousInternalEnergy_J=" << E0
        << " deltaInternalEnergy_J=" << E-E0
        << " gasPressureCorrectionInternalEnergyJump_J="
        << postPressureEnergyJump_J
        << " thermalPredictorEnergyBudget_J="
        << E-E0-postPressureEnergyJump_J
         + dt*(energyAdvectionOut_W+conductionOut_W+mechanicalWork_W)
        << " pressureCorrectionEnergyGap_J="
        << postPressureEnergyJump_J
        << " nativeEnergySolveAdvectionOut_W=" << energyAdvectionOut_W
        << " nativeEnergySolveConductionOut_W=" << conductionOut_W
        << " nativeMechanicalWork_W=" << mechanicalWork_W
        << " mushyDarcyDissipation_W=" << darcyDissipation_W
        << " totalInternalEnergyEquationBalance_J="
        << E-E0
         + dt*(energyAdvectionOut_W+conductionOut_W+mechanicalWork_W)
        << " energyResidualNotYetValidated=1"
        << " liquidAdvectedEnergyOut_W=" << liquidEnergyOut_W
        << " gasAdvectedEnergyOut_W=" << gasEnergyOut_W
        << " deltaInternalPlusAdvectedEnergy_J="
        << E-E0+dt*(liquidEnergyOut_W+gasEnergyOut_W)
        << " globalEnergyBudgetPendingNativeCFDValidation=1"
        << " nativeGasInventory_kg=" << Mgas
        << " previousGasInventory_kg=" << Mgas0
        << " gasBoundaryOut_kg_s=" << gasBoundaryOut
        << " gasContinuityDefect_kg=" << gasContinuityDefect
        << " boundaryMetalOut_kg_s=" << boundaryMassRate
        << " metalMassResidual_kg=" << metalResidual
        << " gasMassBudgetTolerance_kg=" << gasTolerance_kg
        << " gasBudgetAcceptancePendingCheck=1"
        << " thermalVolumeSourceMean_s_1="
        << phaseMass_->thermalVolumeSource()
              .weightedAverage(mesh.V()).value()
        << " combinedMaterialVolumeSourceMean_s_1="
        << phaseMass_->materialVolumeSource()
              .weightedAverage(mesh.V()).value()
        << " phaseChangeVolumeSourceMean_s_1="
        << phaseMass_->phaseVolumeSource()
              .weightedAverage(mesh.V()).value()
        << nl;

    if
    (
        !std::isfinite(metalResidual)
     || mag(metalResidual)>1e-7*max(M,M0)
    )
    {
        FatalErrorInFunction
            << "FS-C08 native METAL mass balance does not close; refuse "
            << "to call this a physical shrinkage result. Residual="
            << metalResidual << " kg" << exit(FatalError);
    }
    if
    (
        !std::isfinite(gasContinuityDefect)
     || !std::isfinite(Mgas)
     || Mgas<0
     || mag(gasContinuityDefect)>gasTolerance_kg
    )
    {
        FatalErrorInFunction
            << "FS-C08 native GAS mass balance fails across PIMPLE "
            << "and the real boundary mass fluxes. Defect="
            << gasContinuityDefect << " kg, allowed="
            << gasTolerance_kg << " kg. No gas mass clipping or "
            << "invented gas pressure sources allowed."
            << exit(FatalError);
    }
    Info<< "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED"
        << " time_s=" << runTime.value()
        << " gasResidual_kg=" << gasContinuityDefect
        << " metalResidual_kg=" << metalResidual
        << " energyNotYetValidated=1" << nl;
}

} // namespace Foam
