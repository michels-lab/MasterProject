# C3D-05 — Caso B: validación independiente FINAL de procedencia CAD, malla HEX8 e interfaz

**Fecha:** 19 de noviembre de 2026. **Fuente primaria:** salida real de Ubuntu WSL proporcionada por el investigador tras ejecutar `run_hex_readiness_review.sh` con la constante SHA-256 corregida. El proceso fue **solo lectura** sobre la malla ya existente; **no generó otra malla ni ejecutó CFD**.

## Dictamen confirmado

```text
PASS: source_STEP_authentic_and_expected_hex8_topology
PASS: native_mesh_OK_all_three
PASS: parent_region_cell_count_consistent
PASS: reciprocal_mappedWall_contact_faces
PASS: contact_area_gate
PASS: native_runner_status_accepted
PASS: severe_nonorth_face_counts_consistent
OVERALL_GEOMETRY_TOPOLOGY: PASSED
PHYSICS: NOT RUN | NO GRID INDEPENDENCE | HIGH NONORTHOGONALITY WARNING
```

**Malla real que aprobó la revisión:** `/home/michel/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` (CAD STEP originales; Gmsh Delaunay, 3.6 mm nominal inicial, subdivisión HEX8/QUAD4). Los siete subpredicados de procedencia y los siete controles agregados de origen, calidad, conectividad e interfaz aparecen `PASS`. Se ejecutaron 2 pruebas de regresión de nombres Python y 9 pruebas del verificador independiente; todas terminaron `OK`. La prueba estática incluye comprobación SHA-256 de los STEP auténticos y seguridad de los ejecutores.

### Resultados cuantitativos de `checkMesh` y del revisor

| Magnitud | Padre | Metal | Arena |
|---|---:|---:|---:|
| Celdas | **270,788** | **92,200** | **178,588** |
| `native_OK` | **True** | **True** | **True** |
| Determinante mínimo | 0.0568401483702 | 0.0568401483702 | 0.0520952173462 |
| Máxima no ortogonalidad (°) | 76.798896286 | 76.798896286 | 76.0932813274 |
| Caras con no ortogonalidad >70° | **1,826** | **595** | **1,231** |

El resultado `Mesh OK` fue observado en las tres comprobaciones nativas de OpenFOAM 14; el nuevo revisor contrastó esos logs con el caso preservado. La advertencia de 1,826 caras altamente no ortogonales **NO se ha resuelto**.

### Procedencia CAD auténtica: siete controles aprobados

| Control | Resultado |
|---|---|
| `mesh_element_topology` | `HEX8_QUAD4_ONLY` |
| `subdivide_to_hex` | `True` |
| `algorithm_3d` | `1` |
| `mesh_size_mm` | `3.6` |
| `source.metal_sha256` | `ea5f65796c5156e4931eaec29ff656c279120925ebc083767a16b80892d0f475` |
| `source.mold_sha256` | `fe126d23bb639196258551fd156591d7fe2b0b4ce1d7c9ece47016e8ad08a40c` |
| `post_subdivision_hex_count` = celdas padre nativas | `270788 = 270788` |

La desviación inicial `source.mold_sha256` NO era una alteración del STEP: el código del revisor contenía una constante esperada **truncada**. La constante se restauró desde el SHA-256 canónico y se añadió una prueba que calcula los hashes directamente de los bytes reales de ambos STEP. Después de esa corrección, el mismo caso **pasó toda la auditoría**, sin modificar malla, geometría o umbrales.

### Contacto metal–arena

La aceptación anterior de `Allmesh` y el revisor independiente corroboran: `metal_to_mold` y `mold_to_metal` `mappedWall` recíprocos, **12,636 caras por lado** y área de **6,349.07567760369 mm²** en ambos lados; `contact_gate=true`, diferencia de área relativa entre lados cero, error respecto a STL de contacto −0.0560 %. No implica transferencia térmica conjugada ensayada.

### Evidencia preservada

El ejecutor indicó `PRESERVED: audit evidence already exists` para `HEX8_NATIVE_ACCEPTANCE_REVIEW_CANONICAL_SHA_20261119.json`. **No lo sobrescribió**; la corrida actual validó el caso en lectura. Los informes históricos de rechazo por SHA truncado y los experimentos Delaunay, HXT, Frontal y HEX8 `_01` permanecen preservados.

**Precisión de la evidencia:** el archivo canónico existía cuando se ejecutó este comando y no fue regenerado; la salida actual confirma la validación por lectura. No afirmar que este comando creó un JSON nuevo.

## Estado académico y puerta siguiente

**`C3D05_HEX8_COARSE_STEP_MESH_GEOMETRY_TOPOLOGY_CONTACT_AND_PROVENANCE_ACCEPTED`**; **`CFD_NOT_RUN`**, **`MESH_INDEPENDENCE_NOT_DEMONSTRATED`**, **`THERMAL_CH_3D_NOT_CONFIGURED_OR_VERIFIED`**. Esto **no equivale** a validación física, modelo de solidificación resuelto o resultados experimentales reproducidos.

Siguiente actividad técnica: localizar y cuantificar las **1,826 caras no ortogonales (>70°)**, especialmente su proximidad a la interfaz metal–arena, con los conjuntos `nonOrthoFaces` de `checkMesh` y topología nativa guardada. Después: decisión fundamentada sobre refinamiento/optimización, estudio de independencia de malla y preparación de BCs/propiedades térmicas. Mantener **una sola instrucción de terminal por etapa**.

**No crear una nueva malla como parte de la auditoría de no ortogonalidad; no ejecutar CFD por defecto.**

Documentos de contexto: [resultado original HEX8](C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md), [incidente de SHA truncado](C3D_05_HEX8_PROVENANCE_REVIEW_20261119_ES.md), [norma de un solo comando](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
