# Bitácora independiente de Operación Granada — QuickCup C3D-01

**Corte: 2026-10-19.** Esta bitácora acompaña el bloque de documentación y QA científico. No modifica la bitácora madre ES/EN, que está ocupada en el PR #18; integrar y reconciliar posteriormente cuando no haya colisiones.

## Inspección inicial
- \`main\`: \`1f684ba01fa7e02aaeda9c27b4b9e0e8138dbc22\` en el momento de abrir el bloque; verificar vigencia de HEAD al integrar.
- PR **#18, borrador**, \`research/c3d01-refinement-max05mm-20261019\`: toca \`NEXT_RESEARCH_ROADMAP_ES.md\`, \`PROJECT_AUDIT_LOG_ES.md\`, \`PROJECT_AUDIT_LOG_EN.md\`, \`cases_3d/C3D_01_metal_mold/MESH_REFINEMENT_POLICY_ES.md\`, \`README.md\`, \`geometry_reference.json\`, \`scripts/test_c3d_background_case.py\`. **No tocar, fusionar, cerrar ni sobrescribir**; política nominal 0.5 mm pendiente de reconsideración a la luz de solidificación dendrítica.
- CI del último \`main\`: exitoso en el momento de la revisión, pero no demuestra malla física ni resultados CFD.
- Evidencia ausente: STL físicos privados no contenidos en repo; \`snappyHexMeshDict\` integral no disponible en main; malla/CHT 3D no verificadas.
- J0 continúa abierto. Composición exacta **medida** no identificada de forma inequívoca en fuentes inspeccionadas; el DOE de CE/S y las propiedades heredadas no la sustituyen.

## Bloque autónomo de esta rama
- \`docs/granada/C3D_01_MALLA_Y_FISICA_ES.md\`: escala dendrítica/continuo, alternativas de malla y puertas de comparación.
- \`docs/granada/COMPOSICION_Y_PROCEDENCIA_ES.md\`: evita contaminación de parámetros por química de papers de terceros y separa DOE/JMatPro/materiales activos.
- \`docs/granada/EQUIPOS_MPI_Y_EJECUCION_ES.md\`: inventario de los dos equipos, diferencias WSL/RAM física y disciplina MPI.
- \`docs/granada/C3D_01_EVIDENCE_GATES.json\`: estados explícitos y verificables mediante prueba estática de CI.
- \`analysis_tools/test_granada_c3d_gates.py\`: prueba de integridad documental; **no** instalación ni corrida de OpenFOAM.
- Entrada nueva de \`README.md\` y CI \`.github/workflows/quickcup-research-audit.yml\` para enlazar y checar este bloque.
- Estado de integración y resultado CI/PR: documentar al terminar. No declarar integrado hasta merge autorizado.

## Próximas tareas independientes (no completadas)
1. Verificar composición medida mediante archivo primario verdadero de tesis / reportes de coladas, distinguir muestras y curva térmica correspondiente; solo entonces parametrizar termofísica.
2. Corroborar microestructura: grafito, distribución eutéctica y SDAS cuando existan mediciones.
3. Revisar con el director si la malla 0.5 mm del PR #18 es hipótesis útil o excesiva, y seleccionar pruebas 2/1/0.5 mm sin suponer convergencia.
4. **Fuera de GitHub:** investigador construye y aprende diccionarios de OpenFOAM. C3D-01 debe ejecutar \`blockMesh\`, \`checkMesh\`, luego \`snappyHexMesh\` y separación/regiones CHT; capturar métricas antes de CFD.
5. Confirmar RAM física Windows del Ryzen 5 5600X, límites WSL y disco; tras validar física, estudiar 1/4/6 procesos MPI en local.
6. Auditar resultados B15/B16/C15/C16 emparejados antes de declarar científicamente cerrada esa etapa; no tocar sus archivos activos por Granada.
7. Sincronizar bitácoras madre ES/EN cuando se libere el área del PR #18; no resolverla mediante overwrite ni afirmar un cierre falso.

**Criterio de salida de este bloque:** PR draft independiente con documentos/metadata/prueba estática, CI aprobada o fallo diagnosticado, sin simulación; siguiente comando Granada buscará otro bloque no ocupado.
