# V12/V13 metalTop pressure-boundary comparison

Both families start from V11, so the corrected OpenFOAM 14 air gap and all V11 diagnostics are retained.

| Case | metalTop p_rgh BC | Meaning |
|---|---|---|
| B12_topFixedValue_airGapOF14 | fixedValue 2667.739248 Pa | Doctor proposal: freeze initially atmosphere-consistent reduced pressure |
| C12_topFixedValue_airGapOF14 | fixedValue 2676.168 Pa | Same proposal with rhoConst |
| B13_prghPressure_airGapOF14 | prghPressure, p=0 gauge relative to pRef | Maintain static atmospheric pressure while rho(T) evolves |
| C13_prghPressure_airGapOF14 | prghPressure, p=0 gauge relative to pRef | Same static-atmosphere condition with rhoConst |

All cases retain U=slip on metalTop.

Because C has constant density and a geometrically level top, V12 and V13 should impose nearly the same reduced pressure after initialization. In B, rho(T) varies, so V12 holds p_rgh fixed while V13 updates p_rgh with rho; this is the key controlled distinction.

Required diagnostics:
- sum(phi) on metalTop;
- integrated top energyAdvectiveFlux;
- p_rgh / p_rghFinalRes evolution;
- continuity and Courant;
- temperature, liquid fraction and velocity fields.
