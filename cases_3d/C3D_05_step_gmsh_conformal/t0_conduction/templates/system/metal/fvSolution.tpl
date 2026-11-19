/* C3D-05 Caso B, T0 CONDUCTION ONLY; OpenFOAM Foundation 14.
 * TEMPLATE — never execute before vetted inputs and WSL checks. */
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system/metal";
    object      fvSolution;
}
// -------------------------------------------------------------------------
// T0 numerical choices are proposed; NOT validated on the QuickCup mesh.
solvers
{
    e
    {
        solver          GAMG;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0.05;
        maxIter         200;
    }
    eFinal
    {
        $e;
        relTol          0;
    }
}
PIMPLE
{
    // Baseline sensitivity hypothesis; compare 0, 1, 2+ correctors later.
    nNonOrthogonalCorrectors 2;
}
