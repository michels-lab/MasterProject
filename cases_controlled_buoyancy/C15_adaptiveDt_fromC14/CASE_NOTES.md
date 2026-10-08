# C15 — adaptive time-step experiment

**Status:** PREPARED_NOT_RUN (2026-10-08). **Parent:** C14_topFixedFlux_explicitRef.
**Execution:** Only on the researcher's laptop with OpenFOAM Foundation 14. Never execute CFD on GitHub.

## Controlled intervention
Only system/controlDict differs from C14:
- adjustTimeStep: no -> yes
- writeControl: timeStep -> adjustableRunTime
- writeInterval: 100 steps -> 0.1 seconds (output scheduling for comparable 0.1 s profiles, **not** a physical model change)

Other C14 parameters are preserved: initial deltaT=0.001 s, maxCo=0.25, maxDeltaT=0.1 s, endTime=10 s, solidificationMelting relax=0.1, all C14 geometry, mesh, interfaces and numerical controls.

The temperature probe writes each solver timestep, so its timestamps will be nonuniform. Align samples by physical time, never by row index. Investigate time-step overshoot and thermophysical accuracy: C6/C8 previously exhibited significant adaptive vs fixed-step phase-front differences.

## Post-push acceptance
- Confirm actual endTime, log return/End and fatal error status; verify effective dt evolution, Co and Courant overshoots.
- Confirm every 0.1s volumetric/line/face output and complete central probe timeline (or explicitly record gaps).
- Compare C15 vs C14 at matched physical times: central T, alphaL, U, phase front, latent-power, facewise top phi, energy flux, continuity, residuals and cost.
- Report baseline decision only after comparing the fields; never equate speed-up with identical physics.

No foamMultiRun/Allrun has been executed for this case.
