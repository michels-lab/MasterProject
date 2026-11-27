# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 42925; classified: 42920; readable documents: 245; above read cap: 1; findings: 10.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 33 |
| data | 39 |
| document | 204 |
| index | 37 |
| license | 1 |
| simulation_case_file | 141 |
| simulation_input | 2683 |
| simulation_log | 3264 |
| simulation_output | 36203 |
| source | 179 |
| test | 81 |
| unknown | 1 |
| web_ui | 1 |
| workflow | 38 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 17 implementation/config paths changed since this log's last commit; examples: .github/workflows/c14-three-model-comparison.yml, analysis_tools/check_run_registry.py, analysis_tools/compare_c14_three_models.py, analysis_tools/full_campaign_audit.py, analysis_tools/test_compare_c14_three_models.py, cases_3d/C3D_05_step_gmsh_conformal/c14_physics/analyze_existing_case_b_c14_metal_mass_phi.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 756dec5822a829e9)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 17 implementation/config paths changed since this log's last commit; examples: .github/workflows/c14-three-model-comparison.yml, analysis_tools/check_run_registry.py, analysis_tools/compare_c14_three_models.py, analysis_tools/full_campaign_audit.py, analysis_tools/test_compare_c14_three_models.py, cases_3d/C3D_05_step_gmsh_conformal/c14_physics/analyze_existing_case_b_c14_metal_mass_phi.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID d20baf27e40e7d09)
- **REVIEW / UNKNOWN_PURPOSE** docs/review/FILE_REVIEW_LEDGER.jsonl: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 70bd3363abfdf819)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
