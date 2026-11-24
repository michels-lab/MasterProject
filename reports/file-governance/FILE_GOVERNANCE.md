# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 39090; classified: 39085; readable documents: 206; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 17 |
| data | 32 |
| document | 168 |
| index | 34 |
| license | 1 |
| simulation_case_file | 119 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 142 |
| test | 70 |
| web_ui | 1 |
| workflow | 33 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 19 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-native-fluid-solid.yml, .github/workflows/c3d04-a-c14-postprocessing-parity.yml, .github/workflows/c3d05-b-c14-native-fluid-solid-q.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/continue_c14_stage07_grouped_evidence.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/probe_c14_native_f14_single_vs_multi_time.py, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_grouped_native_recovery.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 4326180a87dea7e7)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 1 implementation/config paths changed since this log's last commit; examples: docs/C3D04_CASE_A_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 0be9242e70c28482)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
