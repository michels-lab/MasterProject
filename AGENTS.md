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

## FS-C05 / Operación Granada — una aceptación nativa por paquete científico (2026-11-19)

Por instrucción expresa del investigador, queda prohibida la entrega fragmentada de scripts de QA por variable y el traslado al usuario del trabajo que puede cubrir GitHub Actions. Antes de pedir cualquier paso en WSL OpenFOAM 14:

1. **Revisar en conjunto** dependencias, sintaxis FoamFoundation14, mallas, mapeos, esquemas, BC, función de análisis y reportes; contrastar con las fuentes oficiales cuando exista incertidumbre.
2. **Probar automáticamente** con pruebas negativas y de integración *en archivos* el mismo pipeline que usará el investigador. No confundir mocks o CI verde con ejecución CFD nativa.
3. **Consolidar** toda instrumentación viable en un solo orquestador de una copia desechable; una sola ejecución nativa debe producir logs, campos, diagnósticos y un reporte de aceptación. Evitar repetir dos pasos cada vez que falta una variable de salida.
4. **Mostrar un único comando de aceptación para todo el bloque**, nunca una lista de `unittest`, `foamPostProcess`, `foamMultiRun` y scripts aislados para que el usuario haga ingeniería de integración. Sólo solicitar acciones adicionales si el log nativo aporta un error imposible de reproducir o inspeccionar desde las fuentes y CI.
5. **Etiquetas de evidencia estrictas**: `CANDIDATE`, `CI_ONLY`, `NATIVE_RAN`, `FIELDS_MEASURED`, `FLUX_MEASURED`, `MASS_BALANCE_VALIDATED`, `ENERGY_BALANCE_VALIDATED` son hechos distintos. No llamar a un flujo local ni a masa inventariada prueba de balance global; no llamar `alpha.metal` fracción solidificada.
6. **No incrementar el transitorio a segundos físicos** sin cerrar entradas/salidas del gas, entalpía de hierro y aire, densidades, términos de presión y calor de las paredes; conservar la pila aprobada FS-C04/FS-C05, las propiedades de cribado y el unresolved CAD/support con su etiqueta de pendiente.
7. **Bitácoras**: actualizar el README del caso/PR y el Main Repo como índice de continuidad, usando IDs exactos de commit y CI. Una corrida pendiente en WSL sigue `NATIVE_PENDING` aunque CI finalice con éxito.

Estos puntos son el contrato de no regresión contra el antipatrón de muchas pruebas manuales observado en el desarrollo FS-C05.
