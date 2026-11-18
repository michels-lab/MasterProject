# Caso B — C3D-05: interfaz CAD verificada, tetraedros de aristas y ensayo Gmsh Frontal

**Fecha:** 18 de noviembre de 2026. **Evidencia:** salida de terminal WSL del investigador guardada en el mensaje adjunto `Pasted text(20261118-214850).txt`, ejecución previa `run_full_diagnostics.sh` sobre la primera malla `/home/michel/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`. **No hay simulación CFD.** Se mantiene la malla **rechazada por un único check**; la interfaz geométrica **sí pasa**.

## Resultados observados de la malla de control (Gmsh, algoritmo 3D por defecto Delaunay)

| Indicador observado | Malla padre | Metal | Arena |
|---|---:|---:|---:|
| Tetraedros | 525,706 | 190,365 | 335,341 |
| Fallos `checkMesh` | 1 | 1 | 1 |
| Celdas `determinant < 0.001` | 306 | 96 | 402 |
| `Mesh OK` | NO | NO | NO |
| Regiones conectadas | 1 | 1 | 1 |
| Skewness, no ortogonalidad, volumen | Aprobado | Aprobado | Aprobado |

**Topología exacta de las celdas regionales rechazadas** (auditada usando los conjuntos nativos `underdeterminedCells` y listas `owner`/`neighbour`):
- **Metal:** las **96 de 96** celdas afectadas son tetraedros con **2 caras internas y 2 caras de frontera**. Las dos fronteras son siempre **una cara `metalTop` y una `metal_to_mold`**.
- **Arena:** las **402 de 402** celdas afectadas también tienen **2 caras internas y 2 caras de frontera**. **96** de ellas tocan una `mold_to_metal` y una `moldOuterUnclassified`; las otras **306** tocan dos caras de `moldOuterUnclassified`.
- **Celdas rechazadas completamente interiores: 0**. Esto **confirma la asociación** entre determinante pequeño y aristas/esquinas de la malla de frontera en este ensayo. No demuestra que cualquier otro tetraedro que toque dos fronteras tenga bajo determinante ni que un cambio de algoritmo garantice curarlo.
- La discrepancia numérica entre **306 en el padre** y **498 tras dividir regiones** se explica como fenómeno **compatible con el cambio de caras internas/frontera tras `splitMeshRegions`**; no confundir con celdas destruidas o geometría inconsistente. Se requiere corroborar la implementación exacta en OpenFOAM14 para afirmar causalidad algorítmica completa.

## Contacto real metal–arena — auditoría de la malla preservada

El analizador `measure_interface_area.py` se ejecutó sobre la primera malla regional y reportó:

| Magnitud medida | Resultado |
|---|---:|
| `metal_to_mold`: número de caras | **16,218** |
| `mold_to_metal`: número de caras | **16,218** |
| Área metal–arena lado metal | **6,348.106691699194 mm²** |
| Área metal–arena lado arena | **6,348.106691699194 mm²** |
| Diferencia relativa entre ambos lados | **0.0** |
| Referencia CAD STL contacto | 6,352.633693770655 mm² |
| Desviación de área de contacto | **−0.0712618150 %** |
| `metalTop`: número de caras | 1,116 |
| `metalTop`: área de malla | **1,326.5776804745685 mm²** |
| Desviación área `metalTop` frente STL | **−0.0231989194 %** |
| `contact_gate` | **true (aprobado)** |

La auditoría usa área de polígonos de caras OpenFOAM. Su éxito **no sustituye `checkMesh`, ni mide distancia Hausdorff al STEP, ni confirma transferencia térmica por solver**. Ambos parches están etiquetados `mappedWall` recíprocos, pero no se ejecutó acoplamiento térmico de regiones.

## Hipótesis y alternativa de mallado de un solo cambio controlado

**Hipótesis:** el generador Delaunay produce tetraedros apoyados simultáneamente en dos caras de frontera cerca de aristas. La evaluación de `cellDeterminant` en un esquema de volúmenes finitos puede encontrar direcciones independientes insuficientes en esas celdas después de separar regiones. **No arreglar cambiando el umbral** `0.001`, suprimiendo checkMesh ni declarando `Mesh OK` sobre un rechazo.

El siguiente ensayo cambia **SOLAMENTE** el generador volumétrico 3D de Gmsh:

| Variable | Control C3D05_STEP_GMSH_PILOT_01 | Candidato C3D05_STEP_GMSH_FRONTAL_01 |
|---|---|---|
| Sólidos STEP | `metalmm.STEP`, `QuickCupmm.STEP` autentificados | **los mismos** |
| Operación CAD | `occ.fragment` | **idéntica** |
| `Mesh.MeshSizeMax` | 1.8 mm | **1.8 mm** |
| `Mesh.MeshSizeMin` | 0.9 mm | **0.9 mm** |
| `Mesh.MeshSizeFromCurvature` | 18 | **18** |
| `Mesh.Algorithm3D` | **1 Delaunay (por defecto)** | **4 Frontal** |
| `Mesh.ScalingFactor` | 0.001 (m) | **0.001 (m)** |
| MSH y OpenFOAM | MSH2 ASCII; Foundation14 | **idéntico** |
| `checkMesh` | estricto, padre+regiones | **idéntico** |
| Archivo de salida | carpeta original, **intocable** | carpeta nueva, **sin sobrescribir** |

El código `build_step_mesh.py` ahora acepta `--algorithm-3d {1,4,10}`, con valor predeterminado **1** para preservar el protocolo original. `Allmesh` acepta `C3D05_ALGORITHM3D` (predeterminado 1). La nueva ruta **4 Frontal** se ejecuta en un único comando mediante [`scripts/run_frontal_pilot.sh`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_frontal_pilot.sh). Este runner ejecuta pruebas, Gmsh, conversión OpenFOAM14, `checkMesh`, separación regional, diagnóstico automático y área real del contacto **en una sola invocación**. **El candidato NO ha sido ejecutado todavía**, por lo que no se puede afirmar que disminuyan las celdas rechazadas.

**Comando único en WSL** (conserva el control):

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_frontal_pilot.sh
```

**Criterio de éxito:** `Mesh OK` estricto padre + metal + arena, cero celdas `small determinant`, concordancia de volumen y área, parches recíprocos. Si falla, guardar evidencia, comparar los tres recuentos y decidir entre malla híbrida, refinamiento de aristas, ajuste de topología o algoritmo alternativo; no probar al azar una serie de ajustes ni pasar a CFD.

Referencia de valor de Gmsh `Mesh.Algorithm3D`: [Manual oficial](https://gmsh.info/doc/texinfo/gmsh.html), opciones 1 (Delaunay), 4 (Frontal), 10 (HXT).

## Reglas globales
- **Una única instrucción de terminal por etapa**, como pide el investigador, con un orquestador en GitHub: [política permanente](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
- No modificar originales STEP, caso A `C3D-04`, ni caso B original. No sobrescribir experimentos sin autorización.
- Los resultados de **C3D-05 candidato Frontal** se anotarán solamente después de una ejecución nativa verificada. No CFD.
