# CASE_VARIANT — C15_adaptiveDt_fromC14

- Parent C14_topFixedFlux_explicitRef (frozen).
- PREPARED_NOT_RUN.
- **One numerical intervention**: enable adaptive time-step in root system/controlDict.
- Output-only adaptation: adjustableRunTime, every 0.1 s physical time.
- Keep maxCo 0.25, maxDeltaT 0.1 s and initial deltaT 0.001 s.
- Compare with C14 at identical physical times; scrutinize old C6/C8 adaptive-vs-fixed discrepancies.
- This repository never runs a CFD simulation.
