# Controlled buoyancy cases

This directory contains the clean B/C comparison series for the QuickCup solidification study.

Common settings across each B/C pair:
- metalTop convection coefficient: h = 10 W/(m^2 K)
- startFrom: startTime
- same mesh, thermal boundaries, phase-change parameters, timestep controls, and numerical experiment settings

B formulation:
- icoTabulated density
- beta = 0 in solidificationMeltingSource

C formulation:
- rhoConst = 6820 kg/m^3
- beta = 1.13e-04 1/K
- rhoRef = 6820 kg/m^3

Cases:
- B3_reference / C3_reference: reference coupling
- B4_energy2 / C4_energy2: nEnergyCorrectors = 2
- B5_outer3 / C5_outer3: nOuterCorrectors = 3

Historical development cases remain under cases_buoyancy/ and are not overwritten.
