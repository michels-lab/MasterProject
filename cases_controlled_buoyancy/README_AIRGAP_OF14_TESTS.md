# OpenFOAM 14 air-gap comparison matrix

These four cases preserve both B and C families and both V5 and V9 lineages while correcting the metal-mold air-gap syntax for OpenFOAM Foundation v14.

| Case | Parent lineage | Air gap | B density table |
|---|---|---|---|
| B5_airGapOF14 | B5_outer3 | 0.2 mm, k=0.1 W/(m K), OF14 syntax | extended to 2273.15 K |
| C5_airGapOF14 | C5_outer3 | same | rhoConst |
| B9_airGapOF14 | B9_topFixedFlux | same | extended to 2273.15 K |
| C9_airGapOF14 | C9_topFixedFlux | same | rhoConst |

For B, both corrected cases use the identical extended icoTabulated density table. The original values through 1773.15 K are unchanged.

This matrix supports:
1. B5_airGapOF14 vs B9_airGapOF14: effect of the V9 top pressure-boundary correction with the same OF14 air gap and density table.
2. C5_airGapOF14 vs C9_airGapOF14: corresponding C-family control.
3. B vs C at matched V5 or V9 lineage.
