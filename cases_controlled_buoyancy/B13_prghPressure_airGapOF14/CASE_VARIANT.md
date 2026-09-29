# B13_prghPressure_airGapOF14

Parent: `B11_topFixedFlux_airGapOF14`.

Static-atmospheric-pressure test using OpenFOAM v14 prghPressure. With pRef=1e5 Pa, the boundary specifies p=0 Pa gauge relative to pRef; OpenFOAM then updates p_rgh from rho and hydrostatic head. The initial value 2667.739248 Pa is supplied only as the consistent starting value.

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

B13 completed 10 s but allowed significant top exchange:
- max |sum(phi)| = 9.771e-5 kg/s;
- integrated mass = -5.799e-4 kg;
- integrated top advective energy = -559.53 J.

The central probe exhibits a +4.00 K rebound and local alphaL recovery to 1.0, i.e. model remelting coincident with advective energy entering through the top. This is not evidence of metallurgical recalescence.

Conclusion: B13 is retained as the atmospheric-static-pressure diagnostic, not as the impermeable baseline. V11 remains the baseline.
