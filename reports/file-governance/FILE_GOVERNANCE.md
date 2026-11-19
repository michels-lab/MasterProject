# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38954; classified: 38949; readable documents: 171; above read cap: 1; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 8 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 11 |
| data | 31 |
| document | 135 |
| index | 32 |
| license | 1 |
| simulation_case_file | 114 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 99 |
| test | 37 |
| web_ui | 1 |
| workflow | 21 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 4 implementation/config paths changed since this log's last commit; examples: .github/workflows/case-a-t0-stage-contract.yml, .github/workflows/project-delivery-contract.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/run_integrated_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID f2244a47be07a56a)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 4 implementation/config paths changed since this log's last commit; examples: .github/workflows/case-a-t0-stage-contract.yml, .github/workflows/project-delivery-contract.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/run_integrated_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID f4033b1767b156c2)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
