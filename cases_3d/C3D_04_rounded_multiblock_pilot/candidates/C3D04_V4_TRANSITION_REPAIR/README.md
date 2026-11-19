# Caso A — C3D-04 V4: reparación de cuatro celdas metálicas basales

**Estado:** `CODE_PUBLISHED / PREPARED_NOT_RUN / NO_CFD`. Esta rama es **el mallado tridimensional curvilíneo de `blockMesh`**; no modifica ni trabaja el Caso B.

## Hallazgos nativos que motivan la nueva estrategia

El barrido V3 obtuvo resultados en WSL para T01–T06. **Malla global y arena aprobaron `checkMesh` en las seis variantes.** Solo metal falló por **4 celdas con determinante inferior a 0.001**, siempre en el entorno axial `Y = −40..−39.8 mm` (según VTK de las superficies de error). El barrido XZ de cuatro nodos interiores entre ±0.15 y ±0.45 mm no redujo **el número** de celdas defectuosas. Por tanto se interrumpe esa línea de ajuste y se estudian otras dimensiones del problema.

Se escoge `V3/T06` como **referencia de experimento, NO malla aceptada**: arena `Mesh OK`, skew máximo arena 2.841609695, no ortogonalidad máxima metal 79.34727593°, 4 celdas metal defectuosas y padre `Mesh OK`. Su área compartida medida es **6,343.771874 mm²**, idéntica en metal/arena y −0.139498 % frente al STL. La no ortogonalidad de arena ~82.06° sigue requiriendo revisión numérica incluso si se logra `Mesh OK`.

## Dos mecanismos geométricos, ensayados por separado

**V4 T01–T03 (`inner_y`):** ensayan desplazamientos en Y de solo cuatro vértices internos del núcleo metálico, IDs 89, 90, 93, 94, en la estación de transición `Y=−39.8 mm`. Sus superficies externas y la interfaz con el molde **no cambian**; esto permite probar una posible reducción de la distorsión axial sin perder la fidelidad del contorno. Los tres valores son −0.12, +0.12 y +0.18 mm respecto a Y original.

**V4 T04–T07 (`profile`):** si la intervención interior no pasa, se ensaya una interpolación de las coordenadas XZ de los **12 vértices de interfaz** (IDs 84–99 salvo los cuatro internos) y de los **8 puntos intermedios de `arc`** del hierro en `Y=−39.8 mm`. Cada nuevo perfil se construye entre las secciones originales `Y=−40` y `Y=−39.8 mm`, con factor `alpha` de 0.90, 0.78, 0.65 y 0.50. Este ajuste **sí cambia la geometría superficial en una estación**; aunque la interfaz seguirá siendo conformante porque el contorno es común a ambos materiales, debe **volver a pasar** el examen de áreas/volúmenes y, posteriormente, una comparación espacial CAD completa. No afirmar que conserva exactamente el área original.

Ningún modo altera `blockMesh` de los ensayos anteriores, el CAD original, la zona `metal/mold`, los 180 bloques, el número previsto de celdas, ni el número nominal de caras de contacto. No se alteran los parámetros de `checkMesh`, ni se corre `foamMultiRun`.

| Ensayo | Mecanismo | Parámetro | Interfaz geométrica |
|---|---|---:|---|
| T01 | `inner_y` | −0.12 mm | Sin cambios |
| T02 | `inner_y` | +0.12 mm | Sin cambios |
| T03 | `inner_y` | +0.18 mm | Sin cambios |
| T04 | `profile` | alpha 0.90 | Ajuste localizado |
| T05 | `profile` | alpha 0.78 | Ajuste localizado |
| T06 | `profile` | alpha 0.65 | Ajuste localizado |
| T07 | `profile` | alpha 0.50 | Ajuste localizado |

## Único comando de ejecución en Ubuntu WSL

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && \
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/run_v4_sweep.sh
```

El script ejecuta primero cuatro verificaciones sintéticas de generación/diff y topología; usa la **malla nativa V3/T06 ya preservada**, comprueba contra el diccionario versionado V2 la identidad de parámetros T06 (delta 0.45 mm, grading 2.65), y lanza hasta siete nuevas pruebas nativas `blockMesh` + `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` para padre/metal/mold. Tras dividir regiones, exige `mappedWall` recíprocos de **2,496 caras por lado**, coincidencia de volúmenes dentro de ±2 % de CAD y áreas de interfaz/tapa dentro de ±3 %. Cada fallo deja los `VTK`, logs y `C3D04_V4_DIAGNOSTIC.txt`. El primer candidato que pase todos los controles se conserva; **aun así no se puede lanzar CFD sin validar la forma CAD completa y la física CHT**.

La salida raíz nueva es `~/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01`, que no puede sobrescribirse si ya existe. El resumen se almacena en `C3D04_V4_SWEEP_SUMMARY.tsv`, con `SWEEP_FINAL_STATUS.txt`. Los runlogs están en `log.runner.Txx`. En ningún caso se alteran las carpetas V1, V2 o V3. **No declarar ninguna V4 aceptada antes de recibir su salida nativa de Foundation 14.**

Referencia: [comparación de V1, V2 y seis ensayos V3](../../../../docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md).
