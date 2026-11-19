# Caso A / C3D-04 — Resultado nativo del primer mallado curvilíneo (18-11-2026)

**Evidencia primaria:** salida de Ubuntu WSL / OpenFOAM Foundation 14 compartida por el investigador. No se tienen los logs completos subidos al repositorio; se registran solamente los valores visibles en la terminal. **No se ejecutó CFD**, ni se debe interpretar este caso como malla aceptada.

## Resultado de la ejecución existente

La carpeta `~/OpenFOAM/C3D04_ROUNDED_MULTIBLOCK_PILOT_01` **ya existía** al lanzar la prueba estática actualizada, por lo que `Allmesh` de esa invocación se negó a sobrescribirla; la terminal **sí permitió inspeccionar los archivos de la corrida anterior**, que se conservan. La nueva auditoría estática de 180 bloques, 144 arcos, 280 vértices, 716 aristas, 162 caras externas y 2,496 caras previstas por lado fue ejecutada y pasó. No confundirse: el pase estático no revierte el rechazo del `checkMesh` de la corrida anterior.

Estado de la corrida **existente**:

```text
REJECTED / stage=CHECK_REGION_QUALITY / At least one native checkMesh, CAD volume or expected region cell count rejected / NO_CFD
```

| Magnitud | Metal | Mold |
|---|---:|---:|
| Celdas | 8,960 | 12,352 |
| Volumen `checkMesh` (m³) | 4.792144701e-05 | 0.0001028754004 |
| Referencia CAD (m³) | 4.7987697e-05 | 1.02843333e-04 |
| Desviación volumétrica aprox. | -0.1380 % | +0.0312 % |
| `Mesh OK` en el runner | **NO** | **NO** |
| Determinante mínimo | **1.280269566e-05** | 0.003117948625 |
| Celdas con determinante <0.001 | **92** | No reportadas |
| No ortogonalidad máxima | 84.14010705° | 80.37353325° |
| Caras con no ortogonalidad >70° | 580 | 144 |
| Skewness máxima | 2.35713197 | **4.591592248** |
| Caras con skewness elevado | No reportadas | **16** |
| Checks fallidos | **1** | **1** |

En la malla padre: **21,312 celdas**, bounding box `(0,-0.0655,0)` a `(0.0518,0,0.0518)` m, 788 caras con no ortogonalidad >70°, no ortogonalidad máxima 84.14010705°, determinante mínimo 0.0005399662232, **12 celdas con determinante pequeño**, **1 check fallido**.

`splitMeshRegions` entregó correctamente **metal/mold**, sin región CFD exterior:

- `metal_to_mold`: 2,496 caras, `mappedWall`, `neighbourRegion=mold`, `neighbourPatch=mold_to_metal`.
- `mold_to_metal`: 2,496 caras, `mappedWall`, referencia recíproca al metal.
- Fronteras externas del metal: `metalTop` 256 caras.
- Fronteras externas del molde: `moldTop` 192, `moldExterior` 3,264, `moldBottom` 192, `moldRecessWall` 384, `moldRecessRoof` 256 caras.

**Diagnóstico sustentado:** el metal fue rechazado por 92 celdas con determinante pequeño; la arena por 16 caras altamente sesgadas. El contacto topológico recíproco se formó. La elevada no ortogonalidad es un riesgo numérico adicional, aunque `checkMesh` la etiquetó `OK` en esos logs.

**NO está demostrado** todavía dónde están las 92 celdas ni las 16 caras, qué bloques específicos las originan, si se concentran en el radio basal, si el modelo geométrico coincide punto a punto con el CAD ni qué área tiene la interfaz realmente mallada. No atribuir causalidad a las estaciones de la base sin inspeccionar geometría real.

## Estado del análisis del área y próximos pasos

`CONTACT_AREA_REPORT.json` no apareció en la salida de terminal. El ejecutor original abortó en `CHECK_REGION_QUALITY` antes de entrar en `CHECK_CONTACT_AREA`; por tanto **no hay área nativa verificada de C3D-04**. Las 2,496 caras prueban el conteo y reciprocidad declarada, no el área.

Se añadió el diagnóstico de solo lectura `cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py`. Revisa logs previos y busca exportaciones VTK ya disponibles, informando rangos XYZ e histogramas de vértices por intervalos Y. También intenta calcular **solo en memoria y sin escribir ningún archivo** el área `metal_to_mold`, `mold_to_metal` y `metalTop` desde `polyMesh` existente, incluso cuando la calidad está rechazada. Un área preliminar favorable no autoriza CFD. **Vértices VTK ≠ número de celdas defectuosas.** No ejecuta `checkMesh`, `blockMesh`, CFD ni cambia evidencia. Si no hay VTK previo, lo comunica sin fabricar coordenadas.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py --self-test
python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/diagnose_existing_defects.py
```

**Puerta para un nuevo candidato curvilíneo:** identificar espacialmente las celdas de determinante bajo y caras sesgadas, modificar únicamente variables geométricas/discretización que expliquen el defecto, ejecutar en `C3D04_OUT` nuevo y comparar con el ensayo preservado. Mantener las 2 regiones, la abertura inferior y las condiciones científicas; **no reducir umbrales de `checkMesh` ni lanzar `foamMultiRun` con la malla rechazada**. No tocar las rutas del Caso B.

Fuente: salida de terminal aportada por el investigador y scripts del repositorio.

## Diagnóstico espacial y área realmente medidos (salida WSL posterior)

El investigador ejecutó exitosamente el auto-test del lector VTK legacy ASCII/BINARY y el diagnóstico de solo lectura. El reporte confirma los defectos de los logs y **localiza los vértices de las superficies exportadas**:

| Región / exportación | Vértices superficie VTK | Extensión Y [mm] | Extensión X/Z [mm] |
|---|---:|---|---|
| Padre `underdeterminedCells.vtk` | 88 | −40.0 a −39.8 | 10.8871 a 40.9129 |
| Metal `underdeterminedCells.vtk` | 304 | **−40.0 a −39.8** | 10.811 a 40.989 |
| Arena `skewFaces.vtk` | 40 | **−39.8 a −39.5** | 10.291 a 41.509 |
| Padre `nonOrthoFaces.vtk` | 712 | −40.0 a −39.8 | 4.91446 a 46.8855 |
| Metal `nonOrthoFaces.vtk` | 544 | −40.0 a −39.8 | 10.811 a 40.989 |
| Arena `nonOrthoFaces.vtk` | 228 | −40.0 a −39.8 | 4.91446 a 46.8855 |

**Advertencia esencial:** cantidades de vértices VTK de la superficie ≠ cantidades de celdas/caras defectuosas; estas últimas siguen siendo **92 celdas metálicas de determinante pequeño** y **16 caras de arena sesgadas** según el log. Los intervalos Y se basan en límites geométricos de VTK, no centroides de celdas.

El analizador recuperó directamente del `polyMesh` preservado, SIN ejecutar `checkMesh` ni escribir archivos:

- `metal_to_mold`: **2,496 caras, 6,343.771874 mm²**.
- `mold_to_metal`: **2,496 caras, 6,343.771874 mm²**.
- Diferencia de área entre regiones: **0.000000 %**.
- Error de área de contacto frente al STL: **−0.139498 %**, puerta preliminar **PASS**.
- `metalTop`: **256 caras, 1,326.384174 mm²**, error frente al STL **−0.037782 %**.

**La aceptación del área no invalida el rechazo de calidad de las mallas.** Las mediciones respaldan preservar geometría externa e interfaz y trabajar sobre distribución interior de elementos.

## Variante controlada Caso A — C3D-04 V2, preparada, sin corrida

[**C3D04_V2_BASAL_QUALITY**](../cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/README.md) deja el contorno curvilíneo y las 2,496 caras compartidas sin cambios. Contiene dos intervenciones diferenciadas: redistribuir con `smoothstep` 12 vértices interiores del núcleo de hierro en tres estaciones basales; cambiar a `simpleGrading (1.5 1 1)` los 108 bloques anulares de arena de forma continua entre capas. Los 180 bloques, 144 arcos, total de celdas y contornos CAD aproximados se conservan. La comparación textual auditada confirma **12 líneas de vértices + 108 de grading y ninguna otra**, pero no existe resultado `blockMesh`/`checkMesh` de V2 todavía.

La hipótesis es reducir la deformación axial del núcleo del hierro y concentrar celdas de arena en la interfaz. **No afirmar mejora hasta la corrida nativa.** El runner V2 mantiene sin excepciones `Mesh OK` del padre y ambas regiones, cero checks fallidos, contacto y área; no CFD.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/Allmesh
```
