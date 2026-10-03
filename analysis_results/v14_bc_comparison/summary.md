# V14 B/C comparison — controlled impermeable-top reference

**Date:** 2026-10-03  
**Cases:** `B14_topFixedFlux_explicitRef` vs `C14_topFixedFlux_explicitRef`  
**Status:** RUN-VERIFIED / ANALYSIS-VERIFIED

## Purpose

Compare the two buoyancy/density formulations after removing the historical `metalTop` pressure/flux inconsistency. Both V14 cases use the same geometry, mesh, thermal boundary conditions, OF14 air-gap formulation, `U=slip`, `p_rgh=fixedFluxPressure`, explicit pressure reference, timestep and diagnostics.

The remaining intended physical difference is the B/C density-buoyancy formulation.

## Run and top-boundary verification

| Metric | B14 | C14 |
|---|---:|---:|
| Final time | 10 s | 10 s |
| metalTop faces | 80 | 80 |
| Max `sum(abs(phi))`, 0.1–10 s | 8.47033e-22 | 0 |
| Max `|Uy|` on metalTop at sampled 0.1/5/10 s | 0 | 0 |
| Max Courant number | 0.0673434 | 0.0650864 |
| Final cumulative continuity | -3.10190e-02 | 4.44346e-13 |
| Execution time | 499.049 s | 551.741 s |
| Clock time | 533 s | 571 s |

Both cases therefore have a genuinely impermeable top. The B/C comparison is no longer confounded by local inflow/outflow through `metalTop`.

## Thermal and phase state at 10 s

| Metric | B14 | C14 |
|---|---:|---:|
| Central T | 1470.07 K | 1464.19 K |
| Central liquid fraction | 0.988414 | 0.964815 |
| Volume-mean liquid fraction | 0.9606902 | 0.9620593 |
| Total boundary heat power | 316.1799 W | 313.9750 W |
| metalTop heat power | 37.47307 W | 36.55997 W |
| metal→mold heat power | 278.7068 W | 277.4151 W |
| Boundary advective energy power | ~0 | 0 |
| Integrated sensible enthalpy | 1.055746e5 | 1.053151e5 |

The boundary heat removal is very similar. The B/C differences are therefore not explained by different top mass flux or a large difference in external heat extraction.

## Spatial B14–C14 differences at 10 s

RMSE across 80 sampled points:

| Profile | Uy RMSE (m/s) | T RMSE (K) | liquid-fraction RMSE |
|---|---:|---:|---:|
| y = 10 mm | 5.2355e-3 | 7.8166 | 3.1219e-2 |
| y = 20 mm | 3.7677e-3 | 3.2461 | 1.3004e-2 |
| y = 30 mm | 1.8835e-3 | 4.2552 | 8.3893e-3 |
| x = 20 mm vertical | 2.0921e-3 | 6.8132 | 1.3813e-2 |

The flow fields remain substantially different even after the top boundary is made consistent.

## Interpretation

B uses temperature-dependent density through `icoTabulated` with the explicit `solidificationMelting` buoyancy term disabled. C uses constant density with the explicit thermal-buoyancy coefficient.

With the present **rigid, fixed-volume, impermeable** Quick-Cup geometry, B accumulates a large continuity mismatch (`-3.10e-2`) while C remains near machine-zero continuity error. This is consistent with the already identified incompatibility between a prescribed temperature-dependent density and a closed fixed volume when no shrinkage, feeding, moving free surface or other volume-change mechanism is present.

The thermal boundary powers are close, so the large flow-field difference is associated primarily with the density/buoyancy formulation rather than unequal heat extraction.

## Decision for the current thesis model

**C14 is the recommended current physical/production baseline for the rigid fixed-volume model.**

B14 should be retained as a controlled alternative-formulation/sensitivity case, not discarded. It becomes physically more relevant if the model is later extended to include the volume-change physics required by temperature-dependent density, such as shrinkage, feeding or a moving free surface.

V14 also confirms that the supervisor-requested explicit pressure reference does not materially alter the V11 physical solution.

No V15 is created by this analysis.
