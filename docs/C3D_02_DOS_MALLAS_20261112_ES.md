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
