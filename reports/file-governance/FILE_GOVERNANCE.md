# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 42879; classified: 42874; readable documents: 233; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 21 |
| data | 37 |
| document | 194 |
| index | 35 |
| license | 1 |
| simulation_case_file | 141 |
| simulation_input | 2683 |
| simulation_log | 3264 |
| simulation_output | 36203 |
| source | 167 |
| test | 76 |
| web_ui | 1 |
| workflow | 36 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 4 implementation/config paths changed since this log's last commit; examples: docs/C3D04_CASE_A_STATUS.json, docs/PROJECT_STAGE_STATUS.json, tools/run_adaptive_campaign_200s.py, tools/transfer_campaign_200s.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 57cb2219a47e2852)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 4 implementation/config paths changed since this log's last commit; examples: docs/C3D04_CASE_A_STATUS.json, docs/PROJECT_STAGE_STATUS.json, tools/run_adaptive_campaign_200s.py, tools/transfer_campaign_200s.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID c103cfa3cf5bb31b)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
