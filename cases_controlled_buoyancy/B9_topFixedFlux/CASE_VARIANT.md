# B9_topFixedFlux

Parent case: `B5_outer3`.

Controlled change: `0/metal/p_rgh` on `metalTop` changed from `totalPressure` to `fixedFluxPressure`, while `U=slip` and the thermal boundary condition remain unchanged.

Purpose: test whether the previous non-zero top advective-energy flux and B/C circulation differences are influenced by pressure/flux inconsistency at the impermeable top wall.

A `metalTopPhiSum` function object was added to `system/researchDiagnostics` to verify the solver flux directly.

Everything else is inherited unchanged from the parent input case. No calculated results from the parent were copied.
