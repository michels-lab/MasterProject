# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 39088; classified: 39083; readable documents: 206; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 17 |
| data | 32 |
| document | 168 |
| index | 34 |
| license | 1 |
| simulation_case_file | 119 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 141 |
| test | 69 |
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
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 17 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-native-fluid-solid.yml, .github/workflows/c3d04-a-c14-postprocessing-parity.yml, .github/workflows/c3d05-b-c14-native-fluid-solid-q.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/probe_c14_native_f14_single_vs_multi_time.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_grouped_native_recovery.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/tests/test_c14_f14_single_vs_multi_time_probe.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 740a76e7b31cbec7)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 3 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_05_step_gmsh_conformal/c14_physics/run_existing_case_b_c14_native_flux.py, cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_native_flux.py, docs/PROJECT_STAGE_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID f192e0f3afc0d25a)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
