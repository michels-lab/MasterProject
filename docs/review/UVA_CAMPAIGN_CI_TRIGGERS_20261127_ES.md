# Uva — disparadores y gobernanza de CI de campañas 200 s

Corte inmutable: `179d3603e1705b2c5a1d2827092fefea1e0b71fd`. 27-11-2026. Auditoría estática, no CFD.

## Hallazgos y corrección propuesta en este árbol

- Adaptive importa transfer y el test importa el módulo compact y sus fixtures; los cambios de esas dependencias no activaban su workflow. Compact tampoco reaccionaba a cambios de sus fixtures.
- Se amplían los disparadores de adaptive, compact y transfer con rutas explícitas, pull_request a main y workflow_dispatch. Se conservan intactos jobs, comandos, permisos y sparse-checkout. No se añade instalación ni ejecución CFD.
- QuickCup post-push omite audit_postprocessing_config.py en PR y dos tests invocados en los filtros push/PR; queda abierto para bloque independiente.
- GITHUB_EXECUTION_POLICY.md prohíbe absolutamente CFD en CI mientras documenta smoke F14 sintético anterior. No se amplía autorización; delimitar formalmente histórico, pruebas sintéticas autorizadas y ejecución productiva exclusiva de WSL.
- File Steward puede rebasar el informe sobre un HEAD posterior al escaneo; preservar la atribución al SHA escaneado, no presentar informe como prueba del nuevo HEAD. Revisar auditor y proof en otro bloque.

## Evidencia y límites

16 recibos nuevos del corte de entrada; los blobs nuevos requieren verificación posterior. Revisión focalizada de imports no equivale a auditoría íntegra de código. No se ejecutaron pruebas ni se verificaron resultados CI en esta revisión. Caso B: etapa 3/7, 2/7 hitos (29% técnico) según docs/PROJECT_STAGE_STATUS.json; sin cambio de hito, malla, material, resultados, WSL o validación. No hay porcentaje global de auditoría. PR #79 FS-C08 continúa independiente.
