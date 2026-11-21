# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 39012; classified: 39007; readable documents: 182; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 17 |
| data | 32 |
| document | 145 |
| index | 33 |
| license | 1 |
| simulation_case_file | 117 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 116 |
| test | 49 |
| web_ui | 1 |
| workflow | 28 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 6 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-native-fluid-solid.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/native_c14_fluid_solid_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_native_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/stage_c14_3d_case_a.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/tests/test_stage_c14_fluid_solid.py, docs/C3D04_CASE_A_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 9802adc9c712b52c)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 6 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-native-fluid-solid.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/native_c14_fluid_solid_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_native_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/stage_c14_3d_case_a.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/tests/test_stage_c14_fluid_solid.py, docs/C3D04_CASE_A_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 59edcd4953f6d3e2)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
