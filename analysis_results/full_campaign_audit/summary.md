# Full controlled-buoyancy campaign audit

**Read-only analysis of the completed 26-case campaign. No solver execution is performed.**

## Completion

- Complete to target time with runner confirmation and no fatal marker: **26/26**.
- Incomplete/invalid: **0**.
- All 26 cases satisfy the campaign completion criterion.

## Canonical profile availability

- Missing profile products: **0** across y=10, 20, 30 mm and x=20 mm.

## Case-level diagnostics

| case | status.tsv | probe last s | log file | log End | fatal | complete | T final K | mean alphaL final | max Co | cumulative continuity | max abs phi_top kg/s | Eadv top J |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | COMPLETED | 10 | True | False | False | True | 1467.45 | 0.873028 | 0.175912 | 0.00016626 | 0.000500113 | -970.51 |
| B4_energy2 | COMPLETED | 10 | True | False | False | True | 1467.53 | 0.873037 | 0.176643 | 0.000167018 | 0.000500044 | -970.479 |
| B5_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1472.53 | 0.96083 | 0.0600806 | 0.0001757 | 9.73899e-05 | -629.634 |
| B5_outer3 | COMPLETED | 10 | True | False | False | True | 1467.52 | 0.873032 | 0.175874 | 0.000165205 | 0.000500049 | -970.358 |
| B6_adaptiveDt | COMPLETED | 9.99966 | True | False | False | True | 1460.96 | 0.876067 | 0.287759 | 0.00024498 | 0.000270069 | -990.756 |
| B7_outer4 | COMPLETED | 10 | True | False | False | True | 1467.53 | 0.873033 | 0.175849 | 0.000163236 | 0.000500044 | -970.36 |
| B8_adaptiveOuter4 | COMPLETED | 9.9997 | True | False | False | True | 1460.96 | 0.876068 | 0.289774 | 0.000246202 | 0.00027005 | -990.807 |
| B9_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1470.07 | 0.96069 | 0.0673434 | -0.0310209 | 1.69407e-21 | -1.22346e-16 |
| B9_topFixedFlux | COMPLETED | 10 | True | False | False | True | 1459.33 | 0.872829 | 0.107138 | -0.0460268 | 2.5411e-21 | -5.01137e-16 |
| B10_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1472.53 | 0.96083 | 0.0600806 | 0.0001757 | 9.73899e-05 | -629.634 |
| B11_topFixedFlux_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1470.07 | 0.96069 | 0.0673434 | -0.0310209 | 1.69407e-21 | -1.22346e-16 |
| B12_topFixedValue_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1471.29 | 0.962691 | 0.144703 | 1.26875e-06 | 9.73917e-05 | -660.769 |
| B13_prghPressure_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1469.23 | 0.959166 | 0.0691234 | 9.88004e-07 | 9.77146e-05 | -559.527 |
| C3_reference | COMPLETED | 10 | True | False | False | True | 1461.6 | 0.87083 | 0.0700709 | 0.000178349 | 6.75279e-10 | 6.87636 |
| C4_energy2 | COMPLETED | 10 | True | False | False | True | 1461.6 | 0.87083 | 0.0700709 | 0.000178349 | 6.75271e-10 | 6.87649 |
| C5_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1464.27 | 0.962023 | 0.0658195 | 0.000178215 | 5.05451e-10 | 2.9756 |
| C5_outer3 | COMPLETED | 10 | True | False | False | True | 1461.6 | 0.87083 | 0.0700712 | 0.000178172 | 3.80985e-10 | 6.84138 |
| C6_adaptiveDt | COMPLETED | 10.0034 | True | False | False | True | 1460.9 | 0.880248 | 0.287049 | 0.000271897 | 2.01701e-09 | 20.8563 |
| C7_outer4 | COMPLETED | 10 | True | False | False | True | 1461.6 | 0.870829 | 0.070071 | 0.000178173 | 3.71518e-10 | 6.86901 |
| C8_adaptiveOuter4 | COMPLETED | 10.004 | True | False | False | True | 1460.9 | 0.880245 | 0.287098 | 0.000271146 | 1.06064e-09 | 20.685 |
| C9_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1464.19 | 0.962059 | 0.0650864 | 4.44553e-13 | 0 | 0 |
| C9_topFixedFlux | COMPLETED | 10 | True | False | False | True | 1461.46 | 0.871033 | 0.0694019 | 4.44867e-13 | 0 | 0 |
| C10_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1464.27 | 0.962023 | 0.0658195 | 0.000178215 | 5.05451e-10 | 2.9756 |
| C11_topFixedFlux_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1464.19 | 0.962059 | 0.0650864 | 4.44553e-13 | 0 | 0 |
| C12_topFixedValue_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1464.3 | 0.962024 | 0.0663407 | 1.47638e-06 | 4.9009e-10 | 6.29372 |
| C13_prghPressure_airGapOF14 | COMPLETED | 10 | True | False | False | True | 1464.3 | 0.962024 | 0.0663407 | 1.47639e-06 | 4.90089e-10 | 6.29372 |

## B/C controlled comparisons

| generation | T RMSE K | T final C-B K | alphaL mean RMSE | alphaL mean final C-B |
|---|---:|---:|---:|---:|
| v3_reference | 17.6348 | -5.85 | 0.00282741 | -0.0021985 |
| v4_energy2 | 17.6665 | -5.93 | 0.00283398 | -0.0022073 |
| v5_airGapOF14 | 12.4446 | -8.26 | 0.000993644 | 0.0011922 |
| v5_outer3 | 17.6696 | -5.92 | 0.00283037 | -0.0022027 |
| v6_adaptiveDt | 12.9472 | -31.92 | 0 | 0 |
| v7_outer4 | 17.6689 | -5.93 | 0.00283064 | -0.0022036 |
| v8_adaptiveOuter4 | 5.64299 | -16.96 | 0 | 0 |
| v9_airGapOF14 | 5.36499 | -5.88 | 0.00104376 | 0.0013691 |
| v9_topFixedFlux | 10.6843 | 2.13 | 0.00123503 | -0.0017957 |
| v10_airGapOF14 | 12.4446 | -8.26 | 0.000993644 | 0.0011922 |
| v11_topFixedFlux_airGapOF14 | 5.36499 | -5.88 | 0.00104376 | 0.0013691 |
| v12_topFixedValue_airGapOF14 | 8.77405 | -6.99 | 0.000472773 | -0.0006674 |
| v13_prghPressure_airGapOF14 | 5.1269 | -4.93 | 0.00161851 | 0.0028579 |

## Interpretation guardrails

- For runner-managed campaigns, completion means the stored temperature probe reaches at least 9.999 s, status.tsv reports COMPLETED, and no fatal marker is detected in log.foamMultiRun when that log exists.
- A missing log.foamMultiRun is reported separately and is not treated as a fatal solver error. If status.tsv is unavailable, log End is used only as a fallback completion signal.
- sum(phi) is a net top-patch mass flux; a near-zero net value does not by itself prove face-wise impermeability.
- The y=10 mm profile is audited explicitly together with y=20 mm, y=30 mm and x=20 mm.
- Numerical agreement is verification evidence, not experimental validation.
- This script does not run blockMesh, foamMultiRun or foamPostProcess.
