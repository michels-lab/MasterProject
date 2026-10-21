# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38760; classified: 38756; readable documents: 126; above read cap: 0; findings: 3.

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
| workflow | 15 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** PROJECT_AUDIT_LOG.md: Missing: docs/granada/V15_V16_SOURCE_EVIDENCE_20261020.md. Next: Fix link or restore target (ID 7aa831f782018e41)
- **REVIEW / DUPLICATE_DOC_CONTENT** cases_controlled_buoyancy/B11_energy2_test/CASE_VARIANT.md: Identical tracked text: cases_controlled_buoyancy/B11_energy2_test/CASE_VARIANT.md, cases_controlled_buoyancy/B11_topFixedFlux_airGapOF14/CASE_VARIANT.md. Next: Confirm aliases or translated/historical copies before consolidation (ID 4790b4f6be1b7e0f)
- **REVIEW / DUPLICATE_DOC_CONTENT** cases_controlled_buoyancy/C11_energy2_test/CASE_VARIANT.md: Identical tracked text: cases_controlled_buoyancy/C11_energy2_test/CASE_VARIANT.md, cases_controlled_buoyancy/C11_topFixedFlux_airGapOF14/CASE_VARIANT.md. Next: Confirm aliases or translated/historical copies before consolidation (ID c4728d9d269368a5)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
