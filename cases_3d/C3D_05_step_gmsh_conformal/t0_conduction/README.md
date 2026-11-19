# T0 — conduction-only two-solid QuickCup (CASE B C3D-05)

**Status:** template + strict generator; **NO CFD executed, NOT yet a runnable physical case**. The exact accepted source is `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`. This tree **does not contain or modify** original meshes.

## Equation and hypothesis
In each region, a constant-property stationary solid:
`rho * Cv * dT/dt = div(kappa * grad(T))` [W/m³].
Metal and mold are modeled as **two solids** solely to check the numerical
conduction coupling, with reciprocal **`coupledTemperature`** on preserved
`mappedWall` patches and **adiabatic external** boundaries
(`metalTop`, `moldOuterUnclassified`). No free-surface/air exchange,
liquid flow, phase change, latent heat, shrinkage or experimental calibration.
The closed-system energy reference is `hf = 0` by convention.

Energy budget once solving is separately authorized:
`E(t) = sum_region( integral_V rho Cv T dV )` (absolute offset cancels).
For perfectly adiabatic exterior and ideal contact, `E(t)-E(0)` should
be small relative to energy exchanged; define a numerical tolerance from
grid/time convergence, not an invented universal limit.
Verify coupled face flux continuity with native OpenFOAM output.

## Structure
- `T0_INPUTS.json` intentionally contains **null** physical inputs and sources.
- `templates/constant/{metal,mold}/physicalProperties.tpl` uses Foundation
  v14 `heSolidThermo/eConst/rhoConst/constIsoSolid`, **Cv not Cp**.
- `templates/0/{metal,mold}/T.tpl` uses the actual patch names.
- `templates/system/controlDict.tpl` uses `foamMultiRun` and `regionSolvers`.
- `scripts/prepare_t0.py` validates the input and materializes in a
  **new** WSL directory only after all values/sources are supplied.
- `scripts/run_t0_preflight.sh`: **ONE COMMAND** preflight (never launches CFD).

The output directory is `~/OpenFOAM/C3D05_T0_CONDUCTION_01` and is protected
against overwrite. The accepted `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`
remains immutable. The output uses copied `polyMesh` (not a symlink) so
future thermal solver experiments cannot modify the accepted reference.

**Material data are not yet established**. Filling inputs from the thesis
database or a documented literature source is required. `molWeight`
is a model-required species bookkeeping parameter, not a claim that the
mold is a single chemical species; record its chosen model convention.

Do NOT copy values from the official aluminium `heatedDuct` example
as if they were measured QuickCup iron/sand parameters. The numerical
scheme `corrected` and 2 nonorthogonal correctors are *proposals*, not
proof of stability on this 76.8 degree maximum non-orthogonal mesh.

## Basis verified from the official Foundation 14 tutorial
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/0/metal/T
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/constant/metal/physicalProperties
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/system/metal/fvSchemes
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/system/metal/fvSolution
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/system/controlDict

**Scope and gate order:** geometry/STEP/patches PASS already; T0 source/syntax
preflight next; physical-parameter provenance next; materialize separate case;
OpenFOAM dictionary/thermo compilation and *then* any deliberately authorized
solver run. **No automatic CFD**, no claims of thermophysical validity.
