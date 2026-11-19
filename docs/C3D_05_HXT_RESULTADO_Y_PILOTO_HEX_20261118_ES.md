# Caso B — C3D-05: HXT falló el mismo determinante; piloto HEX8 independiente

**Fuente primaria:** transcripción del investigador `Pasted text(20261119-053507).txt`, ejecución en Ubuntu WSL de `run_hxt_pilot.sh` con ambos SolidWorks STEP originales. **Datos nativos de Gmsh + OpenFOAM 14**; el ensayo HXT fue ejecutado, los números **no son estimaciones**. Candidato hexagonal nuevo **preparado, todavía NO ejecutado**. NO CFD.

## Ensayo HXT realmente ejecutado

El comando unificado `git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hxt_pilot.sh` pasó la prueba HXT en memoria (**176 elementos 3D de prueba**), generó, convirtió y separó la malla QuickCup auténtica en `~/OpenFOAM/C3D05_STEP_GMSH_HXT_01`. Falló en `CHECK_REGION_QUALITY`, sin CFD; la salida se preservó.

| Magnitud | Delaunay 3D original | HXT 3D |
|---|---:|---:|
| Celdas totales | **525,706** | **508,924** |
| Celdas metal | 190,365 | 178,290 |
| Celdas arena | 335,341 | 330,634 |
| Volumen metal [m³] | 4.79675605036e−5 | **4.79675605036e−5** |
| Volumen arena [m³] | 1.02843547305e−4 | **1.02843547305e−4** |
| Número de regiones conectadas padre/metal/arena | 1/1/1 | **1/1/1** |
| Determinante < 0.001 en padre | 306 | **306** |
| Determinante < 0.001 en metal | 96 | **96** |
| Determinante < 0.001 en arena | 402 | **401** |
| Máx. no ortogonalidad metal [°] | 68.8037 | 65.4096 |
| Máx. no ortogonalidad arena [°] | 68.6801 | 67.8457 |
| Máx. skewness metal | 0.88950 | 0.95293 |
| Máx. skewness arena | 1.04736 | 0.84561 |
| Área de contacto por lado [mm²] | 6348.106691699194 | **6348.106691699321** |
| Caras recíprocas de contacto por lado | 16,218 | **16,218** |
| Error área contacto vs STL | −0.0712618 % | **−0.0712618 %** |
| `contact_gate` | true | **true** |
| `checkMesh` padre, metal, arena | REJECTED | **REJECTED** |

HXT redujo **16,782 tetraedros (−3.19 %)**, pero **no eliminó el problema** del control `cellDeterminant`. La prueba nativa `checkMesh` reportó un solo check fallido en las tres mallas. `Face tets`, no ortogonalidad, skewness, concavidad, volúmenes y conectividad están aceptables. Las auditorías `mappedWall`/área son recíprocas, **pero la malla HXT no se considera válida para CFD**.

## Evidencia topológica clave: 100 % de las celdas problemáticas están en aristas de frontera

La herramienta `audit_underdetermined_topology.py` leyó los `cellSet` nativos de HXT:
- **96 de 96** celdas malas metal: 2 caras internas + 2 caras frontera; una frontera `metalTop` y otra `metal_to_mold`.
- **401 de 401** celdas malas arena: 2 internas + 2 frontera; **95** tocan `mold_to_metal` y `moldOuterUnclassified`; las restantes **306** tocan dos caras exteriores `moldOuterUnclassified`.
- **Ninguna** celda marcada tiene cero caras de frontera.
- HXT y Delaunay conservaron incluso las **mismas 1116 caras de `metalTop`** y **16218 caras de interfaz**. La geometría y el mallado superficial no parecen la fuente de la variación de los 3D interiores; el patrón de fallo de aristas es robusto en ambos generadores.

**Interpretación:** evidencia muy fuerte de un problema de topología/discretización en celdas tetraédricas adyacentes a la intersección de fronteras; aún **NO** demostración de que cualquier malla HEX8 resolverá las restricciones de wellposedness. No bajar el umbral 0.001 para esconder estas celdas.

## Cambio razonado de familia topológica

En lugar de ensayar indefinidamente Delaunay/Frontal/HXT (Frontal 3D está bloqueado por falta de Netgen en la compilación local), se introduce una prueba de **conversión de tetraedros a hexaedros**, método explícitamente documentado por Gmsh:

- Gmsh `Mesh.SubdivisionAlgorithm = 2` → **all hexahedra** y `gmsh.model.mesh.refine()` después de generar la malla tetraédrica. Gmsh documenta el algoritmo y la llamada de subdivisión en su [manual oficial](https://gmsh.info/doc/texinfo/gmsh.html). El conversor de OpenFOAM Foundation `gmshToFoam` requiere que una malla hexaédrica tenga **caras externas cuadriláteras** ([documentación del conversor](https://cpp.openfoam.org/v13/gmshToFoam_8C.html)); por ello no basta con convertir volúmenes: la nueva ruta exige **HEX8-only 3D / QUAD4-only 2D** como puerta previa al formato MSH2.
- Se añade [`scripts/preflight_hex_subdivision.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/preflight_hex_subdivision.py): prueba Gmsh de **dos pequeños sólidos OCC contiguos con cara compartida** en memoria, grupos físicos metal/molde y contacto, refinamiento tetra→hexa, verificación de tipos **Gmsh 5 para hex y 3 para quad**. No crea resultados persistentes y aborta si esta compilación no soporta la operación.
- `build_step_mesh.py` añade `--subdivide-to-hex`, `--max-base-tets`: tras `occ.fragment`, generar tetraedros originales, contar y **abortAR antes de subdividir si superan el máximo**; solo entonces aplicar la subdivisión, validar todos los tipos físicos y exportar MSH2 ASCII con escala SI `0.001`. Mantener el método tetra original por defecto.
- `Allmesh` acepta las opciones **`C3D05_SUBDIVIDE_HEX`**, **`C3D05_MESH_SIZE_MM`** y **`C3D05_MAX_BASE_TETS`**, conservando valores anteriores cuando no se definen. Mismas pruebas de `checkMesh`, `gmshToFoam`, `mappedWall`, volumen y área de contacto.
- [`scripts/run_hex_subdivision_pilot.sh`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh) cumple la **regla de una sola instrucción**, ejecuta test estático, pruebas de regresión, preflight en memoria, piloto nuevo y diagnóstico. Protege las mallas Delaunay y HXT, y guarda logs aun en error. Rechaza una carpeta objetivo existente y requiere al menos **4 GiB de RAM disponible** reportados por Linux. Cambia la malla base a **3.6 mm** con tope de **150,000 tetraedros ANTES de subdividir** para minimizar riesgo de RAM (la primera malla fue de ~525,706 tets a 1.8 mm).

**IMPORTANTE EN TESIS:** esto es un **estudio de factibilidad topológica**, no un experimento A/B de igual resolución; cambian a la vez el tipo de celda y el tamaño nominal inicial de 1.8→3.6 mm para limitar consumo. Aunque esta malla pase `checkMesh`, faltará luego la **convergencia de malla** y comparar coste/precisión contra los métodos A/B antes de hacer simulación física.

**Un solo comando en Ubuntu WSL** (aún no ejecutado):

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh
```

**Criterio de aceptación:** `Mesh OK` padre + ambas regiones; `Number of regions: 1` para metal y molde, volúmenes ±2 % frente CAD, solo celdas HEX8, caras QUAD4, contacto metal↔arena con `mappedWall` recíproco y diferencia de área <= 3 %, área superior conservada. **NO CFD hasta evidencia nativa de éxito y campos físicos 3D aprobados**.

**Estado de cierre:** Delaunay (tet) REJECTED; Frontal BLOCKED_NETGEN; HXT (tet) REJECTED; **HEX8 piloto PREPARED_NOT_RUN**. Ambos CAD STEP intactos; caso A C3D-04 independiente.
