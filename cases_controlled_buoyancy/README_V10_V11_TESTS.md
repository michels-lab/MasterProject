# Cases 10 and 11 — OpenFOAM 14 air-gap matrix

The numbered continuation after cases 7–9 is:

| Case | Parent lineage | Controlled meaning |
|---|---|---|
| B10_airGapOF14 | B5_outer3 | V5 + corrected OF14 air gap + common extended B density table |
| C10_airGapOF14 | C5_outer3 | V5 + corrected OF14 air gap |
| B11_topFixedFlux_airGapOF14 | B9_topFixedFlux | V9 + corrected OF14 air gap + common extended B density table |
| C11_topFixedFlux_airGapOF14 | C9_topFixedFlux | V9 + corrected OF14 air gap |

The air gap remains physically identical in all four cases:
- thickness: 2e-4 m (0.2 mm)
- thermal conductivity: 1e-1 W/(m K)
- equivalent gap conductance: 500 W/(m2 K)

B10/B11 use the same rho(T) table extended through 2273.15 K. C10/C11 retain rhoConst.

Primary comparisons:
1. B10 vs B11 — effect of top pressure BC with matched OF14 air gap and matched rho(T).
2. C10 vs C11 — same comparison in the C family.
3. B10 vs C10 — B/C formulation contrast in the V5 lineage.
4. B11 vs C11 — B/C formulation contrast in the V9 lineage.
