/* FS-C08 | native FV pressure-volume Newton/Picard building block.
 * This file is deliberately NOT invoked by the legacy split solver yet:
 * the caller must reassemble momentum, energy and gas EOS and iterate
 * before accepting VOF. No standalone projection is a shrinkage result.
 * GPL-3.0-or-later.
 */
#include "FS_C08_VolumeProjection.H"
#include "fvcDiv.H"
#include "fvmLaplacian.H"
#include "fvmSup.H"
#include "fvMatrices.H"
#include "PstreamReduceOps.H"
#include <cmath>

namespace Foam { namespace fsC08 {

tmp<volScalarField> trialVolumeResidual
(
    const volScalarField& mL, const volScalarField& mS,
    const volScalarField& mG, const volScalarField& rhoL,
    const volScalarField& rhoS, const volScalarField& rhoG
)
{
    forAll(mL,i)
    {
        if (!std::isfinite(mL[i]) || !std::isfinite(mS[i])
            || !std::isfinite(mG[i]) || mL[i]<0 || mS[i]<0 || mG[i]<0
            || !std::isfinite(rhoL[i]) || rhoL[i]<=0
            || !std::isfinite(rhoS[i]) || rhoS[i]<=0
            || !std::isfinite(rhoG[i]) || rhoG[i]<=0)
        {
            FatalErrorInFunction << "Invalid FS-C08 trial mass/density cell "
                << i << exit(FatalError);
        }
    }
    return mL/rhoL + mS/rhoS + mG/rhoG
         - dimensionedScalar(dimless,1);
}

void solveVolumePressureIncrement
(
    const volScalarField& residual,
    const volScalarField& mG, const volScalarField& rhoL,
    const volScalarField& rhoG, const volScalarField& psiG,
    const surfaceScalarField& liquidMobility,
    const surfaceScalarField& gasMobility,
    volScalarField& dp,
    surfaceScalarField& deltaLiquidMassFlux,
    surfaceScalarField& deltaGasMassFlux,
    const label referenceCell
)
{
    const fvMesh& mesh=dp.mesh();
    const dimensionedScalar dt=mesh.time().deltaT();
    if (!std::isfinite(dt.value()) || dt.value()<=0)
        FatalErrorInFunction << "Invalid FS-C08 projection dt" << exit(FatalError);
    forAll(residual,i)
    {
        if (!std::isfinite(residual[i]) || !std::isfinite(mG[i])
            || mG[i]<0 || !std::isfinite(psiG[i]) || psiG[i]<0
            || !std::isfinite(rhoL[i]) || rhoL[i]<=0
            || !std::isfinite(rhoG[i]) || rhoG[i]<=0)
            FatalErrorInFunction << "Invalid FS-C08 pressure Jacobian cell "
                << i << exit(FatalError);
    }
    // Exact linearisation at frozen T, densities and face mobilities:
    // delta(m_i)=-dt div(deltaF_i), deltaF_i=-M_i grad(dp).S
    // delta(mG/rhoG)=delta(mG)/rhoG-mG*psiG*dp/rhoG^2
    // Therefore [ -div(M_L grad)/rhoL -div(M_G grad)/rhoG
    //             + mG psiG/(rhoG^2 dt) ] dp = residual/dt.
    // Row scaling by rho_i is important with unequal phase densities.
    // It can make the combined matrix asymmetric even if each diffusion
    // matrix is symmetric. Use an asymmetric-capable solver.
    if (dp.name()!="pVolumeCorrection.fsC08")
        FatalErrorInFunction << "Use dedicated FS-C08 pressure increment field"
            << exit(FatalError);
    // Foundation fvMatrix cannot row-scale a matrix containing a
    // nonorthogonal faceFluxCorrection. Use a named orthogonal
    // projection operator here; the full momentum/pressure iteration
    // must handle nonorthogonality and re-evaluate the exact residual.
    const word scheme("laplacian(fsC08VolumeMobility,pVolumeCorrection.fsC08)");
    mesh.schemes().setFluxRequired(dp.name());
    fvScalarMatrix liquidEqn(-fvm::laplacian(liquidMobility,dp,scheme));
    fvScalarMatrix gasEqn(-fvm::laplacian(gasMobility,dp,scheme));
    const volScalarField gasCompressibility
    (
        "fsC08VolumeGasCompressibility",
        mG*psiG/(sqr(rhoG)*dt)
    );
    fvScalarMatrix volumeEqn
    (
        (scalar(1)/rhoL)*liquidEqn + (scalar(1)/rhoG)*gasEqn
      + fvm::Sp(gasCompressibility,dp)
     == residual/dt
    );
    // Only supply a reference when the pressure BC and EOS require it.
    // The caller must check closed-domain compatibility; a reference
    // cannot repair a nonzero net expansion in a rigid sealed cavity.
    if (referenceCell>=0)
        volumeEqn.setReference(referenceCell,0);
    volumeEqn.solve();

    // Use the exact assembled per-phase matrix flux, not an unrelated
    // interpolation of grad(dp). These are face mass rates, NOT phi.
    deltaLiquidMassFlux=liquidEqn.flux();
    deltaGasMassFlux=gasEqn.flux();
}

tmp<volScalarField> correctedTrialMass
(
    const volScalarField& candidateMass,
    const surfaceScalarField& deltaMassFlux
)
{
    tmp<volScalarField> result =
        candidateMass-candidateMass.mesh().time().deltaT()
                     *fvc::div(deltaMassFlux);
    const volScalarField& mass=result();
    forAll(mass,i)
    {
        if (!std::isfinite(mass[i]) || mass[i]<0)
            FatalErrorInFunction
                << "FS-C08 pressure increment produced inadmissible trial "
                << "mass cell=" << i << " mass=" << mass[i]
                << "; use a bounded nonlinear flux correction, never clip"
                << exit(FatalError);
    }
    return result;
}

tmp<volScalarField> trialMassFromOldTime
(
    const volScalarField& oldMass,
    const surfaceScalarField& massFlux,
    const volScalarField& massSource
)
{
    // A signed FV divergence cancels internal face transfers globally.
    return oldMass + oldMass.mesh().time().deltaT()
                   *(massSource-fvc::div(massFlux));
}

namespace
{
scalar residualNorm(const volScalarField& field)
{
    scalar result=0;
    forAll(field,i) result=max(result,mag(field[i]));
    return returnReduce(result,maxOp<scalar>());
}

bool admissibleTrial
(
    const volScalarField& l, const volScalarField& s,
    const volScalarField& g, const volScalarField& rl,
    const volScalarField& rs, const volScalarField& rg,
    const volScalarField& p, const bool requireVolumeClosure
)
{
    label bad=0;
    forAll(l,i)
    {
        if
        (
            !std::isfinite(l[i]) || l[i]<0
         || !std::isfinite(s[i]) || s[i]<0
         || !std::isfinite(g[i]) || g[i]<0
         || !std::isfinite(rl[i]) || rl[i]<=0
         || !std::isfinite(rs[i]) || rs[i]<=0
         || !std::isfinite(rg[i]) || rg[i]<=0
         || !std::isfinite(p[i]) || p[i]<=0
        )
        {
            ++bad;
            continue;
        }
        // Stationary solid overfill cannot be solved by displacing liquid.
        if (s[i]/rs[i]>1+1e-12) ++bad;
        if (requireVolumeClosure &&
            (l[i]/rl[i]+s[i]/rs[i]>1+1e-12
             || g[i]/rg[i]>1+1e-12))
            ++bad;
    }
    return returnReduce(bad,sumOp<label>())==0;
}
}

bool projectTrialInventories
(
    volScalarField& mL, const volScalarField& mS,
    volScalarField& mG,
    const volScalarField& rhoL, const volScalarField& rhoS,
    volScalarField& rhoG, const volScalarField& psiG,
    volScalarField& pressure,
    const surfaceScalarField& liquidMobility,
    const surfaceScalarField& gasMobility,
    surfaceScalarField& liquidMassFlux,
    surfaceScalarField& gasMassFlux,
    volScalarField& dp,
    const label referenceCell
)
{
    // Local transaction: a failed Newton trial cannot poison the
    // conservative inventories or the caller's physical pressure.
    volScalarField l("fsC08ProjectionTrialL",mL);
    volScalarField g("fsC08ProjectionTrialG",mG);
    volScalarField rg("fsC08ProjectionTrialRhoG",rhoG);
    volScalarField p("fsC08ProjectionTrialP",pressure);
    surfaceScalarField fl("fsC08ProjectionTrialFL",liquidMassFlux);
    surfaceScalarField fg("fsC08ProjectionTrialFG",gasMassFlux);
    surfaceScalarField dfl("fsC08ProjectionDeltaFL",liquidMassFlux*scalar(0));
    surfaceScalarField dfg("fsC08ProjectionDeltaFG",gasMassFlux*scalar(0));
    const fvMesh& mesh=dp.mesh();
    const dimensionedScalar dt=mesh.time().deltaT();
    const scalar tolerance=1e-12;
    const label maxIterations=30;
    const label maxBacktracks=24;

    if (Pstream::parRun())
        FatalErrorInFunction << "FS-C08 first active-set projection is serial only"
            << exit(FatalError);
    if (!admissibleTrial(l,mS,g,rhoL,rhoS,rg,p,false))
        return false;

    for (label iter=0;iter<=maxIterations;++iter)
    {
        const tmp<volScalarField> residual=
            trialVolumeResidual(l,mS,g,rhoL,rhoS,rg);
        const scalar norm=residualNorm(residual());
        if (norm<=tolerance &&
            admissibleTrial(l,mS,g,rhoL,rhoS,rg,p,true))
        {
            // Only a converged, bounded trial reaches the caller.
            dp=p-pressure;
            mL=l; mG=g; rhoG=rg; pressure=p;
            liquidMassFlux=fl; gasMassFlux=fg;
            Info<< "FS_C08_FIXED_T_VOLUME_PROJECTION_CONVERGED"
                << " iterations=" << iter << " maxResidual=" << norm
                << " fullEnergyMomentumCouplingVerified=0" << nl;
            return true;
        }
        if (iter==maxIterations) break;

        dp=dimensionedScalar(dp.dimensions(),0);
        dp.correctBoundaryConditions();
        // Active-set pressure mobilities. A face with an absent donor
        // cannot export that phase. Reassemble the pressure Jacobian
        // instead of clipping the resulting mass or face flux afterwards.
        // First integrated candidate is serial; coupled patch donor
        // communication requires a separate implementation.
        surfaceScalarField mlFace("fsC08ActiveLiquidMobility",liquidMobility);
        surfaceScalarField mgFace("fsC08ActiveGasMobility",gasMobility);
        bool activeSetStable=false;
        for (label sweep=0;sweep<12;++sweep)
        {
            dp=dimensionedScalar(dp.dimensions(),0);
            dp.correctBoundaryConditions();
            solveVolumePressureIncrement
            (
                residual(),g,rhoL,rg,psiG,mlFace,mgFace,
                dp,dfl,dfg,referenceCell
            );
            bool changed=false;
            const auto& own=mesh.owner();
            const auto& nei=mesh.neighbour();
            forAll(nei,facei)
            {
                const label donorL=dfl[facei]>=0 ? own[facei] : nei[facei];
                const label donorG=dfg[facei]>=0 ? own[facei] : nei[facei];
                if (dfl[facei]!=0 && l[donorL]<=0 && mlFace[facei]>0)
                {
                    mlFace.primitiveFieldRef()[facei]=0;
                    changed=true;
                }
                if (dfg[facei]!=0 && g[donorG]<=0 && mgFace[facei]>0)
                {
                    mgFace.primitiveFieldRef()[facei]=0;
                    changed=true;
                }
            }
            forAll(mesh.boundary(),patchi)
            {
                const auto& cells=mesh.boundary()[patchi].faceCells();
                forAll(cells,facei)
                {
                    if (dfl.boundaryField()[patchi][facei]>0
                        && l[cells[facei]]<=0
                        && mlFace.boundaryField()[patchi][facei]>0)
                    {
                        mlFace.boundaryFieldRef()[patchi][facei]=0;
                        changed=true;
                    }
                    if (dfg.boundaryField()[patchi][facei]>0
                        && g[cells[facei]]<=0
                        && mgFace.boundaryField()[patchi][facei]>0)
                    {
                        mgFace.boundaryFieldRef()[patchi][facei]=0;
                        changed=true;
                    }
                }
            }
            if (!returnReduce(label(changed),sumOp<label>()))
            {
                activeSetStable=true;
                break;
            }
        }
        if (!activeSetStable)
        {
            Info<< "FS_C08_VOLUME_PROJECTION_REJECTED"
                << " reason=donor_active_set_limit" << nl;
            return false;
        }

        // Uniform damping of all pressure and face mass increments:
        // no cell-local mass clipping, no independent phase scaling.
        // The same factor multiplies both sides of every internal face.
        const volScalarField dl("fsC08ProjectionDL",-dt*fvc::div(dfl));
        const volScalarField dg("fsC08ProjectionDG",-dt*fvc::div(dfg));
        const volScalarField drg("fsC08ProjectionDRhoG",psiG*dp);
        // Audit the actual assembled matrix flux against the local
        // linearized volume equation, including gas EOS. Distinguish
        // a stiff incompressible startup from a wrong FV Jacobian.
        if (iter==0)
        {
            scalar maxLinearDefect=0, maxMetalResidual=0;
            label metalCell=-1, minDpCell=-1;
            scalar minDp=GREAT;
            forAll(l,i)
            {
                const scalar linearDefect=residual()[i]
                    +dl[i]/rhoL[i]+dg[i]/rg[i]
                    -g[i]*drg[i]/sqr(rg[i]);
                maxLinearDefect=max(maxLinearDefect,mag(linearDefect));
                if (g[i]==0 && l[i]+mS[i]>0
                    && mag(residual()[i])>maxMetalResidual)
                {
                    maxMetalResidual=mag(residual()[i]);
                    metalCell=i;
                }
                if (dp[i]<minDp)
                {
                    minDp=dp[i];
                    minDpCell=i;
                }
            }
            Info<< "FS_C08_VOLUME_JACOBIAN_AUDIT"
                << " dt_s=" << dt.value()
                << " maxLinearizedDefect=" << maxLinearDefect
                << " maxPureMetalResidual=" << maxMetalResidual
                << " pureMetalCell=" << metalCell;
            if (metalCell>=0)
                Info<< " signedMetalResidual=" << residual()[metalCell];
            if (minDpCell>=0)
                Info<< " minDpCell=" << minDpCell
                    << " minDp_Pa=" << minDp
                    << " residualAtMinDp=" << residual()[minDpCell]
                    << " gasMassAtMinDp=" << g[minDpCell]
                    << " metalVolumeAtMinDp="
                    << l[minDpCell]/rhoL[minDpCell]+mS[minDpCell]/rhoS[minDpCell]
                    << " liquidMassIncrementAtMinDp=" << dl[minDpCell];
            Info<< nl;
        }
        bool advanced=false;
        label inadmissibleBacktracks=0, nonDescentBacktracks=0;
        // A finite but tiny donor inventory can make repeated halvings
        // insufficient. Compute the admissible global step directly
        // from the actual conservative mass/pressure increments.
        // Never modify the conserved fields or individual face fluxes.
        scalar step=1;
        label limitingCell=-1;
        word limitingField("none");
        const auto boundStep=[&](scalar value, scalar increment,
                                 label celli, const word& name)
        {
            if (increment<0)
            {
                const scalar bound=value/(-increment);
                if (bound<step)
                {
                    step=max(scalar(0),scalar(0.99)*bound);
                    limitingCell=celli;
                    limitingField=name;
                }
            }
        };
        forAll(l,i)
        {
            boundStep(l[i],dl[i],i,"liquidMass");
            boundStep(g[i],dg[i],i,"gasMass");
            boundStep(rg[i],drg[i],i,"gasDensity");
            boundStep(p[i],dp[i],i,"pressure");
        }
        if (step<1)
        {
            Info<< "FS_C08_VOLUME_STEP_BOUND"
                << " iteration=" << iter
                << " cell=" << limitingCell
                << " field=" << limitingField
                << " boundStep=" << step;
            if (limitingCell>=0)
            {
                const label i=limitingCell;
                Info<< " liquidMass=" << l[i]
                    << " liquidIncrement=" << dl[i]
                    << " gasMass=" << g[i]
                    << " gasIncrement=" << dg[i]
                    << " gasDensity=" << rg[i]
                    << " gasDensityIncrement=" << drg[i]
                    << " pressure=" << p[i]
                    << " pressureIncrement=" << dp[i];
            }
            Info<< nl;
        }
        if (step<=0)
        {
            Info<< "FS_C08_VOLUME_PROJECTION_REJECTED"
                << " reason=zero_admissible_step"
                << " maxResidual=" << norm << nl;
            return false;
        }
        for (label back=0;back<maxBacktracks;++back,step*=0.5)
        {
            const volScalarField lc("fsC08ProjectionCandidateL",l+step*dl);
            const volScalarField gc("fsC08ProjectionCandidateG",g+step*dg);
            const volScalarField rc("fsC08ProjectionCandidateRhoG",rg+step*drg);
            const volScalarField pc("fsC08ProjectionCandidateP",p+step*dp);
            if (!admissibleTrial(lc,mS,gc,rhoL,rhoS,rc,pc,false))
            {
                ++inadmissibleBacktracks;
                continue;
            }
            const tmp<volScalarField> candidate=
                trialVolumeResidual(lc,mS,gc,rhoL,rhoS,rc);
            const scalar nextNorm=residualNorm(candidate());
            if (nextNorm>=norm && nextNorm>tolerance)
            {
                ++nonDescentBacktracks;
                continue;
            }
            Info<< "FS_C08_VOLUME_PROJECTION_ITER"
                << " iteration=" << iter
                << " residualBefore=" << norm
                << " residualAfter=" << nextNorm
                << " acceptedStep=" << step
                << " inadmissibleBacktracks=" << inadmissibleBacktracks
                << " nonDescentBacktracks=" << nonDescentBacktracks << nl;
            l=lc; g=gc; rg=rc; p=pc;
            fl+=step*dfl; fg+=step*dfg;
            advanced=true;
            break;
        }
        if (!advanced)
        {
            Info<< "FS_C08_VOLUME_PROJECTION_REJECTED"
                << " reason=no_admissible_descent"
                << " iteration=" << iter
                << " maxResidual=" << norm
                << " inadmissibleBacktracks=" << inadmissibleBacktracks
                << " nonDescentBacktracks=" << nonDescentBacktracks
                << " minLiquidMass=" << min(l).value()
                << " minGasMass=" << min(g).value()
                << " minGasDensity=" << min(rg).value()
                << " minPressure=" << min(p).value()
                << " dpMin=" << min(dp).value()
                << " dpMax=" << max(dp).value() << nl;
            return false;
        }
    }
    Info<< "FS_C08_VOLUME_PROJECTION_REJECTED"
        << " reason=iteration_limit" << nl;
    return false;
}

}} // namespace Foam::fsC08
