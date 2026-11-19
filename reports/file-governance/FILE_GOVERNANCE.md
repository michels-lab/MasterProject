# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38924; classified: 38919; readable documents: 167; above read cap: 1; findings: 1.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 31 |
| document | 133 |
| index | 30 |
| license | 1 |
| simulation_case_file | 107 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32613 |
| source | 91 |
| test | 35 |
| web_ui | 1 |
| workflow | 19 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 42 implementation/config paths changed since this log's last commit; examples: cases_3d/C3D_03_doctor_multiblock_pilot/tests/test_native_multiblock_static.sh, cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/tests/test_candidate_geometry.py, cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/run_v3_sweep.sh, cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/scripts/build_v3_dictionary.py, cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/scripts/summarize_trial.py, cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/tests/test_v3_diff.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 956952eebca39712)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
