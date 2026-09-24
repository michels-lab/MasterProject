# Controlled Buoyancy Comparison Cases

This directory contains the **clean, controlled B/C comparison series** for the QuickCup solidification study.

Historical development cases remain under `cases_buoyancy/` and must not be overwritten.

## Purpose

The historical B/C series was found to contain additional differences unrelated to the intended buoyancy comparison, notably:

- historical B2–B5: `metalTop h = 10 W/(m²·K)`
- historical C2–C5: `metalTop h = 50 W/(m²·K)`
- different `startFrom` settings

This controlled series removes those confounding differences.

## Controlled case matrix

| Pair | Purpose | Root numerical setting |
|---|---|---|
| `B3_reference` / `C3_reference` | Reference configuration | `nOuterCorrectors 2` |
| `B4_energy2` / `C4_energy2` | Energy-corrector sensitivity | `nOuterCorrectors 2`, `nEnergyCorrectors 2` |
| `B5_outer3` / `C5_outer3` | Outer-corrector sensitivity | `nOuterCorrectors 3` |

Common root settings include:

```text
nCorrectors              2;
nNonOrthogonalCorrectors 1;
```

## Common settings across B and C

Within each controlled pair, the following are intentionally identical:

- geometry and mesh
- initial temperature
- initial velocity and pressure fields
- `phaseChangeSource:alpha1 = 1.0`
- phase-change parameters
- metal/mold interface
- mold properties
- timestep and write controls
- gravity
- laminar/momentum configuration
- numerical experiment corresponding to the 3/4/5 pair

### Common top boundary

Both branches use:

```text
metalTop
{
    type            externalWallHeatFluxTemperature;
    h               uniform 10;
    Ta              constant 300;
    value           $internalField;
    emissivity      0.3;
}
```

Therefore the controlled convection coefficient is:

`h = 10 W/(m²·K)`

### Common run start

All controlled cases use:

```text
startFrom       startTime;
startTime       0;
```

Cases should be run from a clean state.

## B formulation — temperature-dependent density

The B branch uses:

```text
equationOfState icoTabulated;
```

with temperature-dependent density.

The tabulated material definition includes:

```text
T0   1473;
rho0 6820;
```

and in `constant/metal/fvModels`:

```text
beta 0;
```

This disables the explicit Boussinesq contribution inside `solidificationMeltingSource`.

## C formulation — constant density + Boussinesq source

The C branch uses:

```text
equationOfState rhoConst;
rho             6820;
```

and:

```text
beta            1.13e-04;
rhoRef          6820;
```

Thus the controlled C reference density is **6820 kg/m³** in both the equation of state and the buoyancy source.

## Pairwise SHA validation

After creating the controlled series, every pair was audited by Git blob SHA.

For:

- `B3_reference ↔ C3_reference`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

the **only differing tracked input files** are:

```text
constant/metal/fvModels
constant/metal/materials/castIron
```

Those two differences are intentional and define the alternative buoyancy formulations.

If any additional input file differs in a future revision, that difference must be reviewed before interpreting B-vs-C results as a controlled comparison.

## Recommended run order

Run:

```text
B3_reference
C3_reference

B4_energy2
C4_energy2

B5_outer3
C5_outer3
```

For each fresh simulation:

```bash
./Allclean
./Allrun
```

## Quantities to compare

Record at minimum:

- CPU / wall-clock time
- maximum Courant number
- continuity behavior
- solver residual behavior
- central `T(t)`
- central `phaseChangeSource:alpha1(t)`
- liquidus crossing time
- solidus crossing time
- temperature rebounds together with phase-fraction behavior

The purpose of the 3/4/5 sequence is to determine whether additional energy or outer correctors materially change the physical solution or mainly increase computational cost.

## Planned OpenFOAM line profiles

The thesis advisor requested velocity and temperature profiles extracted directly from OpenFOAM rather than ParaView.

Line sampling has not yet been added.

Planned outputs include:

- `T(x,t)`
- `U(x,t)`
- `|U|(x,t)`
- `phaseChangeSource:alpha1(x,t)`
- derived `|U| = f(T)`

Any post-processing addition must not change solver physics.


## Versioned simulation logs

The primary solver log from each controlled simulation is intentionally versioned in Git:

```text
log.foamMultiRun
```

These logs are treated as part of the scientific record because they preserve evidence such as:

- successful solver completion,
- Courant-number evolution,
- solver residuals,
- continuity behavior,
- iteration history,
- CPU and wall-clock timing.

The repository still ignores general OpenFOAM logs, calculated time directories, meshes, and other generated output by default. Only `log.foamMultiRun` inside `cases_controlled_buoyancy/` is explicitly exempted from the log ignore rule.

After completing a controlled run, its `log.foamMultiRun` should be committed together with any deliberately selected compact post-processing data needed for analysis.

## Maintenance rule

This README is a **living description of the current controlled model**.

Whenever a relevant change is made to the controlled series — including physics, material properties, boundary conditions, solver settings, mesh, timestep controls, probes, post-processing, case naming, or comparison methodology — both of the following must be updated:

1. `PROJECT_AUDIT_LOG.md`  
   Records the chronological change, reason, evidence, impact and status.

2. `cases_controlled_buoyancy/README.md`  
   Records the **current accepted configuration and workflow** after the change.

The Audit Log preserves history. This README describes the current state.

No model change should be treated as part of the controlled thesis configuration until both documents reflect it.
