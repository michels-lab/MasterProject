# MasterProject — control de sincronización documental (10-11-2026)

> **Integración Git al 2026-11-10:** 19 documentos de este bloque fueron incorporados a `main` mediante commit `641d3a2d97bc52aac0c4f8f5c8a77670ed4d7c59`. **Seis documentos adicionales están modificados pero pendientes de fusionar** en [PR #33](https://github.com/michels-lab/MasterProject/pull/33) por colisiones con PRs #18, #19 y #28: `README.md`, `docs/DOCUMENTATION_INDEX.md`, `NEXT_RESEARCH_ROADMAP_ES.md`, `PROJECT_AUDIT_LOG_ES.md`, `PROJECT_AUDIT_LOG_EN.md`, `cases_3d/C3D_01_metal_mold/README.md`. **No presentar esas seis ediciones como disponibles en `main` todavía.**


## Alcance del bloque

Objetivo: mantener coherentes los **documentos vivos** de MasterProject con los STL originales publicados, reparación de molde y primera malla 3D ejecutada en laptop el 10-11-2026. Fuente primaria actual: terminal del investigador + logs geométricos versionados; los logs completos del primer snappy están pendientes de archivar. No sustituye datos de CFD ni pruebas experimentales.

| Familia documental | Archivos revisados y ajustados |
|---|---|
| Portada e inventarios | `README.md`, `docs/DOCUMENTATION_INDEX.md`, `docs/MASTERPROJECT_IDENTITY_ES.md` |
| Manuales y capacitación | `OPENFOAM_COMMAND_MANUAL.md`, `OPENFOAM_COMMAND_MANUAL_ES.md`, `OPENFOAM_COMMAND_MANUAL_EN.md`, `CASE_GUIDE_ES.md`, `CASE_GUIDE_INTERACTIVE_ES.html` |
| Protocolo e investigación | `RUN_MASTER_PROTOCOL.md`, `NEXT_RESEARCH_ROADMAP_ES.md`, `JMATPRO_OPENFOAM_TRACEABILITY_ES.md`, `POSTPROCESSING_FIELD_GUIDE_ES.md`, `GITHUB_EXECUTION_POLICY.md` |
| Bitácoras y matriz | `PROJECT_AUDIT_LOG.md`, `PROJECT_AUDIT_LOG_ES.md`, `PROJECT_AUDIT_LOG_EN.md`, `VALIDATION_MATRIX.md`, `VALIDATION_MATRIX_ES.md`, `VALIDATION_MATRIX_EN.md` |
| Modelo tridimensional | `cases_3d/README.md`, `cases_3d/case3d-01/README.md`, `cases_3d/C3D_01_metal_mold/README.md`, `docs/granada/PLAN_D_CASE3D_01_MESH_GATE_20261021.md` |
| Evidencia nueva | `docs/C3D_01_ESTADO_REAL_20261110_ES.md` (registro fuente de esta adenda) |

**Limitación de alcance:** no se han reescrito indiscriminadamente cientos de notas históricas por caso, informes originales, registros brutos o resultados numéricos. Tales artefactos se conservan como fotografías fechadas. `RUN_CASE_REGISTRY.csv` sigue con 34 registros de la campaña 2D, en espera de reconciliación sistemática de los cinco casos con evidencia local subida de octubre; cambiar estado a `RUN_VERIFIED` por un `End` o 10 s de sonda no estaría justificado. La prueba 3D **no añade** un CFD B/C verificado. El manifiesto geométrico original `geometry_reference.json` conserva los hashes CAD fuente y no se sobreescribe para aparentar validación de malla.

## Hallazgos normalizados

- El nombre canónico del repositorio es `MasterProject`; los comandos operativos actuales usan `~/OpenFOAM/MasterProject` sin renombrar casos y artefactos históricos.
- El metal y el molde originales, más el molde reparado, están en GitHub público; geometría cerrada sin autointersecciones en metal y molde reparado.
- El `snappyHexMesh` ejecutado en una carpeta **local ajena al repo** produjo 1,505,847 celdas y 2 fallos `checkMesh`. Malla experimental **rechazada**. Un componente conectado y un `cellZone metal` sin medir no demuestran interfaz conjugada.
- Primer ensayo utilizó COPIAS temporalmente escaladas; la convención preferida para futuros ensayos es STL original en mm + `units [mm];` en diccionarios nativos Foundation 14, todavía pendiente de ejecutar bajo ese esquema. El generador `snappyHexMeshConfig` no admite `-case`.
- **J0/JMatPro, G1/experimento, balance térmico 3D, separación metal/arena y convergencia de malla permanecen abiertos.**

## Colisiones y reglas de integración

A la fecha de revisión existen PRs abiertos #18 (posee `NEXT_RESEARCH_ROADMAP_ES.md`, `PROJECT_AUDIT_LOG_ES.md`, `PROJECT_AUDIT_LOG_EN.md` y README técnico C3D), #19 (`README.md`) y #28 (`docs/DOCUMENTATION_INDEX.md`). Su historial debe reconciliarse antes de integrar las mismas rutas; no sobrescribir ramas ajenas ni afirmar que sus cambios se fusionaron. PRs #20 y #32 también permanecen independientes.

La documentación nueva se presenta como actualización **aditiva y fechada**, manteniendo el contexto histórico. Las comprobaciones CI solo validan estructura, nunca mallado OpenFOAM de GitHub. Una integración posterior debe revisar `main` y confirmar CI sobre el SHA exacto.

## Próximas actualizaciones documentales condicionadas a evidencia

1. Cuando se archiven `log.blockMesh`, `log.snappyHexMesh`, `log.checkMesh.final` y diccionario real con SHA, confirmar los números transcritos y publicar resumen reproducible de mallado local.
2. Al validar regiones y calidad con otra prueba, actualizar el registro técnico y recién entonces el estado científico; sin cambiar arbitrariamente una alerta en éxito.
3. Reconciliar las cinco corridas B11/B15/B16/C15/C16 y actualizar `RUN_CASE_REGISTRY.csv`, notas `CASE_NOTES`, matriz y bitácoras conjuntamente, si los criterios de ejecución y análisis se cumplen.
