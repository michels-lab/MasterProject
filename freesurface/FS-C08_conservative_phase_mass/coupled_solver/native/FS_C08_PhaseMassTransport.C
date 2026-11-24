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
    phaseChangeClosure_(material_.lookup<word>("phaseChangeClosure")),
    metalPresenceThreshold_(material_.lookup<scalar>("metalPresenceThreshold")),
    rhoLiquidT_(Function1<scalar>::New("rhoLiquidT",dimTemperature,dimDensity,material_)),
    rhoSolidT_(Function1<scalar>::New("rhoSolidT",dimTemperature,dimDensity,material_)),
    solidMassFractionT_
    (
        Function1<scalar>::New("solidMassFractionT",dimTemperature,
                               units::fraction,material_)
    ),
    tauPhaseChangeT_(),
    latentHeat_(dimensionedScalar("latentHeat",dimEnergy/dimMass,material_)),
    cpSolid_(dimensionedScalar("cpSolid",dimEnergy/dimMass/dimTemperature,material_)),
    mushyDarcyCu_
    (
        dimensionedScalar("mushyDarcyCu",dimless/dimTime,material_)
    ),
    mushyDarcyQ_(material_.lookup<scalar>("mushyDarcyQ")),
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
    SvolThermal_
    (
        IOobject("SvolThermal.fsC08",mesh.time().name(),mesh,
                 IOobject::NO_READ,IOobject::AUTO_WRITE),
        mesh,dimensionedScalar(dimless/dimTime,0),
        zeroGradientFvPatchScalarField::typeName
    ),
    SvolMaterial_
    (
        IOobject("SvolMaterial.fsC08",mesh.time().name(),mesh,
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
        || (phaseChangeClosure_!="equilibrium"
            && phaseChangeClosure_!="kineticRelaxation")
        || !std::isfinite(metalPresenceThreshold_)
        || metalPresenceThreshold_<=0 || metalPresenceThreshold_>=0.5
        || !std::isfinite(latentHeat_.value()) || latentHeat_.value()<=0
        || !std::isfinite(cpSolid_.value()) || cpSolid_.value()<=0
        || !std::isfinite(mushyDarcyCu_.value())
        || mushyDarcyCu_.value()<=0
        || !std::isfinite(mushyDarcyQ_)
        || mushyDarcyQ_<=0 || mushyDarcyQ_>1)
    {
        FatalErrorInFunction
          << "FS-C08 requires sourced alloy properties, valid temperature "
          << "range and relaxation in (0,1]. Synthetic fixture refused."
          << exit(FatalError);
    }
    // Never reinitialize a partially restored physical inventory.
    // A single saved rhoAlpha field is not a meaningful restart.
    const bool liquidSaved=
        typeIOobject<volScalarField>
        (IOobject("rhoAlpha.liquid",mesh.time().name(),mesh)).headerOk();
    const bool solidSaved=
        typeIOobject<volScalarField>
        (IOobject("rhoAlpha.solid",mesh.time().name(),mesh)).headerOk();
    if (liquidSaved != solidSaved)
    {
        FatalErrorInFunction
            << "FS-C08 partial restart: rhoAlpha.liquid and rhoAlpha.solid "
            << "must both exist or both be initialized from the actual "
            << "initial metal VOF and sourced solid-mass-fraction law."
            << exit(FatalError);
    }

    if (phaseChangeClosure_=="kineticRelaxation")
    {
        // Tau must be sourced by alloy, not fitted to numerical dt.
        tauPhaseChangeT_=Function1<scalar>::New
        (
            "tauPhaseChangeT",dimTemperature,dimTime,material_
        );
    }

    checkAndUpdateProperties(T,metal);
    initializeIfRequired(metal,T);
    reconstructFractions();

    // On restart, VOF and masses represent the SAME physical inventory.
    // Do not silently rewrite an inconsistent saved VOF or clip mass.
    if (massFieldsRestarted_)
    {
        const auto& a=metal.primitiveField();
        const auto& fromMass=alphaMetalFromMass_.primitiveField();
        forAll(a,i)
        {
            if
            (
                !std::isfinite(a[i])
             || mag(a[i]-fromMass[i])>1e-6
            )
            {
                FatalErrorInFunction
                    << "FS-C08 restart volume mismatch cell=" << i
                    << " alphaMetal=" << a[i]
                    << " alphaFromConservedMass=" << fromMass[i]
                    << " ; refusing inconsistent restart."
                    << exit(FatalError);
            }
        }
    }
}

void PhaseMassTransport::checkAndUpdateProperties
(
    const volScalarField& T,
    const volScalarField& metal
)
{
    auto& rl=rhoLiquid_.primitiveFieldRef();
    auto& rs=rhoSolid_.primitiveFieldRef();
    const auto& t=T.primitiveField();
    const auto& a=metal.primitiveField();
    forAll(t,i)
    {
        // Air/VOF trace has no physically meaningful Fe temperature.
        // Retain metal mass; do not infer phase change from gas temperature.
        if (a[i]<metalPresenceThreshold_)
        {
            rl[i]=rhoLiquidT_->value(Tmin_K_);
            rs[i]=rhoSolidT_->value(Tmin_K_);
            continue;
        }
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
            const scalar fs=a[i]<metalPresenceThreshold_
                ? 0 : solidMassFractionT_->value(t[i]);
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

void PhaseMassTransport::evaluateGamma
(
    const volScalarField& T,
    const volScalarField& metal
)
{
    const scalar dt=mesh_.time().deltaTValue();
    if (!std::isfinite(dt) || dt<=0)
        FatalErrorInFunction << "Invalid CFD deltaT" << exit(FatalError);
    auto& gamma=Gamma_.primitiveFieldRef();
    auto& s=SvolPhaseChange_.primitiveFieldRef();
    auto& st=SvolThermal_.primitiveFieldRef();
    auto& sm=SvolMaterial_.primitiveFieldRef();
    const auto& t0=T.oldTime().primitiveField();
    const auto& alpha0=metal.oldTime().primitiveField();
    const auto& ml=mLiquid_.primitiveField();
    const auto& ms=mSolid_.primitiveField();
    const auto& rl=rhoLiquid_.primitiveField();
    const auto& rs=rhoSolid_.primitiveField();
    const auto& t=T.primitiveField();
    const auto& a=metal.primitiveField();
    forAll(gamma,i)
    {
        st[i]=0;
        sm[i]=0;
        if (a[i]<metalPresenceThreshold_)
        {
            gamma[i]=0;
            s[i]=0;
            continue;
        }
        const scalar fs=solidMassFractionT_->value(t[i]);
        if (!std::isfinite(fs) || fs<0 || fs>1 || ml[i]<0 || ms[i]<0)
            FatalErrorInFunction << "Invalid phase masses / fs at cell "
                                 << i << exit(FatalError);
        scalar conversionFactor=1.0;
        if (phaseChangeClosure_=="kineticRelaxation")
        {
            const scalar tau=tauPhaseChangeT_->value(t[i]);
            if (!std::isfinite(tau) || tau<=0)
            {
                FatalErrorInFunction
                    << "FS-C08 invalid sourced kinetic tau(T) in cell "
                    << i << " tau=" << tau << " s."
                    << exit(FatalError);
            }
            // 1-exp(-dt/tau): exact positive bounded relaxation
            // for a constant equilibrium target over this time step.
            conversionFactor=-std::expm1(-dt/tau);
        }
        gamma[i]=conversionFactor*(fs*(ml[i]+ms[i])-ms[i])/dt;
        s[i]=gamma[i]*(1/rs[i]-1/rl[i]);

        // Density(T) material contraction at FIXED transported masses:
        // Δ(alphaMetal)_thermal / Δt, excluding phase transfer/advection.
        // An incoming air-to-metal interface has no iron T(n) history;
        // do NOT interpret its old gas temperature as thermal shrinkage.
        if
        (
            alpha0[i]>=metalPresenceThreshold_
         && std::isfinite(t0[i])
         && t0[i]>=Tmin_K_ && t0[i]<=Tmax_K_
        )
        {
            const scalar rl0=rhoLiquidT_->value(t0[i]);
            const scalar rs0=rhoSolidT_->value(t0[i]);
            if
            (
                !std::isfinite(rl0) || rl0<=0
             || !std::isfinite(rs0) || rs0<=0
            )
            {
                FatalErrorInFunction
                    << "FS-C08 previous temperature produced invalid "
                    << "rho(T) at cell " << i << exit(FatalError);
            }
            st[i]=
            (
                ml[i]*(1.0/rl[i]-1.0/rl0)
              + ms[i]*(1.0/rs[i]-1.0/rs0)
            )/dt;
        }
        sm[i]=s[i]+st[i];
    }
    Gamma_.correctBoundaryConditions();
    SvolPhaseChange_.correctBoundaryConditions();
    SvolThermal_.correctBoundaryConditions();
    SvolMaterial_.correctBoundaryConditions();
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
    // PIMPLE may call prePredictor multiple times in a single physical dt.
    // Recompute from n each outer corrector, not cumulatively from a
    // previous n+1 phase-change update. fvm::ddt(mLiquid_) always uses
    // mLiquid_.oldTime() as the n state; restore solid mass to the
    // same n state before calculating a new Gamma(T) predictor.
    mLiquid_.oldTime();
    mSolid_.oldTime();
    if (lastSolvedTimeIndex_==mesh_.time().timeIndex())
    {
        mSolid_.primitiveFieldRef() =
            mSolid_.oldTime().primitiveField();
        mSolid_.correctBoundaryConditions();
    }
    checkAndUpdateProperties(T,alphaMetal);
    initializeIfRequired(alphaMetal,T);
    reconstructFractions();
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

    // Step A: transport liquid mass on all genuine CFD faces. The
    // stationary solid has no advective flux. Physical dimensions of
    // rhoAlpha.liquid are kg/m3; face rhoPhi.liquid is kg/s.
    fvScalarMatrix lEqn
    (
        fvm::ddt(mLiquid_) == -fvc::div(liquidMassPhi_)
    );
    lEqn.solve();

    // Step B: NOW evaluate the equilibrium driving source from the
    // TRANSPORTED available liquid mass, not its pre-advection value.
    // This prevents Gamma from consuming mass that has already left
    // through a real boundary during the current CFD time step.
    const auto& transportedLiquid=mLiquid_.primitiveField();
    const auto& initialSolid=mSolid_.primitiveField();
    forAll(transportedLiquid,i)
    {
        if
        (
            !std::isfinite(transportedLiquid[i])
         || !std::isfinite(initialSolid[i])
         || transportedLiquid[i] < 0
         || initialSolid[i] < 0
        )
        {
            FatalErrorInFunction
                << "FS-C08: liquid FV advection created negative/nonfinite "
                << "mass in cell " << i
                << "; adjust native CFD Courant / fluxes, no clipping."
                << exit(FatalError);
        }
    }

    evaluateGamma(T,alphaMetal);

    // Step C: equal-and-opposite local mass exchange in the *same*
    // physical CFD time step. For 0<relax<=1 and 0<=fs<=1,
    // the bounded target cannot deplete either phase. This update is
    // exactly conservative to round-off by construction.
    const scalar dt=mesh_.time().deltaTValue();
    auto& ml=mLiquid_.primitiveFieldRef();
    auto& ms=mSolid_.primitiveFieldRef();
    const auto& g=Gamma_.primitiveField();
    forAll(ml,i)
    {
        const scalar dm=dt*g[i];
        ml[i]-=dm;
        ms[i]+=dm;
    }
    mLiquid_.correctBoundaryConditions();
    mSolid_.correctBoundaryConditions();

    reconstructFractions();
    lastSolvedTimeIndex_=mesh_.time().timeIndex();
    Info<< "FS_C08_IN_SOLVER_PHASE_MASS_EQUATIONS t="
        << mesh_.time().value()
        << " gammaMax=" << max(Gamma_).value()
        << " pressure/energy NOT YET linked" << nl;
}
}} // Foam::fsC08
