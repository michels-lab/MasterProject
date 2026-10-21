# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38769; classified: 38764; readable documents: 127; above read cap: 0; findings: 2.

## File roles

| Role | Count |
|---|---:|
| agent | 7 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 19 |
| document | 100 |
| index | 22 |
| license | 1 |
| simulation_case_file | 98 |
| simulation_input | 2667 |
| simulation_log | 3151 |
| simulation_output | 32613 |
| source | 42 |
| test | 12 |
| web_ui | 1 |
| workflow | 18 |

## Findings (human review required)

- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 3 implementation/config paths changed since this log's last commit; examples: .github/workflows/granada-file-steward-head-proof-pr.yml, tools/file_governance_audit_proof.py, tools/test_file_governance_audit_proof.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 989bdfca4794879e)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 3 implementation/config paths changed since this log's last commit; examples: .github/workflows/granada-file-steward-head-proof-pr.yml, tools/file_governance_audit_proof.py, tools/test_file_governance_audit_proof.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID a3b3803ea99dfd59)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
