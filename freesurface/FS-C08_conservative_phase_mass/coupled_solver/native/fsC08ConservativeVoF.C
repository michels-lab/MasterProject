/* FS-C08 | physically distinct native CFD phase mass equations.
 * GPL-3.0-or-later. Does not modify installed OpenFOAM14.
 */
#include "fsC08ConservativeVoF.H"
#include "addToRunTimeSelectionTable.H"
#include "fvcDdt.H"
#include "fvcDiv.H"
#include "fvcInterpolate.H"
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

    reconcileMixtureDensity();
    rhoMetalEffective_.oldTime();
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
    const auto& metal=alpha1.primitiveField();
    auto& rMetal=rhoMetalEffective_.primitiveFieldRef();
    forAll(rMetal,i)
    {
        rMetal[i]=metal[i]>1e-12
            ? (ml[i]+ms[i])/metal[i]
            : rL[i];
    }
    rhoMetalEffective_.correctBoundaryConditions();
    mixtureDensity =
        phaseMass_->liquidMass()
      + phaseMass_->solidMass()
      + alpha2*mixture_.rho2();
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
    const auto& rhoGas=mixture_.rho2().primitiveField();
    const auto& alphaGas=alpha2.primitiveField();
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
          + alphaGas[i]*rhoGas[i]*uGas[i];
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
    // MULES provides a real, all-face metal VOF flux from evolving U.
    compressibleVoF::prePredictor();

    // Actual finite-volume continuity for liquid and stationary solid.
    // No made-up face flux, no post-processed saved-state inference.
    phaseMass_->solve(mixture_.T(),alpha1,alphaPhi1);

    // Reconstruct metal VOF from transported mass and distinct rho(T).
    // The native solid-fraction fvModel must NOT also be active.
    alpha1 = phaseMass_->alphaMetal();
    alpha2 = scalar(1)-alpha1;
    alpha1.correctBoundaryConditions();
    alpha2.correctBoundaryConditions();
    correctInterface();

    // Flow of solid skeleton is zero. Only liquid carries metal mass.
    alphaRhoPhi1 = phaseMass_->liquidMassFlux();
    alphaPhi1 =
        alphaRhoPhi1/fvc::interpolate(phaseMass_->liquidDensity());
    alphaPhi2 = phi-alphaPhi1;
    alphaRhoPhi2 = fvc::interpolate(mixture_.rho2())*alphaPhi2;
    rhoPhi = alphaRhoPhi1+alphaRhoPhi2;

    // Per-phase mass continuity errors are now from physical inventory.
    contErr1 =
    (
        fvc::ddt(phaseMass_->liquidMass())()()
      + fvc::ddt(phaseMass_->solidMass())()()
      + fvc::div(alphaRhoPhi1)()()
    );
    contErr2 =
    (
        fvc::ddt(alpha2,mixture_.rho2())()()
      + fvc::div(alphaRhoPhi2)()()
      - (fvModels().source(alpha2,mixture_.rho2())&mixture_.rho2())()
    );

    mixture_.correct();
    reconcileMixtureDensity();

}

// Audit AFTER the actual gas EOS, pressure corrector and energy solve.
void solvers::fsC08ConservativeVoF::postSolve()
{
    compressibleVoF::postSolve();
    // Update after gas pressure/EOS correction to store full phase energy.
    updatePhaseInternalEnergy();
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
    const auto& rGas0=mixture_.rho2().oldTime().primitiveField();
    const auto& aGas0=alpha2.oldTime().primitiveField();
    scalar M0=0, M=0, Mgas=0, Mgas0=0;
    scalar E0=0,E=0;
    const auto& u=phaseInternalEnergy_.primitiveField();
    const auto& u0=phaseInternalEnergy_.oldTime().primitiveField();
    forAll(V,i)
    {
        M0+=V[i]*(l0[i]+s0[i]);
        M+=V[i]*(l[i]+s[i]);
        Mgas+=V[i]*aGas[i]*rGas[i];
        Mgas0+=V[i]*aGas0[i]*rGas0[i];
        E+=V[i]*u[i];
        E0+=V[i]*u0[i];
    }
    reduce(M0,sumOp<scalar>());
    reduce(M,sumOp<scalar>());
    reduce(Mgas,sumOp<scalar>());
    reduce(Mgas0,sumOp<scalar>());
    reduce(E0,sumOp<scalar>());
    reduce(E,sumOp<scalar>());

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

    const scalar dt=runTime.deltaTValue();
    const scalar metalResidual=M-M0+dt*boundaryMassRate;
    const scalar gasContinuityDefect=Mgas-Mgas0+dt*gasBoundaryOut;
    Info<< "FS_C08_REAL_CFD_MASS_BUDGET"
        << " time_s=" << runTime.value()
        << " liquidSolidMetalMass_kg=" << M
        << " previousMetalMass_kg=" << M0
        << " phaseResolvedInternalEnergy_J=" << E
        << " previousInternalEnergy_J=" << E0
        << " deltaInternalEnergy_J=" << E-E0
        << " nativeEnergySolveAdvectionOut_W=" << energyAdvectionOut_W
        << " nativeEnergySolveConductionOut_W=" << conductionOut_W
        << " partialEnergyBalanceIgnoringMechanicalWork_J="
        << E-E0+dt*(energyAdvectionOut_W+conductionOut_W)
        << " liquidAdvectedEnergyOut_W=" << liquidEnergyOut_W
        << " gasAdvectedEnergyOut_W=" << gasEnergyOut_W
        << " deltaInternalPlusAdvectedEnergy_J="
        << E-E0+dt*(liquidEnergyOut_W+gasEnergyOut_W)
        << " energyBudgetPressureAndCHTNotYetClosed=1"
        << " nativeGasInventory_kg=" << Mgas
        << " previousGasInventory_kg=" << Mgas0
        << " gasBoundaryOut_kg_s=" << gasBoundaryOut
        << " gasContinuityDefect_kg=" << gasContinuityDefect
        << " boundaryMetalOut_kg_s=" << boundaryMassRate
        << " metalMassResidual_kg=" << metalResidual
        << " gasConservationNotYetCertified=1"
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
}

} // namespace Foam
