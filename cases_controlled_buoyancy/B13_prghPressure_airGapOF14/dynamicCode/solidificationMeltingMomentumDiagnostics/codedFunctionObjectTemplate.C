/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) YEAR OpenFOAM Foundation
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

#include "codedFunctionObjectTemplate.H"
#include "volFields.H"
#include "read.H"
#include "addToRunTimeSelectionTable.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

namespace Foam
{

// * * * * * * * * * * * * * * Static Data Members * * * * * * * * * * * * * //

defineTypeNameAndDebug(solidificationMeltingMomentumDiagnosticsFunctionObject, 0);

addRemovableToRunTimeSelectionTable
(
    functionObject,
    solidificationMeltingMomentumDiagnosticsFunctionObject,
    dictionary
);


// * * * * * * * * * * * * * * * Global Functions  * * * * * * * * * * * * * //

extern "C"
{
    // Unique function name that can be checked
    // to ensure the correct library version has been loaded
    void solidificationMeltingMomentumDiagnostics_a28c3d6b0dfa5996ff73f1bf0014ffed29f9c4ff(bool load)
    {
        if (load)
        {
            // code that can be explicitly executed after loading
        }
        else
        {
            // code that can be explicitly executed before unloading
        }
    }
}


// * * * * * * * * * * * * * * * Local Functions * * * * * * * * * * * * * * //

//{{{ begin localCode

//}}} end localCode


// * * * * * * * * * * * * * Private Member Functions  * * * * * * * * * * * //

const fvMesh& solidificationMeltingMomentumDiagnosticsFunctionObject::mesh() const
{
    return refCast<const fvMesh>(obr_);
}


// * * * * * * * * * * * * * * * * Constructors  * * * * * * * * * * * * * * //

solidificationMeltingMomentumDiagnosticsFunctionObject::solidificationMeltingMomentumDiagnosticsFunctionObject
(
    const word& name,
    const Time& runTime,
    const dictionary& dict
)
:
    functionObjects::regionFunctionObject(name, runTime, dict)
{
    read(dict);
}


// * * * * * * * * * * * * * * * * Destructor  * * * * * * * * * * * * * * * //

solidificationMeltingMomentumDiagnosticsFunctionObject::~solidificationMeltingMomentumDiagnosticsFunctionObject()
{}


// * * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * //

bool solidificationMeltingMomentumDiagnosticsFunctionObject::read(const dictionary& dict)
{
    if (false)
    {
        Info<<"read solidificationMeltingMomentumDiagnostics sha1: a28c3d6b0dfa5996ff73f1bf0014ffed29f9c4ff\n";
    }

//{{{ begin code
    
//}}} end code

    return true;
}


Foam::wordList solidificationMeltingMomentumDiagnosticsFunctionObject::fields() const
{
    if (false)
    {
        Info<<"fields solidificationMeltingMomentumDiagnostics sha1: a28c3d6b0dfa5996ff73f1bf0014ffed29f9c4ff\n";
    }

    wordList fields;
//{{{ begin code
    
//}}} end code

    return fields;
}


bool solidificationMeltingMomentumDiagnosticsFunctionObject::execute()
{
    if (false)
    {
        Info<<"execute solidificationMeltingMomentumDiagnostics sha1: a28c3d6b0dfa5996ff73f1bf0014ffed29f9c4ff\n";
    }

//{{{ begin code
    
//}}} end code

    return true;
}


bool solidificationMeltingMomentumDiagnosticsFunctionObject::write()
{
    if (false)
    {
        Info<<"write solidificationMeltingMomentumDiagnostics sha1: a28c3d6b0dfa5996ff73f1bf0014ffed29f9c4ff\n";
    }

//{{{ begin code
    #line 579 "/home/michel/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy/B13_prghPressure_airGapOF14/system/researchDiagnostics!solidificationMeltingMomentumDiagnostics"

        const fvMesh& m = mesh();

        const volScalarField& alphaL =
            m.lookupObject<volScalarField>("phaseChangeSource:alpha1");
        const volVectorField& U =
            m.lookupObject<volVectorField>("U");
        const volScalarField& T =
            m.lookupObject<volScalarField>("T");
        const volScalarField& rho =
            m.lookupObject<volScalarField>("rho");
        const volScalarField& pRgh =
            m.lookupObject<volScalarField>("p_rgh");
        const uniformDimensionedVectorField& g =
            m.lookupObject<uniformDimensionedVectorField>("g");

        IOdictionary fvModelsDict
        (
            IOobject
            (
                "fvModels",
                m.time().constant(),
                m,
                IOobject::MUST_READ,
                IOobject::NO_WRITE
            )
        );

        const dictionary& pc = fvModelsDict.subDict("phaseChangeSource");

        const scalar Cu = pc.lookupOrDefault<scalar>("Cu", 1e5);
        const scalar q = pc.lookupOrDefault<scalar>("q", 1e-3);
        const scalar beta = pc.lookup<scalar>("beta");
        const scalar rhoRef = pc.lookup<scalar>("rhoRef");
        const scalar Tsol = pc.lookup<scalar>("Tsol");
        const scalar Tliq = pc.lookupOrDefault<scalar>("Tliq", Tsol);
        const scalar alpha1e = pc.lookupOrDefault<scalar>("alpha1e", 0.0);

        const dimensionedScalar CuD("Cu", dimless/dimTime, Cu);
        const dimensionedScalar qD("q", dimless, q);
        const dimensionedScalar betaD
        (
            "beta",
            dimless/dimTemperature,
            beta
        );
        const dimensionedScalar rhoRefD("rhoRef", dimDensity, rhoRef);
        const dimensionedScalar accelFloor
        (
            "accelFloor",
            dimLength/sqr(dimTime),
            SMALL
        );

        volScalarField solidFraction
        (
            IOobject
            (
                "phaseChangeSolidFraction",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            scalar(1) - alphaL
        );

        // Positive damping coefficient D [1/s].
        // OpenFOAM inserts S=-D into the momentum matrix diagonal.
        volScalarField darcyCoeff
        (
            IOobject
            (
                "phaseChangeDarcyCoeff",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            CuD*sqr(scalar(1) - alphaL)/(pow3(alphaL) + qD)
        );

        volScalarField darcySp
        (
            IOobject
            (
                "phaseChangeDarcySp",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            -darcyCoeff
        );

        // Acceleration-scale representation of the implicit Darcy resistance.
        volVectorField darcyAccel
        (
            IOobject
            (
                "phaseChangeDarcyAcceleration",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            -darcyCoeff*U
        );

        // Reconstruct deltaT exactly as solidificationMeltingSource does.
        volScalarField modelDeltaT
        (
            IOobject
            (
                "phaseChangeModelDeltaT",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            m,
            dimensionedScalar("zero", dimTemperature, 0),
            zeroGradientFvPatchScalarField::typeName
        );

        forAll(modelDeltaT, celli)
        {
            const scalar a = alphaL[celli];

            const scalar Tphase =
                max
                (
                    Tsol,
                    Tsol
                  + (Tliq - Tsol)*(a - alpha1e)/(1.0 - alpha1e)
                );

            modelDeltaT[celli] = T[celli] - Tphase;
        }
        modelDeltaT.correctBoundaryConditions();

        const dimensionedVector gD("g", g.dimensions(), g.value());

        // Physical acceleration scale g*beta*deltaT [m/s2].
        volVectorField buoyancyAccel
        (
            IOobject
            (
                "phaseChangeBuoyancyAcceleration",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            gD*betaD*modelDeltaT
        );

        // Exact explicit source vector Sb used by solidificationMeltingSource.
        volVectorField buoyancySu
        (
            IOobject
            (
                "phaseChangeBuoyancySu",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            rhoRefD*buoyancyAccel
        );

        // Pressure-gradient acceleration from the solved p_rgh field.
        volVectorField pressureAccel
        (
            IOobject
            (
                "pRghAcceleration",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            -fvc::grad(pRgh)/rho
        );

        volScalarField magDarcyAccel
        (
            IOobject
            (
                "magPhaseChangeDarcyAcceleration",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            mag(darcyAccel)
        );

        volScalarField magBuoyancyAccel
        (
            IOobject
            (
                "magPhaseChangeBuoyancyAcceleration",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            mag(buoyancyAccel)
        );

        volScalarField magPressureAccel
        (
            IOobject
            (
                "magPRghAcceleration",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            mag(pressureAccel)
        );

        volScalarField dragToBuoyancy
        (
            IOobject
            (
                "phaseChangeDragToBuoyancy",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            magDarcyAccel/(magBuoyancyAccel + accelFloor)
        );

        volScalarField dragToPressure
        (
            IOobject
            (
                "phaseChangeDragToPressure",
                m.time().timeName(m.time().value()),
                m,
                IOobject::NO_READ,
                IOobject::NO_WRITE
            ),
            magDarcyAccel/(magPressureAccel + accelFloor)
        );

        solidFraction.write();
        darcyCoeff.write();
        darcySp.write();
        darcyAccel.write();
        modelDeltaT.write();
        buoyancyAccel.write();
        buoyancySu.write();
        pressureAccel.write();
        magDarcyAccel.write();
        magBuoyancyAccel.write();
        magPressureAccel.write();
        dragToBuoyancy.write();
        dragToPressure.write();

        Info<< "solidificationMelting diagnostics: "
            << "max(DarcyCoeff)=" << gMax(darcyCoeff)
            << "  max(|DarcyAccel|)=" << gMax(magDarcyAccel)
            << "  max(|BuoyancyAccel|)=" << gMax(magBuoyancyAccel)
            << "  max(|pRghAccel|)=" << gMax(magPressureAccel)
            << nl;
    
//}}} end code

    return true;
}


bool solidificationMeltingMomentumDiagnosticsFunctionObject::end()
{
    if (false)
    {
        Info<<"end solidificationMeltingMomentumDiagnostics sha1: a28c3d6b0dfa5996ff73f1bf0014ffed29f9c4ff\n";
    }

//{{{ begin code
    
//}}} end code

    return true;
}


// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

} // End namespace Foam

// ************************************************************************* //

