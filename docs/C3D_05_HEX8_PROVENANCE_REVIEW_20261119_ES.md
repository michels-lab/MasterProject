# C3D-05 Caso B — segunda auditoría estricta, discrepancia de procedencia pendiente de identificar

**Fecha:** 19 de noviembre de 2026. **Evidencia primaria:** salida compartida por el investigador al ejecutar `run_hex_readiness_review.sh` en su Ubuntu WSL sobre el caso HEX8 preservado `/home/michel/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`. **Sin nueva ejecución de Gmsh, checkMesh ni CFD.**

## Resultado observado, sin reinterpretar

El investigador sincronizó `main` hasta `46027e726`; la prueba estática, dos tests `volume_tags` y cuatro tests de revisor fueron correctos. La evaluación de archivos ya guardados devolvió:

```text
PARENT: cells=270788 native_OK=True det_min=0.0568401483702 nonorth_max=76.798896286deg severe_nonorth_>70deg=1826
METAL: cells=92200 native_OK=True det_min=0.0568401483702 nonorth_max=76.798896286deg severe_nonorth_>70deg=595
MOLD: cells=178588 native_OK=True det_min=0.0520952173462 nonorth_max=76.0932813274deg severe_nonorth_>70deg=1231
FAIL: source_STEP_authentic_and_expected_hex8_topology
PASS: native_mesh_OK_all_three
PASS: parent_region_cell_count_consistent
PASS: reciprocal_mappedWall_contact_faces
PASS: contact_area_gate
PASS: native_runner_status_accepted
PASS: severe_nonorth_face_counts_consistent
OVERALL_GEOMETRY_TOPOLOGY: NOT_PASSED
PHYSICS: NOT RUN | NO GRID INDEPENDENCE | HIGH NONORTHOGONALITY WARNING
```

El revisor creó **`HEX8_NATIVE_ACCEPTANCE_REVIEW_20261119.json`** dentro del directorio preservado, que debe mantenerse **intacto** como evidencia del primer fallo.

**Interpretación:** el `Mesh OK` reportado anteriormente para padre, metal y arena **sigue respaldado por los logs nativos**; la auditoría recíproca de `mappedWall` y contacto también pasó. **Sin embargo, la nueva revisión independiente NO pasó su puerta global** porque falló un chequeo compuesto de **siete predicados** sobre los metadatos de fuente STEP y topología HEX8. La salida original no permite determinar cuál de ellos falló; no es científicamente válido afirmar que el problema es un hash incorrecto, número de elementos convertido o resolución de Gmsh sin los valores nativos de `STEP_CAD_AUDIT.json`.

**Estado correcto:** `NATIVE_MESH_AND_CONTACT_GATES_PASSED_INDEPENDENT_PROVENANCE_GATE_UNRESOLVED`, `CFD_NOT_RUN`. No sustituir por `OVERALL_ACCEPTED` ni por `REJECTED_NATIVE_CHECKMESH`. La no ortogonalidad severa sigue presente: 1,826 caras por encima de 70° y máximo 76.80°; tampoco es validación de estabilidad térmica.

## Reparación de observabilidad (SIN rebajar ningún requisito)

Se modificó [`scripts/review_accepted_hex_mesh.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/review_accepted_hex_mesh.py) para devolver cada predicado como `passed`, `observed`, `expected`; solo si **TODOS** los predicados pasan se aprueba el gate de procedencia:

1. `mesh_element_topology == HEX8_QUAD4_ONLY`
2. `subdivide_to_hex is True`
3. `algorithm_3d == 1`
4. `mesh_size_mm == 3.6`
5. `source.metal_sha256` coincide con el metal STEP AP214 versionado
6. `source.mold_sha256` coincide con el molde STEP AP214 versionado
7. `post_subdivision_hex_count == checkMesh.parent.cells`

Los detalles se incorporan al JSON de revisión y se imprimen explícitamente en la terminal. Se añadió prueba sintética de **7 PASS**, una diferencia de número Gmsh→OpenFOAM, discrepancia SHA y ausencias; ninguna condición puede aprobarse por omisión. No se ha observado aún el contenido real del `STEP_CAD_AUDIT.json` local de WSL; por tanto **no se aplicó corrección de conteo o esquema especulativa**.

Se actualizó el [orquestador de una sola orden `run_hex_readiness_review.sh`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_readiness_review.sh) para conservar el JSON de rechazo anterior y crear **`HEX8_NATIVE_ACCEPTANCE_REVIEW_PROVENANCE_DETAIL_20261119.json`** como nuevo archivo (exclusivo, nunca sobrescribir). Si la revisión sigue fallando, preserva los siete valores en JSON y sale con error, correctamente. No cambia ni copia el CAD, ni toca `polyMesh`, ni ejecuta un solver.

### Única instrucción para ejecutar en WSL

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_readiness_review.sh
```

**Siguiente decisión:** revisar los siete valores. Si la discrepancia es en `post_subdivision_hex_count`, verificar el registro MSH2 y conversión `gmshToFoam` frente a celdas de OpenFOAM, sin descartar automáticamente elementos ni ajustar el criterio. Si es metadata (tipo, algoritmo, paso de malla o hashes), contrastar con `STEP_CAD_AUDIT.json` y SHA de los archivos originales antes de corregir. **Ningún CFD hasta aprobar las puertas de procedencia, propiedades/BCs térmicas y riesgo de no ortogonalidad**.

Relacionado: [Primer resultado HEX8 nativo](C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md) · [Regla de una sola instrucción](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
