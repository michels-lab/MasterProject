# V10-V13 closure analysis

**Date:** 2026-09-29  
**Status:** RUN-VERIFIED / ANALYSIS-VERIFIED for V10-V13 pressure/top-boundary campaign

## Controlled question

V10 and V11 use the corrected OpenFOAM Foundation v14 air-gap formulation. V11 differs from V10 by using `fixedFluxPressure` at `metalTop` with `U=slip`. V12/V13 descend from V11 and replace only the top `p_rgh` boundary condition with `fixedValue` or `prghPressure`.

This closes the question: how strongly does the top pressure boundary change mass/enthalpy transport and the resolved solidification/convection solution?

## 1. V11 direct verification: the top is impermeable

B11:
- max abs(sum(phi_top)) = **1.694066e-21 kg/s**;
- integrated phi_top = **-1.27055e-22 kg**;
- integrated top advective energy = **-1.22e-16 J**.

C11:
- sum(phi_top) = **0** in the stored diagnostic;
- integrated top advective energy = **0 J**.

Therefore the actual V11 runs, not only their V9 ancestors, verify that `slip + fixedFluxPressure` closes `metalTop` to numerical precision.

## 2. B10 -> B11: closing the top materially changes family B

B10 retains a large top advective contribution:
- Eadv,top = **-629.63 J**;
- heat-only extraction through all selected metal boundaries = **4058.09 J**;
- total selected boundary energy after the advective term = **3428.45 J**.

B11 removes that advective path:
- Eadv,top ≈ **0 J**;
- heat-only selected boundary extraction = **4069.49 J**;
- metal-to-mold heat remains almost unchanged: **3686.64 J (B10)** vs **3687.23 J (B11)**.

Thus the main energy difference is not a changed air-gap or heat-transfer coefficient; it is removal of advective transport through the top.

Center temperature comparison B10 -> B11:
- RMSE = **8.53 K**;
- maximum absolute difference = **16.16 K**;
- final T = 1472.53 -> **1470.07 K**.

Center liquid fraction:
- final alphaL = 0.998163 -> **0.988421**.

The domain-average liquid fraction changes little at 10 s (0.9608303 -> 0.9606902), showing that a small global phase-average difference can coexist with a strong local flow/thermal reorganization.

Final spatial differences are large:
- y=20 mm Uy NRMSE = **44.7%**;
- y=30 mm Uy NRMSE = **217.5%**, Pearson r = -0.086;
- x=20 mm Uy NRMSE = **257.9%**, Pearson r = -0.136;
- flowType class disagreement = **62.5%, 27.5%, 10%** on those three profiles.

Conclusion: historical B solutions with a pressure/open-style top cannot be treated as clean variable-density buoyancy references. The top boundary materially participates in the B flow.

## 3. C10 -> C11: closing the top barely changes family C

C10 already has only a small advective contribution:
- Eadv,top = **+2.976 J**.

C11 removes it:
- Eadv,top = **0 J**.

Thermal/phase differences are tiny:
- center T RMSE = **0.164 K**;
- maximum absolute center-T difference = **0.43 K**;
- final T difference = **-0.08 K**;
- final mean alphaL differs by only **3.68e-5**.

Final spatial Uy differences:
- y=20 mm = **0.52% NRMSE**;
- y=30 mm = **1.70%**;
- x=20 mm = **0.44%**;
- Pearson r > **0.99987** on all three profiles.

Conclusion: C is robust to closing the top because the old top transport was already small. C11 is a clean fixed-volume baseline.

## 4. Pressure coupling and continuity

Closing the top greatly improves outer pressure-coupling contraction:

- B10 median Rp_outer = **0.521** -> B11 **0.00198**;
- B10 Rp_outer>1 = **3.65%** -> B11 **0%**.
- C10 median Rp_outer = **0.758** -> C11 **0.000595**;
- C10 Rp_outer>1 = **13.06%** -> C11 **0%**.

C11 cumulative continuity is essentially zero (**4.45e-13**).

B11 cumulative continuity is **-0.0310** even though direct top mass flux is zero. This is not literal mass loss through the top. It exposes the known inconsistency of imposing rho(T) thermal contraction inside a fixed-volume, impermeable geometry without shrinkage/free-surface/feeding physics.

Therefore better cumulative continuity in B12/B13 is not evidence that they are more physical: those variants reduce the density/volume inconsistency by allowing mass through the top.

## 5. V11 vs V12/V13

### Family B

B12 (`fixedValue p_rgh`) is strongly different from B11:
- top mass exchange reaches **9.739e-5 kg/s**;
- integrated mass exchange magnitude corresponds to ~**0.519%** of initial metal mass;
- Eadv,top = **-660.77 J**;
- center T RMSE vs B11 = **5.39 K**;
- final y=30 mm Uy NRMSE = **182%**;
- y=30 mm flowType class disagreement = **98.75%**.

B13 (`prghPressure`) is numerically closer to B11 in several observables:
- center T RMSE = **0.234 K**;
- final Uy NRMSE = **11.5%, 12.4%, 8.27%** on y20, y30 and x20;
- nevertheless max top mass flux is **9.771e-5 kg/s** and Eadv,top = **-559.53 J**.

This is an important methodological result: **closeness of T(t) does not prove physical equivalence.** B13 can resemble B11 thermally while satisfying variable-density continuity by importing mass/enthalpy through a boundary that is supposed to be an impermeable fixed top.

### Family C

C12 and C13 remain essentially identical to each other and close to C11:
- center T RMSE vs C11 = **0.280 K**;
- final Uy NRMSE = **1.35%, 4.76%, 1.71%**;
- final flowType disagreement = **5%, 2.5%, 0%**.

However V12/V13 retain ~**+6.29 J** integrated top advective energy. Their net sum(phi) is almost zero, so local in/out face fluxes can cancel in mass while not cancelling in enthalpy. They are therefore not the strict impermeable baseline.

## 6. Baseline decision

For the current Quick-Cup model with fixed geometry:

1. **V11 is now directly RUN-VERIFIED and ANALYSIS-VERIFIED.**
2. `fixedFluxPressure + slip` is verified directly in B11/C11 as the impermeable top treatment.
3. **C11 is the preferred physical validation baseline** for fixed-volume Quick-Cup because rhoConst does not demand shrinkage/volume change.
4. B11 remains scientifically useful for diagnosing variable-density behavior, but its cumulative continuity mismatch is a model-physics limitation, not a reason to reopen the top.
5. V12/V13 remain diagnostic pressure-boundary experiments and do not replace V11.
6. No additional V14-style pressure/PIMPLE variant is justified by this campaign.
7. The next scientific step is G1: align the C11 equilibrium model to the experimental Quick-Cup conditions and compare against an actual numerical/digitized thermocouple curve.

## Evidence caveats

- B10/C10 do not contain `metalTopPhiSum` because that function object was added after those runs were already in progress. Their historical top-opening evidence is therefore the stored advective energy flux; no retrospective phi value is invented.
- A near-zero patch-integrated sum(phi) is not by itself proof of face-wise impermeability. Energy advection is retained as an independent check.
- Temperature similarity is verification evidence only; experimental validation requires the measured thermocouple series.
