# C3D-02 — primer mallado hierro + arena (12-11-2026)

**Estado: código fuente de mallado preparado en GitHub, no ejecutado.** Esta etapa sustituye experimentos anteriores sin utilizar sus `polyMesh`, `cellSets`, logs ni carpetas de trabajo. Es el **primer intento controlado** con archivos de fuente nuevos para `C3D_02_metal_sand_clean`.

## Diseño de este bloque

- 2 STL de trabajo: `metal.stl` y `mold_repaired.stl`. El original `mold.stl` se mantiene para trazabilidad.
- Coordenadas STL en mm, declaradas con `units [mm];` en cada geometría de `snappyHexMeshDict`; `blockMeshDict` conserva su `units [mm];`.
- Dos puntos interiores de selección en **SI (m)**: hierro `(0.0259 -0.0200 0.0259)`; arena `(0.0030 -0.0200 0.0259)`.
- `refinementSurfaces` nivel (2 2) por material, `cellZone metal` + `faceZone metalInterface`, sin capas; `snap true` es una configuración candidata, **no** una garantía de calidad.
- Primer mallado únicamente: **no** `splitMeshRegions`, `subsetMesh`, `topoSet`, `foamMultiRun`, desactivación de controles de calidad ni loops de reintento.
- **Carpeta de trabajo única:** `~/OpenFOAM/C3D02_mesh`, creada una vez. `git` contiene fuentes. El script **se niega a ejecutar sobre una carpeta existente**; con ello no puede corromper un conjunto de celdas anterior.

## Ejecución única en la laptop (Foundation 14)

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
bash scripts/run_mesh_only.sh
```

**No borrar la carpeta si la simulación falla.** Los registros en `~/OpenFOAM/C3D02_mesh` permanecen para inspección. La salida de terminal resume calidad, volumen, regiones y zonas; **enviar esa salida y/o los últimos bloques de `log.snappyHexMesh` y `log.checkMesh.full`** para decidir el ajuste sobre fuentes.

## Qué exige una malla aceptable

1. `snappyHexMesh` finaliza sin error real; `checkMesh -allGeometry -allTopology` no presenta checks fallidos. `Mesh OK` en revisión básica no basta.
2. El volumen total (y por separado cada futura región) debe ser compatible con el volumen de los STL: hierro ~**47.9875 cm³** + arena reparada ~**102.8431 cm³**, total ~**150.8306 cm³** (se requiere justificar desviación por discretización). Si se aproxima a 242 cm³, retuvo la caja exterior y **no sirve**.
3. La mera presencia de `cellZone metal` no prueba que todo `mold` sea arena; antes de separar debe verificarse que el resto de celdas no incluye aire.
4. Una interfaz térmica real necesita parches `metal_to_mold` y `mold_to_metal` con áreas y `mappedWall` compatibles. **No basta** con `metalInterface`, dos componentes desconectados o `oldInternalFaces`.
5. Solo después de esas comprobaciones es razonable emitir el comando específico `splitMeshRegions -cellZones 'metal' -defaultRegion mold -noFields`, hacer `checkMesh -region metal` y `-region mold`, inspeccionar `constant/*/polyMesh/boundary`, adaptar `0/*` y preparar `foamMultiRun`.
6. Un defecto de interfaz o una selección exterior incorrecta es un **bloqueador**; no etiquetar el caso como `RUN_VERIFIED`.

## Comandos de inspección, si se necesita leer sin modificar

```bash
CASE="$HOME/OpenFOAM/C3D02_mesh"
grep -Ei 'cells:|Total volume|Number of regions|Failed|Mesh OK|concave|face tets' \
  "$CASE/log.checkMesh.full" | tail -n 50
grep -Ei 'Adding cell zone|face zone|Finished meshing|End|FOAM FATAL|error' \
  "$CASE/log.snappyHexMesh" | tail -n 40
sed -n '1,120p' "$CASE/constant/polyMesh/boundary"
```

## Proveniencia y decisiones

Esta configuración se basa en la sintaxis **Foundation 14** para `insidePoints`, que es explícitamente soportada por `snappyHexMeshConfig`. No extrapolar a ella `locationsInMesh` de la distribución OpenCFD. Referencia: https://cpp.openfoam.org/v14/snappyHexMeshConfig_8C.html y https://openfoam.org/release/14/. La configuración exacta en `system/snappyHexMeshDict` es un primer diseño de ingeniería y **solo se certificará al correrla en OpenFOAM de la laptop**.

Historial previo: [C3D-01](C3D_REINICIO_20261112_ES.md) · [Manual de fallos y comandos](OPENFOAM14_LECCIONES_C3D_20261112_ES.md) · [Caso fuente](../cases_3d/C3D_02_metal_sand_clean/README.md).
