# QuickCup-Solidification

**Master's thesis simulation project:** multi-region casting/Quick-Cup solidification, conjugate heat transfer, buoyancy and enthalpy–porosity using **OpenFOAM Foundation v14**.

## 2026-10-08 research roadmap

[**Research plan: C15 adaptive, C16 phase relaxation, C3D and B free-surface/shrinkage**](NEXT_RESEARCH_ROADMAP_ES.md). B15/B16 and C15/C16 are prepared input-only cases, not simulated in GitHub or validated.

**Stage gate:** complete paired B/C studies through V16 first; then fork into C → 3D and B → metal-air free surface plus shrinkage/feeding. No GitHub-based CFD execution.

## New independent 3D research line — C3D-01

The first three-dimensional QuickCup mesh experiment lives in [`cases_3d/C3D_01_metal_mold`](cases_3d/C3D_01_metal_mold/README.md). It includes a 2 mm Cartesian `blockMeshDict`, native OpenFOAM Foundation v14 `units [mm]` in the background mesh, byte-identical SolidWorks STL staging for future `snappyHexMesh`, mesh-only shell script, region seeds, and static regression tests. **Prepared, not run in OpenFOAM; no 3D CFD results yet.** User CAD/STL data remain local because this repository is public.

See also the [3D case index](cases_3d/README.md). The existing C14 and B/C numerical research runs remain unchanged.

## Scientific agents and postprocessing

**Execution ownership:** all CFD runs occur on the user's laptop. The repository runs no CFD and only audits results after git push.

- [Postprocessing field and function-object guide (Spanish)](POSTPROCESSING_FIELD_GUIDE_ES.md)
- [Initial scientific results from the 2026-10-15 laptop push](analysis_results/v15_v16_postpush_20261015/README.md) — five cases have data to 10 seconds, but are not yet physically/experimentally audited.
- [V15/V16 controlled-input preflight (read-only)](analysis_tools/preflight_sensitivity_cases.py) — verifies B15/B16/C15/C16 provenance and single-variable changes before laptop runs; [evidence report](analysis_results/v15_v16_preflight/README.md).
- [Post-push evidence auditor (read-only)](analysis_tools/audit_pushed_results.py) — checks files already pushed from the user's laptop
- [Static OpenFOAM14 function-object auditor](analysis_tools/audit_postprocessing_config.py)
- [GitHub post-push/manual/scheduled audit workflow](.github/workflows/quickcup-research-audit.yml) — checks committed evidence only, never launches CFD; verify actual Actions success.
- [Specialized scientific agent roles](.github/agents/quickcup-postprocess-forensics.agent.md)

## Start here — all future runs and audits

1. [**RUN_MASTER_PROTOCOL.md — required between-run update checklist**](RUN_MASTER_PROTOCOL.md)
2. [**RUN_CASE_REGISTRY.csv — 30-case status and audit coverage**](RUN_CASE_REGISTRY.csv)
3. [Project audit log (ES/EN)](PROJECT_AUDIT_LOG.md)
4. [Validation matrix (ES/EN)](VALIDATION_MATRIX.md)
5. [Case guide in Spanish](CASE_GUIDE_ES.md)
6. [JMatPro → OpenFOAM traceability](JMATPRO_OPENFOAM_TRACEABILITY_ES.md)

## Coverage at 2026-10-08

- 34 controlled-case directories: **29 verified** and **5 prepared/not run** (`B11_energy2_test`).
- [Historical full-campaign audit](analysis_results/full_campaign_audit/README.md) covers **26 cases only**, not all currently verified cases.
- Additional independently verified results: [V14 B/C comparison](analysis_results/v14_bc_comparison/summary.md) and [C11 two-energy-corrector controlled test](analysis_results/c11_energy2_test/summary.md).
- Current baseline for future fixed-volume experimental validation: `C14_topFixedFlux_explicitRef`; historical frozen reference: C11; JMatPro provenance gate **J0 open**.

**Do not treat a successful run, old copied output, or `git push` alone as a completed scientific audit.** Follow the protocol and preserve the distinction between numerical verification and experimental validation.

Repository guidance lives here, not in a separate Michel's Lab main repository.
