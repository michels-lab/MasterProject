# B11_topFixedFlux_airGapOF14

Parent case: `B9_topFixedFlux`.

Purpose: V9 top fixedFluxPressure lineage + corrected OF14 air gap.

## Controlled configuration

The metal-mold air gap is represented with OpenFOAM Foundation v14 syntax on the metal side only:

```
h
{
    type              wallLayersHeatTransferCoefficient;
    thicknessLayers   (2e-4);
    kappaLayers       (1e-1);
}
```

The mold side remains a plain `coupledTemperature` boundary, avoiding a duplicated series resistance.

Both B10 and B11 use the same extended `icoTabulated` density table through 2273.15 K; all original values through 1773.15 K remain unchanged.

All timestep, PIMPLE, mesh, phase-change, velocity, pressure, top thermal boundary, material and diagnostic settings otherwise remain inherited from the parent lineage.
