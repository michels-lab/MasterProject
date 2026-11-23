# Caso B — CFD C14 metal fluido + arena sólida REAL iniciado en WSL, todavía EN CURSO

**Evidencia de investigador, 23 de noviembre de 2026.** El primer intento del día abortó previamente por `ZSH_NAME` al cargar bashrc de Foundation14; la corrección del wrapper ya fue instalada en WSL por `git pull`. En el segundo intento `run_case_b_c14_native.sh --run-full` pasó el examen de malla original y avanzó hasta el solver nativo.

**Estado del tiempo observado:** **`Time = 1.417s`** de un horizonte configurado `endTime=10s`, `deltaT=0.001s`: 14.17% del tiempo físico simulado. No confundir este porcentaje con avance de hitos ni con duración o tiempo restante.

## Evidencia nativa compartida

El terminal paralelo mostró:

```text
14927 21:09 S+    0.0 0.4 python3 -B .../stage_c14_3d_case_b.py --run-full
15660 21:02 Rl+  97.6 5.5 foamMultiRun -case /home/michel/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01
SOLVER INICIADO
metal Courant Number mean: 0.0138185 max: 0.184568
Time = 1.417s
PIMPLE: Iteration 1
metal DILUPBiCGStab: Solving for h, Initial residual = 0.000332184, Final residual = 4.7932e-07, No Iterations 1
mold DICPCG: Solving for e, Initial residual = 0.000185794, Final residual = 2.5028e-08, No Iterations 1
metal GAMG: Solving for p_rgh, Initial residual = 0.0011836, Final residual = 5.08254e-06, No Iterations 3
metal time step continuity errors : sum local = 3.44392e-12, global = -2.9104e-19, cumulative = -4.55905e-15
mold PIMPLE: Iteration 2
metal DILUPBiCGStab: Solving for h, Initial residual = 1.0714e-06, Final residual = 2.98075e-09, No Iterations 1
```

**Preceding staging geometry message:**

```text
REAL_ACCEPTED_3D_HEX8_NATIVE_EVIDENCE: 270788 cells (metal 92200 / mold 178588), 12636 coupled faces per side, true CAD volumes 4.79754032229e-05 + 0.000102843380345 m3, 1826 severe nonorth faces (WARNING, not solved)
```

This is **real-case WSL OpenFOAM 14 CFD currently active**, not a synthetic regression. The output path is `/home/michel/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01`, with live log `log.foamMultiRun.C3D05_B_C14_10S`.

## Exact scientific status

- C14 exact-source metal as **fluid** and mold as **solid** with `solidificationMeltingSource` configured in case files. The shown terminal excerpt proves native solution of `h/e/p_rgh` but **does not contain the model-selection line**; confirm it from complete solver log before claiming phase source actually selected.
- **Not completed:** 1.417s is less than 10s; no `Time=10s`/`End` evidence in shared excerpt.
- **Not yet demonstrated:** any `phaseChangeSource:alpha1` evolution, latent heat transfer, cooling curves, experimental validity, physical material properties from JMatPro, mesh/dt convergence, resolved stability for entire run or shrinkage.
- The latest observed `CoMax=0.184568` and small equation residuals/continuity are **local diagnostics at reported timestep**, not full-run numerical acceptance. The original mesh still has **1,826 severe nonorthogonal internal faces**.
- `foamMultiRun` had `STAT=Rl+` and `CPU≈97.6%` in a process snapshot. No basis for a completion ETA; the user should **keep the original terminal/process running**, do not re-invoke `--run-full` or delete staged case.
- Progress contract remains **Caso B etapa 3/7, 2/7=29% hitos técnicos**, with G3/G4 physics, G5 phase and G6/G7 still open. **Do not incorrectly set `native_solver_run=true` (defined as successful completed run)** simply because the native process has started.

Read-only state check from a separate Ubuntu terminal if needed:

```bash
LOG="$HOME/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01/log.foamMultiRun.C3D05_B_C14_10S"
grep -E '^ *Time = |^ *End$|Selecting solidificationMeltingSource|FOAM FATAL ERROR' "$LOG" | tail -n 12
```

Do not run the case again while `foamMultiRun` is active.
