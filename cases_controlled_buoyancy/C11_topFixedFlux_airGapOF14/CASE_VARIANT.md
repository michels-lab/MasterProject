# C11_topFixedFlux_airGapOF14

Parent case: `C9_topFixedFlux`.

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

The C family retains `rhoConst` exactly as in the parent case.

All timestep, PIMPLE, mesh, phase-change, velocity, pressure, top thermal boundary, material and diagnostic settings otherwise remain inherited from the parent lineage.
