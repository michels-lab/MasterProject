# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38992; classified: 38987; readable documents: 178; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 16 |
| data | 32 |
| document | 142 |
| index | 32 |
| license | 1 |
| simulation_case_file | 117 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 109 |
| test | 45 |
| web_ui | 1 |
| workflow | 24 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 14 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d05-foundation14-native-build.yml, .github/workflows/case-a-t0-native-f14.yml, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/run_integrated_milestone.sh, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/native_f14_dictionary_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/tests/test_integrated_case_a.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 828a2d4c4ca9590a)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 6 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d05-foundation14-native-build.yml, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/native_flux/c3d05PatchFlux.C, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_native_t0_patch_flux.sh, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_native_flux_atomic_handoff.py, cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_patch_flux.py, docs/PROJECT_STAGE_STATUS.json. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID 5765060388661e7e)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
