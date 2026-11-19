# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38958; classified: 38953; readable documents: 172; above read cap: 1; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 8 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 11 |
| data | 31 |
| document | 136 |
| index | 32 |
| license | 1 |
| simulation_case_file | 114 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 100 |
| test | 38 |
| web_ui | 1 |
| workflow | 22 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 3 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_granada.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_granada.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 969744308d01dba8)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 3 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_granada.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_granada.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID c46838c3f49bcdca)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
