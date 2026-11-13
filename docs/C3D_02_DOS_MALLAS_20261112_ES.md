> **RESULTADO DEL ENSAYO `mold_offface_01` (12-11-2026): HIPÓTESIS DESCARTADA COMO SOLUCIÓN.** El investigador ejecutó el nuevo punto `insidePoint (0.0043 -0.0207 0.0259)` m, interior al STL reparado y separado de las caras regulares de `blockMesh`. **El resultado fue idéntico al ensayo original:** 568,134 celdas, 1 componente, 2 parches, volumen **0.000242142 m³ = 242.142 cm³** frente a CAD arena 102.8431 cm³, **15,164 caras `outerBox`**, 13,367 celdas cóncavas, 10 face-tets defectuosos y 2 fallos `checkMesh -allGeometry -allTopology`. El log confirmó `Selected for keeping : 568134 cells`. Por tanto, **la coincidencia del primer punto con una cara NO explica por sí sola la retención del exterior**. No crear más puntos candidatos ni aumentar el refinamiento sin estudiar cómo se cierran las superficies en el recorte de celdas.

**Inspección de geometría versionada, independiente de OpenFOAM:** `mold_repaired.stl` contiene 3,084 triángulos, 1,544 vértices únicos, 4,626 aristas (todas incidentes a dos caras), orientación de aristas consistente y un componente de superficie. Su volumen firmado es ~102.843097 cm³, consistente con el CAD histórico. **Eso demuestra cierre topológico en la triangulación, NO descarta autointersecciones ni una fuga de conectividad en la malla refinada.** Hay triángulos con aristas muy cortas y proporciones muy alargadas; también se observaron triángulos delgados en el STL del hierro, así que **no atribuir causalidad únicamente a esa propiedad**.

**Próximo paso NO DESTRUCTIVO:** `bash scripts/inspect_mold_leak.sh` sobre los logs ya generados y `surfaceCheck -checkSelfIntersection -outputThreshold 0` (solo si ambas opciones están disponibles en la instalación), sin `blockMesh`, sin `snappyHexMesh`, sin `subsetMesh`, sin modificar los STL ni la malla de hierro. Solo después de revisar las salidas decidir si el problema es autointersección, fuga durante rasterización de superficie, topología de `snappyHexMesh` o conviene generar el volumen de la arena con una herramienta alternativa. **Sigue sin existir CHT ni CFD 3D aprobado.**

> **RESULTADO LOCAL POSTERIOR — 12-11-2026, reanudación `retry1` ejecutada:** las dos mallas corrieron realmente, pero ninguna aprobó `checkMesh -allGeometry -allTopology`. **Metal:** 85,332 celdas; volumen **4.79621e-5 m³ = 47.9621 cm³** frente a STL 47.98749 cm³ (**−0.053 %**); `outerBox` 0 caras; `Face tets OK`; **2,422 celdas cóncavas y 1 check fallido**. **Arena:** 568,134 celdas; volumen **2.42142e-4 m³ = 242.142 cm³** frente a STL 102.8431 cm³ (**+135.4 %**); `outerBox` **15,164** caras; **13,367 cóncavas, 10 face-tets deficientes, 2 checks fallidos**. El hierro está aislado volumétricamente pero su calidad no está aprobada; la arena conserva exterior y no puede utilizarse para CHT.

**Hallazgo de configuración respaldado por `system/blockMeshDict`:** el `insidePoint` anterior de arena `(0.003 -0.0200 0.0259)` m tiene **x=3 mm**, exactamente una cara de la caja uniforme de paso x = (55−(−3))/29 = **2 mm**, con caras en −3, −1, 1, **3**, 5 mm, etc. OpenFOAM Foundation 14 requiere que `insidePoint` no coincida con una cara antes o durante refinamiento ([manual Foundation 14](https://doc.cfd.direct/openfoam/user-guide/snappyhexmesh)). Esto **podría contribuir** a la selección incorrecta, pero todavía no está demostrado como única causa. Mediante prueba geométrica independiente de rayos sobre `mold_repaired.stl`, el candidato **`(4.3 −20.7 25.9)` mm** = `(0.0043 -0.0207 0.0259)` m está dentro del molde; sus componentes no coinciden con los planos de la caja original ni con la subcuadrícula nominal de 0.5 mm. No es todavía un éxito de mallado.

**Siguiente ensayo único y localizado:** se añadió `scripts/try_mold_offface.sh`, que crea **solamente** `~/OpenFOAM/C3D02_materials/mold_offface_01` (sin modificar `metal/` ni `mold/` previos), usa el nuevo punto, ejecuta `blockMesh` + `snappyHexMesh` + `checkMesh` del molde una sola vez y rechaza el resultado si `outerBox>0`, volumen incompatible o fallos de calidad. Se conservan los logs anteriores. **No ejecutar** `resume_material_meshes.sh` otra vez, ni activar solver.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/try_mold_offface.sh
```

> **RESULTADO REAL 2026-11-12, primer intento con mallas independientes:** **ambos subcasos se detuvieron antes del refinamiento** en `snappyHexMesh` por `FOAM FATAL IO ERROR: keyword allowFreeStandingZoneFaces is undefined` dentro de `castellatedMeshControls`. `blockMesh` de metal y mold sí terminó, pero **no hay mallas físicas individuales generadas ni resultados `checkMesh` de este intento**. El fallo es exclusivamente una opción omitida del diccionario, no prueba de STL o material defectuoso. Se añadió `allowFreeStandingZoneFaces false;` a la plantilla y `scripts/resume_material_meshes.sh` para reanudar **sobre las mismas carpetas existentes**, conservar `log.snappyHexMesh`, crear `log.snappyHexMesh.retry1` y `log.checkMesh.retry1`, sin ejecutar de nuevo `blockMesh`. Ejecutar **una vez**:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/resume_material_meshes.sh
```

**Si el script encuentra otro estado o reintento previo, aborta sin sobrescribir la evidencia.** El resultado posterior sigue sin equivaler a CHT/CFD verificado.

# C3D-02 — mallas independientes por material, segundo diseño (12-11-2026)

**Estado:** preparado en GitHub; **NO ejecutado en laptop**. No es una validación CFD ni un reemplazo de la bitácora del ensayo anterior.

## Por qué cambiar la estrategia

Primera prueba C3D-02: `snappyHexMesh` terminó, pero `checkMesh -allGeometry -allTopology` informó **589,701 celdas, volumen 242.130 cm³, 14,586 celdas cóncavas, 10 face-tets malos y dos verificaciones fallidas**. `outerBox` tenía 15,929 caras; conservó exterior pese a `insidePoints` en dos materiales. El log confirma:
- `Keeping all cells in regions containing any point in 2(...)`
- `Selected for keeping : 589701 cells`
- `cellZone metal` y `faceZone metalInterface`, pero solo un componente global conectado.

**Diagnóstico geométrico adicional por inspección de STL versionados (12-11, cálculo independiente por rayos triangulares, no ejecutado con OpenFOAM):** el punto `(25.9,-20,25.9) mm` está dentro de `metal.stl` y fuera de `mold_repaired.stl`; `(3,-20,25.9) mm` está dentro del molde reparado y fuera de metal. Por tanto los dos puntos eran coherentes con las geometrías, y cambiarlos arbitrariamente no es un plan técnico. Ambos STL son superficies cerradas comprobadas en el historial. Compartir algunos vértices CAD tampoco demuestra conformidad de la malla ni parche térmico.

## Nueva estrategia con menor ambigüedad

Crear dos mallas **independientes** bajo una sola carpeta de trabajo, sin tratar de conservar dos materiales mientras aún existe aire conectado:

| Carpeta dentro del workspace | STL cerrado | Punto interior [m] | Volumen CAD [m³] |
|---|---|---|---|
| `metal/` | `metal.stl` | `(0.0259 -0.0200 0.0259)` | `4.79874896432e-5` |
| `mold/` | `mold_repaired.stl` | `(0.003 -0.0200 0.0259)` | `1.0284309608e-4` |

Cada malla tiene una sola `geometry` de `snappyHexMesh`, una superficie cerrada `patchInfo wall` y **un** `insidePoint` (Foundation 14). Se usa el `blockMesh` auxiliar de 58×72×58 mm y refinamiento (2 2); ninguna entrada `cellZone` o `faceZone` se asigna arbitrariamente en esta etapa. Si el mallado funciona, cada subcaso representa físicamente un único material.

## Comando único

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/run_material_meshes.sh
```

El script crea una sola carpeta `~/OpenFOAM/C3D02_materials` con subcarpetas `metal/` y `mold/`. **No sobrescribe** nada si ya existe. Ejecuta `blockMesh`, `snappyHexMesh -overwrite`, `checkMesh -allGeometry -allTopology` independientemente en cada una y guarda logs por material. No usa `subsetMesh`, `topoSet`, `splitMeshRegions`, ni CFD.

## Aceptación conservadora

- **Calidad:** `checkMesh -allGeometry -allTopology` debe finalizar con `Mesh OK`, sin checks fallidos y con código de salida 0.
- **Exterior:** `outerBox` debe tener **0** caras (o no aparecer como patch); esta condición es necesaria, **no suficiente**.
- **Volumen:** tolerancia exploratoria ±10% para detectar fallos groseros, **no aceptación metrológica**. Se requiere una comparación geométrica más estricta antes de aprobar las mallas para transferencia térmica.
- **Contactos:** las dos mallas independientes **no poseen aún parches `mappedWall` recíprocos**. Debemos estudiar posición de las superficies, áreas, orientaciones y compatibilidad de mapeo térmico para `metal_to_mold` / `mold_to_metal` en una etapa posterior. El script **no fusiona ni publica un CFD**.
- **No borrar** `~/OpenFOAM/C3D02_mesh` (primera prueba), las fuentes CAD ni carpetas anteriores antes de consolidar evidencia.

**Referencia:** [bitácora de primer mallado](C3D_02_MALLADO_INICIAL_20261112_ES.md) · [manual OF14](../OPENFOAM_COMMAND_MANUAL_ES.md) · [caso fuente](../cases_3d/C3D_02_metal_sand_clean/README.md). Mantener RUN_CASE_REGISTRY.csv en `PREPARED_NOT_RUN`.
