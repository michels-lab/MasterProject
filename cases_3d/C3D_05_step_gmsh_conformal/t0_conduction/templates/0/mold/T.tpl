/* C3D-05 Caso B, T0 CONDUCTION ONLY; OpenFOAM Foundation 14.
 * TEMPLATE — never execute before vetted inputs and WSL checks. */
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0/mold";
    object      T;
}
// -------------------------------------------------------------------------
dimensions      [0 0 0 1 0 0 0];
internalField   uniform {{T_INITIAL}};
boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"
    moldOuterUnclassified
    {
        // T0 isolated closed two-solid verification; NOT observed QuickCup cooling.
        type            zeroGradient;
    }
    mold_to_metal
    {
        // Foundation 14 coupledTemperature on reciprocal mappedWall patches.
        type            coupledTemperature;
        value           $internalField;
    }
}
