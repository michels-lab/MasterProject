/* C3D-05 B T0: sourced from C14 system/fvSolution and metal energy choice.
 * See C14_FVSOLUTION_PROVENANCE.json for original Git blob SHA.
 * TWO SOLIDS; CFD and stability NOT verified.
 */
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    location "system";
    object fvSolution;
}
PIMPLE
{
    nOuterCorrectors 3;
    nCorrectors 2;
    nNonOrthogonalCorrectors 1;
    nEnergyCorrectors 2;
}
relaxationFactors
{
    equations
    {
        e 1.0;
        eFinal 1.0;
    }
}
