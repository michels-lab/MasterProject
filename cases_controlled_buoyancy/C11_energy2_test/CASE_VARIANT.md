# C11_energy2_test — energy-corrector configuration variant

## 2026-10-21 — provenance clarification (source-verified, not CFD revalidation)

This directory is **not an identical CFD configuration** to `C11_topFixedFlux_airGapOF14`: its `system/fvSolution` explicitly sets `PIMPLE.nEnergyCorrectors 2`, while the paired `C11_topFixedFlux_airGapOF14/system/fvSolution` has no such entry. This is a verified **input-file difference**, not proof that it changes numerical results or that this case was newly run.

The V11 closure figures and `RUN-VERIFIED + ANALYSIS-VERIFIED` claims in the **copied historical description below refer to the canonical `C11_topFixedFlux_airGapOF14` V11 baseline** unless separately linked raw logs and analysis reports establish the same claims for this energy2 folder. Do not use this document alone as evidence of energy2-specific run completion, convergence, or physical/experimental validation.

- Distinct current input: [this `fvSolution`](system/fvSolution).
- Paired original: [`C11_topFixedFlux_airGapOF14` `fvSolution`](../C11_topFixedFlux_airGapOF14/system/fvSolution).
- Research decision and remaining tests: [B11/C11 documentation provenance audit](../../docs/granada/B11_C11_ENERGY2_DOCUMENTATION_AUDIT_20261021.md).
- **Action gate:** compare committed run logs/registered evidence and assess solver-specific effect of `nEnergyCorrectors` before claiming a validated sensitivity result. CFD stays local.

## Preserved baseline description (historical copy)

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
