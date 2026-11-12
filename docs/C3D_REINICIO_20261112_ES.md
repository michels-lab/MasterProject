# C3D — Reinicio controlado del caso 3D (12 de noviembre de 2026)

**Decisión del investigador:** abandonar como base de ejecución las múltiples pruebas temporales de C3D-01, conservar sus resultados y bitácoras como evidencia histórica, y construir un **caso fuente nuevo e independiente**, `cases_3d/C3D_02_metal_sand_clean/`, con dos materiales: `metal` (hierro hipoeutéctico) y `mold` (arena sílica). **No modelar aire como una tercera región.**

## Estado verificado, no confundir con simulación

- **C14 2D** sigue siendo la referencia física para el reinicio, sin modificación: `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef`.
- Propiedades heredadas (documentadas en C14, no atribuir a JMatPro sin export): **hierro**: rho=6820 kg/m³, Cp=827 J/(kg K), mu=5.5e-3 Pa s, Pr=0.14; **sílica**: rho=1500 kg/m³, Cv=700 J/(kg K), kappa=2 W/(m K).
- El origen C14 también conserva `constant/metal/fvModels` (solidificationMeltingSource, Tsol=1423 K, Tliq=1473 K, L=2.286e5 J/kg, alpha1e=0.8, Cu=1e5, q=1e-3, relax=0.1), `g` y `pRef`. Copiar **no equivale a validar** en malla 3D. `fvModels` selecciona `cellZone metal`, lo que requiere revisión después de separar regiones.
- La geometría CAD original contiene `metal.stl`, `mold.stl` y `mold_repaired.stl`. `mold_repaired.stl` fue cerrado mediante reparación geométrica; preservar los originales, las huellas, las unidades y la procedencia.
- La malla de fondo 58×72×58 mm es una **caja auxiliar**, no el dominio físico final.

## Ensayos históricos locales (NO reutilizar como caso limpio)

| Ensayo | Evidencia | Resultado |
|---|---|---|
| `C3D01_snappy_NTC8Dj` | snappy + checkMesh | 1,505,847 celdas, 242.201 cm³; conserva caja exterior; 2 caras ilegales reportadas por snappy y fallos de calidad exhaustiva |
| `C3D01_test_moldOnly` | 1 insidePoint | igual número de celdas, volumen, límites y cellZone metal (383,788); cambiar ese punto **no** resolvió el exterior |
| `C3D01_material_selection` | topoSet surfaceToCell | interior molde 825,994; interior metal 383,783; intersección de conjuntos cero; restante 296,070 celdas no clasificadas |
| `C3D01_materials_H0qgJN` | extracción histórica | 1,209,777 celdas; 151.230 cm³; 3 checks de calidad fallidos y `No interfaces to add` al separar componentes |
| `C3D01_interface_Xp0Mrc` | splitMeshRegions sobre malla conectada | **sí se creó** interfaz `metal_to_surrounding` de 5,334 caras (`mappedWall`), pero `surrounding` mezcla molde/exterior; `metal` 383,788 celdas y `surrounding` 1,122,059; ambas regiones fallan 3 checks exhaustivos |
| `C3D01_metal_sand_v1` | topoSet + subsetMesh | `keepMaterials` 1,209,777 etiquetas; `subsetMesh` abortó por ID `1209778` fuera del rango de la malla ya presente: **set obsoleto o malla modificada**, no repetir sobre esa carpeta |

### Lecciones obligatorias
1. `Mesh OK` en `checkMesh` básico no supera `-allGeometry -allTopology`; el exit code 0 tampoco certifica calidad.
2. Dos componentes de celdas aisladas **no** garantizan un par de parches térmicos. Los parches `oldInternalFaces` creados por `subsetMesh` no equivalen a `mappedWall`.
3. `splitMeshRegions -cellZones 'metal'` sobre la malla conectada **sí fue probado** posteriormente al documento fechado 10-11-2026. Logró 5,334 caras de interfaz con `surrounding`, **no** la interfaz final hierro–arena.
4. Las advertencias `Illegal face index` de `faceZones` tras `splitMeshRegions` ameritan inspección; no afirmar éxito por contar parches.
5. `topoSet` muestra advertencia de deprecación hacia `createZones` en OpenFOAM Foundation 14, pero siguió funcionando en el ensayo. `surfaceToCell` selecciona por geometría/centros y no necesariamente construye superficies conformantes.
6. Las 9 celdas aisladas (7 metal y 2 surrounding) se observaron **en las regiones del ensayo conectado**, no deben confundirse con el estado final de un caso nuevo.
7. No mover, renombrar, limpiar ni borrar automáticamente las carpetas locales históricas. Conservar evidencias hasta que el investigador confirme respaldo y recuperación del caso limpio.

## Puertas del caso limpio

**G0 — Fuente:** geometrías STL verificadas y unidades consistentes, archivos materiales C14 byte-identical.  
**G1 — Malla:** dos volúmenes físicos, sin exterior; `checkMesh -allGeometry -allTopology` revisado, volúmenes coherentes con STL.  
**G2 — CHT:** `constant/metal/polyMesh` y `constant/mold/polyMesh` con parches recíprocos válidos y áreas de interfaz.  
**G3 — Física:** adaptar BC 2D (sin `frontAndBack empty`) y `fvModels`, parámetros y solvers; nunca ejecutar CFD antes de G1 y G2.  
**G4 — Evidencia:** correr solo en Ubuntu del investigador; conservar logs, commits, parches y comparación con curva experimental. Puertas J0 JMatPro y G1 experimental del proyecto siguen abiertas: no confundir la nomenclatura de gates locales.

## Inventario local y sincronización sin borrado

```bash
cd ~/OpenFOAM/MasterProject
git status --short
git fetch origin
git pull --ff-only
find ~/OpenFOAM -maxdepth 1 -type d -name 'C3D01_*' -print | sort
```

Los resultados locales de `C3D01_*` **no se transfieren a GitHub automáticamente**. El caso nuevo no debe depender de esos directorios para ejecutar. Los archivos CAD deben respaldarse también fuera del repositorio cuando aplique.

**Fuente histórica:** [registro 10-11](C3D_01_ESTADO_REAL_20261110_ES.md) y las salidas de terminal posteriores compartidas el 11–12 de noviembre. Ningún solver 3D validado; no release, no CFD en CI.
