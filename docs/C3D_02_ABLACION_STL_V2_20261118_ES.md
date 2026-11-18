# C3D-02 — Ablación controlada de STL v2, resultados reales del 18-11-2026

## Procedencia y alcance

**Fuente primaria de los resultados:** salida literal de terminal proporcionada por el investigador, ejecutada en su equipo `Michel-DuarteHP`, bajo `~/OpenFOAM/MasterProject` con Foundation 14. El investigador ejecutó `git pull --ff-only`, `tests/test_native_allmesh_static.sh` y `scripts/run_stl_v2_ablation.sh`. La salida compartida muestra **cuatro mensajes `OK` de subpruebas**, pero no incluye el mensaje final ni el código de retorno de `test_native_allmesh_static.sh`; por tanto **no se declara aprobada la suite estática completa**. Independientemente se ejecutó la ablación nativa, que **no equivale a aprobación de malla ni de CFD**. Los logs de las variantes y el reporte completo permanecen en el WSL del investigador; el contenido de terminal se transcribe aquí, no se afirma haber descargado los logs binarios o VTK.

**Objetivo:** aislar el efecto de sustituir un solo STL, manteniendo los mismos controles de `blockMesh`, `snappyHexMesh` y los materiales físicos C14. Las geometrías originales y los STL v2 verificados se conservaron. No se ejecutó `foamMultiRun`.

## Comparación de resultados

| Ensayo | STL hierro | STL arena | metal nCells | mold nCells | exterior nCells | contacto metal→mold | Resultado |
|---|---|---|---:|---:|---:|---:|---|
| Baseline original | original | original reparado | 85,350 | 274,788 | no transcrito aquí | 27,501 caras por dirección | Dos regiones volumétricas, pero `checkMesh` **rechazado** |
| v2 combinado | v2 | v2 | 4 | 4 | 589,813 | ausente | Rechazado; ambas zonas colapsaron |
| **v2 hierro solamente** | **v2** | original reparado | **1** | **274,788** | **314,913** | **3 caras** | Rechazado: hierro no representa su volumen |
| **v2 arena solamente** | original | **v2** | **85,350** | **0** | **504,471** | **ausente** | `CHECK_INTERFACE` bloqueó antes de `checkMesh` de ambas regiones |

**Especificación exacta de la prueba:**
- Hierro v2 + arena original: carpeta `~/OpenFOAM/c3d-better-v2-metal-only`. `Allmesh` devolvió código 5. Metal: una celda, `Total volume=6.68873e-12 m³`, un determinante bajo y un check fallido; arena: 274,788 celdas, `0.000103382 m³`, 15,056 cóncavas, un determinante bajo, un face-tet malo, tres checks fallidos. La interfaz de tres caras es **residuo no físico** y no acredita acoplamiento CHT.
- Hierro original + arena v2: carpeta `~/OpenFOAM/c3d-better-v2-mold-only`. `Allmesh` devolvió código 5 en `CHECK_INTERFACE`; `splitMeshRegions` escribió la zona `mold` con cero celdas y ningún parche `metal_to_mold`. No inventar resultados de `checkMesh.mold`: el pipeline se detuvo antes.
- Ensayo v2 combinado, registrado previamente: 589,821 celdas globales, de las cuales 4 fueron etiquetadas metal, 4 mold y 589,813 exterior; no se produjo contacto metal–arena.

**Defecto de formato del reporte**: la versión local ejecutada imprimió `mold_cells=UNKNOWN` en el resumen final, pese a que la tabla nativa escribió `mold 0 mold`. **El valor científico es cero**. La corrección del parser para diferenciar cero de no encontrado ya está en `main` (commit `2be6a96f`); no repetir mallas para corregir el texto.

## Interpretación respaldada y límites

1. Las dos sustituciones individuales producen colapso de **la región sustituida**, por lo que el fallo del par v2 no requiere necesariamente que ambos STL nuevos estén juntos.
2. El colapso está visible en la clasificación de `cellZones` previa/al dividir con `splitMeshRegions`: **no** es un error que se solucione cambiando el texto de `mappedWall`. No está localizado el paso algorítmico exacto dentro de `snappyHexMesh`.
3. La triangulación, el acoplamiento de superficies coincidentes, la conectividad de `faceZones`, el comportamiento de `snap` y la asignación de zonas son **hipótesis abiertas**, no defectos demostrados de los binarios STL. `surfaceCheck`, `snappyHexMesh` y `checkMesh` responden preguntas distintas.
4. Los volúmenes CAD siguen siendo hierro ~47.9877 cm³ y arena ~102.8433 cm³. Una/ninguna celda no preserva esos volúmenes, con independencia de que `snappyHexMesh` finalice con `End`.
5. No hay autorización de solver, CHT, validación experimental, `RUN_VERIFIED`, ni cambio de física heredada de C14.

## Evidencia local preservada

- `~/OpenFOAM/C3D02_STL_V2_ABLATION_REPORT.txt`
- `~/OpenFOAM/c3d-better-v2-metal-only/` — `STL_V2_SOURCE_MAP.txt`, `log.snappyHexMesh`, `log.splitMeshRegions`, `log.checkMesh.*`, `NATIVE_BUILD_STATUS.txt`.
- `~/OpenFOAM/c3d-better-v2-mold-only/` — `STL_V2_SOURCE_MAP.txt`, `log.snappyHexMesh`, `log.splitMeshRegions`, `NATIVE_BUILD_STATUS.txt`.
- `~/OpenFOAM/c3d-better-stl-v2/` — ensayo anterior v2 combinado.
- `~/OpenFOAM/C3D02_NATIVE_OF14_01/` — referencia original.

No borrar, reusar como salida nueva ni forzar los parches. El reporte real que vive en WSL no se ha versionado en GitHub; los conteos de arriba son una transcripción del terminal compartido.

## Próxima comprobación científica, aún no ejecutada

Analizar comparativamente el texto completo de `log.snappyHexMesh` de los dos ensayos y del baseline, en particular `Walking from locations-in-mesh`, asignación `cellZones`, `faceZone`, recorte de celdas y cambios al hacer `snap`. Usar primero evidencia existente, sin lanzar nuevas simulaciones. En paralelo, evaluar la alternativa multibloque conforme del caso original del doctor, detallada en [estudio de referencia](C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). **No asumir que el multibloque de un rectángulo cuasi-2D se copia sin cambios a un QuickCup curvo 3D.**

## Referencias internas

- [Diagnóstico de Foundation 14 y ensayos anteriores](C3D_02_NATIVE_CHECKMESH_20261117_ES.md)
- [Fuentes binarias STL y procedencia](../cases_3d/C3D_02_metal_sand_clean/constant/geometry/STL_V2_APPROVED_SOURCES.md)
- [Orquestador nativo ejecutado](../cases_3d/C3D_02_metal_sand_clean/scripts/run_stl_v2_ablation.sh)
- [Registro de mallas CSV](C3D_02_MESH_TRIAL_REGISTRY_20261118.csv)
