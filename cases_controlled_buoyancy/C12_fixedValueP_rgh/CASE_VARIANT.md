# C12_fixedValueP_rgh

Parent case: `C11_topFixedFlux_airGapOF14`.

Controlled change: `metalTop` in `0/metal/p_rgh` is changed from `fixedFluxPressure` to `fixedValue` with `value uniform 0`.

The case already contains `pRef = 1e5 Pa`; therefore the reduced-pressure boundary is not set to 1e5 Pa again.

All other inputs are inherited unchanged from C11, including the corrected OpenFOAM 14 air gap, U=slip, timestep, PIMPLE settings, phase-change model, C-family rhoConst formulation, and diagnostics.
