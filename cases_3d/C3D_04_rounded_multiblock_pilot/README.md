> **18-11-2026 — RESULTADO NATIVO REAL DEL CASO A, RECHAZADO EN CALIDAD:** la carpeta `C3D04_ROUNDED_MULTIBLOCK_PILOT_01` existe y la terminal WSL confirma malla `blockMesh` curvilínea de **8,960 celdas metal + 12,352 arena**, interfaz recíproca de **2,496 caras `mappedWall` por lado** y volúmenes cercanos al CAD (−0.138 % / +0.031 %). **NO pasó `checkMesh`: metal 92 celdas con determinante bajo (mín. 1.28027e-5); arena 16 caras altamente sesgadas (skewness máx. 4.5916); malla padre 12 celdas con determinante bajo.** La no ortogonalidad máxima metal/arena es 84.14°/80.37°. El auditor estático posterior sí pasó, pero `Allmesh` se negó a sobreescribir la carpeta; **no equivale a repetición/aceptación nativa**. El contacto no tiene área numérica medida porque el runner paró antes de esa etapa. No remallar a ciegas ni ejecutar CFD. Diagnóstico espacial **solo lectura**, tras `git pull`: `python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py`. [Registro científico del primer run](../../docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md).

# C3D-04 — QuickCup 3D de esquinas redondeadas, piloto multibloque conforme

**Estado 18-11-2026:** fuente, `Allmesh`, medidor de área y pruebas estáticas **PUBLICADOS en GitHub, NO ejecutados en WSL**. Caso independiente de la malla C3D-03 aceptada. **No ejecuta `foamMultiRun` ni modifica la física C14**.

## Motivación y CAD medido

C3D-03 superó `checkMesh` y produjo las regiones metal/arena correctas, pero localmente subestimó el área transversal del metal hasta ~9 % cerca de `Y=-39.8` y `-39 mm`. C3D-04 introduce estaciones cerca del radio basal y arcos en las esquinas, con la misma técnica conformante usada por el caso original del doctor: zonas `metal/mold` definidas en `blockMesh`, y la interfaz compartida desde el inicio.

Fuentes CAD: `../C3D_02_metal_sand_clean/constant/geometry/metal_v2.stl` y `mold_v2.stl`, binarios verificados por SHA256; no se usan para `snappyHexMesh`, sino como **referencia de geometría y volúmenes**.

**Estaciones Y en milímetros:** -65.5, -56, -40, -39.8, -39.5, -39, -38.5, -38, -20, 0. La sección exterior del molde es un cuadrado ligeramente redondeado y ligeramente cónico. La sección metálica se aproxima por un cuadrado de ancho variable con esquinas redondeadas; no afirmar que la interpolación entre estaciones equivale a toda la superficie SolidWorks. Se conserva la abertura inferior rectangular 22.5 × 27.5 mm desde Y=-65.5 hasta -56 mm, su techo y las paredes internas.

| Y [mm] | Ancho metálico [mm] | Radio de esquina del modelo [mm] | Área CAD aproximada [mm²] | Área de sección geométrica del modelo [mm²] |
|---:|---:|---:|---:|---:|
| -40 | 28.280 | 2.00 | ~796.406 | 796.325 |
| -39.8 | 30.178 | 1.00 | 909.900 | 909.853 |
| -39.5 | 31.218 | 1.50 | 972.582 | 972.632 |
| -39 | 32.218 | 2.00 | 1,034.616 | 1,034.566 |
| -38.5 | 32.800 | 2.30 | ~1,071.350 | 1,071.299 |
| -38 | 33.116 | 2.50 | 1,091.567 | 1,091.304 |
| -20 | 34.754 | 2.50 | 1,202.446 | 1,202.475 |
| 0 | 36.500 | 2.50 | ~1,326.886 | 1,326.885 |

**ATENCIÓN:** son comparaciones de áreas de perfiles de diseño calculados a partir de cortes del STL, no errores superficiales tridimensionales medidos. El radio de 1.0 mm en Y=-39.8 es **un parámetro de ajuste geométrico**, no una confirmación de un radio original constante del CAD.

## Geometría y resolución prevista (NO son datos de `checkMesh`)

| Magnitud | C3D-04 analítico | Referencia STL | Diferencia prevista |
|---|---:|---:|---:|
| Volumen metal | **47,941.092 mm³** | 47,987.697 mm³ | **−0.0971 %** |
| Volumen arena | **102,888.556 mm³** | 102,843.333 mm³ | **+0.0440 %** |
| Área metal–arena, laterales + base | ~**6,348.06 mm²** | ~6,352.634 mm² | **−0.072 %**, cálculo geométrico aproximado |
| Cantidad de bloques | 180 | — | 63 bloques metal + 117 molde |
| Aristas curvas `arc` | 144 | — | Esquinas curvas en las estaciones horizontales |
| Celdas esperadas | **21,312** | — | 8,960 metal + 12,352 molde |
| Caras de contacto previstas | **2,496 por lado** | — | Incluye base y laterales, `mappedWall` al dividir |
| Abertura inferior rectangular | Conservada | Conservada | No se crea una tercera región material |

El test geométrico del código comprobó estáticamente que **no hay aristas con discretización contradictoria, arcos ajenos a los bloques, bloques con vértices invertidos ni caras de bloque sin clasificar**. Aun así, la calidad real de caras deformadas y celdas cerca de radios inferiores depende de OpenFOAM nativo.

## Ejecución aislada en Ubuntu / Foundation 14 (sin CFD)

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_04_rounded_multiblock_pilot/tests/test_rounded_multiblock_static.sh &&
bash cases_3d/C3D_04_rounded_multiblock_pilot/Allmesh
```

Salida nueva protegida por defecto: `~/OpenFOAM/C3D04_ROUNDED_MULTIBLOCK_PILOT_01`. **Nunca sobrescribe** la salida local de C3D-03 o C3D-02. Si ya existe C3D04, detiene el proceso (se puede definir `C3D04_OUT` con otra ruta absoluta vacía).

El ejecutor hace `blockMesh`, `checkMesh -allGeometry -allTopology` del padre, `splitMeshRegions -cellZones 'metal mold' -noFields`, `checkMesh` de ambas regiones, revisión de `mappedWall` recíprocos, celda por zona, volumen frente al CAD y **área calculada de las caras** desde `polyMesh/points`, `faces` y `boundary` ASCII.

El medidor `scripts/measure_interface_area.py` utiliza solamente la biblioteca estándar de Python para **leer** los datos creados por OpenFOAM; no genera ni altera mallas. Guarda el reporte nuevo `CONTACT_AREA_REPORT.json`. Rechaza si las caras de contacto de ambos lados no son 2,496, si el área difiere entre regiones más de 0.1 %, o si el error frente al STL del área de contacto o la tapa supera ±3 %. El script **no prueba una distancia Hausdorff ni la posición de todas las caras CAD**; son verificaciones preliminares de área, no una certificación de fidelidad absoluta.

**No ejecutar CFD hasta completar después** la inspección CAD de superficie completa, las condiciones térmicas de frontera 3D y la independencia de malla.

## Regla de interpretación de resultados

- `Mesh OK` y `mappedWall` correctos: **topología y calidad nativas aprobadas**.
- `CONTACT_AREA_REPORT.json: contact_gate=true`: **área interfacial preliminarmente aceptada** dentro de tolerancias declaradas; la forma aún necesita validación espacial.
- `NO_CFD`: no hay solver térmico ni campos de solidificación de esta variante.
- Si falla el mallado, preservar `log.blockMesh`, `log.splitMeshRegions`, `log.checkMesh.*`, `log.contactArea` y `NATIVE_BUILD_STATUS.txt`. No repetir parámetros idénticos sobre resultados históricos.

## Documentos relacionados

- [C3D-03 — resultado nativo realmente obtenido](../../docs/C3D_03_RESULTADO_NATIVO_20261118_ES.md)
- [Caso original del doctor](../../doctor_original/cht/system/blockMeshDict)
- [Estrategia A/B/C](../../docs/C3D_02_ESTRATEGIA_MALLADO_CONFORMANTE_20261118_ES.md)
- [Primer avance del director](../../docs/PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md)

## Auditoría estructural adicional — 18-11-2026 (Caso A)

Se revisó el `blockMeshDict` de C3D-04 **sin ejecutar OpenFOAM**, recorriendo las conectividades de los 180 bloques y sus 716 aristas únicas. El conteo estático confirma 280 vértices, 63 bloques de metal, 117 de arena, 8,960 + 12,352 celdas previstas, 144 arcos sobre aristas de bloques, 162 caras exteriores asignadas una sola vez y 2,496 caras de contacto previstas por región. No se encontraron discrepancias de subdivisión en aristas compartidas, caras compartidas con distinta discretización, arcos sin bloque ni caras exteriores huérfanas. **Esto es un cálculo estructural del diccionario, no un resultado nativo de `checkMesh`.**

Para hacer repetible esta revisión, se añadió `scripts/audit_blockmesh_topology.py` a la prueba `tests/test_rounded_multiblock_static.sh`. Este verificador utiliza solo la biblioteca estándar Python; inspecciona los bloques, caras, arcos y parches declarados, y no modifica ni genera mallas. Se ejecuta automáticamente al lanzar el test estático documentado arriba. A fecha de esta nota, **la nueva prueba no se ha ejecutado en Ubuntu WSL** y C3D-04 permanece `PREPARED_NOT_RUN / NO_CFD` hasta registrar la salida nativa de Foundation 14. Si la prueba reporta `REJECTED`, no omitirla: corregir el origen del rechazo antes de usar `Allmesh`.
