/* C3D-05 Caso B, T0 CONDUCTION ONLY; OpenFOAM Foundation 14.
 * TEMPLATE — never execute before vetted inputs and WSL checks. */
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system/mold";
    object      fvSchemes;
}
// -------------------------------------------------------------------------
// Based on Foundation 14 tutorials/multiRegion/CHT/heatedDuct/system/metal/fvSchemes.
ddtSchemes
{
    default         Euler;
}
gradSchemes
{
    default         Gauss linear;
}
divSchemes
{
    default         none;
}
laplacianSchemes
{
    // Preliminary diffusion correction; sensitivity needed for 1,826 >70deg faces.
    default         Gauss linear corrected;
}
interpolationSchemes
{
    default         linear;
}
snGradSchemes
{
    default         corrected;
}
