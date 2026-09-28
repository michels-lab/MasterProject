# V9 metalTop fixedFluxPressure — verified comparison

V9 changes `metalTop/p_rgh` from `totalPressure` to `fixedFluxPressure` while retaining `U=slip` and the same thermal boundary condition.

**Important caveat:** B9 required a diagnostic linear extension of the `icoTabulated rho(T)` table above 1773.15 K after an early table-range failure. Therefore B9-vs-B5 is not a perfectly single-change comparison after that extension. C9-vs-C5 remains a clean single-boundary-condition comparison.

## Boundary closure

### B9

- max |sum(phi) at metalTop| = 2.541e-21
- time-integrated signed top phi = -5.082e-22
- integrated top advective energy = -5.011e-16 J
- integrated total boundary advective energy = -1.606e-14 J

Thus the corrected `fixedFluxPressure + slip` top is impermeable to numerical precision.

B5, by contrast, had:
- integrated top advective energy = -970.358 J
- integrated total boundary advective energy = -970.358 J

### C9

- top phi = exactly 0 in stored diagnostics
- integrated top advective energy = 0 J
- integrated total boundary advective energy = 0 J

C5 had only +6.841 J of integrated advective boundary energy.

## Energy

### B

| metric | B5 | B9 |
|---|---:|---:|
| top advective J | -970.358 | ~0 |
| top diffusive J | 368.167 | 385.229 |
| mold diffusive J | 6732.026 | 6738.636 |
| total boundary energy J | 6129.835 | 7123.865 |

Closing the top removes ~970 J of advective transport and raises integrated total boundary energy by ~994 J. Diffusive mold transport changes only slightly.

### C

| metric | C5 | C9 |
|---|---:|---:|
| top advective J | +6.841 | 0 |
| top diffusive J | 370.877 | 370.628 |
| mold diffusive J | 6686.923 | 6686.993 |
| total boundary energy J | 7064.642 | 7057.622 |

The C energy solution is almost unchanged; the difference is essentially the removal of the small pre-existing top advective term.

## Coupling / continuity

### B

| case | median Rp | p95 Rp | Rp>1 | final cumulative | max |global| | median |global| | max Co | clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B5 | 0.5976 | 0.9452 | 3.44% | 1.652e-4 | 1.162e-10 | 6.282e-12 | 0.1759 | 345 s |
| B9 | 0.0021 | 0.0035 | 0.00% | -0.0460268 | 2.103e-5 | 5.504e-7 | 0.1071 | 397 s |

The pressure outer-loop residual contracts dramatically better in B9, but this does **not** mean the overall formulation is more mass-consistent. The transient mismatch between continuity density and thermodynamic `rho(T)` becomes orders of magnitude larger.

OpenFOAM's reported transient `cumulative continuity` here is the accumulated normalized mismatch between solver `rho` and `thermo.rho()`; it is not a literal final fractional mass loss.

### C

| case | median Rp | p95 Rp | Rp>1 | final cumulative | max |global| | median |global| | max Co | clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C5 | 0.7951 | 1.0247 | 7.14% | 1.782e-4 | 6.506e-12 | 3.796e-13 | 0.0701 | 319 s |
| C9 | 0.0004 | 0.0012 | 0.00% | 4.449e-13 | 1.086e-17 | 7.439e-18 | 0.0694 | 497 s |

For C, closing the top improves pressure coupling and essentially eliminates the already tiny continuity mismatch without materially changing the physical solution.

## Temperature

Center-probe B9 vs B5:
- RMSE = 14.616 K
- max difference = 29.19 K
- final: B5 1467.52 K; B9 1459.33 K (-8.19 K)

Center-probe C9 vs C5:
- RMSE = 0.196 K
- max difference = 0.45 K
- final: C5 1461.60 K; C9 1461.46 K (-0.14 K)

## Flow / phase comparison

### B9 vs B5

#### y = 20 mm
- median Uy NRMSE = 56.38%
- final Uy NRMSE = 61.15%; final correlation 0.7921
- peak Uy NRMSE = 129.86% at 2.8 s
- final vorticity-z RMSE = 2.695 1/s
- final flowType class disagreement = 70%
- final Darcy acceleration NRMSE = 54.23%
- final p_rgh acceleration NRMSE = 37.92%

#### y = 30 mm
- median Uy NRMSE = 94.97%
- final Uy NRMSE = 80.81%; final correlation 0.6399
- final flowType class disagreement = 65%
- final Darcy acceleration NRMSE = 52.81%

#### vertical x = 20 mm
- median Uy NRMSE = 111.93%
- final Uy NRMSE = 99.20%; final correlation 0.1284
- final Darcy acceleration NRMSE = 72.53%
- final p_rgh acceleration NRMSE = 57.33%

Final vertical phase-front positions:
- alphaL=0.05: B5 1.017 mm; B9 0.995 mm
- alphaL=0.50: B5 1.932 mm; B9 1.909 mm
- alphaL=0.95: B5 18.025 mm; B9 20.553 mm

Mushy width:
- B5 = 17.008 mm
- B9 = 19.558 mm
- change = +2.550 mm (+14.99%)

**Conclusion B:** the former top pressure condition materially altered the B solution. Once the boundary is made impermeable, circulation, topology, thermal history and mushy-zone extent change strongly.

### C9 vs C5

#### y = 20 mm
- median Uy NRMSE = 1.10%
- final Uy NRMSE = 1.10%; correlation ~1
- final T RMSE = 0.106 K
- final alphaL RMSE = 0.00042
- final flowType class disagreement = 5%
- final Darcy acceleration NRMSE = 2.84%

#### y = 30 mm
- median Uy NRMSE = 2.94%
- final Uy NRMSE = 2.92%; correlation ~1
- final T RMSE = 0.137 K
- final alphaL RMSE = 0.00055
- final flowType class disagreement = 5%

#### vertical x = 20 mm
- median Uy NRMSE = 1.76%
- final Uy NRMSE = 2.68%; correlation 0.9997
- final T RMSE = 0.150 K
- final alphaL RMSE = 0.00066
- final flowType class disagreement = 0%

The very large normalized centerline vorticity and p_rgh-acceleration percentages are not treated as dominant evidence because their reference magnitudes on that symmetry/center line are very small; Uy, temperature, phase fraction, absolute vorticity RMSE and flowType remain nearly unchanged.

Final vertical phase-front positions:
- alphaL=0.05: C5 0.784 mm; C9 0.786 mm
- alphaL=0.50: C5 1.559 mm; C9 1.560 mm
- alphaL=0.95: C5 17.505 mm; C9 17.742 mm

Mushy width:
- C5 = 16.721 mm
- C9 = 16.956 mm
- change = +0.235 mm (+1.40%)

**Conclusion C:** correcting `metalTop` removes the residual top mass flux and improves numerical coupling/continuity while leaving the physical C solution essentially unchanged.

## Overall interpretation

1. `fixedFluxPressure + slip` is verified to make `metalTop` impermeable.
2. The previous `totalPressure` boundary had negligible physical impact on C because its top mass/advective flux was already tiny.
3. The previous boundary had a major impact on B because B carried a large top advective mass/energy transport.
4. Therefore historical B-vs-C circulation differences cannot be interpreted as a clean density-formulation comparison.
5. For the current fixed-volume Quick-Cup model, C9 is the cleaner baseline for subsequent physical validation.
6. B9 remains scientifically useful as a diagnostic of variable-density/fixed-volume behavior, but its interpretation requires the rho-table-extension caveat and the much larger transient rho-vs-thermodynamic-density mismatch.
