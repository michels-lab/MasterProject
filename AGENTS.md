# QuickCup — independent scientific review instructions

This repository is an autonomous OpenFOAM Foundation v14 scientific research project. It does **not** need FoamLens, a main coordination hub, or an external agent to run or validate simulations.

Before every substantial technical plan, code change, or Operación Granada:
1. Read [RUN_MASTER_PROTOCOL.md](RUN_MASTER_PROTOCOL.md), the [case registry](RUN_CASE_REGISTRY.csv), relevant case notes and [scientific audit log](PROJECT_AUDIT_LOG.md).
2. Check current HEAD, active PRs/claims and owner evidence. Do not collide with existing C3D/V15-V16 work or overwrite raw results.
3. Invoke the scientific skepticism and competing-hypotheses checklists in [critical review protocol](docs/granada/CRITICAL_REVIEW_ES.md); ask what would falsify the planned conclusion.
4. Distinguish observation, inference and speculation. Numerical verification, convergence, physical closure and experimental validation have separate gates.
5. Prefer the smallest decisive sensitivity or comparison; explain at least one counterargument and alternative approach before calling a method "better."
6. Do not run CFD in GitHub. Local laptop execution and actual thermocouple/CAD/JMatPro evidence are owner-dependent; never invent them.
7. Record actual tests, blocked gates, exact SHA and next action in local scientific logs. No release automatically.

Suggested manually invoked specialist agents: [scientific skeptic](.github/agents/scientific-skeptic.agent.md) and [competing hypotheses](.github/agents/experimental-counterfactual.agent.md). These profiles are not permanent running background services and cannot edit data without a reviewed change.
