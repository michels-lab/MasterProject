/* C3D-05 B metal SOLID T0. From C14 system/mold/fvSolution.
 * Uses C14 (h|e) PCG+DIC numerical settings for sensibleInternalEnergy e.
 * C14 FLUID p_rgh, U, momentum controls are not applicable to T0 solids.
 */
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    location "system/metal";
    object fvSolution;
}
solvers
{
    e
    {
        solver PCG;
        preconditioner DIC;
        tolerance 1e-06;
        relTol 0.05;
    }
    eFinal
    {
        $e;
        relTol 0;
    }
}
PIMPLE
{
    nOuterCorrectors 1;
    nCorrectors 2;
    nNonOrthogonalCorrectors 0;
}
