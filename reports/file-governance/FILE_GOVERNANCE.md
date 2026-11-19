# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38964; classified: 38959; readable documents: 173; above read cap: 1; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 8 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 13 |
| data | 31 |
| document | 137 |
| index | 32 |
| license | 1 |
| simulation_case_file | 115 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 101 |
| test | 39 |
| web_ui | 1 |
| workflow | 22 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 11 implementation/config paths changed since this log's last commit; examples: .github/workflows/case-a-t0-stage-contract.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/C14_PARAMETER_BASELINE.json, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/T0_INPUTS.json, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/c14_numerical_reference.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 55d873cdc0debeed)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 6 implementation/config paths changed since this log's last commit; examples: .github/workflows/case-a-t0-stage-contract.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/c14_numerical_reference.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/prepare_t0.py, docs/PROJECT_STAGE_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 45c32ecd2533d349)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
