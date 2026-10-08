# CASE_VARIANT — C16_phaseRelax025_fromC14

- Parent C14_topFixedFlux_explicitRef (frozen).
- PREPARED_NOT_RUN.
- **One input difference**: constant/metal/fvModels/phaseChangeSource relax 0.1 -> 0.25.
- Fixed timestep as C14; no other numerical, material or boundary differences.
- This tests phase-fraction relaxation, NOT p_rgh under-relaxation or Courant maxCo.
- Source https://cpp.openfoam.org/v14/solidificationMelting_8C_source.html
- This repository never runs CFD.
