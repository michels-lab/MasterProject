# C11 energy-corrector controlled test

**Date:** 2026-10-03  
**Baseline:** `C11_topFixedFlux_airGapOF14`  
**Test:** `C11_energy2_test`  
**Status:** RUN-VERIFIED / ANALYSIS-VERIFIED

## Controlled change

Only the root multi-region control was changed:

`system/fvSolution/PIMPLE/nEnergyCorrectors = 2`.

All geometry, mesh, material properties, boundary conditions, timestep, regional solvers and solidification parameters remain those of C11.

## Activation

- C11 normal: `h_0..2`, `e_0..2` = 3 energy solves per timestep.
- C11-energy2: `h_0..5`, `e_0..5` = 6 energy solves per timestep.

With 3 global outer correctors, the test confirms 3 × 2 = 6 energy solves.

## Physical comparison

| Metric | Result |
|---|---:|
| Central T(t), 10,001 points | RMSE 0 K; byte-identical |
| T at 10 s | 1464.19 K in both |
| Central alphaL | RMSE 4.80e-8; max difference 1e-6 |
| Mean alphaL | RMSE 2.22e-8; max difference 1e-7 |
| Central U | RMSE 7.70e-9 m/s; max difference 1e-7 m/s |
| y=20 mm, 10 s, T | identical |
| y=20 mm, 10 s, alphaL | identical |
| y=20 mm, 10 s, Uy | RMSE 4.04e-9 m/s; max difference 1e-8 m/s |
| Max Courant | 0.0650864 in both |
| Final cumulative continuity | 4.44517e-13 vs 4.58617e-13 |

## Residual behavior

The additional correction lowers the enthalpy residual further. In the energy2 run, `h_5` has median residual about 1.05e-10 and final-time residual about 1.57e-11.

This is numerical over-convergence: no measurable physical change accompanies the lower residual.

## Cost

Persisted runs:
- C11: executionTime 289.433 s; clockTime 302 s.
- C11-energy2: executionTime 387.542 s; clockTime 398 s.

Observed overhead in these runs is approximately +34% executionTime and +32% wall-clock. Hosted-run timing is environment-dependent, but the extra computational cost is clear.

## C14 clarification

C14 stores `nEnergyCorrectors 2` in `system/metal/fvSolution`. That regional entry does not control the global energy-corrector loop of `foamMultiRun`.

C14 therefore ran with **1 effective energy corrector**, evidenced by only `h_0..2` and `e_0..2`.

## Decision

For the current Quick-Cup baseline, retain **1 energy corrector**. Two effective correctors reduce energy residuals but do not alter the physical solution within resolved precision and increase computational cost.
