# Caso A — C3D-04 V3: barrido acotado para defectos basales residuales

**Estado:** `SOURCE_PUBLISHED / PREPARED_NOT_RUN / NO_CFD`. No existe todavía evidencia de que esta V3 funcione. **No toca C3D-05 ni ninguna rama ajena al caso A.**

## Origen y progreso realmente constatado

La V2 se ejecutó en WSL (OpenFOAM Foundation 14). Su malla padre obtuvo `Mesh OK`; el hierro registró **4 celdas con determinante menor a 0.001**, la arena **8 caras sesgadas** (skewness máxima **4.070513822**) y ambas regiones siguieron con **un check fallido**. El área real de interfaz siguió igual a la original, **6,343.771874 mm² de cada lado**, error −0.139498 % frente al STL. Por tanto la V2 mejora V1 (92→4 celdas metal, 16→8 caras arena) pero **todavía no está aceptada**.

Los defectos restantes están en capas de transición **Y ∈ [−40, −39.8] mm (metal)** y **Y ∈ [−39.8, −39.5] mm (arena)** según VTK de superficies. No se infiere el centro de las celdas a partir de los vértices VTK.

## Hipótesis controlada y cambios permitidos

En lugar de modificar el contorno curvilíneo y perder la fidelidad geométrica ya lograda, la V3 ensaya **dos parámetros internos** en seis combinaciones predeterminadas:

- `core_delta_mm`: desplazamiento simétrico de **cuatro vértices interiores** del metal en `Y=−39.8 mm`: índices 89, 90, 93, 94. Se prueban signos y magnitudes pequeñas; no se altera ningún punto de la superficie `metal_to_mold`, los `arc` o las otras estaciones.
- `sand_grading`: razón `simpleGrading` radial en los **108 bloques anulares del molde**. Mantener el mismo valor en todas las estaciones evita rupturas de discretización entre capas.

| Ensayo | Variación interior metal [mm] | Grading radial arena |
|---|---:|---:|
| T01 | −0.15 | 1.75 |
| T02 | +0.15 | 1.90 |
| T03 | −0.30 | 2.10 |
| T04 | +0.30 | 2.30 |
| T05 | −0.45 | 2.50 |
| T06 | +0.45 | 2.65 |

**No son resultados experimentales ni se promete éxito:** son seis pruebas paramétricas destinadas a ver si el determinante bajo del metal y la skewness de la arena desaparecen, sin degradar interfaz, topología y volumen. Si una prueba supera los requisitos, el barrido se detiene y preserva ese candidato; si ninguna pasa, retiene seis diagnósticos con fallo real para una siguiente decisión fundada.

## Una sola instrucción para la laptop

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && \
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/run_v3_sweep.sh
```

La carpeta raíz nueva protegida es `~/OpenFOAM/C3D04_V3_BASAL_SWEEP_01`. Se negará a sobrescribirla. Contiene los directorios `T01`…`T06` realmente ejecutados, `log.runner.Txx`, `C3D04_V3_SWEEP_SUMMARY.tsv`, `SWEEP_FINAL_STATUS.txt` y para cada fallo, `C3D04_V3_DIAGNOSTIC.txt` más logs/VTK que haya producido OpenFOAM. No modifica `C3D04_ROUNDED_MULTIBLOCK_PILOT_01` ni `C3D04_V2_BASAL_QUALITY_01`.

`run_v3_sweep.sh` hace pruebas estáticas de sintaxis, generador y topología antes de crear las salidas. Cada intento llama al mismo `Allmesh` que genera un `blockMeshDict` nuevo **exclusivamente** con esas sustituciones controladas, valida diff frente a V2, valida topología y ejecuta utilidades nativas `blockMesh`, `checkMesh -allGeometry -allTopology`, `splitMeshRegions` y medición de área. No hay `foamMultiRun`, modificaciones de temperaturas iniciales ni cambios termofísicos C14.

### Puertas de aceptación

Se exige `Mesh OK` sin checks fallidos de padre, metal y molde; 8,960 metal + 12,352 molde; volúmenes dentro ±2 % CAD; contacto recíproco `mappedWall` con 2,496 caras por lado; área entre caras acopladas dentro 0.1 % y diferencia de área de contacto/tapa vs STL dentro ±3 %. **No modificar ni relajar los criterios nativos de calidad.** Los registros de cada intento dan el número verdadero de celdas problemáticas, de caras sesgadas, no ortogonalidad y área (o `NA` si una fase impidió obtenerlos).

**Incluso una aceptación nativa es preliminar de malla;** antes de CFD siguen pendientes la distancia superficial completa al CAD, la física CHT/solidificación en 3D, las condiciones de frontera y sensibilidad/independencia de malla.

Documentación: [V1 y V2 con salida nativa](../../../../docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md), [V2 preservada](../C3D04_V2_BASAL_QUALITY/README.md).
