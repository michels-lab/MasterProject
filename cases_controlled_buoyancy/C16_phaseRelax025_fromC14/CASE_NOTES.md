# C16 — phase-fraction relaxation experiment

**Status:** PREPARED_NOT_RUN (2026-10-08). **Parent:** C14_topFixedFlux_explicitRef.
**Execution:** Only on the researcher's laptop with OpenFOAM Foundation 14. Never execute CFD on GitHub.

## Controlled intervention
Exactly ONE input file differs from C14:
constant/metal/fvModels, phaseChangeSource: relax 0.1 -> 0.25.

Do not confuse this with the maxCo=0.25 Courant limit in system/controlDict, or root relaxationFactors=1.0 for equations. C16 retains fixed deltaT=0.001 s (adjustTimeStep=no), original thermal/pressure BC, fixed-volume geometry, 3 root outer correctors and all other C14 properties.

Source-based prediction (Foundation v14): solidificationMelting update uses alpha1_new=clamp(alpha1 + relax*Cp*(T-Tphase(alpha1))/L, 0,1) once per time index. A larger relax can change phase-fraction response and thermal evolution; do not classify it as a harmless solver convergence tweak. Reference: https://cpp.openfoam.org/v14/solidificationMelting_8C_source.html

## Post-push acceptance
Compare C16 vs C14 at identical physical time: T(t), phaseChangeSource:alpha1, dAlphaLdt, solidificationRate, latentHeatRateVol, front profiles, pressure residuals, U, top phi, energy power, Courant, continuity and cost. Evaluate stability/overshoot; thermally positive rebound and remelting alone do not prove metallurgical recalescence.

No foamMultiRun/Allrun has been executed for this case.
