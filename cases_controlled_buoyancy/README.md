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
| `B3_reference` / `C3_reference` | Completed to 10 s | Solver logs + central probes committed to Git | Solver and central thermal/phase comparison complete; velocity-field comparison pending |
| `B4_energy2` / `C4_energy2` | Completed to 10 s | Solver logs + central probes committed to Git | Solver and central thermal/phase comparison complete |
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

Both reference cases completed normally. The central `T(t)` and `phaseChangeSource:alpha1(t)` probe histories have now also been reviewed; the solver metrics above should therefore be interpreted together with the thermal/phase results below.


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

These solver differences must not be interpreted as definitive physical superiority. Central temperature and phase fraction have now been compared, but velocity-field/profile analysis and comparison with experimental thermal curves are still required before judging which formulation better represents the physical system.


### Central thermal/phase probe comparison

The central probe is located at `(0.02 0.02 0.005) m`. Both files contain 10,001 samples from 0 to 10 s at 0.001 s spacing.

| Metric | B3_reference | C3_reference |
|---|---:|---:|
| Initial temperature | 1500 K | 1500 K |
| Initial liquid fraction | 1.000000 | 1.000000 |
| First downward crossing of liquidus, 1473 K | 6.666 s | 3.386 s |
| First departure of `alpha1` from 1 | 6.668 s | 3.388 s |
| Time to `alpha1 = 0.99` | 9.619 s | 3.654 s |
| Minimum central temperature over 0–10 s | 1467.45 K at 10 s | 1456.25 K at 4.822 s |
| Minimum central liquid fraction over 0–10 s | 0.978184 at 10 s | 0.932983 at 4.878 s |
| Final temperature at 10 s | 1467.45 K | 1461.60 K |
| Final liquid fraction at 10 s | 0.978184 | 0.954394 |

Additional controlled-pair observations:

- C3 reaches the liquidus approximately **3.280 s earlier** than B3.
- The maximum absolute central-temperature difference is approximately **33.42 K** at **4.644 s** (`B3 = 1489.92 K`, `C3 = 1456.50 K`).
- The maximum absolute central liquid-fraction difference is approximately **0.0670** at **4.878 s**.
- C3 reaches a local temperature minimum of **1456.25 K** at 4.822 s and then rises to **1461.60 K** by 10 s, a rebound of about **5.35 K**.
- C3 liquid fraction reaches **0.932983** at 4.878 s and then increases to **0.954394** by 10 s, which is direct evidence of **local remelting in the model** after the minimum liquid fraction.
- B3 also shows a smaller transient phase reversal: after first crossing 1473 K at 6.666 s, `alpha1` falls to about **0.997042** at 7.045 s, returns to **1.0** at 7.460 s, and the central temperature crosses back above 1473 K at about 7.447 s before crossing downward again near 9.069 s.
- At 10 s, B3 is **5.85 K hotter** at the center and has a liquid fraction higher by about **0.02379**.

These non-monotonic center histories must **not** be labeled physical recalescence from the probe alone. In this equilibrium enthalpy-porosity model, convection/mixing and local remelting can produce temperature rebounds. Velocity fields/profiles and experimental thermal curves are required to determine the mechanism and physical validity.


### B4/C4 energy-corrector convergence result

B4/C4 repeat the controlled B/C comparison with `nEnergyCorrectors = 2` instead of the B3/C3 reference value of 1. All four runs reached 10 s with `End`, with no `FOAM FATAL` entries or warnings.

| Metric | B3_reference | B4_energy2 | C3_reference | C4_energy2 |
|---|---:|---:|---:|---:|
| Peak metal Courant number | 0.175912 | 0.176643 | 0.0700709 | 0.0700709 |
| Final metal Co max | 0.0606638 | 0.0602696 | 0.0241928 | 0.0241928 |
| Final cumulative continuity | 1.66260e-4 | 1.67018e-4 | 1.78349e-4 | 1.78349e-4 |
| Execution time | 249.556 s | 240.667 s | 224.372 s | 225.476 s |
| Thermal solves (`h`) | 20,000 | 40,000 | 20,000 | 40,000 |
| Mold-energy solves (`e`) | 20,000 | 40,000 | 20,000 | 40,000 |

The doubled energy-corrector setting does in fact double the number of `h` and `e` solve calls. The observed wall/CPU times, however, do not scale monotonically in these single runs: B4 was about 3.6% faster than B3, while C4 was about 0.5% slower than C3. This timing variability should not be interpreted as an intrinsic performance advantage without repeated runs under controlled machine load.

Central-probe convergence is much clearer:

| Comparison | Maximum absolute ΔT | Maximum absolute Δalpha_l |
|---|---:|---:|
| B3 vs B4 | 0.19 K | 5.22e-4 |
| C3 vs C4 | 0.01 K | 1.0e-6 |
| B4 vs C4 | 33.42 K | 0.067017 |

Key event times remain essentially unchanged:

- B3 liquidus crossing: 6.666 s; B4: **6.678 s**.
- C3 liquidus crossing: 3.386 s; C4: **3.386 s**.
- B3 `alpha_l = 0.99`: 9.619 s; B4: **9.636 s**.
- C3 `alpha_l = 0.99`: 3.654 s; C4: **3.654 s**.
- C4 reproduces the C3 minimum center temperature of **1456.25 K at 4.822 s** and minimum `alpha_l = 0.932983 at 4.878 s`.
- At 10 s, B4 gives **1467.53 K** and `alpha_l = 0.978506`; C4 gives **1461.60 K** and `alpha_l = 0.954394`.

Therefore increasing `nEnergyCorrectors` from 1 to 2 produces negligible changes in the controlled central thermal/phase histories relative to the much larger B-vs-C formulation difference. The B/C separation and the C-series rebound/remelting behavior are robust to this energy-corrector change over the tested 0–10 s interval.

This does not yet establish physical validity. Velocity-field/profile analysis and experimental comparison are still required, and B5/C5 remain the planned outer-corrector convergence test.


### B4/C4 energy-corrector comparison

B4/C4 increase root `nEnergyCorrectors` from the B3/C3 reference value to **2** while preserving the controlled B/C physical formulations.

The solver logs confirm that the second energy corrector was actually executed:

| Case | `h` solves | `e` solves | `p_rgh` solves |
|---|---:|---:|---:|
| B3_reference | 20,000 | 20,000 | 40,000 |
| B4_energy2 | 40,000 | 40,000 | 40,000 |
| C3_reference | 20,000 | 20,000 | 40,000 |
| C4_energy2 | 40,000 | 40,000 | 40,000 |

Despite doubling the energy solves, the central thermal/phase solution changes only minimally.

| Comparison | Maximum | Location/time |
|---|---:|---:|
| `|T_B3 - T_B4|` | **0.19 K** | 7.456 s |
| `|alpha_B3 - alpha_B4|` | **5.22e-4** | 7.413 s |
| `|T_C3 - T_C4|` | **0.01 K** | 4.607 s |
| `|alpha_C3 - alpha_C4|` | **1e-6** | 3.819 s |

Key B4/C4 center metrics:

| Metric | B4_energy2 | C4_energy2 |
|---|---:|---:|
| First downward 1473 K crossing | 6.678 s | 3.386 s |
| First departure of `alpha1` from 1 | 6.681 s | 3.388 s |
| `alpha1 = 0.99` | 9.636 s | 3.654 s |
| Minimum center temperature | 1467.53 K at 10 s | 1456.25 K at 4.822 s |
| Minimum center liquid fraction | 0.978506 at 10 s | 0.932983 at 4.878 s |
| Final temperature at 10 s | 1467.53 K | 1461.60 K |
| Final liquid fraction at 10 s | 0.978506 | 0.954394 |

The B4/C4 controlled difference remains large: maximum central-temperature separation is **33.42 K** at 4.637 s, and maximum central liquid-fraction separation is **0.067017** at 4.878 s.

Solver-log metrics:

| Metric | B4_energy2 | C4_energy2 |
|---|---:|---:|
| Peak metal Courant number | 0.176643 | 0.0700709 |
| Final metal Co max | 0.0602696 | 0.0241928 |
| Final cumulative continuity | 1.67018e-4 | 1.78349e-4 |
| Execution time | 240.667 s | 225.476 s |
| Clock time | 248 s | 226 s |
| Fatal errors / warnings | 0 / 0 | 0 / 0 |

Interpretation: increasing `nEnergyCorrectors` from 1 to 2 does **not materially alter the controlled central thermal or phase histories**. The large B-vs-C difference therefore persists under the additional energy correction. The single-run timing values should not be treated as a clean cost benchmark because machine load and run-to-run variability were not controlled or replicated.

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
