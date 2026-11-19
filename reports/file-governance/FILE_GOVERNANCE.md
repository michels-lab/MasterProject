# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38884; classified: 38879; readable documents: 156; above read cap: 0; findings: 1.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 31 |
| document | 124 |
| index | 27 |
| license | 1 |
| simulation_case_file | 105 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32613 |
| source | 74 |
| test | 26 |
| web_ui | 1 |
| workflow | 19 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 16 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_03_doctor_multiblock_pilot/tests/test_native_multiblock_static.sh, cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_blockmesh_topology.py, cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py, cases_3d/C3D_04_rounded_multiblock_pilot/scripts/measure_interface_area.py, cases_3d/C3D_04_rounded_multiblock_pilot/tests/test_rounded_multiblock_static.sh, cases_3d/C3D_05_step_gmsh_conformal/scripts/audit_underdetermined_topology.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID f1e2a353ce265e25)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
