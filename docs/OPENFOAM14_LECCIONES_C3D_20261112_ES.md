# OpenFOAM Foundation 14 — lecciones operativas reales C3D (12-11-2026)

Esta es una **adenda** al [manual de comandos español](../OPENFOAM_COMMAND_MANUAL_ES.md), no un sustituto. **Separa comandos ejecutados en Ubuntu de pasos todavía por validar.**

## 1. Identificar versión, caso y ruta
```bash
source /opt/openfoam14/etc/bashrc
echo "$WM_PROJECT_VERSION"
pwd
test -f system/controlDict && echo "controlDict presente"
```
- OpenFOAM14 necesita `system/controlDict` incluso para `topoSet` cuando lee un caso. Error real: `cannot find file .../system/controlDict`.
- No usar `set -u` antes de cargar `bashrc` si desencadena el error `ZSH_NAME: unbound variable`; activar las protecciones después.

## 2. Diccionarios (la barra importa)
```bash
foamDictionary system/snappyHexMeshDict -entry geometry
foamDictionary system/snappyHexMeshDict -entry castellatedMeshControls/insidePoints
foamDictionary system/snappyHexMeshDict -entry castellatedMeshControls/refinementSurfaces
```
- `-entry castellatedMeshControls.insidePoints` **falló**; usar `/`, no `.`.
- `constant/geometry/metal.stl` y `mold_repaired.stl` fueron localizados: ausencia en `constant/triSurface` no implica que faltan.
- `units [mm]` en `blockMeshDict` interpreta vértices en mm y produce malla en SI; evitar doble escalado de STL. Para `snappyHexMesh`, mantener una sola convención por geometría.

## 3. Comprobaciones de malla y visualización de defectos
```bash
checkMesh -case "$CASE" -allGeometry -allTopology \
  -writeSurfaces -surfaceFormat vtk -writeSets -setFormat vtk \
  > "$CASE/log.checkMesh.full" 2>&1
grep -Ei 'cells:|Total volume|face tets|small determinant|concave cells|Failed|Mesh OK' "$CASE/log.checkMesh.full"
find "$CASE/postProcessing" -type f \( -name '*.vtk' -o -name '*.vtu' \) -print
```
- `checkMesh -writeSets vtk` **falló**: `Wrong number of arguments, expected 0 found 1`. `-writeSets` es bandera; formato aparte con `-setFormat vtk`.
- `checkMesh` básico dio `Mesh OK` en 1,505,847 celdas, pero chequeo exhaustivo por regiones mostró defectos: **no dar por aprobada la malla**.
- VTK reportados: `concaveCells.vtk`, `lowQualityTetFaces.vtk`, `underdeterminedCells.vtk`, `nearPoints.vtk`; visualizar en ParaView.

## 4. STL, zonas y geometría
```bash
surfaceCheck constant/geometry/metal.stl
surfaceCheck constant/geometry/mold_repaired.stl
foamDictionary system/snappyHexMeshDict -entry castellatedMeshControls/refinementSurfaces
```
- `surfaceCheck` confirmó metal: 3,896 triángulos, cerrado, un componente; molde reparado: 3,084 triángulos, cerrado, un componente. **No implica calidad volumétrica aceptada**.
- `refinementSurfaces.metal` tenía `faceZone metal`, `cellZone metal`, `mode inside`; `mold_repaired` era parche de pared, no `cellZone mold`.
- `insidePoints` 2 vs. 1 dejó 1,505,847 celdas y 383,788 en `metal` en ambos ensayos. **No seguir cambiando semillas a ciegas**.

## 5. Selección, conjuntos y submalla
```bash
topoSet -case "$CASE" > "$CASE/log.topoSet" 2>&1
subsetMesh -help
subsetMesh -case "$CASE" -cellSet keepMaterials -noFields \
  > "$CASE/log.subsetMesh" 2>&1
```
- `topoSet` avisó que es sustituido por `createZones`, pero seleccionó por `surfaceToCell` según orientación de STL; arena 825,994; metal 383,783; sin intersección (en ese ensayo).
- `subsetMesh keepMaterials -case ...` **falló**: `Wrong number of arguments`. Usar `-cellSet keepMaterials` en OF14.
- **No volver a ejecutar subsetMesh sobre una malla recortada con un cellSet creado antes del recorte**. Error real: etiqueta `1209778` fuera del rango permitido `0..1209777`. Los índices dependen de la topología y pueden cambiar.
- Una selección de 1,209,777 celdas no demuestra que esté lista una interfaz de transferencia de calor.

## 6. Separación regional y acoplamiento
```bash
splitMeshRegions -help
splitMeshRegions -case "$CASE" -cellZones 'metal' -defaultRegion surrounding -noFields \
  > "$CASE/log.splitMeshRegions" 2>&1
```
- Comando superior **ejecutado solo en una copia histórica de malla conectada**: creó `metal_to_surrounding` y `surrounding_to_metal` de 5,334 caras `mappedWall`.
- `surrounding` incluía celdas no clasificadas como arena, por tanto **no es** la solución final metal–molde.
- `splitMeshRegions -disconnected` en la malla ya recortada separó dos componentes pero dijo `No interfaces to add`; no confundir con parches CHT.
- Después de separar, correr `checkMesh -region metal` y `checkMesh -region mold` con opciones exhaustivas. Advertencias `faceZones` con índices fuera de rango requieren revisión.

## 7. Buenas prácticas Git / resultados
```bash
git status --short
git diff --check
git add -- cases_3d/C3D_02_metal_sand_clean docs
git diff --cached --stat
```
- No usar `git add .` después de mallar: pueden existir logs/OBJ/`problemFaces` no revisados.
- Diferenciar `0/` (condiciones iniciales), `constant/` (geometría/materiales), `system/` (controles), `postProcessing/` (evidencia de corridas), `log.*` (evidencia de comandos).
- C14 es base de propiedades constantes; origen JMatPro de valores permanece pendiente. `fvModels` referencia `cellZone metal`: adaptar al mapa de regiones final.
- No publicar `RUN_VERIFIED` ni ejecutar `foamMultiRun` sin malla de 2 sólidos válida, parches acoplados, BC 3D y verificación numérica.

**Referencias externas a contrastar con la instalación Foundation 14:** https://doc.cfd.direct/openfoam/user-guide-v14/ ; ayuda nativa `-help` de cada utilidad. Evitar mezclar documentación de OpenFOAM.com con Foundation.
