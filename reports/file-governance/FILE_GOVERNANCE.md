# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38988; classified: 38983; readable documents: 177; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 15 |
| data | 32 |
| document | 141 |
| index | 32 |
| license | 1 |
| simulation_case_file | 117 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 109 |
| test | 44 |
| web_ui | 1 |
| workflow | 23 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 7 implementation/config paths changed since this log's last commit; examples: .github/workflows/case-a-t0-native-f14.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/run_integrated_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/native_f14_dictionary_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py, docs/C3D04_CASE_A_STATUS.json, docs/PROJECT_STAGE_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID ccca73deb839188e)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 7 implementation/config paths changed since this log's last commit; examples: .github/workflows/case-a-t0-native-f14.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/run_integrated_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/native_f14_dictionary_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py, docs/C3D04_CASE_A_STATUS.json, docs/PROJECT_STAGE_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 6ca2bae143c0b940)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
