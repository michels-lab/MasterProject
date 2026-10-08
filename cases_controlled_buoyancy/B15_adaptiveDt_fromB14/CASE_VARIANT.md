# CASE_VARIANT — B15_adaptiveDt_fromB14

**Estado** PREPARED_NOT_RUN · 2026-10-08

Padre `B14_topFixedFlux_explicitRef`; solo difiere `system/controlDict`.
- `adjustTimeStep yes` desde `no`.
- Instrumentación de output: `writeControl adjustableRunTime`, `writeInterval 0.1` s.
- `maxCo 0.25`, `maxDeltaT 0.1` s, `deltaT` inicial 0.001 s conservados.
- Evaluar contra B14 y en paralelo con C15 contra C14, en tiempos físicos.
- B14 sigue con problema de continuidad de volumen rígido/densidad variable, no declarado resuelto aquí.
- Sólo el usuario ejecuta CFD localmente; GitHub audita tras push.
