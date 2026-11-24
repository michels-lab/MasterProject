/* FS-C08 | Actual OpenFOAM14 in-solver FV mass transport.
   Material tables REQUIRED. Not a shadow, no fabricated properties.
   SPDX-License-Identifier: GPL-3.0-or-later */
#include "FS_C08_PhaseMassTransport.H"
#include "fvcInterpolate.H"
#include "fvmSup.H"
#include "zeroGradientFvPatchFields.H"
#include <cmath>
namespace Foam { namespace fsC08 {

PhaseMassTransport::PhaseMassTransport
(
    const fvMesh& mesh,
    const volScalarField& metal,
    const volScalarField& T
):
    mesh_(mesh),
    material_(IOobject("fsC08Material",mesh.time().constant(),mesh,
                       IOobject::MUST_READ,IOobject::NO_WRITE)),
    materialId_(material_.lookup<word>("materialId")),
    propertySource_(material_.lookup<word>("propertySource")),
    Tmin_K_(material_.lookup<scalar>("Tmin_K")),
    Tmax_K_(material_.lookup<scalar>("Tmax_K")),
    phaseRelaxation_(material_.lookup<scalar>("phaseRelaxation")),
    rhoLiquidT_(Function1<scalar>::New("rhoLiquidT",dimTemperature,dimDensity,material_)),
    rhoSolidT_(Function1<scalar>::New("rhoSolidT",dimTemperature,dimDensity,material_)),
    solidMassFractionT_
    (
        Function1<scalar>::New("solidMassFractionT",dimTemperature,
                               units::fraction,material_)
    ),
    latentHeat_(dimensionedScalar("latentHeat",dimEnergy/dimMass,material_)),
    cpSolid_(dimensionedScalar("cpSolid",dimEnergy/dimMass/dimTemperature,material_)),
    mLiquid_(IOobject("rhoAlpha.liquid",mesh.time().name(),mesh,
                      IOobject::READ_IF_PRESENT,IOobject::AUTO_WRITE),
             mesh,dimensionedScalar(dimDensity,0),
             zeroGradientFvPatchScalarField::typeName),
    mSolid_(IOobject("rhoAlpha.solid",mesh.time().name(),mesh,
                     IOobject::READ_IF_PRESENT,IOobject::AUTO_WRITE),
            mesh,dimensionedScalar(dimDensity,0),
            zeroGradientFvPatchScalarField::typeName),
    rhoLiquid_(IOobject("rhoLiquid.fsC08",mesh.time().name(),mesh,
                        IOobject::NO_READ,IOobject::AUTO_WRITE),
               mesh,dimensionedScalar(dimDensity,0),
               zeroGradientFvPatchScalarField::typeName),
    rhoSolid_(IOobject("rhoSolid.fsC08",mesh.time().name(),mesh,
                       IOobject::NO_READ,IOobject::AUTO_WRITE),
              mesh,dimensionedScalar(dimDensity,0),
              zeroGradientFvPatchScalarField::typeName),
    Gamma_(IOobject("Gamma.fsC08",mesh.time().name(),mesh,
                    IOobject::NO_READ,IOobject::AUTO_WRITE),
           mesh,dimensionedScalar(dimDensity/dimTime,0),
           zeroGradientFvPatchScalarField::typeName),
    SvolPhaseChange_
    (
        IOobject("SvolPhaseChange.fsC08",mesh.time().name(),mesh,
                 IOobject::NO_READ,IOobject::AUTO_WRITE),
        mesh,dimensionedScalar(dimless/dimTime,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    alphaLiquid_(IOobject("alphaLiquid.fsC08",mesh.time().name(),mesh,
                          IOobject::NO_READ,IOobject::AUTO_WRITE),
                 mesh,dimensionedScalar(dimless,0),
                 zeroGradientFvPatchScalarField::typeName),
    alphaSolid_(IOobject("alphaSolid.fsC08",mesh.time().name(),mesh,
                         IOobject::NO_READ,IOobject::AUTO_WRITE),
                mesh,dimensionedScalar(dimless,0),
                zeroGradientFvPatchScalarField::typeName),
    alphaMetalFromMass_
    (
        IOobject("alphaMetalFromMass.fsC08",mesh.time().name(),mesh,
                 IOobject::NO_READ,IOobject::AUTO_WRITE),
        mesh,dimensionedScalar(dimless,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    liquidMassPhi_
    (
        IOobject("rhoPhi.liquid.fsC08",mesh.time().name(),mesh,
                 IOobject::NO_READ,IOobject::NO_WRITE),
        mesh,dimensionedScalar(dimMass/dimTime,0)
    ),
    massFieldsRestarted_
    (
        typeIOobject<volScalarField>
        (IOobject("rhoAlpha.liquid",mesh.time().name(),mesh)).headerOk()
     && typeIOobject<volScalarField>
        (IOobject("rhoAlpha.solid",mesh.time().name(),mesh)).headerOk()
    ),
    initialized_(false),
    lastSolvedTimeIndex_(-1)
{
    if (materialId_.empty() || propertySource_.empty()
        || materialId_=="SYNTHETIC_ONLY_NOT_JMATPRO"
        || propertySource_=="SYNTHETIC_ONLY_NOT_JMATPRO"
        || !std::isfinite(Tmin_K_) || !std::isfinite(Tmax_K_)
        || Tmin_K_<=0 || Tmax_K_<=Tmin_K_
        || !std::isfinite(phaseRelaxation_)
        || phaseRelaxation_<=0 || phaseRelaxation_>1
        || !std::isfinite(latentHeat_.value()) || latentHeat_.value()<=0
        || !std::isfinite(cpSolid_.value()) || cpSolid_.value()<=0)
    {
        FatalErrorInFunction
          << "FS-C08 requires sourced alloy properties, valid temperature "
          << "range and relaxation in (0,1]. Synthetic fixture refused."
          << exit(FatalError);
    }
    checkAndUpdateProperties(T);
    initializeIfRequired(metal,T);
    reconstructFractions();
}

void PhaseMassTransport::checkAndUpdateProperties(const volScalarField& T)
{
    auto& rl=rhoLiquid_.primitiveFieldRef();
    auto& rs=rhoSolid_.primitiveFieldRef();
    const auto& t=T.primitiveField();
    forAll(t,i)
    {
        if (!std::isfinite(t[i]) || t[i]<Tmin_K_ || t[i]>Tmax_K_)
            FatalErrorInFunction << "T out of sourced range at cell " << i
                                 << " T=" << t[i] << exit(FatalError);
        rl[i]=rhoLiquidT_->value(t[i]);
        rs[i]=rhoSolidT_->value(t[i]);
        if (!std::isfinite(rl[i]) || !std::isfinite(rs[i])
            || rl[i]<=0 || rs[i]<=0)
            FatalErrorInFunction << "Invalid material density at " << i
                                 << exit(FatalError);
    }
    rhoLiquid_.correctBoundaryConditions();
    rhoSolid_.correctBoundaryConditions();
}

void PhaseMassTransport::initializeIfRequired
(
    const volScalarField& metal,
    const volScalarField& T
)
{
    if (initialized_) return;
    if (!massFieldsRestarted_)
    {
        auto& ml=mLiquid_.primitiveFieldRef();
        auto& ms=mSolid_.primitiveFieldRef();
        const auto& a=metal.primitiveField();
        const auto& t=T.primitiveField();
        const auto& rl=rhoLiquid_.primitiveField();
        const auto& rs=rhoSolid_.primitiveField();
        forAll(a,i)
        {
            const scalar fs=solidMassFractionT_->value(t[i]);
            if (!std::isfinite(a[i]) || a[i]<0 || a[i]>1
                || !std::isfinite(fs) || fs<0 || fs>1)
                FatalErrorInFunction << "Invalid initial metal or fs in cell "
                                     << i << exit(FatalError);
            const scalar M=a[i]/((1-fs)/rl[i]+fs/rs[i]);
            ml[i]=(1-fs)*M;
            ms[i]=fs*M;
        }
        mLiquid_.correctBoundaryConditions();
        mSolid_.correctBoundaryConditions();
    }
    initialized_=true;
}

void PhaseMassTransport::evaluateGamma(const volScalarField& T)
{
    const scalar dt=mesh_.time().deltaTValue();
    if (!std::isfinite(dt) || dt<=0)
        FatalErrorInFunction << "Invalid CFD deltaT" << exit(FatalError);
    auto& gamma=Gamma_.primitiveFieldRef();
    auto& s=SvolPhaseChange_.primitiveFieldRef();
    const auto& ml=mLiquid_.primitiveField();
    const auto& ms=mSolid_.primitiveField();
    const auto& rl=rhoLiquid_.primitiveField();
    const auto& rs=rhoSolid_.primitiveField();
    const auto& t=T.primitiveField();
    forAll(gamma,i)
    {
        const scalar fs=solidMassFractionT_->value(t[i]);
        if (!std::isfinite(fs) || fs<0 || fs>1 || ml[i]<0 || ms[i]<0)
            FatalErrorInFunction << "Invalid phase masses / fs at cell "
                                 << i << exit(FatalError);
        gamma[i]=phaseRelaxation_*(fs*(ml[i]+ms[i])-ms[i])/dt;
        s[i]=gamma[i]*(1/rs[i]-1/rl[i]);
    }
    Gamma_.correctBoundaryConditions();
    SvolPhaseChange_.correctBoundaryConditions();
}

void PhaseMassTransport::reconstructFractions()
{
    const auto& ml=mLiquid_.primitiveField();
    const auto& ms=mSolid_.primitiveField();
    const auto& rl=rhoLiquid_.primitiveField();
    const auto& rs=rhoSolid_.primitiveField();
    auto& al=alphaLiquid_.primitiveFieldRef();
    auto& as=alphaSolid_.primitiveFieldRef();
    auto& am=alphaMetalFromMass_.primitiveFieldRef();
    forAll(ml,i)
    {
        al[i]=ml[i]/rl[i]; as[i]=ms[i]/rs[i]; am[i]=al[i]+as[i];
        if (!std::isfinite(am[i]) || al[i]<-1e-12 || as[i]<-1e-12
            || am[i]>1+1e-12)
            FatalErrorInFunction
                << "FS-C08 saturation violation at " << i
                << ", alphaL=" << al[i] << ", alphaS=" << as[i]
                << "; no mass clipping" << exit(FatalError);
    }
    alphaLiquid_.correctBoundaryConditions();
    alphaSolid_.correctBoundaryConditions();
    alphaMetalFromMass_.correctBoundaryConditions();
}

void PhaseMassTransport::solve
(
    const volScalarField& T,
    const volScalarField& alphaMetal,
    const surfaceScalarField& alphaPhiMetal
)
{
    if (lastSolvedTimeIndex_==mesh_.time().timeIndex()) return;
    checkAndUpdateProperties(T);
    initializeIfRequired(alphaMetal,T);
    reconstructFractions();
    evaluateGamma(T);
    volScalarField liquidShare
    (
        IOobject("fsC08LiquidShare",mesh_.time().name(),mesh_,
                 IOobject::NO_READ,IOobject::NO_WRITE),
        mesh_,dimensionedScalar(dimless,0),
        zeroGradientFvPatchScalarField::typeName
    );
    auto& f=liquidShare.primitiveFieldRef();
    const auto& aL=alphaLiquid_.primitiveField();
    const auto& aM=alphaMetalFromMass_.primitiveField();
    forAll(f,i) f[i]=aM[i]>1e-12 ? aL[i]/aM[i] : 0;
    liquidShare.correctBoundaryConditions();

    // Real MULES-limited metal flux on ALL CFD mesh faces and boundaries.
    liquidMassPhi_ = alphaPhiMetal*fvc::interpolate(liquidShare)
                    *fvc::interpolate(rhoLiquid_);

    fvScalarMatrix lEqn
    (
        fvm::ddt(mLiquid_) == -fvc::div(liquidMassPhi_) - Gamma_
    );
    lEqn.solve();

    fvScalarMatrix sEqn(fvm::ddt(mSolid_) == Gamma_);
    sEqn.solve();

    reconstructFractions();
    lastSolvedTimeIndex_=mesh_.time().timeIndex();
    Info<< "FS_C08_IN_SOLVER_PHASE_MASS_EQUATIONS t="
        << mesh_.time().value()
        << " gammaMax=" << max(Gamma_).value()
        << " pressure/energy NOT YET linked" << nl;
}
}} // Foam::fsC08
