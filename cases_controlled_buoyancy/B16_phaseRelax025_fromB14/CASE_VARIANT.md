# CASE_VARIANT — B16_phaseRelax025_fromB14

**Estado** PREPARED_NOT_RUN · 2026-10-08

Padre `B14_topFixedFlux_explicitRef`; solo `constant/metal/fvModels` cambia:
- `phaseChangeSource/relax: 0.1 -> 0.25`.
- Mantener `adjustTimeStep=no` y `deltaT=0.001` s, `maxCo=0.25`, `relaxationFactors=1.0` sin cambios.
- Comparar con B14 y en paralelo C16 con C14; no atribuir corrección automática de continuidad.
- CFD únicamente en laptop; GitHub audita outputs después del push.
