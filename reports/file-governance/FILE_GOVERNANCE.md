# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38984; classified: 38979; readable documents: 177; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 14 |
| data | 31 |
| document | 141 |
| index | 32 |
| license | 1 |
| simulation_case_file | 117 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 108 |
| test | 44 |
| web_ui | 1 |
| workflow | 22 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 7 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d05-t0-granada-static.yml, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/native_flux/c3d05PatchFlux.C, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/analyze_t0_patch_flux.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_native_t0_patch_flux.sh, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_patch_flux.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 2dc8e194e6e51dbe)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 7 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d05-t0-granada-static.yml, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/native_flux/c3d05PatchFlux.C, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/analyze_t0_patch_flux.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_native_t0_patch_flux.sh, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_patch_flux.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 2fee470935c11130)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
