# C3D-05 — Diagnóstico del determinante, primer mallado STEP/Gmsh/OF14

**Fecha:** 18-11-2026. **Fuente:** transcripción literal del postmortem `diagnose_existing_mesh.py` ejecutado en WSL por el investigador sobre la primera malla `~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`. Estado **REJECTED**, no CFD ni remallado.

## Resultados nativos reales

| `checkMesh` | Padre (previo a split) | Metal (tras split) | Arena (tras split) |
|---|---:|---:|---:|
| Número de celdas | 525,706 | 190,365 | 335,341 |
| Regiones conectadas | **1** | **1** | **1** |
| Volumen [m³] | 1.50811107809e-4 | 4.79675605036e-5 | 1.02843547305e-4 |
| Error de volumen frente a CAD de referencia | — | −0.04196 % | +0.000208 % |
| Aspect ratio máximo | 8.5407 — OK | 8.3080 — OK | 8.5407 — OK |
| No ortogonalidad máxima [°] | 68.8037 — OK | 68.8037 — OK | 68.6801 — OK |
| Skewness máxima | 1.04736 — OK | 0.88950 — OK | 1.04736 — OK |
| Celdas con determinante < 0.001 | **306** | **96** | **402** |
| Checks fallidos | **1** | **1** | **1** |
| Veredicto | `REJECTED` | `REJECTED` | `REJECTED` |

**Otros ensayos nativos aprobados:** `Cell volumes OK`, `Non-orthogonality check OK`, `Max skewness OK`, `Face tets OK`, `Concave cell check OK`, `Face interpolation weight OK`, `Face volume ratio check OK`, topología y una sola región conectada en padre/ambos materiales. **NO confundir** «la mayor parte de los indicadores es buena» con `Mesh OK`: **la malla sigue rechazada**.

Parches reales:
- Metal: `metalTop` tipo `patch`, **1116 caras**; `metal_to_mold` tipo `mappedWall`, **16218 caras**, `neighbourRegion mold / neighbourPatch mold_to_metal`.
- Arena: `moldOuterUnclassified` tipo `patch`, **29942 caras**; `mold_to_metal` tipo `mappedWall`, **16218 caras**, `neighbourRegion metal / neighbourPatch metal_to_mold`.

**Aclaración importante:** la cantidad de celdas de bajo determinante **aumenta al separar regiones**: 306 en malla conjunta frente a 96 metal + 402 molde = 498 en las mallas separadas. No son celdas con índices directamente comparables: `splitMeshRegions` renumera y cambia las fronteras. La diferencia merece análisis de las caras internas o acopladas, no un promedio ni la declaración de un error de `Gmsh`.

## Hipótesis fundamentada para el siguiente ensayo

El **determinante de celda de OpenFOAM** no es simplemente el determinante geométrico de los cuatro vértices de un tetraedro. En la implementación documentada por Foundation, `cellDeterminant` construye un tensor a partir de las **áreas vectoriales de las caras internas o acopladas**, lo normaliza y calcula su determinante. Si una celda tiene muy pocas direcciones independientes de esas caras, puede resultar un valor cercano a cero **aunque no existan celdas con volumen negativo y otros controles geométricos pasen**.

Por ello, antes de ajustar `Mesh.MeshSizeMin`, elegir un optimizador o cambiar a otro algoritmo, debemos distinguir:
1. Tetraedros problemáticos que tocan **dos o más caras de frontera**, especialmente en esquinas superiores, base, abertura inferior e interfaz metal–arena (problema de conectividad/reconstrucción y condición de frontera).
2. Tetraedros internos que sí tienen caras vecinas suficientes, pero cuyas direcciones normales son casi dependientes (problema de disposición/alineación geométrica).
3. Efecto de la separación regional: clasificar caras `mappedWall` y si contribuyen como caras acopladas a la métrica en OF14. **No asumir** que un `mappedWall` es igual a un `coupledPolyPatch` en este control sin cotejar fuente específica.

**La optimización Gmsh** (método `Gmsh` o `Netgen`) está disponible, pero no se debe asumir que mover nodos resuelve un caso en que faltan **direcciones topológicas independientes**. Si el patrón se concentra en intersecciones de fronteras, priorizar un diseño de malla híbrida o de superficie que garantice mejores conexiones internas; si se concentra en interiores, probar una optimización de tetraedros mediante **nuevo ensayo separado con solo un cambio controlado**, sin sobrescribir la corrida base.

Fuentes públicas: [Foundation 13, `primitiveMeshCheck.C`, rutina `cellDeterminant`](https://cpp.openfoam.org/v13/primitiveMeshCheck_8C_source.html) (verificar cambios específicos de Foundation 14 para las inferencias); [Foundation 14, `checkMesh.C`, control de determinante](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/meshCheck/checkMesh.C); [Gmsh, optimizadores disponibles](https://gmsh.info/doc/texinfo/gmsh.html).

## Herramientas nuevas de lectura, no destructivas

- [`diagnose_existing_mesh.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/diagnose_existing_mesh.py): confirma predicates que fallan, números de regiones, volúmenes, y fragmentos nativos del log.
- [`audit_underdetermined_topology.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/audit_underdetermined_topology.py): **lee** `underdeterminedCells`, `owner`, `neighbour`, `boundary` de mallas regionales y resume número de caras de frontera e internas en cada celda rechazada y qué parche toca. Si no existe el `cellSet`, reporta limitación sin modificar evidencia.
- [`measure_interface_area.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/measure_interface_area.py): aunque `Allmesh` se detuvo antes del análisis, se puede ejecutar **aparte** sobre la malla preservada para medir área real sobre caras, con archivo JSON de salida **nuevo**.

### Comandos para el siguiente diagnóstico del caso B

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only

python3 -m unittest discover -s cases_3d/C3D_05_step_gmsh_conformal/tests -p 'test_audit_underdetermined_topology.py' -v

python3 cases_3d/C3D_05_step_gmsh_conformal/scripts/audit_underdetermined_topology.py \
  ~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01

python3 cases_3d/C3D_05_step_gmsh_conformal/scripts/measure_interface_area.py \
  ~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01 \
  --out ~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01/CONTACT_AREA_DIAGNOSTIC_ONLY.json
```

Los dos diagnósticos leen mallas existentes; el segundo **crea únicamente el JSON indicado** y lo rechaza si el archivo ya existe. No se ejecuta OpenFOAM, Gmsh ni solver CFD. **Si da error de formato de datos, no borrar el caso ni reprocesarlo**: compartir el error textual y localización del archivo problemático.

## Próxima decisión

1. Leer clasificación de las 96/402 celdas y medición independiente de área.
2. Identificar si son tetraedros de esquinas/interfaz con pocas caras internas o interiores de bajo determinante. Sólo entonces cambiar topología, mallador u optimizador **en un caso aparte** y medir reducción en `underdeterminedCells` sin bajar el umbral 0.001.
3. Revalidar simultáneamente el área CAD, parches metal–arena y `Mesh OK` padre/ambas regiones.
4. **NO CFD 3D** hasta aceptación geométrica y condiciones de frontera físicas.

[Primer mallado y resultados](C3D_05_RESULTADO_PRIMER_MALLADO_20261118_ES.md) · [registro comparativo A/B](C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md).
