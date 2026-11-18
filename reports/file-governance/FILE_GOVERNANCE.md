# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38828; classified: 38823; readable documents: 139; above read cap: 0; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 25 |
| document | 110 |
| index | 24 |
| license | 1 |
| simulation_case_file | 99 |
| simulation_input | 2678 |
| simulation_log | 3155 |
| simulation_output | 32613 |
| source | 59 |
| test | 19 |
| web_ui | 1 |
| workflow | 19 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 7 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py, cases_3d/C3D_02_metal_sand_clean/scripts/native_checkmesh_report.sh, cases_3d/C3D_02_metal_sand_clean/scripts/stage_c14_materials.sh, cases_3d/C3D_02_metal_sand_clean/tests/test_native_allmesh_static.sh, cases_3d/C3D_02_metal_sand_clean/tests/test_native_checkmesh_report.sh, cases_3d/C3D_02_metal_sand_clean/tests/test_native_stage_c14.sh. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 572cdd81057128eb)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 7 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py, cases_3d/C3D_02_metal_sand_clean/scripts/native_checkmesh_report.sh, cases_3d/C3D_02_metal_sand_clean/scripts/stage_c14_materials.sh, cases_3d/C3D_02_metal_sand_clean/tests/test_native_allmesh_static.sh, cases_3d/C3D_02_metal_sand_clean/tests/test_native_checkmesh_report.sh, cases_3d/C3D_02_metal_sand_clean/tests/test_native_stage_c14.sh. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 54c29725a8e4a7a8)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
