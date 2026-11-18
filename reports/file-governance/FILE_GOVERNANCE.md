# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38838; classified: 38833; readable documents: 141; above read cap: 0; findings: 4.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 27 |
| document | 112 |
| index | 24 |
| license | 1 |
| simulation_case_file | 99 |
| simulation_input | 2678 |
| simulation_log | 3155 |
| simulation_output | 32613 |
| source | 63 |
| test | 21 |
| web_ui | 1 |
| workflow | 19 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/C3D_02_ABLACION_STL_V2_20261118_ES.md: Missing: docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md. Next: Fix link or restore target (ID 54c8a52e427f3e0f)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/C3D_02_ABLACION_STL_V2_20261118_ES.md: Missing: docs/C3D_02_MESH_TRIAL_REGISTRY_20261118.csv. Next: Fix link or restore target (ID d2ed3c3c420f4b22)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 13 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py, cases_3d/C3D_02_metal_sand_clean/scripts/check_stl_v2.sh, cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_stl_v2_zones.sh, cases_3d/C3D_02_metal_sand_clean/scripts/native_checkmesh_report.sh, cases_3d/C3D_02_metal_sand_clean/scripts/native_interface_audit.sh, cases_3d/C3D_02_metal_sand_clean/scripts/run_stl_v2_ablation.sh. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 34898be3f167929b)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 13 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py, cases_3d/C3D_02_metal_sand_clean/scripts/check_stl_v2.sh, cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_stl_v2_zones.sh, cases_3d/C3D_02_metal_sand_clean/scripts/native_checkmesh_report.sh, cases_3d/C3D_02_metal_sand_clean/scripts/native_interface_audit.sh, cases_3d/C3D_02_metal_sand_clean/scripts/run_stl_v2_ablation.sh. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 4be42a49369ce8c0)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
