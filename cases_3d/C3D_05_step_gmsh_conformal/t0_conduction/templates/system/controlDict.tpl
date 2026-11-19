/* C3D-05 Caso B, T0 CONDUCTION ONLY; OpenFOAM Foundation 14.
 * TEMPLATE — never execute before vetted inputs and WSL checks. */
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}
// -------------------------------------------------------------------------
application     foamMultiRun;
// Foundation 14 syntax: same solid module in both *distinct* regions.
regionSolvers
{
    metal           solid;
    mold            solid;
}
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {{END_TIME}};
deltaT          {{DELTA_T}};
writeControl    timeStep;
writeInterval   {{WRITE_STEPS}};
purgeWrite      0;
writeFormat     binary;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   10;
runTimeModifiable false;
// Do not treat maxCo as a measured quantity: pure solid conduction has no U.
