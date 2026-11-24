/* FS-C08 | physically distinct native CFD phase mass equations.
 * GPL-3.0-or-later. Does not modify installed OpenFOAM14.
 */
#include "fsC08ConservativeVoF.H"
#include "addToRunTimeSelectionTable.H"
#include "fvcDdt.H"
#include "fvcDiv.H"
#include "fvcInterpolate.H"
#include "zeroGradientFvPatchFields.H"

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
    )
{
    reconcileMixtureDensity();
    rhoMetalEffective_.oldTime();
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

} // namespace Foam
