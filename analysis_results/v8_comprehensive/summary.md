# V8 adaptive + 4 outer correctors — comprehensive result

All spatial comparisons were aligned by **physical time**. V8 native stored times were used as the comparison grid and V6/V5 profiles were linearly interpolated in time.

## Decision

**Adding a fourth outer corrector does not recover the fixed-step solution.**

B8 is essentially indistinguishable from B6 in temperature, liquid fraction, Uy, horizontal vorticity, flowType, Darcy acceleration and p_rgh acceleration, while remaining strongly different from B5.

C8 is likewise essentially identical to C6. The fourth outer corrector gives a modest improvement in pressure-coupling statistics for C but produces no meaningful physical-field change and roughly doubles the adaptive-case runtime.

Therefore the V6 differences are not caused by using only three outer PIMPLE correctors.

## B family

### Coupling / cost

| case | median Rp | p95 Rp | Rp>1 | final |continuity| | max Co | clock |
|---|---:|---:|---:|---:|---:|---:|
| B5 fixed outer3 | 0.5976 | 0.9452 | 3.44% | 1.652e-4 | 0.1759 | 345 s |
| B6 adaptive outer3 | 0.3721 | 0.7633 | 1.69% | 2.450e-4 | 0.2878 | 119 s |
| B8 adaptive outer4 | 0.3882 | 0.7510 | 1.44% | 2.462e-4 | 0.2898 | 220 s |

B8 does not improve the median pressure-contraction ratio relative to B6; it is slightly higher (0.388 vs 0.372). Its p95 and fraction of Rp>1 improve only slightly. Continuity is essentially unchanged/slightly worse, while clock time increases from 119 to 220 s.

### B8 vs B6

Across the three spatial profiles, B8 and B6 are practically identical:

- y=20 mm: median Uy NRMSE 0.04%; last 0.09%; corr ~1
- y=30 mm: median Uy NRMSE 0.13%; last 0.39%; corr ~1
- vertical x=20 mm: median Uy NRMSE 0.17%; last 0.66%; corr ~1
- last temperature RMSE: ~0.004–0.005 K
- last alphaL RMSE: ~1e-5 or smaller
- horizontal vorticity differences: <0.2%
- flowType class disagreement: 0%
- Darcy-acceleration differences: <0.1%
- p_rgh-acceleration differences: <=0.1%
- vertical phase-front crossings are identical to the reported precision

The apparently very large normalized vertical-vorticity percentage is not physically important: centerline vorticity is near zero in both adaptive B cases, so normalization by a near-zero reference inflates the percentage. Correlation remains high and flowType classification is unchanged.

### B8 vs B5

The strong adaptive-vs-fixed differences remain:

- y=20 mm:
  - median Uy NRMSE 33.1%
  - final Uy NRMSE 50.2%
  - final vorticity NRMSE 43.0%
  - flowType class disagreement 40%
  - Darcy acceleration NRMSE 42.4%
  - p_rgh acceleration NRMSE 28.1%

- y=30 mm:
  - median Uy NRMSE 59.0%
  - final Uy NRMSE 80.5%
  - final vorticity NRMSE 52.0%
  - flowType class disagreement 85%
  - Darcy acceleration NRMSE 53.2%

- vertical x=20 mm:
  - median Uy NRMSE 75.3%
  - final Uy NRMSE 99.2%
  - final Uy correlation 0.125
  - Darcy acceleration NRMSE 70.7%
  - p_rgh acceleration NRMSE 49.7%

At the last V8 time:
- B5 alphaL=0.05: 1.007 mm; B8: 0.940 mm
- B5 alphaL=0.50: 1.922 mm; B8: 1.828 mm
- B5 alphaL=0.95: 17.923 mm; B8: 19.433 mm

Mushy-zone width (0.05 -> 0.95):
- B5: 16.916 mm
- B8: 18.493 mm
- B8 is wider by ~1.577 mm (~9.3%)

This is essentially the same adaptive-step deformation already observed in B6.

## C family

### Coupling / cost

| case | median Rp | p95 Rp | Rp>1 | final |continuity| | max Co | clock |
|---|---:|---:|---:|---:|---:|---:|
| C5 fixed outer3 | 0.7951 | 1.0247 | 7.14% | 1.782e-4 | 0.0701 | 319 s |
| C6 adaptive outer3 | 0.7900 | 1.0165 | 6.25% | 2.719e-4 | 0.2870 | 65 s |
| C8 adaptive outer4 | 0.7765 | 1.0015 | 5.10% | 2.711e-4 | 0.2871 | 121 s |

C8 modestly improves pressure-coupling statistics relative to C6, but continuity remains essentially unchanged and runtime rises from 65 to 121 s.

### C8 vs C6

C8 and C6 are essentially the same physical solution:

- Uy median differences: ~0.01–0.03%
- temperature RMSE: ~0.003–0.004 K
- alphaL differences: effectively zero
- horizontal vorticity differences: <=0.08%
- flowType class disagreement: 0%
- Darcy acceleration differences: <=0.06%
- p_rgh acceleration differences: <=0.20%
- phase-front crossings are essentially identical

Again, normalized centerline-vorticity percentages are unstable because the centerline vorticity is extremely small.

### C8 vs C5

The adaptive-step differences remain almost exactly those previously observed for C6:

- Uy remains close to fixed:
  - y20 median NRMSE 3.0%; final 3.3%
  - y30 median 4.8%; final 1.7%
  - vertical median/final 3.4%
- temperature RMSE <1 K at the last time
- alphaL NRMSE <=1.4%
- Darcy acceleration differs by ~10–16%
- vertical p_rgh acceleration differs substantially (~56%) even though Uy remains close

Vertical phase crossings:
- C5 alphaL=0.05: 0.619 mm; C8: 0.465 mm
- C5 alphaL=0.50: 1.489 mm; C8: 1.370 mm
- C5 alphaL=0.95: 18.298 mm; C8: 20.087 mm

Mushy-zone width:
- C5: 17.679 mm
- C8: 19.622 mm
- increase ~1.943 mm (~11.0%)

## Final conclusion

The fourth outer corrector is a **diminishing-return test**:

1. It does not recover the fixed-step phase or flow solution.
2. B8 is nearly identical to B6 despite ~85% more clock time.
3. C8 slightly improves pressure-coupling metrics but remains physically identical to C6 and costs ~86% more.
4. The V6/V8 deviations from fixed-step cases therefore originate from the adaptive timestep trajectory/time discretization, not from insufficient root-level PIMPLE outer coupling.

For subsequent physical interpretation:
- keep V5 fixed as the controlled reference;
- V6 may be retained only as a speed/accuracy trade-off study;
- V8 does not warrant further use as a production configuration.
