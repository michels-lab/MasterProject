# C3D-01 — QuickCup 3D: metal y molde de arena

**Estado científico:** preparación CAD y malla de fondo; `blockMesh`/`checkMesh` no ejecutados aún en la laptop, **sin simulación CFD**. Experimento independiente de `cases_controlled_buoyancy/`. Referencia física futura: C14, sin alterar sus archivos.

## Convención nativa de unidades (OpenFOAM Foundation v14)

**Usamos milímetros de forma explícita en los diccionarios de OpenFOAM 14**, no conversores externos de geometría:

- `system/blockMeshDict`: `units [mm];` seguido de vértices con valores como `(-3 -69 -3)`, `(55 3 55)`. OpenFOAM genera la malla en su unidad base SI `[m]`.
- **Geometrías SolidWorks**: `QuickCup.STL` y `metal.STL` mantienen sus coordenadas originales numéricas en **mm**, su orientación, origen y triangulación. `prepare_geometry.py` solo verifica el hash/triangulación y coloca **copias binarias idénticas** en `constant/geometry/mold.stl` y `metal.stl`. No escala ni mueve nada.
- **Paso siguiente con `snappyHexMesh`**: cada entrada de superficie `triSurfaceMesh` declarará `units [mm];`. OpenFOAM convierte las superficies internamente a la escala física correcta.
- **Prohibido doble escalado**: no usar también `scale 0.001;` en la misma geometría, ni convertir previamente los STL a metros; las dos opciones de escalado/units son alternativas.
- Los scripts `analysis_tools/preflight_c3d_stl.py` inspeccionan la geometría **en memoria** en SI para verificar volumen/semillas; los archivos fuente no se cambian. `geometry_reference.json` conserva las huellas SHA-256 originales.
- No se supone que poner `units [mm]` de forma global modifique todas las magnitudes del solver; cada parámetro y utilidad requiere la sintaxis admitida por OpenFOAM.

Referencias oficiales:
- https://doc.cfd.direct/openfoam/user-guide-v14/blockmesh
- https://doc.cfd.direct/openfoam/user-guide-v14/snappyhexmesh
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/meshTools/searchableSurfaces/triSurface/triSurface_searchableSurface.C

## Geometrías recibidas

| STL | Medidas X × Y × Z | Triángulos | Volumen aproximado |
|---|---|---:|---:|
| Molde `QuickCup.STL` | 51.8 × 65.5 × 51.8 mm | 3084 | 102.843 cm³ |
| Metal `metal.STL` | 36.5 × 40 × 36.5 mm | 3896 | 47.987 cm³ |

Los archivos STL de SolidWorks **no están publicados** en este repositorio, que es público. Debes utilizar las exportaciones con origen compartido y SHA-256 especificados en `geometry_reference.json`; una exportación con el mismo nombre puede tener contenido distinto. Si los hashes no coinciden, inspeccionaremos la nueva exportación en lugar de desactivar la comprobación.

## Ubicación local y preparación

En Windows, la carpeta del investigador es:
`C:\Users\HP\Documents\CINVESTAV\Tesis\Pieza dimensiones correctas`.

Desde Ubuntu en **WSL**, si tienes este repositorio clonado bajo `~/OpenFOAM/QuickCup_Solidification`:

```bash
cd ~/OpenFOAM/QuickCup_Solidification
git pull --ff-only
cd cases_3d/C3D_01_metal_mold

STL_DIR="/mnt/c/Users/HP/Documents/CINVESTAV/Tesis/Pieza dimensiones correctas"
ls -lh "$STL_DIR/QuickCup.STL" "$STL_DIR/metal.STL"

python3 scripts/prepare_geometry.py \
    --mold "$STL_DIR/QuickCup.STL" \
    --metal "$STL_DIR/metal.STL"

source /opt/openfoam14/etc/bashrc
bash scripts/run_blockMesh_only.sh
```

Si Ubuntu es un sistema independiente y no WSL, transfiere los STL a Linux o monta la partición Windows antes de ejecutar `prepare_geometry.py`, con las rutas correctas. No presupongas que `/mnt/c` existe.

El script `run_blockMesh_only.sh` ejecuta exclusivamente `blockMesh` y `checkMesh -allTopology -allGeometry` y escribe logs locales. Se niega a sobrescribir `constant/polyMesh`; para repetir un mallado usa una copia nueva del caso, preservando la evidencia.

## ¿Qué malla crea esta etapa?

**Dominio de fondo** (rectángulo cartesiano auxiliar):

| Eje | Mínimo [mm] | Máximo [mm] | Longitud [mm] | Celdas |
|---|---:|---:|---:|---:|
| X | -3 | 55 | 58 | 29 |
| Y | -69 | 3 | 72 | 36 |
| Z | -3 | 55 | 58 | 29 |

En total hay **29 × 36 × 29 = 30,276** celdas hexaédricas uniformes de 2 mm. Las seis caras tienen normales hacia el exterior, cubiertas por la prueba sintética; el parche `outerBox` y los márgenes son **temporales** y no constituyen condiciones térmicas físicas.

`blockMesh` no crea por sí mismo las regiones metal/arena. **La malla física se realizará mediante `snappyHexMesh`, respetando los STL**, una vez que construyamos juntos el `system/snappyHexMeshDict`. Su `geometry` contendrá, conceptualmente:

```cpp
geometry
{
    mold
    {
        type triSurfaceMesh;
        file "mold.stl";
        units [mm];
    }
    metal
    {
        type triSurfaceMesh;
        file "metal.stl";
        units [mm];
    }
}
```

Esto es **un fragmento explicativo**, NO un `snappyHexMeshDict` listo para ejecutar. Faltan los controles de refinamiento, límites de celdas, snapping, selección de regiones y controles de calidad; no confundir una malla superficial correcta con interfaces de CHT validadas.

## Próximas puertas de validación

1. Ejecutar `blockMesh` y `checkMesh` únicamente en Ubuntu del investigador; guardar y revisar logs y dimensiones del `bounding box` en metros.
2. Diseñar `snappyHexMeshDict` entre investigador y asistente, con regiones metal/molde, control de contacto, refino de interfaces, seguimiento de calidad y de volumen físico, sin generar una sola región por accidente.
3. Ejecutar `snappyHexMesh`, analizar interfaz y subdominios, preparar y validar `splitMeshRegions` y `checkMesh` por región.
4. Adaptar con trazabilidad las BC/propiedades térmicas 3D desde la referencia C14, comprobar conservación de energía, pruebas de malla y curvas experimentales.
5. Ejecutar el solver exclusivamente en la laptop. No instalar ni correr OpenFOAM en GitHub Actions; FoamLENS es independiente.

Las pruebas automáticas del repositorio son **solo sintéticas/estáticas**; no certifican una malla OpenFOAM ni validan resultados CFD.
