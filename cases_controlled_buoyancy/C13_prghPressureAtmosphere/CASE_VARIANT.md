# C13_prghPressureAtmosphere

Parent case: `C11_topFixedFlux_airGapOF14`.

Controlled change: `metalTop` in `0/metal/p_rgh` is changed from `fixedFluxPressure` to OpenFOAM v14 `prghPressure`.

The boundary prescribes `p uniform 0` gauge relative to the existing case-level `pRef = 1e5 Pa`. OpenFOAM therefore reconstructs a physical static pressure of 1e5 Pa at the top while applying the hydrostatic rho*g*h correction to p_rgh.

All other inputs are inherited unchanged from C11.
