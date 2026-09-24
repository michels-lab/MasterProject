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


## Current run status

| Pair | Run status | Log status | Analysis |
|---|---|---|---|
| `B3_reference` / `C3_reference` | Completed to 10 s | `log.foamMultiRun` committed to Git | Solver-log review complete; thermal-probe comparison pending |
| `B4_energy2` / `C4_energy2` | Pending | Pending | Pending |
| `B5_outer3` / `C5_outer3` | Pending | Pending | Pending |

The B3/C3 controlled logs were committed in Git commit `d6c307c8`.

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


### B3/C3 reference-run solver metrics

The committed `log.foamMultiRun` files were parsed over the complete 0–10 s run (10,000 steps, `deltaT = 0.001 s`).

| Metric | B3_reference | C3_reference |
|---|---:|---:|
| End time | 10 s | 10 s |
| Time steps | 10,000 | 10,000 |
| Peak metal Courant number | 0.175912 at 0.283 s | 0.0700709 at 2.510 s |
| Last reported metal Co max | 0.0606638 | 0.0241928 |
| Final cumulative continuity | 1.66260e-4 | 1.78349e-4 |
| Final `h` residual | 8.73216e-11 | 2.46231e-11 |
| Final `e` residual | 3.73694e-10 | 3.76994e-10 |
| Final `p_rgh` residual | 3.88108e-8 | 2.68792e-8 |
| Execution time | 249.556 s | 224.372 s |
| Clock time | 258 s | 225 s |
| Fatal errors | 0 | 0 |
| Warnings | 0 | 0 |

Both reference cases completed normally. The solver-log audit alone does not determine the physical difference between the B and C formulations; that comparison requires the central `T(t)` and `phaseChangeSource:alpha1(t)` probe data.


## B3/C3 reference-run results

Both controlled reference cases completed successfully to **10 s** with `End`.

| Metric | B3_reference | C3_reference |
|---|---:|---:|
| Final simulated time | 10 s | 10 s |
| CPU time | 249.556 s | 224.372 s |
| Clock time | 258 s | 225 s |
| Maximum Courant number | 0.175912 | 0.0700709 |
| Final Courant number | 0.0606638 | 0.0241928 |
| Final mean Courant number | 0.0154644 | 0.00934688 |
| Final cumulative continuity error | 1.66260e-4 | 1.78349e-4 |

At the final time, both cases show strongly reduced energy residuals and pressure corrections reaching final residuals below approximately `1e-7` in the final pressure solve.

Interpretation at this stage:

- both runs are numerically stable over 0–10 s;
- B3 reaches a substantially higher Courant number than C3;
- B3 requires approximately 11% more CPU time than C3;
- continuity accumulation is of the same order in both cases.

These differences must not yet be interpreted as definitive physical superiority or as a complete buoyancy comparison. Temperature, phase fraction and velocity-field outputs still need to be compared.

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

Simulation and runtime logs are intentionally **not ignored** in this repository.

Logs are treated as part of the numerical/scientific record because they can preserve evidence such as:

- successful or failed solver completion,
- Courant-number evolution,
- solver residuals,
- continuity behavior,
- iteration history,
- warnings and runtime diagnostics,
- CPU and wall-clock timing.

This policy applies generally to OpenFOAM and project runtime logs, not only to `log.foamMultiRun`.

Large generated solution fields, calculated time directories, meshes, post-processing output, media and temporary build artifacts remain ignored unless deliberately selected for versioning.

Editor-specific temporary logs such as `.vscode/*.log` may remain ignored because they are not part of the simulation record.

After completing a controlled run, relevant logs should be committed so the numerical history can be audited later.


## Maintenance rule

This README is a **living description of the current controlled model**.

Whenever a relevant change is made to the controlled series — including physics, material properties, boundary conditions, solver settings, mesh, timestep controls, probes, post-processing, case naming, or comparison methodology — both of the following must be updated:

1. `PROJECT_AUDIT_LOG.md`  
   Records the chronological change, reason, evidence, impact and status.

2. `cases_controlled_buoyancy/README.md`  
   Records the **current accepted configuration and workflow** after the change.

The Audit Log preserves history. This README describes the current state.

No model change should be treated as part of the controlled thesis configuration until both documents reflect it.
