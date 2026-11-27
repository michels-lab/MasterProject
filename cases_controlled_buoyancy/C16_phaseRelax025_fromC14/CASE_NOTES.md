> **27-11-2026 — Uva: estado de evidencia revisado:** el push del 15-10 (`25e7cf8cb4a30fb0fe5ece5bd9a2e451815ab232`) contiene `logs/Time_0` hasta 10 s y la sonda T hasta 10 s (1464.22 K), comprobados directamente en el commit. Estado `EVIDENCE_PUSHED_PRELIMINARY_COMPARISON`; no `RUN_VERIFIED` ni `ANALYSIS_VERIFIED`. [Cribado publicado](../../analysis_results/v15_v16_postpush_20261015/README.md). Las afirmaciones previas de no ejecución son históricas/no actualizadas; no reejecutar automáticamente antes de auditar el material existente.

> **18-11-2026 — Nota histórica del primer avance (estado de ejecución corregido arriba):** C16 es la prueba controlada necesaria para medir sensibilidad de `phaseChangeSource.relax` de **0.10 (C14) a 0.25 (C16)**, con el resto fijo y postprocesamiento comparativo de `T(t)`, `alpha1(t)`, `U`, residuos, Courant **observado**, continuidad, energía y tiempo CPU. **Permanece `PREPARED_NOT_RUN`: no hay resultados C16 verificados ni curvas de sensibilidad**. `maxCo=0.25` de C14 es una entrada distinta. [Checklist obligatorio del primer avance](../../docs/PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md).

# C16 — phase-fraction relaxation experiment

**Historical preparation status:** PREPARED_NOT_RUN (2026-10-08). **Parent:** C14_topFixedFlux_explicitRef.
**Execution:** Only on the researcher's laptop with OpenFOAM Foundation 14. Never execute CFD on GitHub.

## Controlled intervention
Exactly ONE input file differs from C14:
constant/metal/fvModels, phaseChangeSource: relax 0.1 -> 0.25.

Do not confuse this with the maxCo=0.25 Courant limit in system/controlDict, or root relaxationFactors=1.0 for equations. C16 retains fixed deltaT=0.001 s (adjustTimeStep=no), original thermal/pressure BC, fixed-volume geometry, 3 root outer correctors and all other C14 properties.

Source-based prediction (Foundation v14): solidificationMelting update uses alpha1_new=clamp(alpha1 + relax*Cp*(T-Tphase(alpha1))/L, 0,1) once per time index. A larger relax can change phase-fraction response and thermal evolution; do not classify it as a harmless solver convergence tweak. Reference: https://cpp.openfoam.org/v14/solidificationMelting_8C_source.html

## Post-push acceptance
Compare C16 vs C14 at identical physical time: T(t), phaseChangeSource:alpha1, dAlphaLdt, solidificationRate, latentHeatRateVol, front profiles, pressure residuals, U, top phi, energy power, Courant, continuity and cost. Evaluate stability/overshoot; thermally positive rebound and remelting alone do not prove metallurgical recalescence.

Historical preparation note: no foamMultiRun/Allrun had been recorded at preparation. The subsequent 15 October evidence push supersedes that status; native final log and input provenance still require audit.
