# C3D-02 — Diagnóstico nativo de mallas, 17-11-2026

## Procedencia
Evidencia **real** remitida por el investigador desde Ubuntu WSL con OpenFOAM Foundation 14:
`bash cases_3d/C3D_02_metal_sand_clean/Allmesh` produjo `BLOCKED / checkMesh.metal`; el investigador ejecutó
`bash cases_3d/C3D_02_metal_sand_clean/Allmesh --diagnose`, que leyó el log metálico existente y ejecutó únicamente `checkMesh` para la arena.

Carpeta local de evidencia: `~/OpenFOAM/C3D02_NATIVE_OF14_01`. No se ha corrido `foamMultiRun` ni validado CHT.

## Resultados originales de checkMesh -allGeometry -allTopology

| Métrica | metal | mold |
|---|---:|---:|
| cells | 85,350 | 274,788 |
| Total volume (m³) | 4.79793e-05 | 0.000103389 |
| Volumen (cm³) | 47.9793 | 103.389 |
| CAD (cm³) | 47.9874896432 | 102.84309608 |
| Desviación malla/CAD | -0.0171 % | +0.5308 % |
| Number of regions | 1 (OK) | 1 (OK) |
| Non-orthogonality max / mean (°) | 35.4722 / 9.76134 | 52.0242 / 9.51012 |
| Max skewness | 3.15367 (OK) | 3.36715 (OK) |
| Concave cells | 4,834 (5.664 %) | 14,951 (5.441 %) |
| Small determinant cells (<0.001) | 3 | 1 |
| Low-quality/negative face decomposition tets | 0 (Face tets OK) | 1 |
| Faces with concave adjacent-edge angles | sin dato | 31 (advertencia) |
| Failed mesh checks | **2** | **3** |
| Resultado | **RECHAZADA** | **RECHAZADA** |

Los errores de calidad están presentes a pesar de que los volúmenes y la conectividad global son coherentes. `checkMesh` puede devolver código de salida 0 aun habiendo fallado comprobaciones: **no interpretar RC=0 como Mesh OK**.

## Qué está demostrado y qué todavía no

- `blockMesh`, `snappyHexMesh` y `splitMeshRegions` terminaron sin error de proceso en el flujo nativo; el script encontró interfaz `mappedWall` recíproca con conteo de caras coincidente. **No hay todavía prueba de cobertura/área física correcta de interfaz.**
- `checkMesh` encontró un componente en cada región y volúmenes próximos al CAD.
- La **ubicación espacial** de las celdas con concavidad, determinante bajo y face tets defectuosos **no está disponible en los fragmentos de log recibidos**. No atribuir el defecto a interface, aristas, puntas, snap o STL sin inspeccionar VTK/ParaView.
- Ninguna corrida del 3D está físicamente validada; no bajar umbrales ni ejecutar CFD.

## Diagnóstico siguiente integrado a OpenFOAM, sin Python

Se amplió el mismo `Allmesh --diagnose`: además de consultar los logs, genera **copias independientes de cada `polyMesh` regional** bajo `native_quality/metal` y `native_quality/mold`; llama a `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` **en cada copia**, conservando archivos VTK separados por material y evitando colisión de nombres. La primera ejecución se limita al estado actual; si las carpetas de diagnóstico ya existen, se preservan. No remalla, no reescribe materiales ni ejecuta solver.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --diagnose
```

Resultado esperado: `~/OpenFOAM/C3D02_NATIVE_OF14_01/NATIVE_DIAGNOSTIC.txt`, los `native_quality/{metal,mold}/log.checkMesh` y los VTK específicos exportados por OpenFOAM. La ejecución del nuevo diagnóstico aún no está confirmada en Ubuntu.

## Criterio de la próxima corrección

Inspeccionar las **geometrías reales de defectos** en ParaView superpuestas a las mallas y STL; comprobar si se concentran en interfaces de materiales, aristas o extremos. Solo entonces diseñar una variante controlada de `system/snappyHexMeshDict` (p. ej. opciones de `snapControls` o refinamiento localizado) sobre carpeta **nueva**, documentando comparación de celdas cóncavas, determinantes, volumen CAD y contacto. Conservar siempre intactos C14 y los casos históricos.

## 17-11-2026 — VTK de defectos confirmados y primer ensayo nativo controlado

El investigador ejecutó de nuevo `Allmesh --diagnose` y confirmó **6 VTK en copias físicas** independientes:

- Metal: `concaveCells.vtk` y `underdeterminedCells.vtk`.
- Molde: `concaveCells.vtk`, `concaveFaces.vtk`, `lowQualityTetFaces.vtk` y `underdeterminedCells.vtk`.

No se han remitido aún coordenadas, capturas de ParaView ni métricas de distribución espacial: **la localización real de los defectos sigue desconocida**. No confundir la mera exportación VTK con inspección espacial.

Para producir una primera comparación numérica reproducible sin depender de Python, se preparó un ensayo nativo de sensibilidad al snapping. **Hipótesis, no corrección probada:** duplicar el valor de `snapControls/nSmoothPatch`, de 3 a 6, manteniendo fijos el CAD, el refinamiento L2, las zonas, los restantes controles y los materiales C14.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --candidate-smooth
```

Este comando copia los diccionarios de origen a `~/OpenFOAM/C3D02_NATIVE_SMOOTH_01`, modifica **solo esa copia** mediante `foamDictionary -entry snapControls/nSmoothPatch -set 6`, ejecuta `blockMesh`, `snappyHexMesh`, `splitMeshRegions` y `checkMesh` nativos en **ambos** materiales y entrega una tabla `CANDIDATE_COMPARISON.tsv` con los conteos base/candidato. El caso anterior `C3D02_NATIVE_OF14_01` se utiliza como **referencia de solo lectura**. No sobrescribe carpetas existentes, no baja criterios de calidad, no ejecuta `foamMultiRun`. Si cualquiera de las regiones no pasa, informa rechazo.

**Estado:** solo código preparado y commit; ejecución del experimento aún pendiente de confirmar en Ubuntu. Si la prueba no mejora simultáneamente calidad y compatibilidad geométrica, no declarar avance; revisar VTK en ParaView para diseñar refinamiento localizado, no encadenar cambios a ciegas.


## 17-11-2026 — Prueba real `nSmoothPatch=6`: RECHAZADA

El investigador ejecutó en Ubuntu:

```bash
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --candidate-smooth
```

Resultados de `checkMesh` (ambas regiones):

| Región | Celdas cóncavas base | Candidata | Diferencia | Determinantes bajos base→candidata | Tetraedros defectuosos base→candidata | Checks fallidos |
|---|---:|---:|---:|---|---|---|
| metal | 4,834 | 5,004 | +170 (+3.52 %) | 3→3 | 0→0 | 2→2 |
| mold | 14,951 | 15,079 | +128 (+0.86 %) | 1→1 | 1→1 | 3→3 |

Ambas mallas mantienen **el mismo número de celdas** (metal 85,350; mold 274,788). Aumentar `nSmoothPatch` de 3 a 6 **empeoró la concavidad** y no resolvió ninguno de los checks fallidos. **No adoptar la variante para CFD**. No se puede inferir la distribución espacial de defectos a partir del recuento.

### Bug de posprocesamiento detectado y corregido

El reporte original `CANDIDATE_COMPARISON.tsv` de la variante mostraba en `volume_m3` el **mínimo volumen de celda** (`3.62642e-11` para metal base, `3.01694e-11` para mold base), no el `Total volume` de la región (`4.79793e-05` y `0.000103389` m³, respectivamente). La línea de `checkMesh` contiene **tres signos =**, y el AWK anterior leía el primero. Este defecto afectaba **también el rechazo de candidatos en la puerta de volumen CAD**. Es un bug del script Bash, no de OpenFOAM.

Se centralizó la lectura de `Total volume` en `scripts/native_checkmesh_report.sh`, buscando explícitamente `Total volume =` antes de tomar el valor. Se añadió el test Bash `tests/test_native_checkmesh_report.sh` con formato de log real y los cuatro conteos de concavidad observados. La corrección **no vuelve aceptable** el candidato: las 2+3 fallas de malla persisten.

Para **recalcular desde los logs existentes sin remallar**, ejecutar:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --compare
```

Salida nueva: `~/OpenFOAM/C3D02_NATIVE_SMOOTH_01/CANDIDATE_COMPARISON_CORRECTED.tsv`. Se preserva la tabla defectuosa original para auditoría, no se sobrescriben logs, no se modifica C14 ni se ejecuta OpenFOAM/CFD. **Aún no se ha ejecutado este modo corregido en Ubuntu del investigador.**

### Próxima decisión técnica

Revisar espacialmente los VTK de celdas cóncavas, celdas con determinantes bajos y cara tetraédrica defectuosa en ParaView **antes** de adoptar ajustes de refinamiento o snapping. Mantener ambos experimentos como baseline/candidato rechazado. No relajar `checkMesh` para superar la puerta.

## 17-11-2026 — Repetición limpia identificada como c3d - better

A solicitud expresa del investigador, el siguiente ensayo lleva el nombre **c3d - better**, almacenado como `~/OpenFOAM/c3d-better` para usar una ruta sin espacios compatible con herramientas OpenFOAM.

Comando: `bash cases_3d/C3D_02_metal_sand_clean/Allmesh --better`.

La prueba repite el mallado original con el diccionario fuente L2 y `nSmoothPatch=3` en nueva carpeta y comprueba **ambas** regiones con OpenFOAM. No continúa automáticamente al solver y no toca los STL, valores físicos C14 ni ensayos históricos. Su tabla `C3D_BETTER_COMPARISON.tsv` conserva métricas de los logs del baseline y nueva malla, incluidos volúmenes totales. El nombre **no expresa un logro de calidad** antes de ejecutar `checkMesh`. Todavía no se ha ejecutado en Ubuntu.

## 17-11-2026 — `c3d - better`, REPETICIÓN REAL EJECUTADA: sin mejora

El investigador ejecutó `Allmesh --better` en Ubuntu y entregó el contenido de `~/OpenFOAM/c3d-better/C3D_BETTER_COMPARISON.tsv`. Los cuatro renglones son:

| Fuente | Región | Celdas | Volumen total (m³) | Celdas cóncavas | Determinantes bajos | Tets defectuosos | Checks fallidos | Mesh OK |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BASELINE | metal | 85350 | 4.79793e-05 | 4834 | 3 | 0 | 2 | 0 |
| BETTER | metal | 85350 | 4.79793e-05 | 4834 | 3 | 0 | 2 | 0 |
| BASELINE | mold | 274788 | 0.000103389 | 14951 | 1 | 1 | 3 | 0 |
| BETTER | mold | 274788 | 0.000103389 | 14951 | 1 | 1 | 3 | 0 |

**Conclusión:** la repetición reproduce las **métricas de calidad, conteo y volumen**, pero no demuestra malla byte-idéntica ni mejora la calidad. `c3d-better` está **RECHAZADO**, no solver ni CHT, aunque la carpeta lleve ese nombre. El ensayo con `nSmoothPatch=6` tampoco mejoró.

### Defecto adicional de montaje físico descubierto

`Allmesh` copiaba los archivos `constant/{metal,mold}` de C14 **después** de la validación completa de calidad. En consecuencia, un ensayo rechazado como `c3d-better` quedaba con mallas regionales, pero sin las propiedades termofísicas físicas **copiadas a su carpeta de entrega** (aunque las fuentes controladas continuaran presentes en el repositorio). Esta ausencia de copia no explica las concavidades, porque los materiales no intervienen en `snappyHexMesh`.

**Corrección publicada:** `scripts/stage_c14_materials.sh` copia exclusivamente las siete entradas controladas después de `splitMeshRegions` y **antes** de `checkMesh`, y las compara byte por byte con C14; rechaza sobrescrituras diferentes. `Allmesh --stage-c14-better` permite completar **sin remallar** la carpeta ya creada `~/OpenFOAM/c3d-better`, dejando `C14_MATERIALS_VERIFIED.txt`. El estado de rechazo de malla no cambia ni se autoriza CFD. Hay pruebas de regresión aisladas en `tests/test_native_stage_c14.sh`. Todavía no se ha ejecutado esta verificación nueva en Ubuntu.

### Decisión de investigación

No repetir nuevamente la misma malla, no adoptar `nSmoothPatch=6`, no disminuir criterios. Los `concaveCells.vtk`, `underdeterminedCells.vtk`, `lowQualityTetFaces.vtk` ya exportados para el baseline deben **localizarse visual/espacialmente en ParaView** para decidir si conviene cambiar controles de snap, discretización o tratamiento de intersecciones/superficies; sin evidencia de posiciones no atribuir la causa.

## 17-11-2026 — STL v2: primer mallado en laptop bloqueado en interfaz

Evidencia **real** recibida del usuario, luego de `git pull --ff-only` y `check_stl_v2.sh`:
- `metal_v2.stl` y `mold_v2.stl`: SHA-256 correctos y `surfaceCheck` terminó para ambos en OpenFOAM Foundation 14 (el script suprimía el detalle de superficie; no inferir aún área/cierre del log no recibido).
- `bash cases_3d/C3D_02_metal_sand_clean/Allmesh --stl-v2` llegó a la validación de parches regionales y terminó con **`ERROR [STAGE_C14_MATERIALS]: metal_to_mold is not mappedWall`**. El mensaje de etapa era **incorrecto**: el archivo de materiales ya había sido copiado y controlado, pero `STAGE` no se actualizaba al iniciar la inspección de interfaz. El error de `mappedWall` puede significar parche ausente, tipo no conforme o un problema del parser; **la terminal compartida no contiene el `polyMesh/boundary` real**. No afirmar todavía cuál de esas posibilidades ocurrió.
- Se conservó `~/OpenFOAM/c3d-better-stl-v2`. Ni el script ejecutó `checkMesh` regional (se detuvo antes), ni se ejecutó `foamMultiRun`. No hay comparación de calidad v2 demostrada aún.

**Corrección de trazabilidad:** el pipeline cambia ahora a `STAGE=CHECK_INTERFACE` después de completar con éxito los materiales de C14. Se añadió `scripts/native_interface_audit.sh` (lector Bash/awk del archivo real `polyMesh/boundary`) y `Allmesh --audit-stl-v2` para diagnosticar **el mallado ya generado**, sin `blockMesh`, `snappyHexMesh` ni `splitMeshRegions` adicionales. El modo genera `STL_V2_INTERFACE_AUDIT.txt` con todos los parches/tipos/`nFaces`, incluye extractos del log original `splitMeshRegions`, y realiza `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` en los dos `polyMesh` **existentes** para recuperar las métricas de calidad sin volver a mallar. Genera `STL_V2_COMPARISON_AUDIT.tsv` desde los logs, preservando el estado de fallo original. La ejecución del nuevo modo en Ubuntu aún está pendiente.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --audit-stl-v2
```

**Criterio de decisión científica:** si la interfaz realmente falta, inspeccionar el contacto CAD y la asignación de celdas y superficies del nuevo STL antes de cambiar `mappedWall` a mano. Si el parche existe como `mappedWall` y el script lo interpretó mal, corregir solamente el parser; si hay un tipo distinto o no coincide el número de caras, no falsificar contacto térmico. Independientemente, evaluar las métricas de ambas mallas regionales, los volúmenes y los defectos VTK antes de autorizar CFD.

## 17-11-2026 — Evidencia posterior: OpenFOAM encontró sólo 4 celdas por material (RECHAZO GRAVE)

El investigador ejecutó de verdad `Allmesh --audit-stl-v2` en Ubuntu y proporcionó la salida literal. El historial de `NATIVE_BUILD_STATUS.txt` confirma el bloqueo inicial (etapa desactualizada en el log local anterior) y la nueva auditoría demuestra:
- BASELINE: `metal_to_mold` y `mold_to_metal` son parches `mappedWall` recíprocos, **27,501 caras** por dirección.
- STL v2: ambos parches `metal_to_mold` y `mold_to_metal` **NO EXISTEN**. Sólo hay `metal_to_exterior` y `mold_to_exterior`, ambos con **24 caras**.
- `checkMesh` nativo del hierro v2: **4 celdas**, **4 regiones desconectadas**, `Total volume = 7.46352e-12 m³`, 4 células con determinante inferior a 0.001, **1 mesh check fallido**, no `Mesh OK`.
- `checkMesh` nativo de arena v2: **4 celdas**, **4 regiones desconectadas**, `Total volume = 7.49195e-12 m³`, 4 células con determinante inferior a 0.001, **1 mesh check fallido**, no `Mesh OK`.
- **No confundir cero celdas cóncavas con mejora**: las regiones son restos minúsculos, no volúmenes físicos; no es válida la comparación de calidad.
- **No ejecutar CFD ni reparar a mano `mappedWall`**. `splitMeshRegions` no dispone de una cara de contacto metal–mold en la malla generada; cambiar etiquetas no reconstruiría el dominio.

Auditoría geométrica independiente de los STL definitivos (`metal_v2.stl`, `mold_v2.stl`) usando inspección de triangulación: superficies watertight con orientación coherente, bbox metal aprox. `x,z 7.65–44.15 mm; y -40–0 mm`; arena `x,z 0–51.8 mm; y -65.5–0 mm`, volúmenes CAD `47987.697 mm³` y `102843.333 mm³`. Clasificación puntual independiente por intersecciones de rayos: `(25.9,-20,25.9) mm` cae dentro de metal, `(4.3,-20.7,25.9) mm` dentro de arena, `(-2,-68,-2) mm` fuera de ambos. Por ello, un error trivial de ubicación de los tres `insidePoints` no explica por sí solo los restos de 4 celdas. **Estas comprobaciones no equivalen al análisis del algoritmo `snappyHexMesh` real.**

**Hipótesis abierta y siguiente evidencia necesaria:** las celdas físicas se perdieron o quedaron mal clasificadas en la etapa de zone assignment / snapping / splitting. No está demostrado el paso exacto. Se añadió `scripts/diagnose_stl_v2_zones.sh`, que **únicamente lee los logs existentes** `log.snappyHexMesh`, `log.splitMeshRegions`, `log.checkMesh.metal`, `log.checkMesh.mold` y enumera parches reales. Devuelve tablas de clasificación por zonas, advertencias y estado al final de snapping, sin crear mallas ni solver:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_stl_v2_zones.sh
```

Esta salida debe fijar el punto real de pérdida: no recomendar ajustes arbitrarios de `nSmoothPatch`, `faceType` ni selección de `mappedWall` hasta identificarlo. Mantener `~/OpenFOAM/c3d-better-stl-v2` y la evidencia de STL v2 congelados.

## 18-11-2026 — Diagnóstico de zonas real: 589,821 celdas / 4 metal / 4 arena

El usuario ejecutó `scripts/diagnose_stl_v2_zones.sh` y compartió **la salida completa**. Resultados literales, capturados del caso `~/OpenFOAM/c3d-better-stl-v2`:

- `snappyHexMesh` terminó con **589,821 celdas**, 1,863,574 caras y 683,937 puntos tras refinamiento y snapping; registró 101,678 intersected edges durante refinamiento. La etapa no produjo error fatal, pero generó la topología que luego se clasificó erróneamente.
- Justo antes de asignar `cellZones`, el registro dice **`Walking from locations-in-mesh ... crossing a faceZone face changes cellZone`** y **10 regiones globales**.
- El punto del metal `(0.0259 -0.02 0.0259)` se detectó en región global 1; el punto de arena `(0.0043 -0.0207 0.0259)` se detectó en región global 0; el exterior `(-0.002 -0.068 -0.002)` **también** en región global 0. Esto demuestra que la clasificación nativa conectó el punto de arena con exterior, a pesar de ser interior del STL de arena según inspección volumétrica geométrica independiente.
- La tabla **`splitMeshRegions` confirma que la clasificación ya venía mal**: `metal 4 metal`, `mold 4 mold`, `exterior 589813 <none>`. Las únicas interfaces son `mold_to_exterior 24` y `metal_to_exterior 24`; ninguna `metal_to_mold`.
- `splitMeshRegions` además advierte que `faceZone::checkAddressing()` encuentra `Illegal face index 296053` y `667917` respecto a mallas regionales de solo 24 caras. Conservar como evidencia de zonas heredadas inconsistentes al separar restos; **no tratar como causa primera del colapso de la clasificación**.
- `checkMesh` de ambas regiones: 4 componentes inconexos, determinante mínimo/promedio 0 y fallo; comparación de calidad con baseline es inválida por diferencias radicales de volumen.
- Verificación geométrica del candidato original fuera de OpenFOAM: ambos STL son volúmenes cerrados orientados positivamente. Cortes a `z=25.9 mm` muestran que la pared de hierro y la pared interior de la arena tienen **coordenadas prácticamente coincidentes** para una amplia fracción del contacto. En muestreo geométrico de 250 puntos de superficie de metal, 71.2% coincidían con arena a menos de `1e-5 mm` (solo aproximación; el resto incluye caras de metal expuestas al aire). La interfaz coplanar/coincidente entre dos STL independientes es **hipótesis**, no causa probada.

### Próximo experimento de aislamiento controlado (NO CFD)

Se agregaron dos variantes de `Allmesh` que cambian un solo STL desde los binarios auditados y preservan todo lo demás:
- `--v2-metal-only`: hierro STL nuevo + arena STL antigua `mold_repaired.stl`; salida `~/OpenFOAM/c3d-better-v2-metal-only`.
- `--v2-mold-only`: hierro STL antiguo `metal.stl` + arena STL nueva; salida `~/OpenFOAM/c3d-better-v2-mold-only`.
- Ejecutables en serie mediante `scripts/run_stl_v2_ablation.sh`, que NO elimina carpetas existentes, preserva estados reales aunque se rechace la interfaz y produce `~/OpenFOAM/C3D02_STL_V2_ABLATION_REPORT.txt` con las tablas **reales** `Region nCells cellZone` y `Interface Owner Region ...` de cada ensayo.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/scripts/run_stl_v2_ablation.sh
```

**Criterio:** primero recuperar de forma objetiva decenas de miles de celdas físicas, volúmenes cercanos a CAD e interfaz metal–arena, antes de discutir concavidad o CFD. Un fallo en una variante y no en la otra identificaría qué cambio de geometría interfiere con `cellZone`; si las dos variantes funcionan y la pareja v2 colapsa, investigar interacción entre ambas triangulaciones coincidentes. No modificar originales ni `mappedWall` a mano. La ejecución de estas dos variantes sigue pendiente en la laptop.

## 18-11-2026 — Preferencia del investigador: autoridad de los diagnósticos nativos OpenFOAM

El investigador indicó expresamente **no implementar criterios propios que rechacen STL si `surfaceCheck` de OpenFOAM acepta su ejecución**. Por ello se revirtió `scripts/check_stl_v2.sh` al comportamiento anterior que toma como veredicto la salida/código del comando nativo, sin añadir una segunda decisión textual independiente. Se eliminaron `scripts/native_surfacecheck_gate.sh`, `tests/test_native_surfacecheck_gate.sh` y `scripts/audit_stl_surfaces_of14.sh`, así como sus dependencias en la suite estática.

Regla: los resultados de **`surfaceCheck` (superficie)**, **`snappyHexMesh` (creación/clasificación)** y **`checkMesh` (malla volumétrica)** son evaluaciones distintas de OpenFOAM. Un aprobado de superficie no anula los errores reales de `cellZone` ni de `checkMesh`; no atribuir a STL defectos no reportados por OpenFOAM. No modificar los STL v2, las mallas históricas ni materiales C14, y no incorporar filtros adicionales sin petición explícita.
