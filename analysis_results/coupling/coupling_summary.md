# Coupling analysis

Generated from `logs/` with `analysis_tools/coupling_analysis.py`.

## Definitions

`R_p_outer` = initial residual of the first `p_rgh` solve in the last root-level outer corrector divided by the corresponding initial residual in the first outer corrector.

- lower `R_p_outer`: stronger typical contraction across the outer coupling loop
- `R_p_outer > 1`: the pressure initial residual increased across that outer loop
- this is **not** the same as a linear-solver failure

`R_h_total` and `R_e_total` compare the last and first initial residuals of the energy solves within a timestep. They include the combined effect of outer iterations and any energy correctors.

Linear final residuals remain a separate convergence measure.

## Summary

| Case | outer | energy | median Rp | p95 Rp | Rp>1 | median Rh | median Re | final |continuity| | max Co |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | 2 | 1 | 0.6104 | 0.9489 | 2.73% | 2.158e-3 | 9.995e-6 | 1.663e-4 | 0.1759 |
| B4_energy2 | 2 | 2 | 0.6084 | 0.9397 | 2.60% | 1.918e-6 | 1.197e-5 | 1.670e-4 | 0.1766 |
| B5_outer3 | 3 | 1 | 0.5976 | 0.9452 | 3.44% | 1.175e-4 | 1.198e-5 | 1.652e-4 | 0.1759 |
| B6_adaptiveDt | 3 | 1 | 0.3721 | 0.7639 | 1.69% | 4.316e-4 | 1.445e-4 | 2.450e-4 | 0.2878 |
| B7_outer4 | 4 | 1 | 0.5989 | 0.9530 | 3.16% | 6.647e-6 | 1.197e-5 | 1.632e-4 | 0.1758 |
| C3_reference | 2 | 1 | 0.8054 | 1.019 | 6.68% | 1.049e-3 | 9.916e-6 | 1.783e-4 | 0.07007 |
| C4_energy2 | 2 | 2 | 0.8054 | 1.026 | 7.22% | 3.099e-7 | 1.184e-5 | 1.783e-4 | 0.07007 |
| C5_outer3 | 3 | 1 | 0.7951 | 1.025 | 7.14% | 3.284e-6 | 1.185e-5 | 1.782e-4 | 0.07007 |
| C6_adaptiveDt | 3 | 1 | 0.7900 | 1.017 | 6.25% | 3.086e-4 | 2.282e-4 | 2.719e-4 | 0.2870 |
| C7_outer4 | 4 | 1 | 0.8019 | 1.069 | 9.76% | 2.336e-6 | 1.184e-5 | 1.782e-4 | 0.07007 |

## Interpretation

### Fixed B family

B5 provides only a modest improvement in typical pressure outer-loop contraction relative to B3:
- median Rp: 0.6104 -> 0.5976

However:
- p95 is not materially better than B3/B4
- the fraction of Rp>1 is slightly worse than B3/B4
- fixed-step physical fields and integrated energy diagnostics remain very close

B7 adds another outer corrector but does not improve pressure coupling relative to B5:
- median Rp 0.5989
- p95 0.9530
- Rp>1 3.16%

Therefore the fourth outer corrector is a clear diminishing-return case.

### Fixed C family

C5 only modestly improves the median pressure contraction:
- C3 0.8054
- C5 0.7951

The p95 and Rp>1 statistics do not improve meaningfully. C7 is worse on these pressure-coupling metrics.

Since C3/C4/C5/C7 are essentially identical in Uy, vorticity and energy transport, the extra outer correctors are not justified by a meaningful change in the physical solution.

### Energy corrector

B4/C4 leave pressure coupling essentially unchanged, but the second energy corrector reduces the h coupling residual by several orders of magnitude:
- B3 median Rh ~2.16e-3 -> B4 ~1.92e-6
- C3 median Rh ~1.05e-3 -> C4 ~3.10e-7

However:
- Re does not improve
- the physical velocity/vorticity fields and integrated energy transport remain essentially unchanged

Thus the second energy corrector strongly over-converges one numerical energy residual without providing an observed physical benefit in these tests.

### Adaptive cases

B6 shows a much lower pressure-coupling ratio (median Rp 0.3721), but it also:
- increases max Courant to ~0.288
- worsens cumulative continuity error
- strongly changes Uy and vorticity topology

Therefore B6 cannot be called 'better coupled overall' simply because Rp is smaller.

C6 changes Rp only slightly relative to C5 and also worsens continuity while increasing Courant. Uy remains fairly close, but vorticity topology changes.

## Decision rule

A coupling configuration should be considered numerically preferable only if it simultaneously:

1. contracts the outer-loop residuals consistently;
2. keeps linear final residuals acceptably small;
3. maintains or improves continuity;
4. respects timestep/Courant constraints;
5. preserves the physical solution under a controlled comparison;
6. achieves the above without unnecessary computational cost.

Additional correctors that reduce one residual but do not improve the physical solution, continuity, or robustness are diminishing returns.
