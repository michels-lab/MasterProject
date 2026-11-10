# MasterProject — auditoría de documentación viva y comandos (10 de noviembre de 2026)

**Alcance:** revisión de los documentos vivos del repositorio respecto a la evidencia de terminal de OpenFOAM Foundation 14 recibida durante el día. Esta es una **auditoría de coherencia documental**, no una validación científica, una corrida CFD o una comprobación de que los logs locales se encuentran en GitHub. Los documentos históricos se conservan con su cronología.

## Último estado real del caso 3D

| Prueba o etapa | Evidencia local y resultado | Estado |
|---|---|---|
| STL metal y molde reparado | Originales versionados; mold_repaired es una superficie cerrada | Registrado |
| Primera malla snappy | 1,505,847 celdas; 6,974 cóncavas, 23 face tets deficientes | 2 comprobaciones checkMesh fallidas |
| Segunda malla castellated nativa mm | 1,505,826 celdas; 21,353 cóncavas, 0 face tets deficientes | 1 comprobación checkMesh fallida |
| Clasificación geométrica STL | 6,959 de 6,974 defectos en la primera malla y 21,353 de 21,353 en la segunda, fuera de ambos STL | Diagnóstico, NO malla aceptada |
| Recorte `subsetMesh -cellSet materialVolume -noFields` | 1,209,777 celdas, 151.230 cm³; 15 cóncavas; 8 face-tets deficientes; 17 determinantes pequeños | 3 comprobaciones fallidas |
| `splitMeshRegions -disconnected` | `region1` probable arena: 825,994 celdas, 103.256 cm³, 3 fallos; `region2` probable metal: 383,783 celdas, 47.9735 cm³, 2 fallos | **`No interfaces to add`**; SIN interfaz térmica |
| `splitMeshRegions -cellZones 'metal'` desde original conectado | Propuesta para inspeccionar caras compartidas en otra copia | **NO ejecutada** |
| Solver 3D / comparación experimental | No se ha ejecutado solver 3D ni comprobado contacto térmico metal–arena | **SIN CFD/CHT validado** |

**Fuentes:** [registro científico con procedencia](C3D_01_ESTADO_REAL_20261110_ES.md) y [manual de comandos OpenFOAM 14](../OPENFOAM_COMMAND_MANUAL_ES.md). La última separación `-disconnected` terminó con dos componentes topológicas, **no** con dos dominios físicamente acoplados. Los volúmenes individuales aproximan los STL de referencia pero no prueban interfaces.

## Documentación viva cotejada y sincronizada

**Manuales y operación:** [manual ES](../OPENFOAM_COMMAND_MANUAL_ES.md), [manual EN](../OPENFOAM_COMMAND_MANUAL_EN.md), [selector](../OPENFOAM_COMMAND_MANUAL.md), [guía textual](../CASE_GUIDE_ES.md), [guía interactiva](../CASE_GUIDE_INTERACTIVE_ES.html), [protocolo maestro](../RUN_MASTER_PROTOCOL.md), [política de GitHub](../GITHUB_EXECUTION_POLICY.md).

**Bitácoras y estado:** [registro C3D](C3D_01_ESTADO_REAL_20261110_ES.md), [bitácora cronológica ES](../PROJECT_AUDIT_LOG_ES.md), [bitácora cronológica EN](../PROJECT_AUDIT_LOG_EN.md), [selector de bitácoras](../PROJECT_AUDIT_LOG.md), [sincronización documental](DOCUMENT_SYNC_20261110_ES.md), [identidad del proyecto](MASTERPROJECT_IDENTITY_ES.md), [índice documental](DOCUMENTATION_INDEX.md), [README principal](../README.md).

**Investigación y calidad:** [plan 2026-10-08 con adenda](../NEXT_RESEARCH_ROADMAP_ES.md), [matriz ES](../VALIDATION_MATRIX_ES.md), [matriz EN](../VALIDATION_MATRIX_EN.md), [selector de matrices](../VALIDATION_MATRIX.md), [postprocesamiento 2D](../POSTPROCESSING_FIELD_GUIDE_ES.md), [gate JMatPro](../JMATPRO_OPENFOAM_TRACEABILITY_ES.md), [gate de Plan D](granada/PLAN_D_CASE3D_01_MESH_GATE_20261021.md).

**Geometría y árbol 3D:** [índice 3D](../cases_3d/README.md), [identificador canónico](../cases_3d/case3d-01/README.md), [README técnico](../cases_3d/C3D_01_metal_mold/README.md), [STL y unidades](../cases_3d/C3D_01_metal_mold/constant/geometry/README.md) y [ruta triSurface heredada](../cases_3d/C3D_01_metal_mold/constant/triSurface/README.md).

## Normas de interpretación

1. Las notas históricas de octubre describen el estado en su fecha: **no deben reescribirse como si se hubieran ejecutado simulaciones que todavía no existían**. Se añadieron adendas recientes con enlaces al registro científico.
2. El **manual de comandos** distingue acciones ejecutadas (por ejemplo `topoSet`, `subsetMesh -cellSet`, `splitMeshRegions -disconnected`) de propuestas sin prueba (`-cellZones 'metal'`); evita comandos destructivos sobre mallas ya recortadas.
3. La bitácora automatizada `docs/audits/FILE_GOVERNANCE_LOG.md` pertenece al robot auditor, y `analysis_results/` y `cases_controlled_buoyancy/` contienen evidencia histórica. No se alteran sus datos, fechas, campos físicos, salidas ni registros de corrida.
4. La línea B/C 2D, referencia C14, propiedades JMatPro J0 y validación G1 conservan puertas abiertas según su propia evidencia. **No se actualizó `RUN_CASE_REGISTRY.csv`** a estados que no están comprobados.
5. **Sincronización Git distinta de evidencia CFD:** los commits documentales existen en `main`, pero las mallas, sets VTK y logs completos citados se mantienen en carpetas locales del investigador.
6. El [PR #33](https://github.com/michels-lab/MasterProject/pull/33) conserva **seis propuestas documentales anteriores** pendientes de reconciliar con PR #18, #19 y #28. Sus cambios **no se declaran integrados**; las adendas de estado actual se añadieron directamente a los documentos vigentes en `main`.

## Pendientes reales

**Científicos:** restaurar o generar contacto térmico emparejado metal–arena, analizar `splitMeshRegions -cellZones 'metal'` en copia de malla original, corregir fallos `checkMesh` en ambas regiones y validar volúmenes/interfaces; finalmente integrar configuración térmica y validación J0/G1 según corresponda. **No correr CFD 3D aún**.

**Documentales:** incorporar logs locales reales con identificadores/huellas para auditoría reproducible; reconciliar contenido del PR #33 antes de fusionar; revisar resultados B/C V15/V16 solo cuando haya evidencia de esas corridas y criterios de aceptación. La documentación viva de C3D ha sido actualizada; no se certifica que todos los archivos históricos del repositorio hayan sido reescritos (no sería apropiado).
