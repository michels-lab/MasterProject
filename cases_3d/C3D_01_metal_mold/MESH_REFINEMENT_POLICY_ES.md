# C3D-01 — acuerdo de malla máxima nominal de 0.5 mm (metal y arena)

**Decisión del investigador, 2026-10-19.** Versión objetivo: **OpenFOAM Foundation v14**. Estado: **CONFIGURACIÓN ACORDADA / NO MALLADA NI VALIDADA**.

## Qué se acordó

- Mantener `system/blockMeshDict` como **malla de fondo provisional de 2 mm** (29 × 36 × 29 celdas, caja 58 × 72 × 58 mm). No cambiarla a 0.5 mm en bloque.
- Refinar **el volumen completo de metal y el volumen completo de molde de arena** hasta **tamaño nominal no mayor a 0.5 mm**, **no solo la piel STL ni el contacto**.
- La operación será `snappyHexMesh`, con refinamiento por dentro de las dos superficies cerradas y superficies metal/molde ajustadas con snap; no usar Python como generador de malla.
- La resolución acordada de ambas regiones es la misma, hasta que un estudio de independencia de malla justifique modificarla.
- Preservar los archivos fuente `QuickCup.STL` / `metal.STL` en sus **milímetros originales**, y declarar `units [mm];` en las entradas de geometría de Foundation 14 (no duplicar `scale`).
- Mantener todo el trabajo C3D separado de B14/C14 y no ejecutar CFD fuera de la laptop del investigador.

**Aritmética del refinamiento octree** (para celdas regulares antes de snapping): `2 mm / 2^2 = 0.5 mm`; nivel 0 = 2 mm, nivel 1 = 1 mm, nivel 2 = 0.5 mm. Cada refinamiento completo divide una celda en 8 subceldas.

## Sintaxis de intención (FRAGMENTO, NO diccionario ejecutable)

```cpp
// OpenFOAM FOUNDATION v14: modo inside usa level, no niveles heredados.
// En system/snappyHexMeshDict cuando esté listo para validarse:
castellatedMeshControls
{
    refinementSurfaces
    {
        mold  { level (2 2); }
        metal { level (2 2); }
    }
    refinementRegions
    {
        mold  { mode inside; level 2; }
        metal { mode inside; level 2; }
    }
    // Para preservar ambos materiales sin descartar uno:
    // insidePoints ((0.0259 -0.020 0.0259) (0.003 -0.020 0.0259));
    // Es preciso verificar asignación de zonas y patches CHT antes de RUN.
}
```

Las coordenadas de semillas están en **metros (SI)**, no en milímetros; las entradas de geometría STL sí usan `units [mm]`. La presencia de semillas no certifica `cellZone`, `faceZone` o un par de patches conjugados. El fragmento anterior **NO** autoriza ejecutar `snappyHexMesh` sin un diccionario completo con controles, zonas, selección, calidad, topología y comandos de preservación de resultados.

## Gate técnico previo a cualquier simulación

1. En la segunda computadora, comprobar `foamVersion`, memoria/RAM, swap, núcleos, rutas de los STL y `sha256sum`. No asumir ni cambiar hardware aquí.
2. Sobre **copia nueva** y limpia de C3D-01, ejecutar `blockMesh`, `checkMesh` y `surfaceCheck` de ambos STL. Preservar logs; no `Allclean`, no sobrescribir históricos.
3. Construir y revisar `snappyHexMeshDict` **completo Foundation 14**, con `refinementSurfaces` + `refinementRegions` para ambos materiales, `insidePoints` o estrategia de zonas justificada, selección/retención de ambas regiones y configuración de calidad; preferir prueba incremental/serial antes de paralelizar. No adoptar sintaxis de OpenFOAM.com sin verificarla.
4. En laptop: correr `snappyHexMesh` sobre una copia sin sobrescribir mallas anteriores; comprobar límites de celdas, histograma de tamaños **por región**, `cellLevel`, localización y tamaños físicos, `checkMesh`, volúmenes mallados contra STL, interfaces, normales y `splitMeshRegions`. Si el límite de `maxGlobalCells` trunca refinamientos, **no** declarar logrado 0.5 mm.
5. Determinar **longitud máxima** de celdas en metal y molde (medición real, no inferencia por `level` ni longitud cúbica `V^(1/3)` en células deformadas), indicando regla y tolerancia para `snapping`. Un nivel 2 nominal no prueba un techo geométrico estricto de 0.5 mm.
6. Verificar patches de interfaz de transferencia térmica conjugada y acoplamiento posterior; `checkMesh` exitoso no equivale a validación térmica o de solidificación.
7. Mantener J0 (JMatPro) y G1 (experimentos) abiertos; no etiquetar `RUN_VERIFIED`, `ANALYSIS_VERIFIED` ni `EXPERIMENTALLY_VALIDATED` sin evidencia.

**Magnitud aproximada, solo estimación:** metal 47.987 cm³ y arena 102.843 cm³; dos volúmenes rellenados idealmente con cubos de 0.5 mm serían alrededor de **1.21 millones de celdas** antes de transiciones, snap y efectos de topología. No es un conteo real ni una cota de memoria.

## Fuentes verificadas para Foundation v14

- Guía oficial: https://doc.cfd.direct/openfoam/user-guide-v14/snappyhexmesh
- Ejemplo oficial: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/mesh/snappyHexMesh/flange/system/snappyHexMeshDict
- Código fuente de selección múltiple `insidePoints`: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/mesh/snappyHexMesh/snappyHexMeshDriver/refinementParameters/refinementParameters.C
- Nota de versión Foundation 14: https://openfoam.org/release/14/

**Diferenciar:** acuerdo de resolución **sí**; `snappyHexMeshDict` completo **no**, ejecución **no**, QA de tamaño de celda **no**, validación CFD **no**.
