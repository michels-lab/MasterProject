# V8/V9 controlled diagnostic matrix

These cases are deliberately orthogonal tests. Historical B3-B7/C3-C7 cases are unchanged.

| Case | Parent | Single controlled change | Question |
|---|---|---|---|
| B8_adaptiveOuter4 | B6_adaptiveDt | nOuterCorrectors 3 -> 4 | Does extra PIMPLE coupling recover B6 flow? |
| C8_adaptiveOuter4 | C6_adaptiveDt | nOuterCorrectors 3 -> 4 | Does extra PIMPLE coupling materially change C6? |
| B9_topFixedFlux | B5_outer3 | metalTop p_rgh totalPressure -> fixedFluxPressure | Does enforcing flux consistency remove B top advective leakage / alter circulation? |
| C9_topFixedFlux | C5_outer3 | metalTop p_rgh totalPressure -> fixedFluxPressure | Control counterpart for C |

## Interpretation

V8 isolates outer-coupling count while retaining the adaptive timestep.
V9 isolates the top pressure boundary while retaining fixed timestep and V5 coupling.

Do not compare V8 vs V9 as if they differed by one variable; they answer different questions.
