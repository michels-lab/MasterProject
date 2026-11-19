# C3D-05 Caso B — QuickCup 3D desde STEP: primer piloto HEX8 aceptado en OpenFOAM Foundation 14

**Fecha de ejecución comunicada:** 19 de noviembre de 2026 (hora local del investigador). **Fuente primaria:** registro textual de terminal de la ejecución de `run_hex_subdivision_pilot.sh`, que sincronizó `MasterProject/main` de `8736a58c1` a `9ec6c0a74`. Los resultados son **mediciones nativas reales**, no estimaciones. **No se ejecutó CFD**.

## Resultado principal y alcance de la aceptación

**ÉXITO DE MALLADO / `Mesh OK` EN TRES DOMINIOS:** el piloto `CAD STEP auténticos → Gmsh Delaunay 3D de base 3.6 mm → Mesh.SubdivisionAlgorithm=2 (HEX8/QUAD4) → gmshToFoam → splitMeshRegions` generó una malla nueva en:

`/home/michel/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`

El ejecutor terminó con **`HEX8 PILOT: ACCEPTED | NO CFD`**. `checkMesh -allGeometry -allTopology` devolvió **`Mesh OK`** sobre el dominio padre, metal y arena por separado. El informe real de `Allmesh` también aprobó sus puertas de conectividad, volúmenes, parches `mappedWall` recíprocos y áreas de contacto. `STEP_CAD_AUDIT.json`, `PILOT_MESH_REPORT.tsv`, `PILOT_INTERFACE_REPORT.txt`, `CONTACT_AREA_REPORT.json` y logs están guardados **solo en WSL**, no en GitHub.

| Magnitud medida | Dominio padre | Metal | Arena |
|---|---:|---:|---:|
| Celdas [HEX8] | **270,788** | **92,200** | **178,588** |
| Volumen [m³] | **1.50818783568e−4** | **4.79754032229e−5** | **1.02843380345e−4** |
| Componentes conectados | 1 | 1 | 1 |
| `checkMesh` | **Mesh OK** | **Mesh OK** | **Mesh OK** |
| Determinante mínimo | **0.0568401483702** | **0.0568401483702** | **0.0520952173462** |
| Máximo `non-orthogonality` [°] | **76.798896286** | **76.798896286** | **76.0932813274** |
| Caras con no ortogonalidad >70° | **1,826** | **595** | **1,231** |
| Máximo `skewness` | **1.40075736622** | **1.36064188814** | **1.40075736622** |
| `Face tets`, concavidad, volumen | OK | OK | OK |

**La no ortogonalidad severa (1,826 caras >70°) sí existe pese al `Mesh OK`**. Es un indicador de riesgo para la estabilidad y exactitud de futuras ecuaciones; se conserva explícitamente y NO debe ocultarse al seleccionar esta malla. No se ha ejecutado un solver para caracterizar ese riesgo.

## Auditoría de la geometría metal–arena

La salida del proceso y el `CONTACT_AREA_REPORT.json` compartido indican:

| Indicador | Resultado verificado |
|---|---:|
| `metal_to_mold` | `mappedWall` con `neighbourRegion=mold` y `neighbourPatch=mold_to_metal` |
| `mold_to_metal` | `mappedWall` con `neighbourRegion=metal` y `neighbourPatch=metal_to_mold` |
| Caras de contacto por lado | **12,636** |
| Área contacto por lado [mm²] | **6,349.07567760369** |
| Diferencia relativa de áreas entre lados | **0** |
| Desviación contacto vs referencia STL | **−0.056008520851 %** |
| `contact_gate` | **true** |
| `metalTop`: caras | **942** |
| `metalTop`: área [mm²] | **1,326.6753792194886** |
| Desviación `metalTop` vs STL | **−0.015835906901 %** |

Los volúmenes nativos coinciden con las referencias CAD dentro del ±2 % exigido por `Allmesh`. Las dos partes están conectadas individualmente y la interfaz posee área recíproca exacta. La auditoría de área mide caras de polyMesh, **no prueba Hausdorff/curvatura CAD ni acoplamiento térmico ejecutado**.

## Explicación científica de la mejora

Los experimentos previos, todos preservados, dieron:

| Alternativa | Celdas | Resultado |
|---|---:|---|
| `C3D05_STEP_GMSH_PILOT_01` | 525,706 tetraedros | `checkMesh REJECTED`: 306 bajo determinante padre, 96 metal, 402 arena |
| `C3D05_STEP_GMSH_FRONTAL_01` | **No hubo malla 3D** | `BLOCKED`: compilación Gmsh sin Netgen requerido |
| `C3D05_STEP_GMSH_HXT_01` | 508,924 tetraedros | `checkMesh REJECTED`: 306 padre, 96 metal, 401 arena |
| `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01` | **No hubo malla QuickCup** | Error Python `volume_tags` antes de importación STEP; corregido |
| **`C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`** | **270,788 HEX8** | **`Mesh OK` padre, metal, arena + contacto OK** |

En los tetraedros, el 100 % de las celdas regionales de bajo determinante estaba junto a dos fronteras (2 caras internas + 2 de frontera), concentradas en aristas. Convertir a hexaedros mediante subdivisión eliminó el fallo de determinante **en este piloto concreto**.

**Advertencia de diseño experimental:** en el piloto se cambió **también la talla base** de 1.8 a 3.6 mm, con límite de 150,000 tetraedros iniciales. Por tanto, **no atribuir la totalidad de las diferencias de calidad ni precisión solamente a la familia de celdas** sin un experimento de resolución controlada. La malla HEX8 es más gruesa en su generación base y no hay independencia de malla demostrada.

## Gates pendientes antes de la simulación de solidificación

1. Auditoría compacta adicional de evidencia nativa y cuantificación del riesgo por no ortogonalidad severa, **sin rerun de `checkMesh` ni remallar**.
2. Estudio de sensibilidad/convergencia de malla y resolución de interfaz y gradientes, respetando límites de memoria en WSL.
3. Configuración de **regiones térmicas reales y condiciones de frontera físicas**: metal, arena, `metalTop`, `moldOuterUnclassified`, acoplamiento compatible con Foundation 14. La existencia de `mappedWall` **no equivale** a un caso de transferencia de calor conjugado listo para correr.
4. Propiedades de materiales dependientes de temperatura, parámetros de solidificación, condiciones iniciales y estrategia de validación contra curvas experimentales QuickCup.
5. Comprobación de estabilidad/conservación de energía una vez exista un caso CFD configurado y validado; **aún sin CFD 3D**.

**Estado científico que debe usarse:** `PRELIMINARY_NATIVE_MESH_TOPOLOGY_AND_CONTACT_ACCEPTED_HEX8_COARSE`, `CFD_NOT_RUN`. No usar `CFD_VERIFIED`, `MESH_INDEPENDENT` ni `CHT_VERIFIED`.

**Protocolo del investigador:** todas las instrucciones en **un solo bloque ejecutable por etapa**, con scripts orquestadores y evidencia preservada. [Regla permanente](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).

Relacionado: [Primer intento HEX8 y reparación Python](C3D_05_HEX8_PRIMER_INTENTO_PYTHON_20261119_ES.md), [Delaunay/HXT y estrategia HEX8](C3D_05_HXT_RESULTADO_Y_PILOTO_HEX_20261118_ES.md).
