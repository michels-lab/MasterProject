COMMAND: /opt/openfoam14/platforms/linux64GccDPInt32Opt/bin/foamDictionary /home/michel/OpenFOAM/.C3D04_A_C14_FAITHFUL_RUNTIME_10S_01.staging.gh4_e9q2/candidate/0/mold/T
RC: 0
STDOUT:
FoamFile
{
    version         2;
    format          ascii;
    class           volScalarField;
    location        "0/mold";
    object          T;
}

dimensions      [ 0 0 0 1 0 0 0 ];

internalField   uniform 300;

boundaryField
{
    moldTop
    {
        type            externalTemperature;
        h               uniform 10;
        Ta              constant 300;
        emissivity      0.5;
        value           $internalField;
    }
    moldExterior
    {
        type            externalTemperature;
        h               uniform 10;
        Ta              constant 300;
        emissivity      0.5;
        value           $internalField;
    }
    moldBottom
    {
        type            externalTemperature;
        h               uniform 10;
        Ta              constant 300;
        emissivity      0.5;
        value           $internalField;
    }
    moldRecessWall
    {
        type            externalTemperature;
        h               uniform 10;
        Ta              constant 300;
        emissivity      0.5;
        value           $internalField;
    }
    moldRecessRoof
    {
        type            externalTemperature;
        h               uniform 10;
        Ta              constant 300;
        emissivity      0.5;
        value           $internalField;
    }
    mold_to_metal
    {
        type            coupledTemperature;
        value           $internalField;
    }
}

STDERR:
