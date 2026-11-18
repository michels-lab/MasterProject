# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38847; classified: 38842; readable documents: 145; above read cap: 0; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 28 |
| document | 115 |
| index | 25 |
| license | 1 |
| simulation_case_file | 100 |
| simulation_input | 2680 |
| simulation_log | 3155 |
| simulation_output | 32613 |
| source | 63 |
| test | 22 |
| web_ui | 1 |
| workflow | 19 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 1 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_03_doctor_multiblock_pilot/tests/test_native_multiblock_static.sh. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID c299d5671fec3980)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 1 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_03_doctor_multiblock_pilot/tests/test_native_multiblock_static.sh. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID acabae4a6f943b11)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
