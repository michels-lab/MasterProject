## MANDATORY — Concurrent WSL CFD source isolation (2026-11-23)

The investigator runs three independent OpenFOAM projects simultaneously: **C3D04 Case A**, **C3D05 Case B**, and **FS contraction**. No agent may issue or silently execute a generic git pull/checkout/merge/reset/clean on ~/OpenFOAM/MasterProject or on a worktree that could be supplying a live solver. **Always use project-specific development worktrees**, and preserve immutable OUT-OF-TREE native solver inputs/results. A git pull on main updates tracked source and tracked postProcessing for ALL cases, not just the named case.

Approved WSL development layout: A=~/OpenFOAM/C3D04_A_WORKTREE (work/c3d04-a-isolated); B=~/OpenFOAM/C3D05_B_WORKTREE (work/c3d05-b-isolated); contraction=~/OpenFOAM/FS_C02_WORKTREE (existing research/fs-c02-metal-air-vof-20261117). The existing FS worktree and FS_C01/05/06/07_RUNS must NEVER be reset, moved, pruned, recreated or merged into A/B. **FS_C02_WORKTREE may legitimately be detached HEAD via git switch --detach FETCH_HEAD**; accept it read-only if ancestry to origin/research/fs-c02-metal-air-vof-20261117 and the committed FS-C06 source marker verify. NEVER reattach or switch it just to satisfy the installer. Source isolation does not authorize re-running CFD or changing C14/material/mesh physics.

The single approved fail-closed one-shot installer is tools/isolate_active_openfoam_cases.py. **It creates only missing A/B worktrees with --no-track and verifies the existing contraction worktree; --plan is strictly read-only.** Safest initial execution is via git fetch plus git show origin/main:... | python3 - (see docs/WSL_CONCURRENT_CASE_WORKTREES_20261123_ES.md) without pulling the live checkout. If the historical FS checkout is missing/mismatched, STOP; never fabricate its state. CI tests cannot attest the actual laptop or an active CFD process. Every future CFD command must specify its case-specific worktree AND an independent native-run destination; never update a branch during a solver that reads it. If status unknown, use fetch+diff (non-checkout) and not pull.

---

## Mandatory project contract — PROJECT_PROGRESS_CONTRACT_20261119

For ALL MasterProject 2D/3D cases, consult `docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md` and `docs/PROJECT_STAGE_STATUS.json` before any work and report case, stage, progress N/Y with properly bounded %, evidence/blocker and next full integrated milestone in EVERY update. No iterative one-off WSL tests or fake validation; integrate root-cause fixes, internal tests and synchronized ES/EN logs. Preserve accepted mesh/STEP. Only user's laptop runs OpenFOAM. This overrides any older piecemeal flow.

## MANDATORY project reporting and integrated delivery rule (2026-11-19)

**Direct instruction from the project owner, persistent across conversations and agents.** Never omit project **stage and progress** when responding about MasterProject. Always inspect the owning case status first and explicitly say "**Etapa N/Total · Avance D/Total = P% de hitos**", what was concretely done, blockers, and the next integrated milestone. Explain the metric; it is NOT a percent of physical validation or time remaining. For **Caso A C3D-04**, the canonical machine-readable register is [`docs/C3D04_CASE_A_STATUS.json`](docs/C3D04_CASE_A_STATUS.json), and its mandatory scoped instructions live in [`cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md`](cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md). Other cases must use their own truthful register; NEVER borrow Caso A's percentage.

**Do NOT impose serial one-issue/one-new-script/one-WSL-command feedback loops** or rerun completed geometry investigations. Deliver full engineering milestones with integrated internal QA, one optional end-to-end execution only when needed, and a self-diagnostic, preserving all native scientific evidence. A test or code commit is NOT the same as an OpenFOAM run or a validated model. This requirement supersedes older text suggesting a single terminal command *per small check*: the intended unit is a **meaningful integrated phase**, not a micro-test.

This is a release/reporting contract: omitting the stage/progress or reverting to piecemeal testing is a project delivery defect, requiring correction of the process rather than apology alone.

## Mandatory agent prevention — root-cause and evidence (2026-10-21)

Owner instruction: do not merely correct a recurring mistake; improve the agent/process rule and add a regression/verification that catches the same failure again. Applicable to ALL assistance, maintenance, QA, audits and task-automation roles; an agent instruction is not evidence that a separate AI agent has executed. For shared software-source governance see https://github.com/michels-lab/Michel-Software-Standards/blob/main/standards/AGENT_RECURRENCE_PREVENTION_STANDARD.md. This repository remains its OWN source of truth; do not move sensitive or product-specific contents across repo boundaries.

1. Before acting, inspect the latest repository HEAD, source notes, pending branches/claims and current evidence. Never infer completion from old summaries, a different repo's status or a green workflow on another SHA.
2. Root cause: reproduce or precisely identify the recurring mistake, its owning file/process, and the previous control that missed it. Correct that cause; add a negative regression/static check when meaningful. Documentation alone does not resolve operational or functional problems.
3. Truth and provenance: give dates and actual citations/source paths; separate observed facts, estimates, suggestions, decisions, real outcomes and unknowns. Do not invent tests, actions, user approvals or background jobs. Reconcile README, owning project log/bitácora and any shared index after change.
4. Scientific safeguards: never fabricate OpenFOAM cases, convergence, real temperatures, physical measurements, solver output or experimental validation; numerical reproducibility and actual local runs are separate from static checks.
5. Respect repository purpose and access controls. No paid services/subscription, new connectors, deployments, provider/account modifications, hidden data uploads or relationship/content actions unless explicitly approved. Missing permission or validation is BLOCKED/PENDING, not PASS.
6. For multi-repo operations, report the whole result in ONE consolidated user-facing summary including actual modifications, evidence, blockers and next corrective owner; do not force the user to open every repository just to know what happened.

This is a preventive process contract. Existing project-specific agent rules below remain in force.

# Local agent entrypoint

Read README.md and the owning project log; keep this repository's scientific/personal scope separate. Agent behavior must be evidenced; no hidden execution or guessed results.
