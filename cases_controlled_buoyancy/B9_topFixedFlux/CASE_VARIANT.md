# B9_topFixedFlux

Parent case: `B5_outer3`.

Controlled change: `0/metal/p_rgh` on `metalTop` changed from `totalPressure` to `fixedFluxPressure`, while `U=slip` and the thermal boundary condition remain unchanged.

Purpose: test whether the previous non-zero top advective-energy flux and B/C circulation differences are influenced by pressure/flux inconsistency at the impermeable top wall.

A `metalTopPhiSum` function object was added to `system/researchDiagnostics` to verify the solver flux directly.

Everything else is inherited unchanged from the parent input case. No calculated results from the parent were copied.


## Diagnostic rho(T) extension

After the first closed-top run failed at T=1782.04 K because the original `icoTabulated` density table ended at 1773.15 K, the B9 table was extended **for diagnostic purposes only**.

The added points continue the slope of the original final interval (1573.15–1773.15 K):

`d rho / dT = -0.8 kg/(m3 K)`

Added extrapolated points:
- 1873.15 K -> 6500 kg/m3
- 1973.15 K -> 6420 kg/m3
- 2073.15 K -> 6340 kg/m3
- 2173.15 K -> 6260 kg/m3
- 2273.15 K -> 6180 kg/m3

These values are **not validated cast-iron property data** and must not be used as experimental material-property evidence. Their only purpose is to observe how the closed variable-density formulation evolves beyond the original table limit.
