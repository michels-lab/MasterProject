# V12/V13 metalTop pressure-boundary comparison

Both families start from V11, so the corrected OpenFOAM Foundation v14 air gap and all V11 diagnostics are retained.

## Canonical cases

| Case | metalTop `p_rgh` BC | Controlled meaning |
|---|---|---|
| B12_topFixedValue_airGapOF14 | `fixedValue 2667.739248 Pa` | Doctor proposal: freeze the initially atmosphere-consistent reduced pressure |
| C12_topFixedValue_airGapOF14 | `fixedValue 2676.168 Pa` | Same proposal with `rhoConst` |
| B13_prghPressure_airGapOF14 | `prghPressure`, `p=0` relative to the solver's `pRef` offset | Keep reconstructed static pressure at 1e5 Pa while `rho(T)` evolves |
| C13_prghPressure_airGapOF14 | `prghPressure`, `p=0` relative to the solver's `pRef` offset | Same static-pressure condition with `rhoConst` |

Canonical runner:

`run_v12_v13_tests.sh`

Only the canonical V12/V13 case directories are retained in the repository. Duplicate provisional case directories were removed to preserve a one-version/one-case-configuration structure.

## Controlled-change verification

A recursive SHA comparison against V11 confirms that, apart from the documentation files `CASE_NOTES.md` and `CASE_VARIANT.md`, the **only simulation input that changes is `0/metal/p_rgh`**.

The following remain identical to V11:
- mesh and geometry;
- `U=slip` on `metalTop`;
- thermal top BC;
- corrected OF14 air-gap resistance;
- timestep and write controls;
- root and regional PIMPLE settings;
- phase-change parameters;
- B/C buoyancy formulations;
- B-family `rho(T)` table;
- diagnostics including `metalTopPhiSum` and `energyAdvectiveFlux`.

## Why the V12 values are 2667.739248 Pa and 2676.168 Pa

OpenFOAM 14 defines the reduced buoyant pressure as:

`p_rgh = p - rho*gh - pRef`

with `gh=(g·x)-ghRef`.

For these cases:
- `g=(0,-9.81,0) m/s2`;
- no `hRef` file is present, so OF14 uses `hRef=0`;
- `metalTop` is at `y=0.040 m`;
- `constant/metal/pRef=1e5 Pa`;
- target atmospheric static pressure is `p=1e5 Pa`.

Therefore `gh=-0.3924 m2/s2` and the atmospheric reduced pressure at the top is simply:

`p_rgh = rho*9.81*0.040`.

B family:
- `rho(1500 K)=6798.52 kg/m3`, obtained by linear interpolation of the `icoTabulated` table;
- `p_rgh=2667.739248 Pa`.

C family:
- `rho=6820 kg/m3`;
- `p_rgh=2676.168 Pa`.

These are derived values, not fitted parameters.

## Why V13 uses `p uniform 0`

The OF14 `prghPressure` implementation converts a specified static-pressure offset to reduced pressure using the local density and hydrostatic head. The solver later reconstructs:

`p = p_rgh + rho*gh + pRef`.

With `constant/metal/pRef=1e5 Pa`, `p uniform 0` in `prghPressure` reconstructs `p=1e5 Pa` at the boundary. Supplying `p=1e5` inside this BC would double-count the reference offset in this setup.

The `value` entry in V13 is only the hydrostatically consistent initial patch value:
- B: `2667.739248 Pa`;
- C: `2676.168 Pa`.

## Important: the two pressure references are not the same thing

`constant/metal/pRef` belongs to the buoyant-pressure transformation itself.

`system/metal/fvSolution/PIMPLE/pRefPoint` and `pRefValue` are the pressure-reference-cell mechanism used when the solved pressure field needs an internal reference.

OF14's `needReference()` logic disables the internal reference requirement when a boundary condition fixes the pressure value. Consequently V12/V13 do not rely on the PIMPLE reference point to set the pressure level in the same way V11 does.

## Physical interpretation

### V11 — `fixedFluxPressure + slip`

OF14 documents `fixedFluxPressure` as adjusting the pressure gradient so that the boundary flux is consistent with the velocity BC in the presence of body forces. For the present model of a rigid, fixed, impermeable top with `U=slip`, V11 is the physically coherent wall baseline.

### V12 — fixed `p_rgh`

V12 tests the doctor's proposal directly. It freezes the initially atmosphere-consistent reduced pressure.

In family C, density is constant, so this remains compatible with the same atmospheric static pressure.

In family B, density varies with temperature. As `rho(T)` changes, frozen `p_rgh` implies that the reconstructed static pressure can change:

`p = pRef + p_rgh + rho*gh`.

Thus B12 is specifically a **fixed-reduced-pressure** experiment; it is not equivalent to maintaining atmospheric static pressure throughout the transient.

### V13 — fixed static atmospheric pressure

V13 uses `prghPressure` so that the static pressure remains at the atmospheric reference while `p_rgh` updates with density and hydrostatic head.

With `rhoConst` and a level top, C12 and C13 should impose the same top `p_rgh` to numerical precision. This makes C12/C13 a useful control.

In B, the meaningful controlled distinction is:
- B12: frozen `p_rgh`;
- B13: atmospheric static pressure, dynamically updated `p_rgh(rho)`.

## Boundary-compatibility caveat

Neither V12 nor V13 should be declared impermeable merely because `U=slip`. Both pressure BCs fix a pressure value, whereas OF14's standard wall treatment with body forces uses `fixedFluxPressure`. Conversely, an actually open atmospheric boundary normally uses a pressure condition together with a velocity BC that permits inflow/outflow, not `slip`.

Therefore V12/V13 are deliberate controlled diagnostics. Their physical acceptability must be checked from the run, not assumed from the dictionary.

## Required diagnostics

For all four cases:
- `sum(phi)` on `metalTop`;
- integrated top `energyAdvectiveFlux`;
- `p_rgh` and `p_rghFinalRes` evolution versus physical time and timestep;
- outer pressure-coupling contraction;
- continuity and Courant number;
- temperature, liquid fraction, velocity, vorticity and flow topology;
- computational cost.

Acceptance for an impermeable interpretation requires `sum(phi)` and top advective energy transport to remain compatible with zero.

## Official OpenFOAM 14 source basis

- Buoyant pressure definition: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/finiteVolume/cfdTools/general/buoyancy/buoyancy.H
- `prghPressure` implementation: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/finiteVolume/fields/fvPatchFields/derived/PrghPressure/PrghPressureFvPatchScalarField.C
- Static pressure base BC: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/finiteVolume/fields/fvPatchFields/derived/pressure/pressureFvPatchScalarField.C
- `fixedFluxPressure` definition: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/finiteVolume/fields/fvPatchFields/derived/fixedFluxPressure/fixedFluxPressureFvPatchScalarField.H
- Pressure-reference logic: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/finiteVolume/cfdTools/general/findRefCell/findRefCell.C
- `needReference()` logic: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/finiteVolume/fields/GeometricFields/GeometricField/GeometricField.C
- Pressure reconstruction and flux correction: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/isothermalFluid/correctBuoyantPressure.C

Also see the OF14 User Guide discussion of `fixedFluxPressure` on walls:
https://doc.cfd.direct/openfoam/user-guide-v14/dambreak
