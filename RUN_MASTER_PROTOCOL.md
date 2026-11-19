> **19-11-2026 — Caso A C3D-04: protocolo de progreso 5/10 y 4/10 = 40% de hitos.** El caso curvilíneo 3D `C3D04_V4_TRANSITION_REPAIR_01/T02` conserva `Mesh OK` en sus 3 dominios y contacto; la diferencia **64/64** de caras severas se explicó por identidad de las caras reales del interfaz y **no se debe volver a auditar aisladamente**. Nuevo hito en preparación: [**T0 integral metal/arena**](cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md), con un único flujo de reportes+QA+fuentes y sin valores físicos supuestos; no se ha ejecutado en WSL ni se ha corrido el solver. **Toda actualización de Caso A debe mostrar Etapa N/10, avance D/10=P%, datos realmente verificados, bloqueos y siguiente paquete completo** según [registro canónico](docs/C3D04_CASE_A_STATUS.json) y [`AGENTS.md` local](cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md). El 40% NO estima avance de tesis ni validez física; CFD e independencia de malla **NO** demostrados.

> **19-11-2026 — PROJECT_PROGRESS_CONTRACT_20261119 (aplica a TODOS los casos):** regla permanente de **entregas integrales, corrección de raíz, verificaciones internas y cero cadenas de micropruebas WSL**. Cada actualización DEBE mostrar **caso, ETAPA, AVANCE cuantificable, evidencia, bloqueo y siguiente hito integrado**. Caso B C3D-05 **etapa 3/7 T0, 2/7 = 29% de hitos técnicos (NO tesis/CFD)**: geometría STEP y 270,788 HEX8/contacto comprobados, 1,826 caras nonorth >70°; T0 preparado sin propiedades documentadas, no materializado ni ejecutado. [Política](docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [estado](docs/PROJECT_STAGE_STATUS.json). Historial y resultados anteriores preservados.

> **19-11-2026 — CASO B C3D-05, ETAPA T0 ABIERTA: CONFIGURACIÓN SIN EJECUCIÓN.** Conservando `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` (geometry/STEP/HEX8/contacto PASS, 270,788 celdas), se creó [`t0_conduction/`](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/README.md) para conducción transitoria de dos **sólidos** (metal y arena): `foamMultiRun` + `regionSolvers { metal solid; mold solid; }`, `coupledTemperature` interfaz, exterior adiabático, `physicalProperties` y campos T con valores obligatorios y fuentes (ahora `null`). **T0 no equivale a solidificación ni a BCs experimentales del QuickCup**. Orden WSL T0a: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_preflight.sh` (pruebas, revisión nativa guardada, verifica OpenFOAM14, NO CFD). **Todavía no ejecutada**, caso térmico no generado. No materializar sin parámetros contrastados ni dar resultados de energía/solver sin corrida real. [Justificación térmica y gates](docs/C3D_05_T0_CONDUCCION_MULTIRREGION_F14_20261119_ES.md).

> **19-11-2026 — DECISIÓN DE ETAPA CASO B C3D-05:** auditoría de **distancia topológica a interfaz/pared completada y PASS** en malla aceptada `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` (270,788 HEX8, 3/3 Mesh OK, contacto y procedencia). De 1,826 caras internas con >70°: 226 de metal a 1 salto del contacto, 235 de arena a 1 salto, 398 de arena a 1 salto del exterior; 992 total a ≤2 saltos de cualquier frontera. **No fingir que están lejanas de la zona térmica**. Cerrar diagnóstico básico de malla, conservar geometría sin modificaciones; nueva prioridad: **caso T0 conducción transitoria de dos regiones, conservativo y separado** con Foundation 14 `foamMultiRun`, temperatura acoplada donde sea compatible, BC, k/rho/cp con procedencia, esquema de no ortogonalidad y energía. Después T1 entalpía/solidificación con validación experimental. No ejecutar CFD automáticamente. [Resultados y plan](docs/C3D_05_NOORTH_HOPS_REALES_Y_TRANSICION_FISICA_20261119_ES.md). Reglas de una instrucción unificada.

> **19-11-2026 — CASO B C3D-05, RIESGO NONORTH ACOTADO TOPOLÓGICAMENTE:** control de fuente STEP CAD/HEX8 y calidad nativa sigue `PASSED`. `nonOrthoFaces` regionales leídos y comparados con checkMesh **1,826=595 metal+1,231 arena**; TODOS son internos, sin contacto directo con `mappedWall`, `metalTop` ni `moldOuterUnclassified`. Queda riesgo de difusión interna; evitar inferir validez física. Para cuantificar cercanía por capas, probar [`run_nonorth_hop_distance.sh`](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_hop_distance.sh), sin CFD ni remallar, con una sola instrucción; [bitácora científica](docs/C3D_05_NOORTH_CARAS_INTERNAS_20261119_ES.md). Después diseñar esquema de difusión/BC de solidificación y sensibilidad de malla.

> **19-11-2026 — ESTADO CANÓNICO CASO B C3D-05:** la malla CAD STEP conformal HEX8 `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` **pasó `checkMesh` nativo padre/metal/arena + área y recíproca de contacto + auditoría independiente de procedencia exacta SHA256/HEX8**. Estado `ACCEPTED_NATIVE_GEOMETRY_TOPOLOGY_CONTACT_AND_INDEPENDENT_STEP_PROVENANCE_HEX8_COARSE_HIGH_NONORTH` con **CFD_NOT_RUN** y **MESH_INDEPENDENCE_NOT_DEMONSTRATED**. `nonOrtho >70°` en **1,826 caras**: riesgo cuantitativo aún sin estudio de distribución. Prioridad: script [`run_nonorth_face_audit.sh`](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_face_audit.sh) (read-only, una sola ejecución) y después preparar esquema de corrección y BCs térmicas verificables. No degradar gates ni declarar validación física anticipada. [Registro completo](docs/C3D_05_HEX8_VALIDACION_INDEPENDIENTE_FINAL_20261119_ES.md).

> **19-11-2026 — REGLA DE ACEPTACIÓN C3D-05 (SEGUNDA AUDITORÍA):** aunque `checkMesh` padre/metal/arena y el área recíproca de contacto **sí** pasaron en WSL sobre la malla HEX8 270,788, **la auditoría de procedencia CAD/HEX8 no pasó** (`source_STEP_authentic_and_expected_hex8_topology=FAIL`, causa específica aún no revelada en el primer revisor). Estado: `NATIVE_MESH_CONTACT_PASSED_INDEPENDENT_PROVENANCE_GATE_UNRESOLVED`; **NO afirmar aceptación global ni aptitud física; no CFD**. Se corrigió el revisor para desglosar siete valores medidos/esperados con tests de éxito, SHA incorrecto, conteo distinto y metadatos ausentes. JSON previo conservado y nueva auditoría independiente en archivo diferente, de solo lectura. [Evidencia y único comando](docs/C3D_05_HEX8_PROVENANCE_REVIEW_20261119_ES.md).

> **19-11-2026 — C3D-05 CASO B HA ALCANZADO EL PRIMER `Mesh OK` REAL CON CAD STEP:** salida WSL verificada: 270,788 HEX8 (metal 92,200, arena 178,588) desde `metalmm.STEP` y `QuickCupmm.STEP` mediante Gmsh `Mesh.SubdivisionAlgorithm=2`, 3.6 mm base. `checkMesh` completo padre/metal/arena **Mesh OK**, todas las regiones conectadas; contacto recíproco **12,636 caras/lado, 6,349.07567760369 mm²/lado, `contact_gate=true`**. Causa de fallos tetraédricos (`cellDeterminant`) superada para esta discretización. **Límite importante:** máximo 76.80° nonorth, 1,826 caras >70°, no independencia de malla, condiciones de frontera ni física de solidificación 3D validadas. Evidencia preservada `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`. Prohibido ejecutar CFD hasta auditoría de configuración térmica 3D. [Datos nativos y próximos gates](docs/C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md). Un solo comando por etapa.

> **18–19/11/2026 — C3D-05 HEX8: PRUEBA REAL PARCIAL Y CORRECCIÓN DE FUNCIÓN:** la prueba en memoria de dos sólidos sí generó 3,092 HEX8 y preservó contacto QUAD4/grupos físicos; el primer piloto QuickCup `_01` **abortó antes del import STEP** por `UnboundLocalError` al sombrear la función global `volume_tags` con variable local en `main()`. Se corrigió asignación a `hex_element_tags`, se añadió test AST/symtable para evitar regresiones, se cambió runner a destino **`C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`** y se exige presencia de log anterior sin sobrescribirlo. **Un único comando** `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh`. [Registro factual](docs/C3D_05_HEX8_PRIMER_INTENTO_PYTHON_20261119_ES.md). `checkMesh` HEX8 real y CFD NO ejecutados aún.

> **18–19-11-2026 — CASO B HXT RECHAZADO CON MISMA PATOLOGÍA DE ARISTAS:** HXT sí produjo malla 3D desde los STEP originales; 508,924 tetraedros, `checkMesh` 306 celdas bajo determinante malla padre, 96 metal y 401 arena; contacto térmico CAD conformante 16,218 caras recíprocas y área 6,348.106691699321 mm² por lado, **contact_gate true**, sin CFD. Todas las celdas regionales fallidas contienen 2 caras internas y 2 de frontera. Se cambia la estrategia de **algoritmo tetraédrico** a **familia topológica HEX8 mediante subdivisión Gmsh `Mesh.SubdivisionAlgorithm=2`**; el piloto nuevo es más grueso (3.6 mm) y limita número de tetraedros previos a 150,000 y RAM WSL disponible, por lo que es factibilidad, **no estudio de independencia de malla**. [Informe, prueba de capacidad en memoria y único comando](docs/C3D_05_HXT_RESULTADO_Y_PILOTO_HEX_20261118_ES.md). Conservar casos A/B, no CFD, no rebajar quality gate.

> **18-11-2026 — CASO B 3D, FRONTAL BLOQUEADO, HXT PREPARADO:** los STEP son válidos. El ensayo alternativo Gmsh 3D `Mesh.Algorithm3D=4` **NO generó malla 3D** porque el Gmsh Ubuntu enlazado a Python informó `Frontal algorithm requires Netgen`. Conservar carpeta original Frontal parcial y control Delaunay, no reinstalar paquetes a ciegas. Nueva alternativa **HXT `Mesh.Algorithm3D=10`**: preflight rápido de capacidad en memoria, luego **solo si funciona** mallado en carpeta nueva, verificación nativa padre+metal+arena, contacto y análisis de bajo determinante. [Un comando por etapa](docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md); [informe y runner](docs/C3D_05_FRONTAL_NETGEN_BLOQUEO_HXT_20261118_ES.md). NO CFD.

> **18-11-2026 — Protocolo de ensayo controlado para CASO B / C3D-05:** interfaz metal–arena de la primera malla CAD AP214 confirmada: 16,218 caras y 6,348.106691699194 mm² por lado, `contact_gate=true`, pero **checkMesh NO** por 96 celdas metal y 402 arena (todas con 2 caras internas+2 de frontera). **Siguiente experimento Frontal Gmsh algoritmo 4 frente a Delaunay algoritmo 1**; iguales STEP, escalas, mallado nominal 1.8 mm, regiones y umbrales de aceptación. Fuente/ejecutor [documentados](docs/C3D_05_AREA_ARISTAS_Y_ENSAYO_FRONTAL_20261118_ES.md). Un solo comando conforme a [norma del investigador](docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md); preservar el control y evitar CFD hasta `Mesh OK` padre/metal/arena.

> **NORMA OBLIGATORIA DE COMUNICACIÓN/OPERACIÓN (18-11-2026):** **NO fragmentar instrucciones ni comandos**. Si se requieren test, `git pull`, análisis y reportes, crear un script orquestador con validaciones y presentar **una única instrucción ejecutable en un solo bloque para copiar y pegar**. Respetar preservación de evidencia y separación de mallas/CFD; no exigir al investigador ejecutar varios fragmentos manualmente. [Política documentada](docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).

> **18-11-2026 — GATE PARALELO 3D:** se preserva C3D-03 (mesh preliminarmente aceptada en OpenFOAM14), se desarrolla C3D-04 (malla **curvilínea dentro de `blockMesh`**, no técnica distinta), y se abre C3D-05 (CAD STEP dos sólidos, **Gmsh/OpenCASCADE + gmshToFoam**, independiente de blockMesh). No hay STEP auténticos para la segunda ruta ni ejecución nativa todavía de C3D-04/C3D-05. Prohibido declarar interfaces/áreas/`Mesh OK` sin logs reales. No correr solver 3D hasta validación de zonas, area, calidad y BC. [Comparación académica](docs/C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md).

> **18-11-2026 — Estado C3D-03 / primera ejecución nueva de malla:** caso independiente [C3D_03_doctor_multiblock_pilot](cases_3d/C3D_03_doctor_multiblock_pilot/README.md) preparado tras inspeccionar secciones del CAD. El runner nativo `Allmesh` verifica SHA de STL fuente y genera malla 3D con bloques conformantes, zonas metal/mold y comprobaciones `checkMesh`/`mappedWall`, sin instalar campos ni ejecutar CFD. Salida protegida `~/OpenFOAM/C3D03_DOCTOR_MULTIBLOCK_PILOT_01`; nunca borrar ni sobrescribir si falla. Conteos y volúmenes esperados son **previos a la corrida**, no verificados. [Estrategia y gates](docs/C3D_02_ESTRATEGIA_MALLADO_CONFORMANTE_20261118_ES.md).

> **18-11-2026 — Requisito permanente para la PRIMERA PRESENTACIÓN DE MAESTRÍA:** además de las puertas de corrida, documentar **ecuaciones y significado físico**, **BC/IC con archivo fuente**, **parámetros de solver y Courant realmente medido** y **análisis de sensibilidad de `phaseChangeSource.relax`**. C14: `relax=0.10`, `deltaT=0.001`, `maxCo=0.25`, `adjustTimeStep=no`; C16 preparado: `relax=0.25`, aún NO ejecutado. **Nunca rotular `maxCo` como `Co_max` medido**. [Contrato académico del primer avance](docs/PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md).

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — estado prioritario:** `C3D_02_metal_sand_clean` ya tiene **ensayos de malla nativos ejecutados y rechazados**, no una simulación: baseline 85,350 metal/274,788 arena pero `checkMesh` fallido; STL v2 combinados 4/4; v2 metal solo 1/274,788; v2 arena sola 85,350/**0**. El campo `PREPARED_NOT_RUN` del registro maestro **se refiere a solver CFD no corrido** y NO niega las pruebas de malla. Para pruebas y estados de mallado usar el [registro específico](docs/C3D_02_MESH_TRIAL_REGISTRY_20261118.csv); [evidencia](docs/C3D_02_ABLACION_STL_V2_20261118_ES.md); [comparación con el doctor](docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). La ruta prioritaria para preparación/diagnóstico geométrico es OpenFOAM **Foundation 14 nativo**; el constructor Python documentado en notas antiguas es experimental/legado, no la ruta vigente. Ningún `Mesh OK` aislado, `End` o contacto mínimo acredita G1/CFD. Conservar C14 y todos los casos históricos.

> **Adenda obligatoria 2026-11-12:** reinicio 3D [C3D_02_metal_sand_clean](cases_3d/C3D_02_metal_sand_clean/README.md), fuente **PREPARED_NOT_RUN**. C3D-01 y carpetas `~/OpenFOAM/C3D01_*` son históricos, NO eliminar sin respaldo local. No promover un caso a `RUN_VERIFIED` por `Mesh OK` básico, `subsetMesh`, `topoSet` o `splitMeshRegions`; se requieren malla física sin exterior, `checkMesh -allGeometry -allTopology`, parches `metal_to_mold` / `mold_to_metal` compatibles y prueba CFD real. [Registro de reinicio](docs/C3D_REINICIO_20261112_ES.md).

# QUICKCUP — PROTOCOLO MAESTRO DE CORRIDAS Y SINCRONIZACIÓN

> **Estado C3D-01 actualizado al 10-11-2026:** la malla recortada metal+arena produjo **1,209,777 celdas y 151.230 cm³** (15 cóncavas, 8 face-tets deficientes, 17 determinantes pequeños; **3 fallos checkMesh**). `splitMeshRegions -disconnected` separó `region1` (**825,994 celdas, 103.256 cm³, 3 fallos**) y `region2` (**383,783 celdas, 47.9735 cm³, 2 fallos**) pero reportó **`No interfaces to add`**. No existe una interfaz CHT verificada, malla aceptada, solver CFD 3D ni validación experimental. `-cellZones 'metal'` **no se ha ejecutado**. [Bitácora](docs/C3D_01_ESTADO_REAL_20261110_ES.md). Los logs y mallas siguen locales y NO deben generar automáticamente nuevos estados en `RUN_CASE_REGISTRY.csv`.


**Versión original:** 2026-10-08; **adenda de estado 2026-11-10** · **Alcance:** repositorio `MasterProject` (antes `QuickCup-Solidification`) (autónomo, no depende de Michel's Lab/main)  
**Autoridad:** este archivo define qué revisar y actualizar antes/durante/después de **cada** corrida o auditoría de OpenFOAM Foundation 14.  
**Regla:** ningún agente ni conversación debe dar por actualizado el proyecto basándose solo en un `git push`, en un `End`, en un termopar que llega a 10 s o en una nota aislada. Usar este protocolo + `RUN_CASE_REGISTRY.csv`.

## Adenda de estado 3D — 2026-11-10

- El estado de geometría y malla `C3D-01` se registra en [docs/C3D_01_ESTADO_REAL_20261110_ES.md](docs/C3D_01_ESTADO_REAL_20261110_ES.md). **No es un CFD ejecutado ni un resultado validado**. Los STL originales y molde reparado se versionaron, pero la prueba local `snappyHexMesh` aún no tiene logs completos en Git.
- **No cambiar automáticamente estados del `RUN_CASE_REGISTRY.csv` de los 34 casos 2D.** Ese CSV sigue representando la campaña B/C y debe reconciliar por separado la evidencia V15/V16 de octubre. `case3d-01` requiere registro geométrico propio hasta que exista malla multirregión aceptada.
- La primera prueba local C3D tiene 1,505,847 celdas, 23 fallos de *face tets*, 6,974 celdas cóncavas y **2 pruebas de malla fallidas**. El `End` de `snappyHexMesh` **no** autoriza `RUN_VERIFIED` ni `EXPERIMENTALLY_VALIDATED`.
- La próxima malla debe preservar los originales en mm con `units [mm];` y demostrar metal/arena complementarios, interfaces térmicas y geometría; la prueba ejecutada en noviembre usó copias escaladas transitorias y no certifica todavía el diccionario nativo.

## Arquitectura obligatoria — ejecución local, revisión después del push

**La simulación pertenece exclusivamente a la laptop del usuario.** El usuario crea/prepara y corre el caso localmente, genera postProcessing/ y logs/, verifica los resultados localmente y decide qué preservar mediante git commit + git push. GitHub **nunca ejecuta** `Allrun`, `Allclean`, `foamMultiRun`, `blockMesh` ni cualquier solver.

Agentes científicos (declaraciones en `.github/agents/`):
- Run Evidence Auditor: identifica resultados nuevos o incompletos que ya aparecen en Git.
- Postprocessing Forensics: explica y comprueba función, variable, unidades y salida de cada postproceso.
- Physics Verifier: audita interpretación física, convergencia y conservación con datos guardados.
- Documentation Steward: coteja resultados nuevos contra bitácoras, inventario, manuales y matrices.

Automatización real **de solo lectura** tras push, PR, manual o planificación:
- `analysis_tools/audit_pushed_results.py`: inspecciona archivos conservados; entrega un informe con evidencia y alertas, sin datos fabricados.
- `analysis_tools/check_run_registry.py`: verifica el inventario de casos y cobertura.
- `analysis_tools/audit_postprocessing_config.py`: verifica definiciones V14 y catálogo de 37 `functionObjects`.
- `.github/workflows/quickcup-research-audit.yml`: intenta ejecutar esos scripts; se considera **activo solo con una ejecución Actions exitosa**.

Los archivos `.agent.md` no son procesos residentes ni agentes LLM que se ejecuten automáticamente con un push; requieren invocación o un sistema de agentes realmente conectado. Una ejecución GitHub Actions genera un artefacto; **no modifica automáticamente las conclusiones de tesis**. La actualización de manuales y bitácoras requiere una edición Git separada basada en resultados verificados.

## Nuevas líneas de trabajo — 2026-10-08

Se prepararon cuatro nuevos casos limpios, dos derivados de B14 y dos derivados de C14, como parejas V15/V16: **B15/C15** estudian adaptive timestep y **B16/C16** estudian relax de fase = 0.25 frente a 0.1. Los primeros casos C ya existían y se añadieron sus equivalentes B. Descripción de los C:  `C15_adaptiveDt_fromC14` (adaptive `deltaT` con tiempos de salida físicos alineados) y `C16_phaseRelax025_fromC14` (únicamente `fvModels/relax=0.25` frente a 0.1 de C14). **Total actualizado: 34 carpetas; 29 verificadas y 5 PREPARED_NOT_RUN** (B11-energy2, B15, B16, C15, C16).

Solo después de completar y auditar las cuatro variantes V15/V16 se bifurca el desarrollo: C3D desde C14 o baseline justificada; B-FS/B-SH con interfaz aire-metal y shrinkage/feeding. Plan científico completo: [NEXT_RESEARCH_ROADMAP_ES.md](NEXT_RESEARCH_ROADMAP_ES.md). Ningún workflow de GitHub puede iniciar CFD, y ningún caso nuevo puede declararse corrido solo por existir en el repo. Tras cada push, auditar resultados y añadir un registro científico ES/EN con evidencia.

## A. Fotografía inicial, 2026-10-08

- **30 carpetas** en `cases_controlled_buoyancy/`: 26 casos del batch histórico V3–V13 (todos RUN/ANALYSIS-VERIFIED), B14/C14 (ambos RUN/ANALYSIS-VERIFIED), C11-energy2 (RUN/ANALYSIS-VERIFIED), B11-energy2 (solo PREPARED; sus salidas heredadas se retiraron).
- **29 casos verificados, 1 no ejecutado**. El CSV `analysis_results/full_campaign_audit/case_metrics.csv` **solo representa 26**. `bc_pair_metrics.csv` contiene 13 parejas B/C; no incluye B14/C14. `profile_inventory.csv` tiene 104 entradas, solo 26×4.
- V14: `analysis_results/v14_bc_comparison/summary.md`; C11-energy2: `analysis_results/c11_energy2_test/summary.md`. **Estos resultados NO son filas de `full_campaign_audit/`** todavía.
- **Baseline para la futura validación G1:** `C14_topFixedFlux_explicitRef`, con `C11_topFixedFlux_airGapOF14` congelado como referencia histórica. La puerta **J0 JMatPro está abierta**; no crear G1 definitivo sin cerrar trazabilidad termofísica.
- **Separar estado:** `PREPARED_NOT_RUN` ≠ `RUN_VERIFIED` ≠ `ANALYSIS_VERIFIED` ≠ `EXPERIMENTALLY_VALIDATED`.

## B. Documentos de verdad y cuándo cambiarlos

| Registro / archivo | Regla por corrida o análisis |
|---|---|
| **`RUN_MASTER_PROTOCOL.md`** | Consultarlo **antes** de toda acción; modificarlo si cambia el procedimiento, los entregables o la arquitectura científica, no por cada número nuevo. |
| **`RUN_CASE_REGISTRY.csv`** | **SIEMPRE**: añadir caso al prepararlo; cambiar `run_status`, `analysis_status`, fuente, fecha, cobertura de consolidado después de la corrida. Nunca marcar verificado por salidas heredadas. |
| **`cases_controlled_buoyancy/<CASO>/CASE_NOTES.md`** | **SIEMPRE**: pregunta, parentesco, cambio aislado, preflight, prueba, evidencia, métricas, interpretación, resultados, pendientes, conclusión y estado. |
| **`cases_controlled_buoyancy/<CASO>/CASE_VARIANT.md`** | **SIEMPRE** al crear/concluir una variante: diferencia exacta respecto al padre y decisión científica final. No dejar texto desactualizado de «por correr». |
| **`PROJECT_AUDIT_LOG_ES.md` y `PROJECT_AUDIT_LOG_EN.md`** | **SIEMPRE**: la misma entrada cronológica en ambos idiomas, con fecha, hipótesis, archivos, evidencia, hallazgo, costo, decisión, límites y siguiente paso. |
| **`analysis_results/<EXPERIMENTO>/`** | **SIEMPRE** que existan resultados nuevos: `summary.md` y métricas legibles (CSV/TSV) con procedencia, unidades, comparador y script de análisis. |
| **`analysis_results/full_campaign_audit/*.csv` y `summary.md`** | **AL CAMBIAR LA COBERTURA DEL CONSOLIDADO**: regenerar y comprobar **los cinco archivos conjuntamente**. El script actual `analysis_tools/full_campaign_audit.py` está limitado a 26 por sus listas fijas `CASES` y `BC_PAIRS`. No llamar «global completo» a un archivo que omite casos. **Pendiente de integración:** B14, C14 y C11-energy2. B11-energy2 solo al ejecutarse y verificarse. |
| **`VALIDATION_MATRIX_ES.md` / `VALIDATION_MATRIX_EN.md`** | Al cambiar baseline, decisión científica, estado de J0/G1, sensibilidad o conclusión: mantener coherentes ambos. |
| **`CASE_GUIDE_ES.md` + `CASE_GUIDE_INTERACTIVE_ES.html`** | Actualizar si la corrida cambia lo que enseñamos del solver, una condición de frontera, la comparación B/C o la recomendación de baseline. |
| **`OPENFOAM_COMMAND_MANUAL_ES.md` / `OPENFOAM_COMMAND_MANUAL_EN.md`** | Añadir o corregir **procedimientos nuevos reutilizables**, explicando comando y opciones antes de pedir ejecutarlo. |
| **`JMATPRO_OPENFOAM_TRACEABILITY_ES.md`** | Actualizar al incorporar datos reales de JMatPro: composición, propiedades, origen, rango de T y conversiones. No fingir procedencia. |
| **`analysis_tools/` y `.github/agents/openfoam-solidification.agent.md`** | Actualizar cuando cambie el método de cálculo, control automatizado o reglas de auditoría. No permitir que los scripts de análisis y sus reportes contradigan el inventario. |
| **`.gitignore` / archivos trackeados** | Comprobar ausencia de salidas pesadas/temporales y de resultados heredados como prueba falsa; preservar resultados legítimos locales, no borrar físicamente sin autorización. |

**Principio de conservación:** mantener la campaña de 26 como fotografía histórica identificada por alcance. Si se decide transformar `full_campaign_audit/` en el consolidado de todos los casos, extender los analizadores, regenerar **todos** los productos a partir de entradas verificadas y actualizar su fecha/cobertura conjuntamente. Nunca añadir números a mano ni mezclar nuevos resultados con inventarios viejos sin avisarlo.

## C. Ciclo obligatorio para cada nueva corrida (PRE → RUN → MAZAPÁN)

### C1. Antes de ejecutar — PREPARED
- [ ] Decir al usuario **exactamente** qué se cambiará antes de tocar archivos, Git o ejecutar el solver.
- [ ] Identificar hipótesis, objetivo, caso padre, baseline vigente, **única variable** a modificar, predicción y criterio de éxito/fallo.
- [ ] Crear variante limpia: solo `0/`, `constant/`, `system/` y scripts de entrada; **no copiar** tiempos de solución, `logs/`, `postProcessing/` ni `log.*` y tomarlos como una corrida independiente.
- [ ] Comparar entradas contra padre con hash/diff; archivar lista explícita de diferencias activas. Para la campaña B15/C15/B16/C16 ejecutar también `python3 analysis_tools/preflight_sensitivity_cases.py --strict` (solo lectura, no sustituye el RUN/MAZAPÁN).
- [ ] Registrar nombre, familia, estado `PREPARED_NOT_RUN`, fecha, pregunta y fuente en `RUN_CASE_REGISTRY.csv` y `CASE_NOTES.md`.
- [ ] Verificar versión **OpenFOAM Foundation v14**; solvers realmente activos, `foamMultiRun`, control PIMPLE global/regional, malla/regiones, campos, unidades y BC.
- [ ] Confirmar `deltaT`, `endTime`, write intervals, output de sonda, perfiles y `functionObjects`; comparar valores reales del directorio, no declaraciones.
- [ ] Para casos de tapa impermeable, preparar evidencia por cara `phi` y velocidad normal; `sum(phi)≈0` solo **no basta**.

### C2. Ejecutar — RUNNING/FAILED/RUN_VERIFIED
- [ ] Guardar fecha/hora, comando efectivo, entorno, versión, revisión Git de entradas, ID de ejecución y ubicación del log.
- [ ] Confirmar `blockMesh`, `splitMeshRegions` y `foamMultiRun`; revisar `checkMesh` si corresponde.
- [ ] Confirmar fin: retorno del runner, tiempo objetivo/último paso y ausencia de `FOAM FATAL`, excepciones, killed/segfault; cuando no hay `End` no inventarlo. Clasificar `RUN_VERIFIED` solo con evidencia.
- [ ] Separar claramente resultados **locales** de datos persistidos en GitHub; no llamar «verificado en Git» a lo que solo existe en el PC.
- [ ] Preservar resultados antes de limpieza; **no** `Allclean`, `git push --force`, `git add -f` ni eliminación destructiva por defecto.

### C3. Auditoría numérica y física — ANALYSIS_VERIFIED
- [ ] **PIMPLE/energía:** número efectivo de solves `h_n/e_n`; residuales iniciales/finales de `p_rgh`, `p_rghFinalRes`, contracción interna/externa `R_p_outer`, mesetas vs costo, continuidad local/global/acumulada, Courant por tiempo y timestep.
- [ ] **Termofísica:** T central `T(t)`, dT/dt, puntos térmicos adicionales, mapas T y U, extremos, media de `alphaL`, `alphaL(t)`, `rho`, balance y cambios de fase.
- [ ] **Fronteras/energía:** `phi` por cara y `sum(abs(phi))` de `metalTop`, `Uy` normal, transporte advectivo, `heatFlux` y `energyFlux` en tapa e interfaz metal–molde, energía/entalpía integrada y revisión de signos/unidades.
- [ ] **Perfiles comparables:** y=10/20/30 mm y x=20 mm, verificar puntos, tiempo, T, U, alphaL, vorticidad/flowType si existen. No inventar perfiles faltantes.
- [ ] **Comparación controlada:** padre vs hijo; B vs C equivalentes cuando proceda; RMSE, máximos, tiempo de eventos, mapas/series y costo computacional; registrar si la diferencia es numérica o física.
- [ ] **Validación experimental:** solo con CSV/serie medida accesible, composición y condiciones realmente alineadas; registrar RMSE/MAE, tiempos de nucleación, recalescencia y solidificación con incertidumbre; **recalentamiento por remelting local ≠ recalescencia metalúrgica demostrada**.
- [ ] Justificar cada afirmación con fuente específica; etiquetas `GIT-VERIFIED`, `RUN-VERIFIED`, `ANALYSIS-VERIFIED`, `INTERPRETATION`, `OPEN`.

### C4. Cierre = **MAZAPÁN**
- [ ] Persistir `logs/`, `postProcessing/`, CSV/TSV, resumen por experimento, notas de caso, variantes y decisiones; sincronizar sin sobrescribir datos locales válidos.
- [ ] Actualizar **registro de casos + bitácoras ES/EN** y todas las guías/matrices afectadas.
- [ ] Revisar la lista de casos incluida en `full_campaign_audit.py` y las 5 salidas de `full_campaign_audit/`. Si los nuevos casos no están integrados, declararlo **PENDIENTE DE CONSOLIDACIÓN** con un informe de brecha, no «actualizado».
- [ ] Confirmar estado y cobertura con `python3 analysis_tools/check_run_registry.py`. La opción `--require-consolidated` es una puerta estricta para cuando el objetivo sea tener **todos** los casos verificados dentro de los CSV globales; **hoy falla justificadamente por tres casos**.
- [ ] Auditar `git status`, `git diff`, `git log`, archivos ignorados/rastreados, enlaces y consistencia documentación↔datos. Comprobar readback tras commit/push.
- [ ] Responder al usuario con **qué corrió**, resultados/conclusión, qué archivos se actualizaron, pendientes reales, commit y **qué NO quedó validado**.

## D. Gates científicos del proyecto

1. **Preservar originales:** `doctor_original/`, C11 histórico y casos históricos congelados; nuevos tests en copias controladas. C14 es baseline para nueva validación de modelo rígido.
2. **J0 antes de G1:** composición, JMatPro raw numérico por condiciones CE/S/Mn; `Tliq/Tsol/L/Cp(T)/k(T)/rho(T)/fL(T)`, criterio `rhoRef+beta`, procedencia y chequeo frente a `alpha1e=0.8`.
3. **G1 = equilibrio alineado contra experimento:** no inventar condiciones ni resultados; comparar curva termopar antes de introducir física adicional.
4. **Cinética/recalescencia solo si G1 lo exige:** no editar `solidificationMelting` para obtener artificialmente un pico.
5. **No versiones por reflejo:** una variante nueva responde una pregunta concreta y no reemplaza baseline solo por converger o minimizar un residual.

## E. Comprobación de cobertura (desde la raíz del repositorio)

`python3 analysis_tools/check_run_registry.py`  
Lee el registro, carpetas de casos y CSV de campaña; informa casos omitidos, discrepancias y estados pendientes **sin ejecutar OpenFOAM ni modificar datos**.

`python3 analysis_tools/check_run_registry.py --require-consolidated`  
Hace la misma lectura pero termina con error si cualquier caso `RUN_VERIFIED + ANALYSIS_VERIFIED` carece de fila en `case_metrics.csv`. Es la condición necesaria para declarar que el consolidado incluye todos los casos.

**Importante:** esta comprobación verifica *cobertura administrativa*, no la validez física de una corrida, la calidad del CSV ni que las métricas sean de una ejecución genuinamente distinta.

## F. Obligación para agentes y futuras sesiones

1. Leer primero `RUN_MASTER_PROTOCOL.md`, `RUN_CASE_REGISTRY.csv`, últimos apartados de `PROJECT_AUDIT_LOG_ES.md`, `VALIDATION_MATRIX_ES.md` y notas del caso.
2. Comparar estado actual Git/runner con el último registro, informar brechas y explicar acción propuesta **antes** de ejecutarla.
3. Cualquier cambio de datos → completar C1–C4; si falta evidencia, dejar estado abierto, sin datos fabricados.
4. Al cambiar el procedimiento, mantener este archivo vivo; **no depender de un repositorio `main` externo ni de la memoria de un chat**.

**MAZAPÁN = ejecutar/comprobar + preservar/sincronizar + analizar + decidir + documentar + actualizar inventarios + verificar coherencia.**
