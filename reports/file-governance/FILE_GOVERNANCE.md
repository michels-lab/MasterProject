# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 39005; classified: 39000; readable documents: 181; above read cap: 1; findings: 9.

## File roles

| Role | Count |
|---|---:|
| agent | 9 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 17 |
| data | 32 |
| document | 144 |
| index | 33 |
| license | 1 |
| simulation_case_file | 117 |
| simulation_input | 2683 |
| simulation_log | 3155 |
| simulation_output | 32615 |
| source | 112 |
| test | 48 |
| web_ui | 1 |
| workflow | 27 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: docs/granada/scripts/run_t0_granada.py. Next: Fix link or restore target (ID 7d85a3c81dba8e2e)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **CONFIRMED / BROKEN_RELATIVE_LINK** docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md: Missing: outside-repo. Next: Fix link or restore target (ID 2fa56a22be90f045)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_EN.md: 8 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-physics-fidelity.yml, .github/workflows/case-a-t0-native-f14.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/C14_3D_PHYSICS_CONTRACT.json, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/c14_source_fidelity.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/native_f14_coupled_runtime_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID e5d4c9f5650bd274)
- **REVIEW / POTENTIAL_UNLOGGED_CHANGES** PROJECT_AUDIT_LOG_ES.md: 8 implementation/config paths changed since this log's last commit; examples: .github/workflows/c3d04-a-c14-physics-fidelity.yml, .github/workflows/case-a-t0-native-f14.yml, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/C14_3D_PHYSICS_CONTRACT.json, cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/c14_source_fidelity.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/native_f14_coupled_runtime_smoke.py, cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/scripts/prepare_case_a_t0.py. Next: Inspect diffs and reconcile only meaningful decisions/results in the canonical log (ID d7ab4ca1df9738db)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
