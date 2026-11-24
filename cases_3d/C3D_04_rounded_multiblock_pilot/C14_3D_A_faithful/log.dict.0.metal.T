COMMAND: /opt/openfoam14/platforms/linux64GccDPInt32Opt/bin/foamDictionary /home/michel/OpenFOAM/.C3D04_A_C14_FAITHFUL_RUNTIME_10S_01.staging.gh4_e9q2/candidate/0/metal/T
RC: 0
STDOUT:
FoamFile
{
    version         2;
    format          ascii;
    class           volScalarField;
    location        "0/metal";
    object          T;
}

dimensions      [ 0 0 0 1 0 0 0 ];

internalField   uniform 1500;

boundaryField
{
    metalTop
    {
        type            externalTemperature;
        h               uniform 10;
        Ta              constant 300;
        emissivity      0.3;
        value           $internalField;
    }
    metal_to_mold
    {
        type            coupledTemperature;
        h
        {
            type            wallLayersHeatTransferCoefficient;
            thicknessLayers ( 0.0002 );
            kappaLayers     ( 0.1 );
        }
        value           $internalField;
    }
}

STDERR:
