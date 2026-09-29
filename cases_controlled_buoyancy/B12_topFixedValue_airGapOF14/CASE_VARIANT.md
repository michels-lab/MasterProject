# B12_topFixedValue_airGapOF14

Parent: `B11_topFixedFlux_airGapOF14`.

Doctor-proposed pressure test. metalTop/p_rgh is fixed directly to 2667.739248 Pa, the initially hydrostatically consistent reduced pressure for p=1e5 Pa with the current pRef=1e5 Pa, hRef=0 and the family's initial density.

## Controlled-change rule

Only `0/metal/p_rgh -> metalTop` differs from V11. The following remain unchanged:
- U=slip on metalTop;
- corrected OpenFOAM 14 air-gap resistance;
- mesh;
- timestep;
- PIMPLE settings;
- phase-change parameters;
- B/C buoyancy formulation;
- B-family rho(T) table;
- thermal boundary condition;
- diagnostics including metalTopPhiSum and energyAdvectiveFlux.

## Pressure-reference context

The case contains `constant/metal/pRef = 1e5 Pa` and no hRef file, so OpenFOAM v14 uses `hRef=0`.

The solver definition is:

`p_rgh = p - rho*gh - pRef`.

At the 40 mm top surface, `gh = -9.81*0.04 = -0.3924 m2/s2`.

Initial density:
- B: rho(1500 K)=6798.52 kg/m3 from the icoTabulated table -> p_rgh(atm,initial)=2667.739248 Pa.
- C: rho=6820 kg/m3 -> p_rgh(atm)=2676.168 Pa.

For the prghPressure variant, `p uniform 0` is intentional because `pRef=1e5 Pa`; using `p=1e5` there would double-count the atmospheric reference in this solver setup.

## Run result and interpretation

Status: **RUN-VERIFIED + ANALYSIS-VERIFIED; diagnostic only**.

B12 completed 10 s, but the fixed reduced-pressure boundary allowed significant exchange through `metalTop`:
- max |sum(phi)| = 9.739e-5 kg/s;
- integrated mass = -5.642e-4 kg;
- integrated top advective energy = -660.77 J.

The central probe shows a +4.34 K thermal rebound while remaining above Tliq, with no local remelting.

Conclusion: this case is retained as the controlled `fixedValue p_rgh` experiment, not as the impermeable baseline. V11 remains the baseline for the current fixed-top model.
