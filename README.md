# QuickCup-Solidification

**Master's thesis simulation project:** multi-region casting/Quick-Cup solidification, conjugate heat transfer, buoyancy and enthalpy–porosity using **OpenFOAM Foundation v14**.

## Scientific agents and postprocessing

- [Postprocessing field and function-object guide (Spanish)](POSTPROCESSING_FIELD_GUIDE_ES.md)
- [Guarded local case launcher with simultaneous observer](analysis_tools/run_with_agents.py)
- [Live local observer](analysis_tools/live_run_watch.py) — run as a separate process beside active OpenFOAM
- [Static OpenFOAM14 function-object auditor](analysis_tools/audit_postprocessing_config.py)
- [GitHub scheduled/manual/static workflow](.github/workflows/quickcup-research-audit.yml) — verify its actual Actions status; it cannot see live local runs.
- [Specialized scientific agent roles](.github/agents/quickcup-postprocess-forensics.agent.md)

## Start here — all future runs and audits

1. [**RUN_MASTER_PROTOCOL.md — required between-run update checklist**](RUN_MASTER_PROTOCOL.md)
2. [**RUN_CASE_REGISTRY.csv — 30-case status and audit coverage**](RUN_CASE_REGISTRY.csv)
3. [Project audit log (ES/EN)](PROJECT_AUDIT_LOG.md)
4. [Validation matrix (ES/EN)](VALIDATION_MATRIX.md)
5. [Case guide in Spanish](CASE_GUIDE_ES.md)
6. [JMatPro → OpenFOAM traceability](JMATPRO_OPENFOAM_TRACEABILITY_ES.md)

## Coverage at 2026-10-08

- 30 controlled-case directories: **29 verified** and **1 prepared/not run** (`B11_energy2_test`).
- [Historical full-campaign audit](analysis_results/full_campaign_audit/README.md) covers **26 cases only**, not all currently verified cases.
- Additional independently verified results: [V14 B/C comparison](analysis_results/v14_bc_comparison/summary.md) and [C11 two-energy-corrector controlled test](analysis_results/c11_energy2_test/summary.md).
- Current baseline for future fixed-volume experimental validation: `C14_topFixedFlux_explicitRef`; historical frozen reference: C11; JMatPro provenance gate **J0 open**.

**Do not treat a successful run, old copied output, or `git push` alone as a completed scientific audit.** Follow the protocol and preserve the distinction between numerical verification and experimental validation.

Repository guidance lives here, not in a separate Michel's Lab main repository.
