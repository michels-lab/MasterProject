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

## Current methodological status

**RUN-VERIFIED + ANALYSIS-VERIFIED.**

Direct C11 evidence confirms strict closure of the stored top diagnostics:
- `sum(phi)=0`;
- integrated top advective energy = 0 J.

Relative to C10, the physical solution changes only slightly (center T RMSE 0.164 K; final Uy NRMSE below 1.71% on the three canonical profiles). C11 also yields essentially zero cumulative continuity error.

C11 is therefore the preferred fixed-volume physical baseline for the next G1 experimental validation stage. V12/V13 remain pressure-boundary diagnostics.
