# C3D-02 — Auditoría histórica + geometría STL (17-11-2026)

**Decisión propuesta:** antes de otra variante de `snappyHexMesh`, auditar y mejorar **la triangulación superficial** desde CAD, preservando todas las geometrías originales y la física C14. No se ha probado todavía que el STL sea la única causa de los defectos volumétricos.

## Fuente y antecedentes verificados

Se revisaron:
- [C3D-01: estado real](C3D_01_ESTADO_REAL_20261110_ES.md), 10–11 noviembre
- [Reinicio C3D](C3D_REINICIO_20261112_ES.md), 12 noviembre
- [Mallado inicial](C3D_02_MALLADO_INICIAL_20261112_ES.md)
- [Dos mallas metal/arena](C3D_02_DOS_MALLAS_20261112_ES.md)
- [Lecciones OpenFOAM 14](OPENFOAM14_LECCIONES_C3D_20261112_ES.md)
- [Diagnóstico nativo, sensibilidad y c3d-better](C3D_02_NATIVE_CHECKMESH_20261117_ES.md)

**Datos históricos:** `metal.stl` original de SolidWorks: 3,896 triángulos, cerrado. `mold.stl`: 3,084 triángulos, 74 aristas abiertas y 16 pares de puntos próximos según `surfaceCheck`. `mold_repaired.stl`, derivado mediante `surfacePointMerge`, cerró el dominio sin cambiar el número de triángulos; no presentó autointersecciones detectadas. **Cierre topológico no implica triangulación de buena calidad ni conformidad entre las dos superficies.**

En los ensayos antiguos `C3D01`, muchas concavidades estaban fuera de los dos volúmenes físicos, dentro de la caja exterior. No extrapolar esos recuentos a las dos mallas físicas de noviembre 17.

## Inspección adicional directa de los tres archivos STL versionados en GitHub

Se leyeron los archivos STL actuales de `cases_3d/C3D_02_metal_sand_clean/constant/geometry/`, incluyendo sus triángulos (binarios en metal/molde original y ASCII en molde reparado). Se reconstruyeron longitudes de aristas y ángulos internos a partir de las coordenadas de cada triángulo en milímetros. **Estos son indicadores geométricos descriptivos**, no una certificación de que los STL sean inválidos ni una ejecución de `surfaceCheck` en Ubuntu.

| Indicador | `metal.stl` | `mold.stl` | `mold_repaired.stl` |
|---|---:|---:|---:|
| Triángulos | 3,896 | 3,084 | 3,084 |
| Vértices distintos (coordenadas agrupadas a 1e-6 mm) | 1,950 | 1,634 | 1,544 |
| Triángulos con ángulo mínimo <5° | **726 (18.6%)** | **976 (31.6%)** | **976 (31.6%)** |
| Triángulos con ángulo mínimo <1° | 635 | 881 | 879 |
| Arista mínima (mm) | 0.00298 | 0.00308 | 0.00306 |
| Arista máxima (mm) | 48.09 | 78.93 | 78.93 |
| Arista mediana (mm) | 0.192 | 0.240 | 0.240 |

**Interpretación cautelosa:** existe una abundancia de triángulos agudos y aristas de escala muy pequeña respecto de la malla volumétrica nominal de ~0.5 mm. La reparación del molde unió vértices, pero no re-trianguló de forma material la superficie (mismo recuento y distribución de ángulos). Este patrón merece estudiar el origen CAD, aristas diminutas, caras alargadas, zonas de la interfaz y discretización. **Más triángulos por sí solo no corrige el problema; un triángulo estrecho puede ser perfectamente válido sobre una cara plana.**

## Otros factores independientes del STL

El `system/snappyHexMeshDict` actual usa `features ();`, `nFeatureSnapIter 0;`, `implicitFeatureSnap false;`, `explicitFeatureSnap false;`, `multiRegionFeatureSnap false;`. Por tanto, **el tratamiento de aristas geométricas está desactivado** en esta ruta; es otro factor candidato, no una prueba de culpabilidad.

La prueba `nSmoothPatch 3 -> 6` **empeoró** la concavidad de metal 4,834 -> 5,004 y molde 14,951 -> 15,079. Repetir la malla original como `c3d-better` reprodujo exactamente las métricas del baseline (4,834 / 14,951 cóncavas; 2 / 3 checks fallidos). No repetir estos experimentos.

## Plan de mejora de superficies, sin alterar física ni historia

**Vía preferida:** si existe CAD paramétrico (`.SLDPRT`, `.SLDASM` o STEP), regenerar superficies de hierro y arena **desde el mismo origen y la misma geometría maestra**, preferiblemente como sólidos complementarios del modelo, y exportar dos nuevos STL en milímetros. Comprobar que arena excluya el metal, que las superficies de contacto sean coincidentes dentro de tolerancia documentada y que no aparezcan solapes ni huecos artificiales. En SolidWorks, la exportación `STL > Options > Fine/Custom` permite controlar desviación y tolerancia angular; **la estrategia debe procurar elementos superficiales de buena forma, no solo aumentar la cantidad**. No suavizar o alterar detalles físicos de la interfaz sin justificación.

Si el CAD ya no está disponible, ensayar un remallado superficial conservador del STL en **copias** mediante herramientas apropiadas de reparación/remallado, seguido de los mismos controles; `surfacePointMerge` por sí solo no realiza remallado de calidad.

Los candidatos se guardarán como nuevas versiones (`metal_v2.stl`, `mold_v2.stl`) con SHA-256, procedencia, tolerancias, número de triángulos, bbox, volumen `surfaceInertia`, cierre y autointersecciones `surfaceCheck -checkSelfIntersection`. **No sustituir** `metal.stl`, `mold.stl`, `mold_repaired.stl`, ni desactivar validaciones de integridad hasta disponer de candidato comprobado.

Solo después ejecutar una **nueva** comparación en OpenFOAM Foundation 14 con `blockMesh`, `snappyHexMesh`, `splitMeshRegions`, `checkMesh -allGeometry -allTopology` y VTK en ambas regiones, **manteniendo sin cambios C14**. La calidad aceptable requiere ausencia de checks fallidos, coherencia de volúmenes, contacto metal–arena físico y parches recíprocos; aún no autoriza CFD sin BCs 3D y verificación CHT.

## Estado

**Propuesta de diseño, no reparación aplicada.** Esta auditoría no reemplaza ni modifica STL, malla o propiedades termofísicas. Falta un candidato CAD/STL nuevo y la inspección espacial de los VTK defectuosos.

## 17-11-2026 — Nuevos STL v2 de SolidWorks, SUBIDOS A GIT

El investigador confirmó que los **archivos definitivos** son `metalmm(2).STL` y `QuickCupmm.STL`. Fueron inspeccionados como superficies con una región, orientadas consistentemente y cerradas tras unificación geométrica de vértices duplicados.

| Característica | metal v2 | mold v2 |
|---|---:|---:|
| Ruta Git | `cases_3d/C3D_02_metal_sand_clean/constant/geometry/metal_v2.stl` | `cases_3d/C3D_02_metal_sand_clean/constant/geometry/mold_v2.stl` |
| Origen | `metalmm(2).STL` | `QuickCupmm.STL` |
| Triángulos | 4,628 | 3,716 |
| Volumen | 47.987697 cm³ | 102.843333 cm³ |
| SHA-256 | `f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf` | `ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32` |
| SHA de blob Git | `10b41a9edbf32ec6642587d21fa3cc6ad76a880d` | `6ea3ccbab486ccc45842723f68af289b61d9d029` |

**Commit real con ambos STL binarios:** [`e8be4afeae847411cd35b815f90748d71d1c5d90`](https://github.com/michels-lab/MasterProject/commit/e8be4afeae847411cd35b815f90748d71d1c5d90). Se comprobó que los SHA de blob Git coinciden exactamente con los calculados sobre los binarios recibidos; no hubo conversión a formato ASCII ni modificación geométrica por la transferencia.

No se han reemplazado `metal.stl`, `mold.stl`, `mold_repaired.stl` ni archivos de C14. Los dos nuevos son las **fuentes candidatas correctas** del próximo ensayo de mallado. La opción `Allmesh --stl-v2` verifica ambos SHA y ejecuta `surfaceCheck` nativo, copia los STL a una carpeta nueva `~/OpenFOAM/c3d-better-stl-v2` y realiza `blockMesh`, `snappyHexMesh`, `splitMeshRegions` y `checkMesh` sin solver. Que los STL sean correctos **no implica** que la malla volumétrica esté validada: habrá que comparar sus resultados con el baseline y revisar la interfaz metal–arena.
