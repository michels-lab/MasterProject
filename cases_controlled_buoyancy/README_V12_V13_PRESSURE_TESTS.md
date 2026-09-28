# V12/V13 pressure-boundary comparison

Both V12 and V13 descend from V11. The corrected OpenFOAM 14 air gap and all other numerical/physical settings remain unchanged.

| Family | V11 | V12 | V13 |
|---|---|---|---|
| B | fixedFluxPressure | fixedValue p_rgh=0 | prghPressure with p=0 gauge |
| C | fixedFluxPressure | fixedValue p_rgh=0 | prghPressure with p=0 gauge |

Interpretation:
- V11: pressure gradient adjusts to make boundary flux consistent with U=slip.
- V12: the solved reduced pressure p_rgh is fixed directly to a uniform value.
- V13: static pressure is prescribed through prghPressure; OpenFOAM converts it to p_rgh using rho, g and h.

The cases already contain pRef=1e5 Pa. Hence V13 uses p=0 Pa gauge relative to pRef, which corresponds to a reconstructed static pressure of 1e5 Pa at metalTop.

Required comparisons:
- sum(phi) on metalTop;
- integrated top energyAdvectiveFlux;
- p_rgh and p_rghFinal residual evolution;
- continuity and Courant number;
- temperature, alphaL, velocity and flow topology;
- computational cost.
