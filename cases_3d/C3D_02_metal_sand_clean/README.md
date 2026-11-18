> **18-11-2026 — C3D02 STL v2: causa inmediata localizada en `cellZones`.** El diagnóstico real de OpenFOAM 14 conserva 589,821 celdas tras `snappyHexMesh`, pero `splitMeshRegions` confirma que ya estaban clasificadas como **4 metal + 4 mold + 589,813 exterior**. El punto de arena y el exterior quedaron en la misma región global 0 durante el `Walking from locations-in-mesh`; sólo existen interfaces `*_to_exterior`, ninguna `metal_to_mold`. No es un error de `mappedWall` ni evidencia de mejora de concavidad. Ya se prepararon **dos experimentos controlados**: `--v2-metal-only` y `--v2-mold-only`, ejecutables con `bash scripts/run_stl_v2_ablation.sh`. El informe real quedará en `~/OpenFOAM/C3D02_STL_V2_ABLATION_REPORT.txt`; fuentes STL y material C14 intactos; no CFD. [Bitácora](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — STL v2: falló la clasificación de regiones, no la integridad binaria de CAD.** La salida nativa real de `Allmesh --audit-stl-v2` evidencia que `splitMeshRegions` produjo sólo **4 celdas** en metal (`7.46352e-12 m³`) y **4** en arena (`7.49195e-12 m³`), ambos con **4 componentes desconectados** y determinante bajo. Los parches `metal_to_mold` y `mold_to_metal` **no existen** (sólo `*_to_exterior` de 24 caras). La prueba no demuestra mejora por la ausencia de celdas cóncavas. Semillas `insidePoints` clasificadas dentro de material CAD por inspección geométrica independiente; el momento de pérdida en `snappyHexMesh` no se ha identificado todavía. **No cambiar `mappedWall`, no borrar ni remallar, no CFD.** Ejecutar tras `git pull`: `bash cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_stl_v2_zones.sh` para extraer el log completo de clasificación/retención antes de tocar el diccionario. [Auditoría](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — STL v2 PRIMER INTENTO REAL: PARADA EN INTERFAZ.** Tras validar ambos STL mediante SHA y `surfaceCheck`, `Allmesh --stl-v2` produjo las dos regiones pero falló antes de sus `checkMesh`: `metal_to_mold is not mappedWall`. La etapa `STAGE_C14_MATERIALS` del mensaje era una etiqueta obsoleta; se corrigió a `CHECK_INTERFACE`. **No se sabe todavía si falta el parche, tiene otro tipo o hubo una lectura incorrecta; la terminal no incluye las entradas `polyMesh/boundary`.** No borrar la carpeta `~/OpenFOAM/c3d-better-stl-v2`, ni volver a generar la malla. Después de `git pull`, ejecutar `Allmesh --audit-stl-v2`: inspecciona los parches reales, ejecuta `checkMesh` de ambas regiones ya creadas y entrega la comparación V2 vs baseline, sin remallar ni CFD. [Bitácora](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — STL v2 definitivos desde SolidWorks, verificados fuera de Git:** el investigador confirmó como pareja correcta `metalmm(2).STL` y `QuickCupmm.STL`. Se identifican en el proyecto como `metal_v2.stl` (SHA256 `f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf`) y `mold_v2.stl` (`ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32`). Se verificó geometría cerrada y volúmenes 47.987697/102.843333 cm³. **Los dos STL binarios YA ESTÁN VERSIONADOS en `main`**, commit `e8be4afeae847411cd35b815f90748d71d1c5d90`, verificados por su SHA de objeto Git. El validador `scripts/check_stl_v2.sh` y la ruta nativa `Allmesh --stl-v2` están listos para probar la nueva triangulación. La corrida v2 siempre es nueva, en `~/OpenFOAM/c3d-better-stl-v2`, compara `checkMesh` por ambas regiones y no ejecuta CFD. Nunca reemplazar los STL originales. [Manifest](constant/geometry/STL_V2_APPROVED_SOURCES.md).

> **17-11-2026 — `c3d - better` EJECUTADO Y RECHAZADO.** La repetición en WSL reprodujo los volúmenes, celdas y **todas** las fallas de `checkMesh` del baseline: hierro 4,834 cóncavas / 3 determinantes bajos / 2 checks fallidos y arena 14,951 cóncavas / 1 determinante bajo / 1 face-tet deficiente / 3 checks fallidos. Sin mejora ni CFD. **Corrección física importante:** previamente, `Allmesh` intentaba copiar materiales C14 solo después de aprobar la malla, dejando carpetas rechazadas sin `physicalProperties` y `materials`. Ahora se copian y verifican **antes de los checks**; para completar los archivos de la carpeta ya creada sin repetir el mallado se añadió `Allmesh --stage-c14-better`, que conserva el rechazo y no ejecuta CFD. [Bitácora](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — NUEVA ENTREGA `c3d - better` (ruta compatible: `~/OpenFOAM/c3d-better`).** A petición del investigador, se programó una repetición limpia y totalmente nativa con `bash cases_3d/C3D_02_metal_sand_clean/Allmesh --better`. Usa exactamente el diccionario original L2 y `nSmoothPatch=3`, CAD y materiales C14 sin cambios. Se genera en carpeta **nueva**, no modifica `C3D02_NATIVE_OF14_01` ni `C3D02_NATIVE_SMOOTH_01`, y revisa las dos regiones incluso si una falla. `C3D_BETTER_COMPARISON.tsv` compara los logs originales con la repetición usando `Total volume` correctamente parseado. **El nombre no implica que el mallado sea mejor: `checkMesh` debe demostrarlo. No se ejecuta `foamMultiRun` ni se autoriza CFD con mallas rechazadas.** Estado: ruta publicada en GitHub, todavía no ejecutada en Ubuntu.

> **17-11-2026 — ENSAYO nSmoothPatch 3→6 EJECUTADO Y RECHAZADO:** metal 4,834→5,004 celdas cóncavas (+170, +3.52 %), arena 14,951→15,079 (+128, +0.86 %); determinantes bajos y pruebas fallidas sin mejora (2 metal, 3 arena). No CFD. **Bug corregido:** la columna `volume_m3` de `CANDIDATE_COMPARISON.tsv` leía por error el volumen mínimo de celda porque la línea de `checkMesh` contiene varios signos `=`; la puerta de volumen también estaba afectada. Se introdujo `scripts/native_checkmesh_report.sh` y pruebas Bash. Para regenerar **solo la comparación** con los logs actuales, sin volver a ejecutar OpenFOAM, usar `bash cases_3d/C3D_02_metal_sand_clean/Allmesh --compare` después de `git pull`. Produce `CANDIDATE_COMPARISON_CORRECTED.tsv` sin alterar la tabla anterior. [Resultados y auditoría](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — NUEVO ENSAYO DE SNAPPING 100 % NATIVO, SIN MODIFICAR EL CASO ORIGINAL.** Se confirmó mediante Ubuntu la existencia de seis VTK de defectos, dos para hierro y cuatro para arena. Los VTK no han sido interpretados espacialmente. Para comparar una única modificación controlada de `nSmoothPatch: 3 → 6`, ejecutar `bash cases_3d/C3D_02_metal_sand_clean/Allmesh --candidate-smooth` desde la raíz del repositorio después de `git pull --ff-only`. OpenFOAM `foamDictionary` edita **solo la copia candidata**, luego `blockMesh`/`snappyHexMesh`/`splitMeshRegions`/`checkMesh` generan resultados y `CANDIDATE_COMPARISON.tsv` de ambas regiones. Destino `~/OpenFOAM/C3D02_NATIVE_SMOOTH_01` (no se sobrescribe). **Es una hipótesis para evaluar, no un arreglo certificado ni CFD.** [Métricas, límites y bitácora](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — RESULTADO REAL del flujo nativo:** hierro 85,350 celdas (47.9793 cm³), 4,834 cóncavas y 3 determinantes bajos, **2 checks fallidos**; arena 274,788 celdas (103.389 cm³), 14,951 cóncavas, 1 determinante bajo y 1 face-tet defectuoso, **3 checks fallidos**. Ambas regiones conectadas; NO se ejecutó CFD. Para localizar defectos con **OpenFOAM nativo en copias independientes y VTK separados por material**, ejecutar el mismo `Allmesh --diagnose` después de `git pull`. El diagnóstico original ya está guardado, y la localización espacial sigue **sin verificar en Ubuntu**. [Bitácora y cifras](../../docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — Primer run nativo, diagnóstico obligatorio sin remallar.** El usuario ejecutó `Allmesh` y pasó `blockMesh`, `snappyHexMesh` y `splitMeshRegions`, pero el pipeline se detuvo en `checkMesh.metal`: *no se reportó Mesh OK*. La causa concreta **NO está demostrada** sin el log local. El comando `bash cases_3d/C3D_02_metal_sand_clean/Allmesh --diagnose` lee el `log.checkMesh.metal` existente y ejecuta exclusivamente `checkMesh` para la región mold si todavía no hay log. Resume incidencias y volúmenes en `~/OpenFOAM/C3D02_NATIVE_OF14_01/NATIVE_DIAGNOSTIC.txt` **sin reconstruir mallas, copiar materiales ni ejecutar CFD**. No volver a lanzar el modo de construcción: conservar el directorio y usar --diagnose.

> **17-11-2026 — PRIORIDAD ACTUAL: OPENFOAM NATIVO.** En C3D-02, el mallado, la creación de regiones y la comprobación de calidad se ejecutan con **utilidades OpenFOAM Foundation 14**, no con un constructor Python. El diccionario fuente `system/snappyHexMeshDict` declara `cellZone metal` y `cellZone mold`. El integrador anterior `scripts/build_c3d02.py` queda como ruta experimental histórica y **NO es el comando recomendado**. La nueva ruta de preparación de malla es `Allmesh`, descrita aquí; **NO ejecuta el solver ni afirma una malla aprobada sin evidencia real de Ubuntu**.

## Ruta actual — mallado nativo OpenFOAM (SIN Python)

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh
```

El script Bash **solo coordina** `blockMesh`, `snappyHexMesh`, `splitMeshRegions`, `checkMesh` y `foamDictionary`. No crea los diccionarios físicos mediante Python y conserva en disco el diccionario `snappyHexMeshDict` como fuente de verdad. Los archivos termofísicos se copian idénticos de C14 (hierro: `castIron`; arena: `silica`), sin modificar coeficientes. Para cada material, `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` produce logs y exportaciones de diagnóstico **nativos**. El script exige `Mesh OK`, ausencia de checks fallidos, una única región conectada, volumen compatible con CAD (±2 %) e interfaz de contacto `mappedWall` recíproca con igual número de caras.

Destino fijo sin sobreescritura: `~/OpenFOAM/C3D02_NATIVE_OF14_01/`. Su `NATIVE_BUILD_STATUS.txt` indica la etapa. Si el destino ya existe, el comando se detiene **para preservar evidencia**. No relanzar sobre la misma carpeta ni eliminar ensayos anteriores sin respaldo.

**Límite científico obligatorio:** `Allmesh` termina después de comprobar la malla. Siguen pendientes las condiciones de frontera tridimensionales (incluidas paredes hacia el exterior auxiliar), los campos `0/`, la lectura por `foamMultiRun`, la comprobación de la fuente de solidificación y la validación experimental. El exterior auxiliar no es un material del solver CHT. No interpretar una malla con `Mesh OK` como resultado CFD.

## Ruta anterior — integrador Python (legado, no prioritaria)

> **17-11-2026 — CONSTRUCTOR ÚNICO CON DIAGNÓSTICO DE ERRORES OBLIGATORIO:** `build_c3d02.py` crea automáticamente `ERROR_ZONES.json` y `ERROR_ZONES.md` desde preflight, y los actualiza al concluir o fallar. Para `global/metal/mold`, si la malla existe, analiza una copia con `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` y extrae coordenadas XYZ en mm/rangos Y de sus VTK; si falla antes de mallar, registra etapa y errores de log, sin coordenadas inventadas. Los rangos corresponden a vértices exportados, no centroides de celdas. **Ningún comando manual adicional** para localizar defectos. G1 sigue bloqueando `foamMultiRun` si no hay calidad o contacto recíproco. [Política](../../docs/AUTOMATIC_MESH_ERROR_LOCALIZATION_POLICY_ES.md).

## Registro previo 17-11-2026 — Constructor Python experimental (NO recomendado actualmente)

**Comando integral:** desde la raíz local de MasterProject actualizado, ejecutar **una sola vez**:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py
```

Este comando **intenta entregar la simulación 3D CHT**, sin exigir ejecutar a mano malladores, selectores, diagnósticos, parches o solver:
1. Valida fuentes de C3D-02 y C14; genera **una malla común para hierro+arena**, usa **ambos STL cerrados** y etiquetas `cellZone metal`/`cellZone mold`, L2 y `snap true`.
2. Usa `splitMeshRegions -cellZones '(metal mold)' -defaultRegion exterior -noFields` de **Foundation 14** para crear los **dos polyMesh regionales desde el mismo padre** y los **parches metal_to_mold/mold_to_metal de tipo mappedWall**. La región exterior es solo auxiliar, **NO** se integra en `regionSolvers`; se convierten en paredes los parches hacia ella.
3. Ejecuta `checkMesh -allGeometry -allTopology` por material, comprueba 1 región, volumen próximo a CAD (±2 %), parches recíprocos con caras positivas y conteos idénticos, `Mesh OK` verdadero y **cero tests fallidos**. Esto detecta que `checkMesh rc=0` puede esconder fallos.
4. **Solo con ambas mallas y contacto conformante aprobados**, prepara **C14** copiando sus `system/{metal,mold}`, `constant/{metal,mold}` de C3D02 controlado y sus campos `0/{metal,mold}`, reescribiendo las BC para los parches 3D, sin `empty`. El punto `pRefPoint` se adapta de y=+0.04 m (fuera de la geometría 3D) a `(0.0259 -0.0200 0.0259)` m; `fvModels` conserva los coeficientes originales, adaptando `selectionMode all` solo si la región metal carece de `cellZone metal` tras separar.
5. Arranca `foamMultiRun` solamente al cruzar la puerta G1. El producto reside en `~/OpenFOAM/C3D02_DELIVERY_01` con `BUILD_STATUS.json` y un log por operación. El código **NO borra ni sobrescribe** `C3D02_materials/`, los STL históricos o el CAD. Si el destino ya existe, muestra su estado y no lo reejecuta.

**Estado REAL a la fecha:** el código y sus tests estáticos están en revisión de GitHub; **NO se ha ejecutado el nuevo flujo de producción en la laptop**. No hay base para asegurar antes de ese run que ambas mallas pasarán G1 ni que `foamMultiRun` finalizará. A diferencia de ensayos previos, este pipeline entrega una **salida única**, éxito numérico real o bloqueo explícito con logs. No pedir al usuario ejecutar scripts exploratorios en cadena. Un `End` numérico tampoco valida todavía curvas experimentales ni parámetros JMatPro.

Fuente: [splitMeshRegions Foundation 14](https://cpp.openfoam.org/v14/splitMeshRegions_8C.html) genera los mappedWall recíprocos desde una malla común.

---

> **15-11-2026, VTK de calidad EXPORTADOS sobre COPIAS:** `quality_evidence_01/metal` produjo `concaveCells.vtk` con **2,422 celdas cóncavas**; `quality_evidence_01/mold` produjo `concaveCells.vtk` (**22,737**), `underdeterminedCells.vtk` (una con determinante <0.001) y `twoInternalFacesCells.vtk` (una advertencia topológica). Ambos `checkMesh` fallaron; metal 47.9621 cm³, arena 103.409 cm³ ya aislados. Para conocer el rango XYZ y la distribución axial de los vértices de las superficies de errores, usar **`python3 scripts/analyze_bad_mesh_vtk.py`** tras `git pull`. No requiere instalar VTK; no modifica las mallas ni ejecuta CFD. **Los vértices no equivalen a contajes de celdas defectuosas**. [Bitácora y limitaciones](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **15-11-2026 — Extracción física de arena coherente pero checkMesh RECHAZADO:** la COPIA `mold_extracted_l2_01` contiene **274,788 celdas, 103.409 cm³ (+0.550% vs CAD), una región y outerBox=0**; falla dos verificaciones por **22,737 celdas cóncavas y una con determinante <0.001**. `oldInternalFaces type=internal nFaces=97492` NO es contacto térmico válido. Metal: **85,332 celdas, 47.9621 cm³, 2,422 cóncavas y una verificación fallida**. Nuevo diagnóstico read-only en COPIAS `scripts/inspect_extracted_mesh_quality.sh` exportará conjuntos de celdas/caras/puntos problemáticos (VTK si Foundation 14 soporta flags) y parches para ubicar defectos antes de cambiar snapping. **Sin CFD ni CHT.** [Bitácora](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **ESTADO 15-11-2026 — MOLDVOLUME MEDIDO EN OPENFOAM:** `foamPostProcess` local obtuvo **274,788 celdas y 103.409 cm³** en `cellZone moldVolume` (+0.550 % vs 102.8431 cm³ CAD). El volumen GLOBAL todavía es 242.208 cm³ con exterior y 49,034 cóncavas; no es malla aceptada. Se preparó `scripts/extract_mold_zone_copy.sh`, que creará una **copia física nueva** `mold_extracted_l2_01` con solo la zona de arena mediante `subsetMesh -cellZone moldVolume -noFields` Foundation 14, comprobando volumetría, conectividad, `outerBox`, parches y calidad exhaustiva. **No ejecutado localmente aún; no CHT ni CFD.** [Evidencia](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **13-11-2026 — PRUEBA DE ZONAS FUNCIONÓ EN ETIQUETAS:** `mold_zoned_l2_01` generó `cellZone moldVolume` con **274,788 celdas** y `faceZone moldInterface` con **97,492 caras**, de 568,135 celdas globales. El aire todavía forma parte de la malla (**242.208 cm³**, `outerBox=15164`); `checkMesh` halló 49,034 cóncavas y **1 check fallido** aunque devolvió rc=0. **No sabemos todavía el volumen de la zona `moldVolume`.** Nuevo comando `bash scripts/measure_mold_zone_volume.sh` calcula exclusivamente ese volumen con `volFieldValue` Foundation 14 desde un caso sombra temporal (sin remallado/CFD). [Criterios y bitácora](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **ESTADO REAL 13-11-2026 — L3 NO AISLÓ ARENA:** `mold_level3_cast_01` con `level(3 3)` y `snap false` retuvo 2,334,117/2,334,123 celdas; volumen **242.208 cm³**, IGUAL al volumen de toda la caja auxiliar, en vez de 102.843 cm³ de arena. `outerBox=17543`; 225,732 cóncavas/1 check fallido. No aumentar niveles ni repetir cambios de punto. Se añadió `scripts/test_mold_geometric_zone.sh`, que solicita clasificación cerrada `cellZone moldVolume` / `faceZone moldInterface`, `mode inside` a L2 `snap false`; **la ejecución en Ubuntu y validación siguen pendientes**. No toca metal, geometrías ni historial; no produce por sí solo malla/CHT/CFD aceptada. [Evidencia](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **13-11-2026 — STL ARENA VALIDADO POR SURFACECHECK FOUNDATION 14:** `mold_repaired.stl` está cerrado, tiene 1 componente, aristas con dos caras, normales consistentes y **NO presenta autointersecciones**. El mallado fallido retuvo **568134/568135 celdas** en el recorte anterior a `snap`, por lo que la fuga se origina en la topología/discretización del volumen, no se ha demostrado que el STL esté dañado. Experimento controlado siguiente: **solo arena, nivel (3 3), `snap false`**, script `bash scripts/test_mold_level3_castellation.sh` en subcarpeta nueva `mold_level3_cast_01`. Los ensayos previos y la malla del metal se conservan. **Aún no ejecutado; sin CHT ni CFD.** [Guía](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **12-11-2026: recorte del molde eliminó solo 1 celda.** `snappyHexMesh`: 568,135 celdas antes del recorte y 568,134 después, sin delimitar el volumen de arena (242.142 cm³, `outerBox=15164`). El cambio de `insidePoint` fue ineficaz. El script `scripts/inspect_mold_leak.sh` se corrigió para **sí ejecutar `surfaceCheck`** en la instalación Foundation 14, sin depender de `-outputThreshold`; utiliza directorio temporal y no remalla ni toca el STL. Próxima evidencia: salida nativa de cierre y autointersecciones. Sin malla de arena ni CHT aprobadas. [Guía](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **ESTADO REAL, 12-11-2026, CORRECCIÓN DE PUNTO NO RESOLVIÓ MOLDE.** `mold_offface_01` con un `insidePoint` claramente interior al STL y fuera de caras de `blockMesh` produjo **exactamente el mismo resultado fallido:** 568,134 celdas, volumen 242.142 cm³ (STL arena 102.8431), `outerBox=15164`, 13,367 cóncavas, 10 face-tets malos y 2 comprobaciones fallidas. Causa de fuga **NO identificada todavía**; no realizar nuevos ensayos de puntos. El metal sigue en 85,332 celdas y 47.9621 cm³, `outerBox=0`, pero con 2,422 cóncavas/1 fallo. **Comando siguiente: `bash scripts/inspect_mold_leak.sh`** para inspeccionar logs y autointersecciones sin regenerar mallas. [Procedencia y evidencia](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **ESTADO C3D-02 12-11-2026, resultados efectivos `retry1`:** Hierro: **85,332 celdas; 47.9621 cm³ ≈ 47.9875 cm³ CAD; outerBox=0; 2,422 celdas cóncavas; 1 checkMesh fallido**. Arena: **568,134 celdas; 242.142 cm³ vs. 102.8431 cm³ CAD; outerBox=15,164 caras; 13,367 cóncavas + 10 face-tets; 2 checks fallidos**. *Ambas mallas siguen rechazadas y sin interfaz CHT.* Hallazgo: el `insidePoint` original de arena tenía `x=3 mm` **sobre una cara** de la caja de paso 2 mm; Foundation 14 advierte contra esa ubicación. Próximo ensayo **únicamente del molde**, sin tocar hierro: `bash scripts/try_mold_offface.sh` con punto `(0.0043 -0.0207 0.0259)` m comprobado dentro del STL. [Bitácora](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **CORRECCIÓN OF14 2026-11-12:** el primer intento de mallar metal y mold por separado se detuvo en `snappyHexMesh` por falta de la clave requerida `allowFreeStandingZoneFaces`; ambos `blockMesh` terminaron. Ya se añadió `allowFreeStandingZoneFaces false;` a la plantilla. Para **continuar sin cambiar el workspace ni remallar de cero**, usar `bash scripts/resume_material_meshes.sh` (requiere el error exacto en los logs, conserva logs previos y NO ejecuta CFD). **La malla física aún no ha sido validada**. [Bitácora y comando](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **Nuevo diseño geométrico (2026-11-12):** el primer intento de malla combinada resultó rechazado (242.130 cm³, 2 checks fallidos). Los puntos interiores eran geométricamente válidos. Se preparó `scripts/run_material_meshes.sh` para mallar por separado metal y mold en una sola carpeta `C3D02_materials`, sin usar `subsetMesh` ni reutilizar el mallado anterior; **NO ha sido ejecutado**, ni configura `mappedWall`/CHT. [Guía de la nueva etapa](../../docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **FALLO REAL DE MALLADO, 12-11-2026 (NO CORRER CFD):** prueba local de `scripts/run_mesh_only.sh`: 589,701 celdas, 242.130 cm³ (vs. 150.831 cm³ CAD), 1 componente, 14,586 cóncavas, 10 face-tets deficientes, 2 checks fallidos. El exterior no quedó excluido; la malla **NO es válida**, ni se ha creado interfaz CHT. Antes de cualquier otro ensayo de snappy, ejecutar `bash scripts/diagnose_mesh_readonly.sh` para estudiar los logs **existentes** y diferenciar problema de selección interior, geometría o parches. [Resultado y puertas](../../docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

> **ACTUALIZACIÓN 2026-11-12 — primer diccionario físico de malla preparado (SIN EJECUTAR).** Se añadió `system/snappyHexMeshDict` con `insidePoints` para dos interiores (hierro y arena), `faceZone/cellZone metal` y el script de ejecución protegida `scripts/run_mesh_only.sh`. Es una **hipótesis de mallado que requiere prueba en Ubuntu**, no una malla aceptada. El script no usa recortes de otras carpetas ni ejecuta solver; deja los logs completos y exige `checkMesh -allGeometry -allTopology`. [Manual de la etapa](../../docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

# C3D-02 — QuickCup 3D limpio: hierro y arena

**Estado 2026-11-12: NUEVO CASO FUENTE / PREPARED_NOT_RUN.** Sin malla final, sin interfaz de transferencia térmica validada y **sin solver 3D ejecutado**. Sustituye al experimento C3D-01 como línea activa, no borra su evidencia.

## Alcance innegociable
- Dos materiales: **metal** (hierro hipoeutéctico) y **mold** (arena sílica). El volumen de aire **no** es una región del solver.
- Heredar la física **sin cambios arbitrarios** desde `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef`: `constant/metal/materials/castIron`, `constant/mold/materials/silica`, respectivos `physicalProperties`, `constant/metal/fvModels`, `g`, `pRef`.
- Geometrías SolidWorks y reparación de molde con procedencia y huellas conservadas, ver `constant/geometry/README.md`.
- Crear malla conformante y **parches metal–arena recíprocos** antes de adaptar y ejecutar física C14.
- El 2D es una referencia material/metodológica: no copiar `frontAndBack` tipo `empty` ni `0/T` sin revisar los nombres de parches 3D.

## Estructura
```text
C3D_02_metal_sand_clean/
  constant/
    geometry/README.md       # STL se importan explícitamente al iniciar
    metal/materials/castIron  # copia exacta de C14
    metal/physicalProperties
    metal/fvModels            # no habilitar antes de validar cellZone
    metal/g
    metal/pRef
    mold/materials/silica     # copia exacta de C14
    mold/physicalProperties
  system/
    blockMeshDict            # caja AUXILIAR, no modelo físico
    controlDict              # preparación, no foamMultiRun
  scripts/
    prepare_geometry.sh      # MIGRACIÓN ÚNICA desde CAD histórico
    validate_sources.sh      # comparaciones byte a byte
    run_background_only.sh   # genera solo malla de fondo en carpeta local independiente
  tests/test_sources.sh      # verificación estática, no CFD
```

No existe `Allrun` de solver deliberadamente: ejecutarlo ahora sería científicamente engañoso. `constant/metal/polyMesh`, `constant/mold/polyMesh`, `0/metal`, `0/mold` y configuraciones CFD regionales se generan **después** de demostrar una malla válida y de diseñar condiciones 3D.

## Primera instalación, sin perder los STL antes de borrar nada

En Ubuntu, desde la raíz del repositorio **actualizado con el commit que integre este caso**:

```bash
cd ~/OpenFOAM/MasterProject/cases_3d/C3D_02_metal_sand_clean
bash scripts/prepare_geometry.sh
bash tests/test_sources.sh
bash scripts/run_background_only.sh
```

El primer script **copia** los 3 STL desde la carpeta histórica versionada a este directorio. Hasta comprobar las huellas y hacer `git add`/commit/push de las copias que se quieran conservar, **NO borrar las geometrías originales ni sus respaldos**. Si la fuente histórica falta, el script se detiene; obtener los STL desde la copia de SolidWorks aprobada antes de proceder. El script de malla de fondo nunca llama a `snappyHexMesh` ni al solver.

## Puertas científicas pendientes
1. Malla de fondo y STL auditados: mallas de `blockMesh` no son evidencia de metal/molde.
2. Definir **una única estrategia nueva** de mallado de dos sólidos, sin exterior, con parches de contacto conformantes; ejecutar `checkMesh -allGeometry -allTopology` en malla y regiones y comprobar volúmenes y áreas con tolerancias justificadas.
3. Crear y validar regiones `metal` y `mold`, respetando nomenclatura, interfaces `mappedWall`, continuidad térmica y conectividad.
4. Adaptar desde C14 `0/`, `system/metal`, `system/mold`, `system/fvSolution`, `controlDict` a `foamMultiRun` después de las puertas previas; revisar `fvModels` porque usa `selectionMode cellZone`.
5. Correr solamente en laptop; conservar logs y comparar B/C/experimental; puertas J0/JMatPro/G1 siguen abiertas.

[Historial y decisión](../../docs/C3D_REINICIO_20261112_ES.md) · [Errores y comandos OF14](../../docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md) · [Protocolo](../../RUN_MASTER_PROTOCOL.md). No fusionar resultados de carpetas experimentales con este caso.
