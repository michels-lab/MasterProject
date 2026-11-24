# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 39110; classified: 39105; readable documents: 212; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 17 |
| data | 32 |
| document | 174 |
| index | 34 |
| license | 1 |
| simulation_case_file | 121 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 150 |
| test | 74 |
| web_ui | 1 |
| workflow | 33 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 31 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-native-fluid-solid.yml, .github/workflows/c3d04-a-c14-postprocessing-parity.yml, .github/workflows/c3d05-b-c14-native-fluid-solid-q.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/continue_c14_stage07_grouped_evidence.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/native_bilateral_flux/c3d04C14FluidSolidFlux.C, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/probe_c14_native_f14_single_vs_multi_time.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 72bab834f476f257)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 4 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_05_step_gmsh_conformal/c14_physics/ABRIR_CASO_B.sh, cases_3d/C3D_05_step_gmsh_conformal/c14_physics/open_case_b_review.py, docs/C3D04_CASE_A_STATUS.json, docs/PROJECT_STAGE_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID e6b2e6fad05bda8f)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
