/* C3D-05 Caso B, T0 CONDUCTION ONLY; OpenFOAM Foundation 14.
 * TEMPLATE — never execute before vetted inputs and WSL checks. */
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant/metal";
    object      physicalProperties;
}
// -------------------------------------------------------------------------
// Material values loaded from T0_INPUTS.json, always with citations.
// NO latent heat, phase change, velocity or liquid metal in T0.
thermoType
{
    type            heSolidThermo;
    mixture         pureMixture;
    transport       constIsoSolid;
    thermo          eConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleInternalEnergy;
}
mixture
{
    specie
    {
        molWeight   {{MOL_WEIGHT}};
    }
    equationOfState
    {
        rho         {{RHO}};
    }
    transport
    {
        kappa       {{KAPPA}};
    }
    thermodynamics
    {
        hf          0;
        Cv          {{CV}};
    }
}
