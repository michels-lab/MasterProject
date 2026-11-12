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
