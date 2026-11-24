/* FS-C08: GPL-3.0 adaptation of Foundation14 thermophysicalPredictor.C.
 * New: mass-effective metal Cv(T) and ONE Gamma L latent source.
 * The old VoFSolidificationMelting energy model MUST NOT also be loaded.
 * Solid enthalpy convection (zero solid velocity), p*dV and advanced
 * thermodynamic consistency are still unverified, no physical validation.
 * Original upstream license header retained below.
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
#include "fvmDiv.H"
#include "fvmSup.H"
#include "fvmLaplacian.H"

// * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * * //

void Foam::solvers::fsC08ConservativeVoF::thermophysicalPredictor()
{
    const volScalarField& rho1(rhoMetalEffective_);
    const volScalarField& rho2(mixture.rho2());

    const volScalarField& e1(mixture.thermo1().he());
    const volScalarField& e2(mixture.thermo2().he());

    const fvScalarMatrix e1Source(fvModels().source(alpha1, rho1, e1));
    const fvScalarMatrix e2Source(fvModels().source(alpha2, rho2, e2));

    // EFFECTIVE mass-specific metal heat capacity, from conserved phase
    // masses. First-order sensible heat approximation. Do not declare
    // thermodynamically exact until the separate solid enthalpy closure.
    volScalarField cvMetal("CvMetal.fsC08",mixture.thermo1().Cv());
    const auto& ml=phaseMass_->liquidMass().primitiveField();
    const auto& ms=phaseMass_->solidMass().primitiveField();
    auto& cv=cvMetal.primitiveFieldRef();
    const scalar cvS=phaseMass_->cpSolid().value();
    forAll(cv,celli)
    {
        const scalar M=ml[celli]+ms[celli];
        if (M>1e-20)
            cv[celli]=(ml[celli]*cv[celli]+ms[celli]*cvS)/M;
    }
    cvMetal.correctBoundaryConditions();

    volScalarField& T = mixture_.T();

    fvScalarMatrix TEqn
    (
        correction
        (
            cvMetal
           *(
                fvm::ddt(alpha1, rho1, T) + fvm::div(alphaRhoPhi1, T)
              - (
                    e1Source.hasDiag()
                  ? fvm::Sp(contErr1(), T) + fvm::Sp(e1Source.A(), T)
                  : fvm::Sp(contErr1(), T)
                )
            )
          + mixture.thermo2().Cv()()
           *(
                fvm::ddt(alpha2, rho2, T) + fvm::div(alphaRhoPhi2, T)
              - (
                    e2Source.hasDiag()
                  ? fvm::Sp(contErr2(), T) + fvm::Sp(e2Source.A(), T)
                  : fvm::Sp(contErr2(), T)
                )
            )
        )

      + fvc::ddt(alpha1, rho1, e1) + fvc::div(alphaRhoPhi1, e1)
      - contErr1()*e1
      + fvc::ddt(alpha2, rho2, e2) + fvc::div(alphaRhoPhi2, e2)
      - contErr2()*e2

      - fvm::laplacian(thermophysicalTransport.kappaEff(), T)

      + (
            mixture.totalInternalEnergy()
          ?
            fvc::div(fvc::absolute(phi, U), p)()()
          + (fvc::ddt(rho, K) + fvc::div(rhoPhi, K))()()
          - (U()&(fvModels().source(rho, U)&U)()) - (contErr1() + contErr2())*K
          :
            p*fvc::div(fvc::absolute(phi, U))()()
        )
     ==
        (e1Source&e1)
      + (e2Source&e2)
      + phaseMass_->latentHeat()*phaseMass_->gamma()
    );

    TEqn.relax();

    fvConstraints().constrain(TEqn);

    TEqn.solve();

    fvConstraints().constrain(T);

    mixture_.correctThermo();
    mixture_.correct();
    reconcileMixtureDensity();
}


// ************************************************************************* //
