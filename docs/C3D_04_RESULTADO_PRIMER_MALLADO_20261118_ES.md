# Caso A / C3D-04 — Resultado nativo del primer mallado curvilíneo (18-11-2026)

**Evidencia primaria:** salida de Ubuntu WSL / OpenFOAM Foundation 14 compartida por el investigador. No se tienen los logs completos subidos al repositorio; se registran solamente los valores visibles en la terminal. **No se ejecutó CFD**, ni se debe interpretar este caso como malla aceptada.

## Resultado de la ejecución existente

La carpeta `~/OpenFOAM/C3D04_ROUNDED_MULTIBLOCK_PILOT_01` **ya existía** al lanzar la prueba estática actualizada, por lo que `Allmesh` de esa invocación se negó a sobrescribirla; la terminal **sí permitió inspeccionar los archivos de la corrida anterior**, que se conservan. La nueva auditoría estática de 180 bloques, 144 arcos, 280 vértices, 716 aristas, 162 caras externas y 2,496 caras previstas por lado fue ejecutada y pasó. No confundirse: el pase estático no revierte el rechazo del `checkMesh` de la corrida anterior.

Estado de la corrida **existente**:

```text
REJECTED / stage=CHECK_REGION_QUALITY / At least one native checkMesh, CAD volume or expected region cell count rejected / NO_CFD
```

| Magnitud | Metal | Mold |
|---|---:|---:|
| Celdas | 8,960 | 12,352 |
| Volumen `checkMesh` (m³) | 4.792144701e-05 | 0.0001028754004 |
| Referencia CAD (m³) | 4.7987697e-05 | 1.02843333e-04 |
| Desviación volumétrica aprox. | -0.1380 % | +0.0312 % |
| `Mesh OK` en el runner | **NO** | **NO** |
| Determinante mínimo | **1.280269566e-05** | 0.003117948625 |
| Celdas con determinante <0.001 | **92** | No reportadas |
| No ortogonalidad máxima | 84.14010705° | 80.37353325° |
| Caras con no ortogonalidad >70° | 580 | 144 |
| Skewness máxima | 2.35713197 | **4.591592248** |
| Caras con skewness elevado | No reportadas | **16** |
| Checks fallidos | **1** | **1** |

En la malla padre: **21,312 celdas**, bounding box `(0,-0.0655,0)` a `(0.0518,0,0.0518)` m, 788 caras con no ortogonalidad >70°, no ortogonalidad máxima 84.14010705°, determinante mínimo 0.0005399662232, **12 celdas con determinante pequeño**, **1 check fallido**.

`splitMeshRegions` entregó correctamente **metal/mold**, sin región CFD exterior:

- `metal_to_mold`: 2,496 caras, `mappedWall`, `neighbourRegion=mold`, `neighbourPatch=mold_to_metal`.
- `mold_to_metal`: 2,496 caras, `mappedWall`, referencia recíproca al metal.
- Fronteras externas del metal: `metalTop` 256 caras.
- Fronteras externas del molde: `moldTop` 192, `moldExterior` 3,264, `moldBottom` 192, `moldRecessWall` 384, `moldRecessRoof` 256 caras.

**Diagnóstico sustentado:** el metal fue rechazado por 92 celdas con determinante pequeño; la arena por 16 caras altamente sesgadas. El contacto topológico recíproco se formó. La elevada no ortogonalidad es un riesgo numérico adicional, aunque `checkMesh` la etiquetó `OK` en esos logs.

**NO está demostrado** todavía dónde están las 92 celdas ni las 16 caras, qué bloques específicos las originan, si se concentran en el radio basal, si el modelo geométrico coincide punto a punto con el CAD ni qué área tiene la interfaz realmente mallada. No atribuir causalidad a las estaciones de la base sin inspeccionar geometría real.

## Estado del análisis del área y próximos pasos

`CONTACT_AREA_REPORT.json` no apareció en la salida de terminal. El ejecutor original abortó en `CHECK_REGION_QUALITY` antes de entrar en `CHECK_CONTACT_AREA`; por tanto **no hay área nativa verificada de C3D-04**. Las 2,496 caras prueban el conteo y reciprocidad declarada, no el área.

Se añadió el diagnóstico de solo lectura `cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py`. Revisa logs previos y busca exportaciones VTK ya disponibles, informando rangos XYZ e histogramas de vértices por intervalos Y. También intenta calcular **solo en memoria y sin escribir ningún archivo** el área `metal_to_mold`, `mold_to_metal` y `metalTop` desde `polyMesh` existente, incluso cuando la calidad está rechazada. Un área preliminar favorable no autoriza CFD. **Vértices VTK ≠ número de celdas defectuosas.** No ejecuta `checkMesh`, `blockMesh`, CFD ni cambia evidencia. Si no hay VTK previo, lo comunica sin fabricar coordenadas.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py --self-test
python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py
```

**Puerta para un nuevo candidato curvilíneo:** identificar espacialmente las celdas de determinante bajo y caras sesgadas, modificar únicamente variables geométricas/discretización que expliquen el defecto, ejecutar en `C3D04_OUT` nuevo y comparar con el ensayo preservado. Mantener las 2 regiones, la abertura inferior y las condiciones científicas; **no reducir umbrales de `checkMesh` ni lanzar `foamMultiRun` con la malla rechazada**. No tocar las rutas del Caso B.

Fuente: salida de terminal aportada por el investigador y scripts del repositorio.

## Diagnóstico espacial y área realmente medidos (salida WSL posterior)

El investigador ejecutó exitosamente el auto-test del lector VTK legacy ASCII/BINARY y el diagnóstico de solo lectura. El reporte confirma los defectos de los logs y **localiza los vértices de las superficies exportadas**:

| Región / exportación | Vértices superficie VTK | Extensión Y [mm] | Extensión X/Z [mm] |
|---|---:|---|---|
| Padre `underdeterminedCells.vtk` | 88 | −40.0 a −39.8 | 10.8871 a 40.9129 |
| Metal `underdeterminedCells.vtk` | 304 | **−40.0 a −39.8** | 10.811 a 40.989 |
| Arena `skewFaces.vtk` | 40 | **−39.8 a −39.5** | 10.291 a 41.509 |
| Padre `nonOrthoFaces.vtk` | 712 | −40.0 a −39.8 | 4.91446 a 46.8855 |
| Metal `nonOrthoFaces.vtk` | 544 | −40.0 a −39.8 | 10.811 a 40.989 |
| Arena `nonOrthoFaces.vtk` | 228 | −40.0 a −39.8 | 4.91446 a 46.8855 |

**Advertencia esencial:** cantidades de vértices VTK de la superficie ≠ cantidades de celdas/caras defectuosas; estas últimas siguen siendo **92 celdas metálicas de determinante pequeño** y **16 caras de arena sesgadas** según el log. Los intervalos Y se basan en límites geométricos de VTK, no centroides de celdas.

El analizador recuperó directamente del `polyMesh` preservado, SIN ejecutar `checkMesh` ni escribir archivos:

- `metal_to_mold`: **2,496 caras, 6,343.771874 mm²**.
- `mold_to_metal`: **2,496 caras, 6,343.771874 mm²**.
- Diferencia de área entre regiones: **0.000000 %**.
- Error de área de contacto frente al STL: **−0.139498 %**, puerta preliminar **PASS**.
- `metalTop`: **256 caras, 1,326.384174 mm²**, error frente al STL **−0.037782 %**.

**La aceptación del área no invalida el rechazo de calidad de las mallas.** Las mediciones respaldan preservar geometría externa e interfaz y trabajar sobre distribución interior de elementos.

## Variante controlada Caso A — C3D-04 V2, preparada, sin corrida

[**C3D04_V2_BASAL_QUALITY**](../cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/README.md) deja el contorno curvilíneo y las 2,496 caras compartidas sin cambios. Contiene dos intervenciones diferenciadas: redistribuir con `smoothstep` 12 vértices interiores del núcleo de hierro en tres estaciones basales; cambiar a `simpleGrading (1.5 1 1)` los 108 bloques anulares de arena de forma continua entre capas. Los 180 bloques, 144 arcos, total de celdas y contornos CAD aproximados se conservan. La comparación textual auditada confirma **12 líneas de vértices + 108 de grading y ninguna otra**, pero no existe resultado `blockMesh`/`checkMesh` de V2 todavía.

La hipótesis es reducir la deformación axial del núcleo del hierro y concentrar celdas de arena en la interfaz. **No afirmar mejora hasta la corrida nativa.** El runner V2 mantiene sin excepciones `Mesh OK` del padre y ambas regiones, cero checks fallidos, contacto y área; no CFD.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/Allmesh
```

## Resultado nativo V2 y preparación V3 — 18-11-2026

El usuario ejecutó `C3D04_V2_BASAL_QUALITY/Allmesh` en WSL tras `git pull --ff-only`. La suite estática probó los 12 vértices interiores corregidos y los 108 bloques de arena con grading 1.5. **`checkMesh` del padre V2 PASÓ (`Mesh OK`)**, sin celdas de determinante pequeño ni caras sesgadas registradas; valores máximos: no ortogonalidad 83.30878084°, skewness 2.575040287. Las regiones **continuaron rechazadas**:

| Indicador | Metal V1 | Metal V2 | Arena V1 | Arena V2 |
|---|---:|---:|---:|---:|
| Celdas de determinante bajo | 92 | **4** | 0 reportadas | 0 reportadas |
| Caras de skewness elevado | 0 reportadas | 0 reportadas | 16 | **8** |
| No ortogonalidad máxima [°] | 84.14010705 | 80.25771334 | 80.37353325 | 81.21165315 |
| Skewness máxima | 2.35713197 | 2.018379667 | 4.591592248 | 4.070513822 |
| Checks fallidos | 1 | **1** | 1 | **1** |

Los VTK del segundo ensayo limitan `metal/underdeterminedCells.vtk` a `Y=-40..-39.8 mm` (32 vértices superficiales; **son 4 celdas** según el log) y `mold/skewFaces.vtk` a `Y=-39.8..-39.5 mm` (24 vértices superficiales; **son 8 caras** según log). La nueva área real del `polyMesh` permanece **6,343.771874 mm² por lado**, diferencia entre regiones 0.000 %, desviación −0.139498 % frente al STL. Tapa `metalTop` = 1,326.384174 mm² (−0.037782 %).

**V2 es un progreso experimental, NO una malla aprobada.** La terminal reportó:
```text
REJECTED / stage=CHECK_REGION_QUALITY / At least one native checkMesh, CAD volume or expected region cell count rejected / NO_CFD
```

La carpeta `~/OpenFOAM/C3D04_V2_BASAL_QUALITY_01` está preservada. Se publica ahora [**C3D04 V3: ensayo acotado**](../cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/README.md) con un solo comando que analiza seis pares de parámetros de geometría **interior** del hierro y grading radial en arena, conserva contorno, arco, contacto, volumes, los archivos anteriores y exige todas las puertas nativas. **V3 sigue `PREPARED_NOT_RUN`; no afirmar que pase el mallado ni ejecutar CFD.**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && \
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/run_v3_sweep.sh
```

## V3: seis ensayos nativos completados — evidencia WSL recibida

La salida del investigador confirma `ALL_TRIALS_REJECTED_OR_BLOCKED / NO_CFD` de `C3D04_V3_BASAL_SWEEP_01`. Las seis carpetas `T01`–`T06` contienen `checkMesh` real y la tabla `C3D04_V3_SWEEP_SUMMARY.tsv`. **En las seis, el padre y la arena son `Mesh OK`; solo falla la región metal por exactamente 4 celdas de determinante <0.001.** Ninguna pasó las tres puertas simultáneamente. No se ejecutó CFD.

| Ensayo | Core Δ [mm] | Grading arena | Padre | Metal | Arena | Celdas metal det bajo | Caras arena muy skew | Max skew arena | Max no orto metal [°] |
|---|---:|---:|---|---|---|---:|---:|---:|---:|
| T01 | −0.15 | 1.75 | YES | NO | YES | 4 | 0 | 3.711322729 | 80.56302942 |
| T02 | +0.15 | 1.90 | YES | NO | YES | 4 | 0 | 3.527405153 | 79.95376529 |
| T03 | −0.30 | 2.10 | YES | NO | YES | 4 | 0 | 3.311127175 | 80.87007118 |
| T04 | +0.30 | 2.30 | YES | NO | YES | 4 | 0 | 3.121918438 | 79.6505921 |
| T05 | −0.45 | 2.50 | YES | NO | YES | 4 | 0 | 2.95478911 | 81.17902399 |
| T06 | +0.45 | 2.65 | YES | NO | YES | 4 | 0 | **2.841609695** | **79.34727593** |

El área de contacto se mantuvo en **6,343.771874 mm² en todos los ensayos**, por ambos lados cuando se midió. La malla de arena queda **resuelta según el protocolo nativo**; todavía es necesaria prueba de independencia de malla y no ortogonalidad, máxima ~82.058° en T06.

**Conclusión empírica:** mover ±0.15..±0.45 mm la cuadrícula interior XZ del metal en Y=−39.8 no reduce el **número** de cuatro celdas con determinante deficiente; no afirmar que tampoco cambiaron sus valores mínimos, aún no reportados. El cambio de `simpleGrading` radial de 1.5 hasta 2.65 llevó la arena a `Mesh OK` a partir de T01. T06 es un **punto de partida para la siguiente corrección**, no ganador ni modelo CFD aprobado.

El siguiente candidato debe modificar otra dimensión de la deformación (Y interior o transición de contorno metal) bajo una comparación nativa y de área CAD estrictas. Toda modificación del contorno curvilíneo, aunque preserve continuidad y parches, puede empeorar el ajuste local CAD: se debe volver a medir.

## V4 preparada — nueva dimensión de corrección, NO resultado

Tras comprobar que los seis cambios XZ del núcleo metálico V3 no redujeron las 4 celdas de determinante bajo, se implementó [`C3D04_V4_TRANSITION_REPAIR`](../cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/README.md). Los tres primeros ensayos desplazan **solo 4 vértices interiores en Y**, sin modificar la interfaz. Los cuatro restantes, si persiste el fallo, prueban interpolaciones suaves del contorno exterior metálico en la única estación **Y=−39.8 mm**, incluyendo los 8 puntos de `arc` pertinentes. Todos toman como punto de partida la corrida real **V3/T06** y validan su procedencia contra V2, además de imponer `Mesh OK` de padre, metal y arena, área CAD, `mappedWall` recíproco y 2,496 caras de contacto.

Las variantes de perfil quedan limitadas a alpha **0.95, 0.90, 0.84 y 0.78** porque una extrapolación mayor del perfil deformaría excesivamente el corte horizontal del CAD. Como salvaguarda cuantitativa, el generador rechaza todo candidato con **error analítico del área de sección redondeada a Y=−39.8 mm mayor al 3 %** frente a **909.900 mm²** del STL. Este guard adicional no sustituye el ajuste tridimensional de toda la superficie CAD, que aún debe comprobarse. El resumen V4 incluirá los **mínimos reales de determinante de OpenFOAM** y el error de área del corte; el script no falsea aceptaciones ni cambia los umbrales.

**Estado actual V4: código publicado, ensayos nativos todavía no ejecutados. NO CFD.**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && \
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/run_v4_sweep.sh
```

## V4/T02: primera aceptación nativa de C3D-04 curvilíneo — 19-11-2026

**Fuente primaria:** salida de la terminal del investigador en WSL tras `git pull --ff-only` y el script nativo `C3D04_V4_TRANSITION_REPAIR/run_v4_sweep.sh`. No se han cargado los logs brutos a GitHub ni ejecutado el solver; las cifras provienen de la salida compartida, no de una inspección independiente de los archivos locales.

El test estático V4 superó AST de Python y cuatro casos sintéticos de modificaciones geométricas; todavía **no** certifica el mallado nativo. La posterior corrida OpenFOAM 14 produjo:

- **T01 `inner_y=-0.12 mm`: RECHAZADO.** Padre `Mesh OK=NO`, hierro `Mesh OK=NO` y molde `Mesh OK=YES`; 12 celdas metálicas con determinante bajo, mínimo metal **0.0002033082206**. No ortogonalidad máxima del metal 81.44720378°.
- **T02 `inner_y=+0.12 mm`: `MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED`.** El ejecutor devolvió código 0; **padre, hierro y arena `Mesh OK=YES`**, cero celdas con determinante pequeño en padre/metal, cero caras muy sesgadas de arena y puerta de área aprobada. Los otros cinco ensayos T03–T07 **no se ejecutaron**, porque el orquestador se detuvo correctamente al encontrar el primer candidato que cumplió todas las puertas.
- **Cambio causal acotado de T02:** mover axialmente de **Y=-39.8 a -39.68 mm** los cuatro vértices **internos** del hierro (IDs 89/90/93/94) respecto a la referencia nativa V3/T06. Contorno metal–arena, arcos y caras de frontera no se cambiaron en T02. No significa que se haya resuelto la no ortogonalidad elevada.

| Indicador nativo V4/T02 | Resultado |
|---|---:|
| `checkMesh` padre / metal / mold | **YES / YES / YES** |
| Determinante mínimo padre | **0.002165381027** |
| Determinante mínimo metal | **0.001566024926** (umbral de reporte 0.001) |
| Determinante mínimo arena | **0.002165381027** |
| Celdas de hierro con determinante pequeño | **0** |
| Caras de arena altamente sesgadas | **0** |
| No ortogonalidad máxima padre | **82.92036178°** |
| No ortogonalidad máxima metal | **77.9303929°** |
| No ortogonalidad máxima arena | **82.058116°** |
| Skewness máxima arena | **2.841609695** |
| Área metal–arena (mm²) | **6,343.771874** |
| Diferencia área entre lados | **0 %** (registrada en las corridas de referencia y misma interfaz geométrica) |
| Error del área frente a STL | **−0.139498 %** (misma interfaz geométrica) |

**Carpeta aceptada y preservada (no sobreescribir):**

```text
/home/michel/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02
```

**Resumen auténtico del orquestador:**

```text
T02 inner_y 0.12 0 MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED YES YES YES 0 0 0 0.002165381027 0.001566024926 0.002165381027 NA 82.92036178 77.9303929 82.058116 2.841609695 6343.771874
SELECTED PRELIMINARY NATIVE MESH: /home/michel/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02
```

**Estado científico exacto:** **PRIMERA MALLA 3D CURVILÍNEA CON CHECKMESH DE PADRE Y AMBAS REGIONES APROBADO, MÁS ÁREA DE CONTACTO PRELIMINAR APROBADA.** No confundir con malla suficientemente ortogonal para todos los esquemas de discretización, coincidencia superficial plena CAD, independencia de malla, validación de condiciones de frontera, ejecución de transferencia térmica CHT o solidificación. `NO_CFD` sigue vigente.

**Próximos controles previos a la física 3D:** comparación bidireccional de distancias **superficie CAD–superficie `polyMesh`** para metal y arena por separado, incluyendo cortes basales; inventario de caras con non-orthogonality severa y su ubicación; sensibilidad de resultados a discretización/mallas; revisión explícita de BC en `metalTop`, `moldTop`, `moldExterior`, `moldBottom`, `moldRecessWall`, `moldRecessRoof` y las interfaces recíprocas. `phaseChangeSource`/CHT 3D debe montarse **solo con trazabilidad a los casos C14 validados**, no asumirse configurado por esta prueba de malla.

## Resultado real de distancias superficiales STL ↔ malla — 19/11/2026

Auditoría WSL con `audit_accepted_surface_fit.py` completada sobre la **malla previamente aceptada por los gates nativos T02**; self-test de punto-triángulo, BVH, STL binario y unidades: `SELF_TEST_OK`. Ambas fuentes STL SHA256 originales validadas. **Cuatro distancias direccionales muestreadas**: hierro STL→malla: 4,421 muestras, máx. **0.104769 mm**, p95 0.084237 mm, RMS 0.045467 mm; hierro malla→STL: 2,910, máx. **0.102346 mm**, p95 0.051427 mm, RMS 0.022718 mm; arena STL→malla: 3,897, máx. **0.104973 mm**, p95 0.079895 mm, RMS 0.041814 mm; arena malla→STL: 4,311, máx. **0.099904 mm**, p95 0.042799 mm, RMS 0.018157 mm. **0 % de muestras con error >0.5 mm**. JSON original preservado en `~/OpenFOAM/C3D04_V4_T02_CAD_SURFACE_AUDIT_01/SAMPLED_CAD_SURFACE_REPORT.json`.

**No es un Hausdorff exacto ni una cota garantizada de error superficial**, tampoco valida directamente STEP ni establece una tolerancia de aceptación. El resultado es favorable como evidencia **muestral**; el `Mesh OK` sigue fundamentado por los controles nativos previos y el área de interfaz recíproca, no por este nuevo estudio. **Alta no ortogonalidad y sensibilidad de malla pendientes; NO CFD.** [Informe y limitaciones](C3D_04_VALIDACION_SUPERFICIE_T02_20261119_ES.md).

## Siguiente control C3D-04: auditor de no ortogonalidad preparado

[Auditor de no ortogonalidad V4/T02](C3D_04_NO_ORTHO_T02_20261119_ES.md) listo para leer los registros y VTK nativos preservados: recuenta caras con ángulo >70° desde los **logs**, identifica rangos espaciales solo a partir de **ocurrencias de vértices VTK**, y revalida las puertas de malla y contacto guardadas. **La herramienta no ha sido ejecutada en WSL; no inventar recuentos ni localizar caras usando cantidades de vértices. NO CFD.**
