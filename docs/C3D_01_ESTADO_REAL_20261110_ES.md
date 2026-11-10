# MasterProject — C3D-01: estado experimental y numérico al 10-11-2026

**Tipo de registro:** transcripción técnica de salidas que el investigador ejecutó en su laptop con OpenFOAM Foundation 14, más comprobaciones de objetos versionados en GitHub. **No es una corrida CFD ni validación experimental.** El directorio local de prueba `~/OpenFOAM/C3D01_snappy_NTC8Dj` y sus logs completos no se han incorporado al repositorio; los números de esa prueba proceden de la terminal compartida por el investigador y requieren importación de archivos fuente antes de una auditoría reproducible.

## Identidad, material y conservación
- Repositorio: `michels-lab/MasterProject`; ruta local confirmada: `~/OpenFOAM/MasterProject`; OpenFOAM **Foundation 14**.
- Línea científica Plan D `case3d-01`; árbol técnico histórico `cases_3d/C3D_01_metal_mold`. Son **el mismo estudio**, no dos casos CFD independientes.
- `constant/geometry/metal.stl`: STL original de SolidWorks con coordenadas numéricas en **mm**, SHA-256 `fc8e6b7f3c229369b856aca7dab936347732028d9cd695499bf0e249363fb810`.
- `constant/geometry/mold.stl`: original en mm, SHA-256 `2e62e31875dc3c86dd7e6f2efe60d4c173ee4cee5e4f6ff63205c08efee3a638`.
- `constant/geometry/mold_repaired.stl`: copia derivada de `surfacePointMerge`, SHA-256 `860525e8a9fb2de483cf90f331f2753a339d82c5eee706ecfc1b8186bf49e9fe`. Conserva 3,084 triángulos. No reemplaza al original. Los dos originales fueron publicados en `main` mediante `e391f7591`; el reparado con sus registros se incorporó, tras un rebase, en `06426781f`.
- **Advertencia de difusión:** estos STL están en un repositorio GitHub público; evitar publicar otras exportaciones CAD sin revisar propiedad intelectual/permisos.

## OpenFOAM: geometría (evidencia local + logs versionados)
| Comprobación | Metal original | Molde original | Molde reparado |
|---|---:|---:|---:|
| Triángulos | 3,896 | 3,084 | 3,084 |
| Superficie cerrada | Sí | No | Sí |
| Aristas incidentes a una sola cara | 0 | 74 | 0 |
| Aristas incidentes a más de dos caras | 0 | 0 | 0 |
| Puntos casi coincidentes reportados | 0 | 16 parejas | 0 |
| Autointersecciones | No | No comprobadas aquí | No |
| `surfaceInertia` volumen con coordenadas mm | 47,987.4896432 mm³ | — | 102,843.09608 mm³ |
| Volumen expresado en cm³ | 47.9874896 | — | 102.8430961 |

El `Mass` de `surfaceInertia` se interpreta como volumen geométrico a densidad unitaria; no es una masa física del metal o la arena. El `surfaceCheck` del molde reparado y del metal acabó con `End` y sin autointersecciones. Los registros de la reparación están versionados bajo `surfaceCheck_outputs/mold_repair_trial/`. El nombre `mold_merged.stl` designa el candidato local; el archivo versionado permanente es `mold_repaired.stl`.

## Malla 3D: primera prueba local, NO ACEPTADA
1. `blockMesh` generó la caja de fondo de 58 × 72 × 58 mm (29 × 36 × 29 = **30,276 hexaedros**, nominalmente 2 mm). El caso técnico publicado tiene `units [mm];` en `system/blockMeshDict`.
2. En la prueba independiente `/home/michel/OpenFOAM/C3D01_snappy_NTC8Dj`, el investigador utilizó **copias temporales escaladas a metros con `surfaceTransformPoints`** y `snappyHexMeshConfig` para generar `snappyHexMeshDict`. Ese primer ensayo **no** verificaba `units [mm]` en geometry; el **segundo ensayo** descrito más abajo sí ejecutó esa variante, aunque también fue rechazado por calidad.
3. `snappyHexMesh` finalizó y `checkMesh -allGeometry -allTopology` informó **1,505,847 celdas**, malla 3D, un componente conectado, volumen total **0.000242201 m³ = 242.201 cm³**, malla de **toda la caja**, no exclusivamente metal + arena.
4. `refinementSurfaces`: `mold_repaired` nivel (2 2) como pared externa; `metal` nivel (2 2), `faceZone metal`, `cellZone metal`, `mode inside`. `refinementRegions` configuró ambas superficies con `mode inside; level 2`. `insidePoints`: `(0.0259 -0.02 0.0259)` y `(0.003 -0.02 0.0259)` m.
5. La zona `metal` aparece con **383,788 etiquetas de celda**, pero su **volumen físico, pertenencia, interfaz y no solapamiento NO están demostrados**; tampoco hay `cellZone mold` comprobada ni separación multirregión. `Number of regions: 1` en `checkMesh` es el número de componentes conectados, no una certificación de acoplamiento térmico.
6. Resultado de calidad: máximo de no ortogonalidad **68.2102°**, máximo skewness **2.60187**, **23 caras** con tetraedros de descomposición deficientes y **6,974 celdas cóncavas**; `checkMesh` termina con **Failed 2 mesh checks**. También se informaron avisos de snapping con desplazamientos que atraviesan caras cercanas. **Esta malla no está aceptada para CFD.**
7. La resolución de **0.5 mm** es el objetivo nominal de dos niveles octree desde celdas de 2 mm; no es una cota máxima garantizada, ni prueba de independencia de malla. La propuesta de refinamiento del PR #18 sigue pendiente de integrar y contrastar.

## Reglas de reproducibilidad y errores aprendidos
- `snappyHexMeshConfig` en Foundation 14 **no admite `-case`**; ejecutar desde el directorio del caso (`cd "$TRIAL"`). Las opciones deben comprobarse con `snappyHexMeshConfig -help`.
- No activar `set -u` antes de `source /opt/openfoam14/etc/bashrc`: se observó el error `ZSH_NAME: unbound variable`.
- Los `*.STL` originales con extensión mayúscula no fueron leídos correctamente por el `surfaceCheck` usado; las copias `*.stl` minúsculas se analizaron sin problemas.
- Para próximas pruebas preferir los **STL originales en mm** y declarar `units [mm];` en la geometría del diccionario Foundation 14, **sin doble escalado**; no presentar como comprobada una ejecución todavía no realizada bajo esa modalidad.
- Ejecutar mallas y CFD **solo en la laptop**; GitHub almacena fuentes, scripts, logs seleccionados y auditorías estáticas. Las carpetas de pruebas `~/OpenFOAM/C3D01_snappy_*` están fuera del repositorio y no se sincronizan automáticamente.
- No sobrescribir `constant/polyMesh`, no ejecutar `Allclean` sobre casos históricos y no hacer `git push --force` si existen nuevos commits remotos.


## Segundo ensayo local: unidades nativas y etapa castellated sin snapping (10-11-2026)

**Fuente:** terminal del investigador, carpeta local `/home/michel/OpenFOAM/C3D01_castellated_7X7rLt`. Este caso y sus logs completos **aún no están versionados en Git**. Se copió la configuración del primer ensayo a una carpeta nueva, se utilizaron los STL originales versionados en **mm** con `units [mm];` en las dos entradas `geometry` y se establecieron `snap false` y `addLayers false`. `blockMesh`, `snappyHexMesh -overwrite` y `checkMesh -allGeometry -allTopology` corrieron en la laptop; **no hubo simulación del solver**.

| Métrica checkMesh | Ensayo 1: snappy con snap, copias en m | Ensayo 2: castellated sin snap, STL en mm + units [mm] |
|---|---:|---:|
| Celdas | 1,505,847 | 1,505,826 |
| No ortogonalidad máxima | 68.2102° | 25.2394° |
| Skewness máxima | 2.60187 | 0.333333 |
| Caras con face tets deficientes | 23 | 0 (Face tets OK) |
| Celdas cóncavas | 6,974 | **21,353** |
| Verificaciones fallidas | 2 | **1** |

**Conclusión acotada:** el ensayo con `units [mm];` ha demostrado ejecutarse, sin conversión explícita de los STL fuente. Desactivar snapping eliminó el aviso de face tets y redujo no ortogonalidad/skewness, pero **no eliminó concavidad: la incrementó**. Esto impide adjudicar toda la concavidad al snapping; se requiere localizar defectos de la etapa castellated y verificar volúmenes/interfaces antes de otro diseño de malla. Los casos comparados **también difieren en el mecanismo de lectura de unidades**, así que no atribuir diferencias únicamente a snapping sin un control adicional.

**Gates invariables:** ambas mallas **rechazadas** para CFD térmico 3D; las cantidades de células no son volúmenes validados de metal y arena. El exterior de la caja continúa sin excluirse con evidencia suficiente. Preferencia del investigador: comandos ejecutables **directamente en OpenFOAM sin Python**. No relajar criterios de `checkMesh` para declarar éxito; antes localizar concave cells, diagnosticar zona exterior, crear regiones físicas complementarias y volver a verificar.


## Exportación de defectos a VTK (10-11-2026, evidencia local)

El investigador ejecutó en **ambos** casos `checkMesh -allGeometry -allTopology -writeSurfaces -surfaceFormat vtk -writeSets`, siempre en su laptop. Los comandos terminaron y los defectos fueron exportados a `postProcessing/checkMesh/constant/` y `constant/polyMesh/sets/`; `checkMesh` **siguió informando fallos**. La finalización del comando no equivale a aprobación de calidad.

- Caso con snapping `C3D01_snappy_NTC8Dj`: `nearPoints.vtk`, `lowQualityTetFaces.vtk`, `concaveFaces.vtk`, `concaveCells.vtk`. Sets: `concaveCells` **6,974**, `concaveFaces` **30**, `lowQualityTetFaces` **23**, además de `nearPoints` y `wrongFaces`.
- Caso castellated sin snapping `C3D01_castellated_7X7rLt`: `nearPoints.vtk`, `concaveCells.vtk`; set `concaveCells` **21,353**; `Face tets OK`.
- **Estado:** los VTK y sets **son archivos locales**, no están subidos a GitHub; no se ha estudiado su distribución espacial ni su intersección con la `cellZone metal`. El próximo paso debe cuantificar defectos dentro/fuera de metal y visualizar agrupaciones, evitando atribuirlos sin pruebas a mold/snap o a un supuesto CFD ya validado.

## Próximas puertas técnicas (abiertas)
1. Archivar `log.blockMesh`, `log.snappyHexMesh`, `log.checkMesh.final` y `snappyHexMeshDict` de la prueba local en un paquete nuevo e identificado por SHA, sin sustituir evidencia previa; cotejar cantidad y volumen real de `cellZone metal`.
2. Construir un segundo ensayo explícito con STL originales `units [mm]`, zonas metal y arena complementarias, interfaz/faceZones para transferencia de calor conjugada y eliminación correcta del aire exterior; demostrar que el sólido NO incluye el volumen del metal.
3. Diagnosticar los **23 face tets** y **6,974 concave cells**; comparar etapas castellated/snap sin relajar artificialmente los criterios de aceptación.
4. Verificar `splitMeshRegions`/patches conjugados, volúmenes, áreas, `checkMesh` por región, conservación de energía y sensibilidad de malla. Solo después preparar solver y curvas de enfriamiento.
5. Mantener puertas **J0** (propiedades JMatPro reales) y **G1** (validación experimental) **ABIERTAS**. No cambiar estados históricos B/C ni declarar un 3D `RUN_VERIFIED`.

## Puente a documentos vivos
[README](../README.md) · [Manual ES](../OPENFOAM_COMMAND_MANUAL_ES.md) · [Manual EN](../OPENFOAM_COMMAND_MANUAL_EN.md) · [Guía de casos](../CASE_GUIDE_ES.md) · [Índice documental](DOCUMENTATION_INDEX.md) · [Bitácora ES](../PROJECT_AUDIT_LOG_ES.md) · [Bitácora EN](../PROJECT_AUDIT_LOG_EN.md) · [Validación ES](../VALIDATION_MATRIX_ES.md) · [Plan D](../cases_3d/README.md).

## Distribución de defectos respecto a la zona etiquetada metal (10-11-2026)

**Fuente:** comparación local de identificadores de `constant/polyMesh/sets/concaveCells` con `constant/polyMesh/cellZones`, mediante `awk`, `sort` y `comm` sobre las dos mallas. Resultados reportados por el investigador; los sets y mallas **no** están archivados íntegramente en GitHub.

| Ensayo | Celdas en `cellZone metal` | Cóncavas totales | Cóncavas dentro de zona metal | Cóncavas fuera de zona metal |
|---|---:|---:|---:|---:|
| `C3D01_snappy_NTC8Dj` | 383,788 | 6,974 | **1** | **6,973** |
| `C3D01_castellated_7X7rLt` | 383,788 | 21,353 | **0** | **21,353** |

En el primer ensayo, la proporción de defectos **que se encuentran dentro de la zona etiquetada metal** es aproximadamente **0.0143 %** (1/6,974); la incidencia de celdas cóncavas **entre celdas de metal** es aproximadamente **0.00026 %** (1/383,788). En el segundo ensayo ambas cantidades son cero. **No se debe equiparar «fuera de cellZone metal» con arena:** el mallado conserva aire/volumen exterior de la caja. Tampoco está medido el volumen físico real de `cellZone metal` ni comprobada una interfaz CHT conforme. La concavidad por sí sola no determina el error térmico hasta localizarla respecto a zonas e interfaz.

**Próxima separación espacial:** clasificar defectos que están fuera del envolvente AABB del STL reparado (x = 0..51.8 mm, y = -65.5..0 mm, z = 0..51.8 mm); estos son exterior inequívoco. Los defectos dentro del envolvente todavía pueden estar en arena, cavidad o aire y requieren una prueba geométrica más precisa.

## Concavidad fuera del envolvente del molde (10-11-2026)

El investigador utilizó `topoSet` con `cellToCell` y `boxToCell` para intersectar `concaveCells` con el **AABB** del STL del molde reparado (x = 0..0.0518 m, y = -0.0655..0 m, z = 0..0.0518 m), sin remallar.

| Ensayo local | Cóncavas totales | Centros dentro AABB | Centros fuera AABB | Fuera AABB (%) |
|---|---:|---:|---:|---:|
| `C3D01_snappy_NTC8Dj` | 6,974 | 2,194 | 4,780 | **68.54 %** |
| `C3D01_castellated_7X7rLt` | 21,353 | 5,700 | 15,653 | **73.31 %** |

Estos valores se suman a la observación previa de que solo **1** y **0** celdas cóncavas, respectivamente, pertenecen a la `cellZone metal`. **Lectura correcta:** al menos 4,780 / 15,653 centros defectuosos están inequívocamente fuera de la caja que contiene el molde y no tienen por qué formar parte de la futura malla física. Sin embargo, estar dentro del AABB **no demuestra** pertenencia al volumen material de la arena; hay que clasificar geométricamente la superficie cerrada del molde. Tampoco se garantiza que recortar la caja elimine exactamente ese número de defectos en una **malla regenerada**, pues la topología puede cambiar. La primera prueba sigue fallando 2 checks, la segunda 1; ambas rechazadas para CFD 3D.

## Clasificación material por superficies cerradas STL (10-11-2026)

Evidencia adicional transcrita del investigador: `topoSet` con `surfaceToCell`, `useSurfaceOrientation true`, `includeCut false`, `includeInside true`, `includeOutside false`, para `mold_repaired.stl` y `metal.stl` en la geometría **temporal en metros** del primer ensayo. Ambas mallas se clasificaron mediante la misma geometría de referencia en metros. Los conteos son de selección geométrica **de centros de celdas**, no de volúmenes integrados o de patches CHT completos.

| Conteo | `C3D01_snappy_NTC8Dj` | `C3D01_castellated_7X7rLt` |
|---|---:|---:|
| Celdas dentro del STL molde | 825,994 | 825,918 |
| Celdas dentro del STL metal | 383,783 | 383,788 |
| Celdas cóncavas dentro de molde | **15** | **0** |
| Celdas cóncavas dentro de metal | **0** | **0** |
| Celdas cóncavas fuera de ambos STL | **6,959** (99.78 % de 6,974) | **21,353** (100 % de 21,353) |
| Celdas clasificadas dentro de ambos STL | 0 | 7 |
| Celdas de `cellZone metal` fuera de interior STL metal | 7 | 0 |

**Interpretación:** la gran mayoría de defectos aparece fuera de los materiales seleccionados. Las **15 celdas cóncavas clasificadas como molde** de la primera malla merecen atención, como también las 23 caras de mala descomposición tetraédrica cuyo lugar aún no se ha discriminado. Las 7 coincidencias y 7 discrepancias de clasificación en torno al metal indican que la interfaz debe verificarse, pero **NO** prueban por sí solas interpenetración real de STL. Una malla de prueba recortada puede eliminar mucho exterior; no valida automáticamente la conectividad térmica metal–arena, calidad ni conservación geométrica: `surfaceToCell` con `includeCut false` no hace una construcción de interfaz conformante. Se requiere geometría+volumen+parches físicos antes de CFD.

## Recorte real `subsetMesh` metal + molde — prueba local C3D01_materials_H0qgJN (10-11-2026)

El investigador creó `~/OpenFOAM/C3D01_materials_H0qgJN` como copia de la primera malla con snapping y seleccionó la unión de `insideMoldSTL` + `insideMetalSTL` con `topoSet`. La primera sintaxis `subsetMesh materialVolume -case ...` falló por pasar un argumento posicional no permitido; la corrección nativa Foundation 14 `subsetMesh -case "$CASE" -cellSet materialVolume -noFields` **terminó**. No se ejecutó CFD.

| Indicador | Antes de recortar | Después de recortar |
|---|---:|---:|
| Celdas | 1,505,847 | **1,209,777** |
| Volumen total malla | 242.201 cm³ | **151.230 cm³** |
| Componentes topológicas conectadas | 1 | **2** (`Number of regions: 2` en checkMesh) |
| Concave cells | 6,974 | **15** |
| Caras de baja calidad face-tets | 23 | **8** |
| Celdas con determinante <0.001 | No reportadas | **17** |
| No ortogonalidad máxima | 68.2102° | 68.2102° |
| Skewness máximo | 2.60187 | 2.60187 |
| `checkMesh` | 2 tests fallidos | **3 tests fallidos** |

Los volúmenes geométricos de los STL, 47.9874896432 cm³ (metal) + 102.84309608 cm³ (molde reparado) = **150.8305857232 cm³**, frente a los **151.230 cm³** de la unión recortada; diferencia ~**0.3994 cm³** (~0.26 %). Es **comparación aproximada de volumen global**, no prueba de volumen ni interfaz por región.

La malla recortada tiene estos patches: `outerBox` **0** caras, `mold_repaired` **114,807** caras (`wall`), `oldInternalFaces` **8,384** caras (`type internal` en la salida); esta frontera debe interpretarse con extrema precaución ya que `subsetMesh` expone caras sin preservar necesariamente tipos de frontera; **no constituye un par de interfaces térmicas metal–arena**. `Number of regions: 2` describe componentes desconectadas, no necesariamente dos regiones CFD físicamente acopladas. El nuevo `checkMesh` reportó 8 face-tets deficientes, 17 celdas de pequeño determinante y 15 cóncavas. **Malla NO aceptada para solver**. Logs `log.subsetMesh`, `log.checkMesh` aún están en carpeta local de prueba, no archivados en Git.

**Reentrada técnica:** separar/nombrar componentes sobre otra copia con `splitMeshRegions` para inspección, verificar volúmenes y fronteras por región, corregir interfaz y 3 fallos geométricos antes de cualquier simulación térmica. Evitar confundir componentes topológicas con acoplamiento de calor.

## Separación topológica de la unión recortada (10-11-2026)

**Evidencia local del investigador:** `splitMeshRegions -case ~/OpenFOAM/C3D01_regions_Xd1POM -disconnected -noFields` sobre una **copia** de `C3D01_materials_H0qgJN` se completó, produciendo dos mallas. La utilidad informó **`No interfaces to add`**, de modo que esta variante **NO dispone de parches de contacto térmico conjugado generados automáticamente**. No se ejecutó ningún solver.

| Resultado por región | `region1` (arena inferida) | `region2` (metal inferido) |
|---|---:|---:|
| Celdas | 825,994 | 383,783 |
| Volumen malla | 103.256 cm³ | 47.9735 cm³ |
| Volumen STL original | 102.843096 cm³ | 47.987490 cm³ |
| Desviación relativa STL (aprox.) | +0.402 % | −0.029 % |
| No ortogonalidad máx. | 64.9304° | 68.2102° |
| Skewness máx. | 2.60187 | 1.42431 |
| Caras deficientes face tets | 6 | 2 |
| Celdas con determinante <0.001 | 14 | 3 |
| Celdas cóncavas | 15 | 0 (no reportadas) |
| `checkMesh` | **3 fallos** | **2 fallos** |
| Patch `mold_repaired` | 90,093 caras (`wall`) | 24,714 caras (`wall`) |
| Patch `oldInternalFaces` | 3,077 caras (`internal`) | 5,307 caras (`internal`) |

Los volúmenes apoyan la identidad de los dos componentes pero NO demuestran que sus superficies de contacto coincidan. Los conteos de `oldInternalFaces` son diferentes y no constituyen un par de patches acoplados. **No es válido iniciar CFD conjugado con esta separación.**

**Ruta técnica siguiente:** inspeccionar sobre **otra copia de la malla original conectada** `C3D01_snappy_NTC8Dj` la opción propia de OpenFOAM 14 `splitMeshRegions -cellZones 'metal' -noFields`, en lugar de `-disconnected`, para comprobar si la frontera interna de la `cellZone metal` produce patches emparejados. La región restante seguirá incluyendo exterior de la caja; la prueba NO constituye el dominio final ni acepta calidad `checkMesh`. Fuente de sintaxis: código oficial OpenFOAM-14 de `splitMeshRegions.C`, opción `-cellZones <names>`.
