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
