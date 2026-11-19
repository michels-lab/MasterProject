> **19-11-2026 — C3D-04 A: paquete T0 de 10 archivos con fvSolution global.** [**Revisión integral de `foamMultiRun` Foundation14, `coupledTemperature`, materialización atómica, QA por CI y objetivo energético adiabático**](../cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md). [Estado canónico 5/10, 40 % de hitos](C3D04_CASE_A_STATUS.json); fuente V4/T02 inmutable, datos físicos aún pendientes, sin corrida WSL ni CFD. [Normas permanentes](../cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md): etapa+avance en toda actualización y una sola entrega integrada, nunca un comando por subpieza.

> **19-11-2026 | GRANADA_C3D05_T0_INTEGRAL_20261119 — NUEVO PAQUETE GRANADA CASO B:** [T0 integrado sin micropruebas y con preservación de malla](granada/C3D05_T0_INTEGRATED_GRANADA_20261119_ES.md), [runner único](../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_granada.py), [test sintético](../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_granada.py), [CI estático](../.github/workflows/c3d05-t0-granada-static.yml). **C3D-05/B: etapa 3/7, 2/7 = 29% de hitos técnicos; G3 abierto, T0 no materializado ni ejecutado.** Ver [registro canónico](PROJECT_STAGE_STATUS.json).

> **19-11-2026 — Caso A C3D-04: etapa 5/10 y avance 4/10=40% de hitos verificados.** [**Registro canónico**](C3D04_CASE_A_STATUS.json), [**contrato de respuesta y entrega integral**](../cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md), [**nuevo paquete T0 metal/arena y límites**](../cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md) y [**pruebas estáticas automatizadas CI**](../.github/workflows/case-a-t0-stage-contract.yml). Diagnóstico malla: 64/64 caras severas extras del padre identificadas como interfaz; malla fuente V4/T02 intacta, NO CFD. El porcentaje es operacional y **no** cuantifica validación física. Prohibido solicitar ejecuciones WSL por subcomponente.

> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119:** [Contrato obligatorio de entregas integrales y avance siempre visible](POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [Etapa/avance canónicos por hitos](PROJECT_STAGE_STATUS.json) · [Validador estático de sincronización](../tools/check_project_delivery_contract.py). C3D-05/B etapa 3/7, 2/7 = 29% de hitos técnicos, no CFD. Aplicable a A/B, 2D/3D y casos futuros; ver auditoría ES/EN y matrices actualizadas.

> **19-11-2026 — C3D-04-A RESULTADO 64/64 CARAS DE INTERFAZ VERIFICADO:** [**Auditoría real de identidad de caras del mallado curvilíneo V4/T02**](C3D_04_NO_ORTHO_T02_20261119_ES.md): **64/64 caras severas adicionales del padre pertenecen a la interfaz** (Y−40..−39.8 mm), mapeadas uno a uno mediante `polyMesh` y VTK; 0 fuera de ella; padre 572, metal 276, arena 232; 2,496 caras por lado recíproco. **Investigación cerrada, no pedir otra prueba individual.** Siguiente hito solo como paquete integrado de condiciones térmicas, acoplamiento y criterios numéricos; NO CFD ni estabilidad física validada.

> **19-11-2026 — C3D-05 Caso B / transición a física T0:** [**Preparación completa de archivos OpenFOAM Foundation14 para conducción transitoria acoplada metal–arena, con procedencia obligatoria, `foamMultiRun`, BC `coupledTemperature`, y tests sin CFD**](C3D_05_T0_CONDUCCION_MULTIRREGION_F14_20261119_ES.md). [Fuente versionada T0](../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/README.md), [runner único de preflight](../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_preflight.sh). Malla geométrica y no ortogonalidad ya caracterizadas; T0 se encuentra **preparado, no materializado ni ejecutado en WSL**.

> **19-11-2026 — C3D-04 V4/T02, 64 CARAS SEVERAS RESTRINGIDAS AL FILLETE BASAL:** [**VTK nativos 572/276/232 polígonos igualados a los logs de `checkMesh`, centroides parent/metal/mold medidos por bandas Y**](C3D_04_NO_ORTHO_T02_20261119_ES.md). Excedente padre–regiones **64/0/0** en los tres cortes, respectivamente; sin demostrar aún pertenencia individual a la interfaz. Publicado [**auditor read-only de identidad de cara contra `polyMesh` y `mappedWall`**](../cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_v4_t02_face_identity.py), **sin corrida WSL aún**. No CFD.

> **19-11-2026 — C3D-04 CASO A, NO ORTOGONALIDAD REAL CUANTIFICADA:** [**Auditoría nativa guardada V4/T02: padre 572 caras >70°, hierro 276, arena 232; interfaz de 2,496 caras, sin CFD**](C3D_04_NO_ORTHO_T02_20261119_ES.md). Diferencia padre vs regiones de 64 caras severas **sin resolver**, aunque el balance de todas las caras sí da exactamente 2,496 por la interfaz. [**Lector de polígonos VTK para centroides de cara**](../cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_v4_t02_vtk_faces.py) publicado, **pendiente de ejecución WSL**. No declarar independencia de malla ni estabilidad física.

> **19-11-2026 — C3D-05, DISTANCIA TOPOLOGICA NOORTH FINALIZADA:** [**Resultados WSL: 226 caras severas metal y 235 arena a 1 salto de la interfaz; 398 arena a 1 salto de exterior; 992/1826 a ≤2 saltos de alguna pared**](C3D_05_NOORTH_HOPS_REALES_Y_TRANSICION_FISICA_20261119_ES.md). Geometría/topología/STEP/contacto `PASS`, no CFD, no independencia de malla. Nuevo foco: diseño térmico T0 bicuerpo y fase de cambio T1 en Foundation14 con BC y propiedades verificables, evitando repetir auditorías de la misma malla.

> **19-11-2026 — CASO A C3D-04: AUDITOR NO ORTOGONALIDAD CORREGIDO, PENDIENTE REVISIÓN WSL:** [**Fallo real por comparación incorrecta `metalTop=patch` cuando el CAD multibloque declara `metalTop=wall`, reparado sin modificar la malla ni puertas de contacto**](C3D_04_NO_ORTHO_T02_20261119_ES.md). El primer revisor no alcanzó el recuento de caras >70°; el nuevo autocontrol incluye casos positivos y negativos, aún no ejecutado localmente. **NO CFD.**

> **19-11-2026 — C3D-05 Caso B, distribución nativa de `nonOrthoFaces`:** [**1,826 caras >70°: metal 595 internas, arena 1,231 internas, ninguna de frontera ni incidente directamente a celdas de contacto/exterior**](C3D_05_NOORTH_CARAS_INTERNAS_20261119_ES.md). Auditoría `NATIVE_FACESET_AUDIT: PASSED`, malla 3/3 `Mesh OK` y procedencia STEP/HEX8 `PASSED` conservadas. [Runner próximo de distancia por saltos](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_hop_distance.sh) con test de graph BFS, preparado/no ejecutado. CFD y convergencia aún sin correr.

> **19-11-2026 — C3D-04 CASO A, NO ORTOGONALIDAD PENDIENTE DE MEDIR ESPACIALMENTE:** [**Nuevo auditor seguro para V4/T02 de `checkMesh` padre/regiones, conteo de caras >70° y ubicación VTK, conservando control de contacto `mappedWall`**](C3D_04_NO_ORTHO_T02_20261119_ES.md). Publicado con autotest y un comando único, **todavía no ejecutado**. El resultado STL↔malla muestreado anterior sigue documentado por separado; **NO CFD**.

> **19-11-2026 — CASO B C3D-05: DOCUMENTACIÓN DE ACEPTACIÓN FINAL DE MALLA:** [**Auditoría independiente `OVERALL_GEOMETRY_TOPOLOGY: PASSED`, 270,788 HEX8, procedencia CAD exacta, interfaz recíproca y advertencia de 1,826 caras nonorth >70°**](C3D_05_HEX8_VALIDACION_INDEPENDIENTE_FINAL_20261119_ES.md). [Próximo orquestador read-only `nonOrthoFaces`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_face_audit.sh) para cuantificar adyacencia a la interfaz; pruebas preparadas, **no ejecutado todavía**. No CFD, no convergencia de malla.

> **19-11-2026 — CASO A C3D-04/V4-T02: AUDITORÍA STL–MALLA REAL COMPLETADA.** [Resultados de comparación bidireccional por material](C3D_04_VALIDACION_SUPERFICIE_T02_20261119_ES.md): máximo de distancias muestreadas **0.104973 mm**, sin muestras >0.5 mm, STL autenticados y JSON inmutable. Resultado **muestral**, NO Hausdorff exacto, NO CFD; siguiente control es no ortogonalidad severa y sensibilidad de malla.

> **19-11-2026 — HEX8 CASO B, CAUSA DEL `FAIL` INDEPENDIENTE RESUELTA EN CÓDIGO (NO AÚN REVALIDADA):** [**Informe del error de SHA truncado de 52 vs 64 caracteres y corrección exacta, con pruebas sobre los STEP**](C3D_05_HEX8_PROVENANCE_REVIEW_20261119_ES.md). El revisor sigue exigiendo padres/regiones/contacto/procedencia estrictos y deja los resultados anteriores intactos; **pendiente su nueva ejecución en WSL**, NO CFD, no independencia ni estabilidad térmica.

> **19-11-2026 — Caso B C3D-05, segunda revisión estricta:** [**`Mesh OK` nativo padre/metal/arena y contacto aprobados, PERO puerta de procedencia HEX8/STEP independiente fallida, con nuevo diagnóstico de siete valores reales/esperados**](C3D_05_HEX8_PROVENANCE_REVIEW_20261119_ES.md). Primer JSON fallido preservado; [revisor ampliado](../cases_3d/C3D_05_step_gmsh_conformal/scripts/review_accepted_hex_mesh.py) y [runner único](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_readiness_review.sh). No CFD.> **19-11-2026 — SIGUIENTE VALIDACIÓN 3D-A:** [**Protocolo y herramienta reproducible para comparar por muestreo las superficies de T02 `polyMesh` contra STL originales, bidireccionalmente y por material**](C3D_04_VALIDACION_SUPERFICIE_T02_20261119_ES.md). Resumen p95/p99/RMS/máximo, SHA de las fuentes y salvaguardas de `NO_CFD`. **Pendiente ejecución WSL.** No llamar al muestreo "distancia de Hausdorff certificada".

> **19-11-2026 — CASO A C3D-04, HITO NATIVO:** [**V4/T02 `blockMesh` curvilíneo ya pasa `Mesh OK` para malla padre, metal y arena y el control de interfaz/área**](C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md). Cuatro vértices interiores de hierro desplazados +0.12 mm en Y fueron decisivos; T01 falló, T02 pasó, T03–T07 no se ejecutaron. [**Candidato V4/T02 preservado**](../cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/README.md). **NO equivale a solver CFD ejecutado ni CAD validado:** quedan comparación espacial metal/arena, análisis de no ortogonalidad elevada, independencia de malla y BC CHT/solidificación 3D.

> **19-11-2026 — HITO C3D-05:** [**Primer caso B CAD STEP con `Mesh OK` padre/metal/arena: 270,788 HEX8, contacto 12,636 caras y área recíproca, pero alto non-orth de 1,826 caras**](C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md). Estado `PRELIMINARY_NATIVE_MESH_TOPOLOGY_AND_CONTACT_ACCEPTED_HEX8_COARSE`, sin independencia de malla, BCs ni CFD. Mantener histórico de Delaunay/HXT rechazados y Frontal bloqueado. Se conserva evidencia exclusivamente local en WSL.

> **18-11-2026 — CASO A C3D-04: MALLADO CURVILÍNEO `blockMesh` Y V4 LISTA:** [**Informe actualizado con primer rechazo, mejora V2 y seis ensayos V3 nativos**](C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md): V3 pasa `Mesh OK` en padre y arena 6/6; metal conserva 4 celdas de determinante bajo y no existe simulación CFD. [**Nuevo ensayo V4 basado en T06: tres movimientos axiales de nodos interiores + cuatro ajustes del contorno basal bajo puerta CAD local ±3 %**](../cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/README.md). Un único script nativo, pruebas geométricas, diagnóstico automático, salida inmutable y tabla comparativa. **V4 aún no ejecutada**. Esta entrada sustituye las referencias antiguas que describen C3D-04 como no ejecutado.

> **18–19/11/2026 — C3D-05 HEX8:** [**Preflight de 3092 HEX8 en geometría de prueba, colisión local `volume_tags` detectada y reparada, prueba regresiva nueva y relanzamiento seguro `_02`**](C3D_05_HEX8_PRIMER_INTENTO_PYTHON_20261119_ES.md). La primera carpeta `_01` está preservada; QuickCup aún no generó malla HEX8. [Runner único](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh).

> **18–19-11-2026 — C3D-05 CASO B: HXT vs Delaunay y siguiente cambio de topología:** [**HXT 508,924 tetraedros, 306/96/401 celdas determinant<0.001, interfaz 16,218 caras / 6,348.106691699321 mm² por lado aprobada, y piloto de subdivisión HEX8/QUAD4 con topes de recursos**](C3D_05_HXT_RESULTADO_Y_PILOTO_HEX_20261118_ES.md). [Preflight HEX de dos sólidos](../cases_3d/C3D_05_step_gmsh_conformal/scripts/preflight_hex_subdivision.py) y [orquestador único](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh). No CFD; HEX8 preparado no ejecutado.

> **18-11-2026 — C3D-05 / CORRIDA FRONTAL REAL:** [**Frontal abortó en 3D por falta de Netgen en compilación Gmsh, no por defectos de la malla; nueva ruta HXT 10 con preflight y un comando**](C3D_05_FRONTAL_NETGEN_BLOQUEO_HXT_20261118_ES.md). [Preflight de capacidad HXT](../cases_3d/C3D_05_step_gmsh_conformal/scripts/preflight_hxt.py) · [Orquestador HXT](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hxt_pilot.sh). Prueba HXT todavía no ejecutada; preservar corridas y no CFD.

> **18-11-2026 — Casos 3D / C3D-05 segunda auditoría y prueba de solución:** [**Área CAD 16,218 caras, lados idénticos, concentraciones de tetraedros de 2 caras frontera y prueba controlada con Gmsh Frontal**](C3D_05_AREA_ARISTAS_Y_ENSAYO_FRONTAL_20261118_ES.md). [Ejecutor único de nuevo piloto Frontal](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_frontal_pilot.sh). El ensayo Frontal NO ha sido ejecutado; el Delaunay original sigue `REJECTED` por determinante; CFD no ejecutado.

> **NORMA DE COMANDOS DEL PROYECTO — 18-11-2026:** [**Un solo bloque ejecutable por etapa; no separar instrucciones; usar orquestadores en GitHub**](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md). En C3D-05, el [runner unificado de diagnóstico](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_full_diagnostics.sh) integra pruebas, bajo determinante y área en una sola invocación, sin remallar.

> **18-11-2026 — RESULTADO POSTMORTEM C3D-05:** [**La causa del rechazo es exclusivamente el control del determinante de celda (306 padre; 96 metal; 402 arena) y nueva auditoría de topología/área sin remallar**](C3D_05_DIAGNOSTICO_DETERMINANTE_20261118_ES.md). [Script de adyacencia de `underdeterminedCells`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/audit_underdetermined_topology.py) y [prueba sintética](../cases_3d/C3D_05_step_gmsh_conformal/tests/test_audit_underdetermined_topology.py). **No CFD ni malla aprobada**.

> **18-11-2026 — C3D-05 primer resultado NATIVO:** [**525,706 celdas Gmsh/OF14, volúmenes metal/arena correctos, checkMesh regional RECHAZADO y diagnóstico de lectura de logs**](C3D_05_RESULTADO_PRIMER_MALLADO_20261118_ES.md). Recurso [`diagnose_existing_mesh.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/diagnose_existing_mesh.py) para examinar salida preservada **sin regenerar la malla**. Causa específica de los dos `mesh_ok NO`: pendiente de recibir `log.checkMesh.*`. No CFD.

> **18-11-2026 — CAD STEP PUBLICADO:** los originales `metalmm.STEP` y `QuickCupmm.STEP` ya están en [`C3D-05/constant/geometry`](../cases_3d/C3D_05_step_gmsh_conformal/constant/geometry/), y `Allmesh` los selecciona sin rutas manuales tras el `git pull` local. Hashes Git de los archivos coincidieron exactamente con las fuentes cargadas. [Auditoría de los STEP y conversión de unidades](C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md) · [procedimiento completo](../cases_3d/C3D_05_step_gmsh_conformal/README.md). **Estado:** preparado para prueba local, sin ejecución Gmsh/OF14 ni CFD.

> **18-11-2026 — C3D-05 con CAD STEP REAL INSPECCIONADO:** [**Auditoría de archivos `metalmm.STEP` y `QuickCupmm.STEP`, SolidWorks AP214, validación B-Rep, unidades y área de contacto**](C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md). Dos sólidos auténticos y compatibles; aún falta hacerlos accesibles en WSL y correr Gmsh/OF14. Documentos anteriores que dicen «STEP pendiente» describen el estado anterior a la carga de CAD.

> **18-11-2026 — LANZAMIENTO DE RUTAS PARALELAS 3D:** [Comparación `blockMesh` curvilíneo C3D-04 vs CAD STEP/Gmsh C3D-05, puertas, comandos y fuentes](C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md) · [C3D-04](../cases_3d/C3D_04_rounded_multiblock_pilot/README.md) · [C3D-05](../cases_3d/C3D_05_step_gmsh_conformal/README.md) · [matriz CSV de estado REAL de mallas](C3D_MESH_PROGRESS_20261118.csv). **C3D-03 sí se malló; C3D-04 no se ha corrido; C3D-05 depende de STEP de SolidWorks. Ninguna tiene CFD 3D.**

> **18-11-2026 — Nuevo recurso técnico C3D-03:** [**Piloto 3D multibloque inspirado en el doctor, resultados geométricos analíticos, runner nativo y criterios de validación**](../cases_3d/C3D_03_doctor_multiblock_pilot/README.md). Se ejecutará como nuevo caso local separado, nunca sobre C3D-02. [Estrategia del piloto](C3D_02_ESTRATEGIA_MALLADO_CONFORMANTE_20261118_ES.md) · [test estático sin solver](../cases_3d/C3D_03_doctor_multiblock_pilot/tests/test_native_multiblock_static.sh). `blockMesh` Foundation 14 todavía NO se ha ejecutado para C3D-03.

> **18-11-2026 — Estrategia para continuar C3D-02:** [**Alternativa de mallado conformante 3D basada en el caso del doctor, rutas A/B/C, condiciones de selección y puertas de aceptación**](C3D_02_ESTRATEGIA_MALLADO_CONFORMANTE_20261118_ES.md). El primer ensayo nuevo **NO** está ejecutado; se requiere caracterizar la geometría real antes de decidir cómo distribuir los bloques.

> **18-11-2026 — Entregable académico PRIORITARIO:** [**Primer avance: requisitos del director, ecuaciones, BC, Courant real, sensibilidad del `relax` 0.10→0.25 y pendientes**](PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md). Esta es la referencia canónica para preparar la primera presentación; las medidas no verificadas aparecen expresamente como pendientes. No mezclar `maxCo` nominal con máximo observado.

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — documentación vigente C3D-02:** [resultados REALES de las dos ablaciones de STL v2](C3D_02_ABLACION_STL_V2_20261118_ES.md) (1 celda metal con STL metal v2; 0 celdas arena con STL arena v2); [revisión de `doctor_original/cht` y alternativa multibloque SOLO PROPUESTA](C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md); [registro tabular de ensayos de malla, separado del estado CFD](C3D_02_MESH_TRIAL_REGISTRY_20261118.csv). **Prioridad de estado:** esta adenda reemplaza los «pendientes de ejecutar» anteriores de esas ablaciones, pero preserva íntegra la evidencia histórica; no hubo `foamMultiRun` 3D. La línea de ejecución prioritaria es OpenFOAM Foundation 14 nativo, no el constructor Python experimental.

> **15-11-2026 — C3D-02 extracción validada por volumen, calidad fallida:** [bitácora de `moldVolume` (274,788 celdas, 103.409 cm³, outerBox=0)](C3D_02_DOS_MALLAS_20261112_ES.md), 22,737 cóncavas + un determinante bajo; [script de diagnóstico de defectos en copias](../cases_3d/C3D_02_metal_sand_clean/scripts/inspect_extracted_mesh_quality.sh). Aún no hay interfaz CHT ni CFD.

> **15-11-2026, C3D-02:** [medición local de moldVolume 103.409 cm³ y protocolo de extracción en copia](C3D_02_DOS_MALLAS_20261112_ES.md). Nuevo `scripts/extract_mold_zone_copy.sh` usa `subsetMesh -cellZone moldVolume -noFields` exclusivamente en carpeta nueva. Pendientes fronteras/convexidad, no CFD.

> **13-11-2026 — C3D-02:** [geometric zoning result](C3D_02_DOS_MALLAS_20261112_ES.md): `moldVolume` 274,788 cells and `moldInterface` 97,492 faces, but global box volume 242.208 cm³ and checkMesh failure. Next operation is **read-only zone-volume measurement** through `scripts/measure_mold_zone_volume.sh`, *not* new meshing or CFD.

> **13-11-2026, C3D-02:** el aumento de refinamiento a L3 conservó el volumen total de la caja (242.208 cm³) y eliminó solo seis celdas. [Registro y nueva prueba explícita de cellZone en L2](C3D_02_DOS_MALLAS_20261112_ES.md); no se publican mallas CHT ni CFD sin checks.

> **12-11-2026, actualización real C3D-02:** el nuevo punto interior de arena no cambió el fallo (568,134 celdas y 242.142 cm³; `outerBox=15164`). [Bitácora científica del intento y lecciones](C3D_02_DOS_MALLAS_20261112_ES.md), [script de auditoría sin remallado](../cases_3d/C3D_02_metal_sand_clean/scripts/inspect_mold_leak.sh). Próximo paso: comprobar autointersecciones y conectividad.

> **12-11-2026, C3D-02 retry1:** la malla del hierro alcanzó **47.9621 cm³** sin exterior (pero 2,422 cóncavas); la arena retuvo **242.142 cm³ y 15,164 caras exteriores**, calidad fallida. [Resultado real, condición insidePoint y prueba solo del molde](C3D_02_DOS_MALLAS_20261112_ES.md). El punto x=3 mm de arena se encontraba sobre una cara de la malla de fondo; corrección candidata **NO ejecutada**.

> **12-11-2026, actualización C3D-02:** [error y corrección de `allowFreeStandingZoneFaces` en las dos mallas materiales](C3D_02_DOS_MALLAS_20261112_ES.md), [manual OF14 con comando de reanudación](../OPENFOAM_COMMAND_MANUAL_ES.md). `snappyHexMesh` se detuvo sin malla física; el único reintento previsto preserva el workspace existente.

> **C3D-02 12-11-2026:** [siguiente etapa — mallas geométricas independientes hierro/arena](C3D_02_DOS_MALLAS_20261112_ES.md), seguida del diseño y validación de contacto térmico. Esta ruta está **preparada, NO CORRIDA**; no reemplaza la evidencia del primer mallado fallido.

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
