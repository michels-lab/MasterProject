# Caso A — C3D-04 V2: corrección controlada de calidad basal en `blockMesh`

**Estado:** `PREPARED_NOT_RUN`. Fuente publicada, sin ejecución nativa de esta variante, sin CFD y sin modificación de la malla histórica `C3D04_ROUNDED_MULTIBLOCK_PILOT_01`.

## Evidencia que justifica la variante

Los VTK reales de la malla original de C3D-04 ubican todas las superficies exportadas de determinante bajo del metal entre **Y = -40 y -39.8 mm** (92 celdas en el log), y las caras de arena con `skewness` elevada entre **Y = -39.8 y -39.5 mm** (16 caras en el log). No se equiparan los vértices de las superficies VTK a centros ni a número de celdas.

El área de contacto nativa ya fue recuperada directamente del `polyMesh` original: **6,343.771874 mm² por lado**, diferencia 0.000 %, error **−0.139498 %** frente al CAD. La tapa metálica tiene **1,326.384174 mm²** (−0.037782 %). Por ello, se preservan el contorno curvilíneo, los 144 `arc`, el contacto de 2,496 caras, la base, el receso inferior y los 180 bloques.

## Cambios exactos de V2

**Intervención metal (malla interior):** se redistribuyen SOLO 12 vértices **internos** de la cuadrícula de hierro, cuatro por estación en `Y=-39.8,-39.5,-39.0 mm`. Se utiliza interpolación `smoothstep` desde la estación interior original de `Y=-40 mm` hasta la de `Y=-38.5 mm`, con derivada inicial/final suavizada. Los vértices de la superficie exterior del metal, las esquinas redondeadas, los arcos y la interfaz metal/arena permanecen idénticos al diccionario de referencia. **Hipótesis:** reducir el salto axial de la cuadrícula interior responsable de elementos cercanos al radio basal con determinante bajo.

**Intervención arena (distribución de celdas):** `simpleGrading (1 1 1)` cambia a `simpleGrading (1.5 1 1)` SOLO en los **108 bloques anulares de arena**. Se aplica de forma uniforme en las 9 capas para preservar la conformidad de las discretizaciones sobre caras horizontales compartidas. Los bloques del núcleo de arena no se tocan. **Hipótesis:** agrupar discretización radial hacia la interfaz y reducir deformación de caras de la arena en la zona cercana a su contacto con metal. Este cambio no garantiza disminuir `skewness`; el veredicto pertenece a `checkMesh` nativo.

Ambas intervenciones se hacen en diferentes materiales con la **misma interfaz geométrica**. La prueba `tests/test_candidate_geometry.py` comprueba que **no existe ningún otro cambio** frente al diccionario original. Se mantiene `units [mm]`, igual geometría externa y número de bloques/celdas/caras nominales. Ningún valor de propiedades térmicas C14 ni física 3D se incorpora todavía.

## Comando único — ejecución nativa solo de malla en la laptop

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/Allmesh
```

`Allmesh` comprueba primero el diff físico del diccionario y la topología, después genera una **carpeta nueva** `~/OpenFOAM/C3D04_V2_BASAL_QUALITY_01`. Si esta carpeta existe, detiene la ejecución sin sobreescribirla; para otro intento se puede escoger `C3D04_V2_QUALITY_OUT` absoluto y nuevo. Usa exclusivamente utilidades nativas `blockMesh`, `checkMesh`, `splitMeshRegions`; el auxiliar Python solo comprueba el diccionario y mide áreas de `polyMesh`.

La puerta obligatoria exige: regiones `metal/mold` únicas; `Mesh OK` y cero checks fallidos para malla padre y ambas regiones; 8,960 y 12,352 celdas esperadas; volumen dentro de ±2 %; parches recíprocos `mappedWall` con 2,496 caras por lado; área interfacial recíproca dentro de 0.1 % y diferencia frente al CAD de hasta ±3 %. **No relajar esas puertas.** No se ejecuta `foamMultiRun` ni se preparan `0/`, BC térmicas o solver.

Si V2 falla cualquier puerta nativa, **el mismo `Allmesh` ejecuta automáticamente el analizador espacial y de área de solo lectura** y guarda `C3D04_V2_DIAGNOSTIC.txt` dentro de la carpeta nueva de salida, además de imprimir su resumen. No pedir un segundo script ni reejecutar el mallado para obtener evidencia. Si V2 no supera ambas verificaciones, conservar sus logs y comparar `checkMesh` con la corrida original. En particular, la redistribución interna puede reducir el determinante del hierro pero no corrige automáticamente deformaciones del molde; ambas métricas deben mejorar o al menos identificarse para decidir una siguiente modificación. Ningún resultado exitoso se presupone.

Referencia: [resultado nativo original](../../../../docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md).
