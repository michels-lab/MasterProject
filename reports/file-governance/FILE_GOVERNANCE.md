# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38761; classified: 38757; readable documents: 126; above read cap: 0; findings: 4.

## File roles

| Role | Count |
|---|---:|
| agent | 6 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 19 |
| document | 99 |
| index | 22 |
| license | 1 |
| simulation_case_file | 98 |
| simulation_input | 2667 |
| simulation_log | 3151 |
| simulation_output | 32613 |
| source | 41 |
| test | 10 |
| web_ui | 1 |
| workflow | 16 |

## Findings (human review required)

- **REVIEW / DUPLICATE_DOC_CONTENT** cases_controlled_buoyancy/B11_energy2_test/CASE_VARIANT.md: Identical tracked text: cases_controlled_buoyancy/B11_energy2_test/CASE_VARIANT.md, cases_controlled_buoyancy/B11_topFixedFlux_airGapOF14/CASE_VARIANT.md. Next: Confirm aliases or translated/historical copies before consolidation (ID 4790b4f6be1b7e0f)
- **REVIEW / DUPLICATE_DOC_CONTENT** cases_controlled_buoyancy/C11_energy2_test/CASE_VARIANT.md: Identical tracked text: cases_controlled_buoyancy/C11_energy2_test/CASE_VARIANT.md, cases_controlled_buoyancy/C11_topFixedFlux_airGapOF14/CASE_VARIANT.md. Next: Confirm aliases or translated/historical copies before consolidation (ID c4728d9d269368a5)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 20 implementation/config paths changed since this log's last commit; examples: .github/workflows/file-steward-domain-pr-validation.yml, .github/workflows/fs-c01-case-integrity.yml, .github/workflows/granada-bfs01-vof.yml, .github/workflows/granada-boundary-spatial.yml, .github/workflows/granada-energy-phase-evidence.yml, .github/workflows/granada-mold-bilateral-readiness.yml. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 2d0f730d0d7c1885)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 20 implementation/config paths changed since this log's last commit; examples: .github/workflows/file-steward-domain-pr-validation.yml, .github/workflows/fs-c01-case-integrity.yml, .github/workflows/granada-bfs01-vof.yml, .github/workflows/granada-boundary-spatial.yml, .github/workflows/granada-energy-phase-evidence.yml, .github/workflows/granada-mold-bilateral-readiness.yml. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 40be4049dd89fea4)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
