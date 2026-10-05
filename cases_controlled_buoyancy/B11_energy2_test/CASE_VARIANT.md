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

## Current methodological status

**RUN-VERIFIED + ANALYSIS-VERIFIED.**

Direct V11 evidence confirms that `fixedFluxPressure + slip` closes `metalTop` to numerical precision:
- max `|sum(phi)| = 1.694066e-21 kg/s`;
- integrated top advective energy ≈ 0 J.

Relative to B10, closing the top removes ~629.6 J of advective transport and strongly reorganizes the B velocity field. The variable-density cumulative continuity mismatch remains and is interpreted as a fixed-volume/model-physics limitation, not as top leakage.

V11 therefore remains the impermeable baseline for family B; V12/V13 remain diagnostic pressure-value variants.
