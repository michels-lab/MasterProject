# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38779; classified: 38774; readable documents: 130; above read cap: 0; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 22 |
| document | 103 |
| index | 22 |
| license | 1 |
| simulation_case_file | 98 |
| simulation_input | 2667 |
| simulation_log | 3155 |
| simulation_output | 32613 |
| source | 42 |
| test | 12 |
| web_ui | 1 |
| workflow | 18 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 1 implementation/config paths changed since this log's last commit; examples: CASE_GUIDE_INTERACTIVE_ES.html. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 38e9781209aab42a)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 1 implementation/config paths changed since this log's last commit; examples: CASE_GUIDE_INTERACTIVE_ES.html. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID a81977bce1235f5b)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
