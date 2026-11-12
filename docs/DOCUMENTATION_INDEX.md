> **Estado 12-11-2026:** primera malla local C3D-02 rechazada, 242.130 cm³ / 589,701 celdas / 2 checks fallidos. [Resultado y decisiones](C3D_02_MALLADO_INICIAL_20261112_ES.md) · [Script de diagnóstico sin remallar](../cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_mesh_readonly.sh). No confundir configuración fuente con solver 3D verificado.

> **Nuevo 12-11-2026:** [Guía de primer mallado físico C3D-02](C3D_02_MALLADO_INICIAL_20261112_ES.md), con comando único, selección `insidePoints`, prueba de calidad exhaustiva y condiciones de aceptación. **No confundir candidato no ejecutado con resultados.**

> **12-11-2026:** [Reinicio de C3D y consolidación de pruebas](C3D_REINICIO_20261112_ES.md) · [Lecciones y comandos verificables de OpenFOAM 14](OPENFOAM14_LECCIONES_C3D_20261112_ES.md) · [Nuevo caso fuente 3D](../cases_3d/C3D_02_metal_sand_clean/README.md). Las notas fechadas 10-11 se conservan como evidencia histórica; las actualizaciones posteriores tienen prioridad de estado.

# MasterProject — índice de documentación científica

> **Estado científico actualizado, 10-11-2026 — C3D-01:** recorte local metal + arena: **1,209,777 celdas; 151.230 cm³; 15 celdas cóncavas, 8 face-tets deficientes, 17 celdas de determinante pequeño; 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` separó `region1` (probable arena, **825,994 celdas; 103.256 cm³; 3 fallos**) y `region2` (probable metal, **383,783 celdas; 47.9735 cm³; 2 fallos**); **`No interfaces to add`**. **Sin interfaz CHT, sin CFD 3D ni malla aprobada.** El ensayo `-cellZones 'metal'` aún **NO** se ejecutó. [Evidencia](C3D_01_ESTADO_REAL_20261110_ES.md) · [Manual](../OPENFOAM_COMMAND_MANUAL_ES.md).


Este índice organiza la documentación **sin mover ni reemplazar** archivos existentes. Este proyecto es completamente independiente de FoamLens y de cualquier repositorio coordinador.

- [Identidad canónica de MasterProject y conservación de nombres de casos](MASTERPROJECT_IDENTITY_ES.md)

- [Auditoría de documentación viva al 10-11-2026](DOCUMENTATION_AUDIT_20261110_ES.md) — cobertura real, comandos registrados, discrepancias y límites de evidencia

## Empezar / operación
- [README](../README.md) — descripción y estado por confirmar en cada actualización
- [RUN_MASTER_PROTOCOL](../RUN_MASTER_PROTOCOL.md) — reglas obligatorias antes/después de cada corrida **local**
- [Manual de comandos y selector ES/EN](../OPENFOAM_COMMAND_MANUAL.md)
- [Manual práctico español](../OPENFOAM_COMMAND_MANUAL_ES.md)
- [OpenFOAM command manual English](../OPENFOAM_COMMAND_MANUAL_EN.md)
- [Guía técnica de casos](../CASE_GUIDE_ES.md)
- [Guía interactiva](../CASE_GUIDE_INTERACTIVE_ES.html)

## Física, propiedades y validación
- [Guía de campos/posproceso](../POSTPROCESSING_FIELD_GUIDE_ES.md)
- [Trazabilidad JMatPro](../JMATPRO_OPENFOAM_TRACEABILITY_ES.md)
- [Matriz de validación ES/EN](../VALIDATION_MATRIX.md)
- [Hoja de ruta física](../NEXT_RESEARCH_ROADMAP_ES.md)
- [Casos tridimensionales](../cases_3d/README.md)

## Registro, resultados y bitácoras
- [Inventario de casos CSV](../RUN_CASE_REGISTRY.csv) — estados físicos/numericos independientes
- [Bitácora auditada ES/EN](../PROJECT_AUDIT_LOG.md) — registro histórico canónico
- [Granada](../.michelslab/GRANADA.md) — protocolo local de continuación
- [Granada coordinación 2026-10-20](granada/GRANADA_GRANDE_GOVERNANCE_20261020.md)
- [Resumen de campaña histórica](../analysis_results/full_campaign_audit/README.md)
- [Evidencia V15/V16 2026-10-20](../analysis_results/granada_v15v16_postrun_20261020/summary.md)
- [Granada: auditoría de procedencia B11/C11 energy2 y documentos duplicados](granada/B11_C11_ENERGY2_DOCUMENTATION_AUDIT_20261021.md) — hallazgo documental, no validación CFD

## Relación voluntaria con otros proyectos
- [FoamLens](https://github.com/michels-lab/FoamLens) es un **visor genérico e independiente**. No es requisito para resolver, validar o publicar este trabajo.
- [Contrato público de límites](OPENFOAM_ECOSYSTEM.md). La coordinación externa nunca gobierna los cálculos ni sustituye este registro.

**Norma:** cambios científicos aquí, manuales científicos aquí, resultados reales aquí. Un informe de GitHub/CI no equivale a validación experimental. Para reubicar un documento debe existir un inventario de referencias y una migración revisada por separado.
- [Granada: constancia de acceso coordinador en modo lectura](granada/OPENFOAM_HUB_READ_ACCESS_20261021.md)
