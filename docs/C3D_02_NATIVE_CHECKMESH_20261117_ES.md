# C3D-02 — Diagnóstico nativo de mallas, 17-11-2026

## Procedencia
Evidencia **real** remitida por el investigador desde Ubuntu WSL con OpenFOAM Foundation 14:
`bash cases_3d/C3D_02_metal_sand_clean/Allmesh` produjo `BLOCKED / checkMesh.metal`; el investigador ejecutó
`bash cases_3d/C3D_02_metal_sand_clean/Allmesh --diagnose`, que leyó el log metálico existente y ejecutó únicamente `checkMesh` para la arena.

Carpeta local de evidencia: `~/OpenFOAM/C3D02_NATIVE_OF14_01`. No se ha corrido `foamMultiRun` ni validado CHT.

## Resultados originales de checkMesh -allGeometry -allTopology

| Métrica | metal | mold |
|---|---:|---:|
| cells | 85,350 | 274,788 |
| Total volume (m³) | 4.79793e-05 | 0.000103389 |
| Volumen (cm³) | 47.9793 | 103.389 |
| CAD (cm³) | 47.9874896432 | 102.84309608 |
| Desviación malla/CAD | -0.0171 % | +0.5308 % |
| Number of regions | 1 (OK) | 1 (OK) |
| Non-orthogonality max / mean (°) | 35.4722 / 9.76134 | 52.0242 / 9.51012 |
| Max skewness | 3.15367 (OK) | 3.36715 (OK) |
| Concave cells | 4,834 (5.664 %) | 14,951 (5.441 %) |
| Small determinant cells (<0.001) | 3 | 1 |
| Low-quality/negative face decomposition tets | 0 (Face tets OK) | 1 |
| Faces with concave adjacent-edge angles | sin dato | 31 (advertencia) |
| Failed mesh checks | **2** | **3** |
| Resultado | **RECHAZADA** | **RECHAZADA** |

Los errores de calidad están presentes a pesar de que los volúmenes y la conectividad global son coherentes. `checkMesh` puede devolver código de salida 0 aun habiendo fallado comprobaciones: **no interpretar RC=0 como Mesh OK**.

## Qué está demostrado y qué todavía no

- `blockMesh`, `snappyHexMesh` y `splitMeshRegions` terminaron sin error de proceso en el flujo nativo; el script encontró interfaz `mappedWall` recíproca con conteo de caras coincidente. **No hay todavía prueba de cobertura/área física correcta de interfaz.**
- `checkMesh` encontró un componente en cada región y volúmenes próximos al CAD.
- La **ubicación espacial** de las celdas con concavidad, determinante bajo y face tets defectuosos **no está disponible en los fragmentos de log recibidos**. No atribuir el defecto a interface, aristas, puntas, snap o STL sin inspeccionar VTK/ParaView.
- Ninguna corrida del 3D está físicamente validada; no bajar umbrales ni ejecutar CFD.

## Diagnóstico siguiente integrado a OpenFOAM, sin Python

Se amplió el mismo `Allmesh --diagnose`: además de consultar los logs, genera **copias independientes de cada `polyMesh` regional** bajo `native_quality/metal` y `native_quality/mold`; llama a `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` **en cada copia**, conservando archivos VTK separados por material y evitando colisión de nombres. La primera ejecución se limita al estado actual; si las carpetas de diagnóstico ya existen, se preservan. No remalla, no reescribe materiales ni ejecuta solver.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --diagnose
```

Resultado esperado: `~/OpenFOAM/C3D02_NATIVE_OF14_01/NATIVE_DIAGNOSTIC.txt`, los `native_quality/{metal,mold}/log.checkMesh` y los VTK específicos exportados por OpenFOAM. La ejecución del nuevo diagnóstico aún no está confirmada en Ubuntu.

## Criterio de la próxima corrección

Inspeccionar las **geometrías reales de defectos** en ParaView superpuestas a las mallas y STL; comprobar si se concentran en interfaces de materiales, aristas o extremos. Solo entonces diseñar una variante controlada de `system/snappyHexMeshDict` (p. ej. opciones de `snapControls` o refinamiento localizado) sobre carpeta **nueva**, documentando comparación de celdas cóncavas, determinantes, volumen CAD y contacto. Conservar siempre intactos C14 y los casos históricos.

## 17-11-2026 — VTK de defectos confirmados y primer ensayo nativo controlado

El investigador ejecutó de nuevo `Allmesh --diagnose` y confirmó **6 VTK en copias físicas** independientes:

- Metal: `concaveCells.vtk` y `underdeterminedCells.vtk`.
- Molde: `concaveCells.vtk`, `concaveFaces.vtk`, `lowQualityTetFaces.vtk` y `underdeterminedCells.vtk`.

No se han remitido aún coordenadas, capturas de ParaView ni métricas de distribución espacial: **la localización real de los defectos sigue desconocida**. No confundir la mera exportación VTK con inspección espacial.

Para producir una primera comparación numérica reproducible sin depender de Python, se preparó un ensayo nativo de sensibilidad al snapping. **Hipótesis, no corrección probada:** duplicar el valor de `snapControls/nSmoothPatch`, de 3 a 6, manteniendo fijos el CAD, el refinamiento L2, las zonas, los restantes controles y los materiales C14.

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --candidate-smooth
```

Este comando copia los diccionarios de origen a `~/OpenFOAM/C3D02_NATIVE_SMOOTH_01`, modifica **solo esa copia** mediante `foamDictionary -entry snapControls/nSmoothPatch -set 6`, ejecuta `blockMesh`, `snappyHexMesh`, `splitMeshRegions` y `checkMesh` nativos en **ambos** materiales y entrega una tabla `CANDIDATE_COMPARISON.tsv` con los conteos base/candidato. El caso anterior `C3D02_NATIVE_OF14_01` se utiliza como **referencia de solo lectura**. No sobrescribe carpetas existentes, no baja criterios de calidad, no ejecuta `foamMultiRun`. Si cualquiera de las regiones no pasa, informa rechazo.

**Estado:** solo código preparado y commit; ejecución del experimento aún pendiente de confirmar en Ubuntu. Si la prueba no mejora simultáneamente calidad y compatibilidad geométrica, no declarar avance; revisar VTK en ParaView para diseñar refinamiento localizado, no encadenar cambios a ciegas.


## 17-11-2026 — Prueba real `nSmoothPatch=6`: RECHAZADA

El investigador ejecutó en Ubuntu:

```bash
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --candidate-smooth
```

Resultados de `checkMesh` (ambas regiones):

| Región | Celdas cóncavas base | Candidata | Diferencia | Determinantes bajos base→candidata | Tetraedros defectuosos base→candidata | Checks fallidos |
|---|---:|---:|---:|---|---|---|
| metal | 4,834 | 5,004 | +170 (+3.52 %) | 3→3 | 0→0 | 2→2 |
| mold | 14,951 | 15,079 | +128 (+0.86 %) | 1→1 | 1→1 | 3→3 |

Ambas mallas mantienen **el mismo número de celdas** (metal 85,350; mold 274,788). Aumentar `nSmoothPatch` de 3 a 6 **empeoró la concavidad** y no resolvió ninguno de los checks fallidos. **No adoptar la variante para CFD**. No se puede inferir la distribución espacial de defectos a partir del recuento.

### Bug de posprocesamiento detectado y corregido

El reporte original `CANDIDATE_COMPARISON.tsv` de la variante mostraba en `volume_m3` el **mínimo volumen de celda** (`3.62642e-11` para metal base, `3.01694e-11` para mold base), no el `Total volume` de la región (`4.79793e-05` y `0.000103389` m³, respectivamente). La línea de `checkMesh` contiene **tres signos =**, y el AWK anterior leía el primero. Este defecto afectaba **también el rechazo de candidatos en la puerta de volumen CAD**. Es un bug del script Bash, no de OpenFOAM.

Se centralizó la lectura de `Total volume` en `scripts/native_checkmesh_report.sh`, buscando explícitamente `Total volume =` antes de tomar el valor. Se añadió el test Bash `tests/test_native_checkmesh_report.sh` con formato de log real y los cuatro conteos de concavidad observados. La corrección **no vuelve aceptable** el candidato: las 2+3 fallas de malla persisten.

Para **recalcular desde los logs existentes sin remallar**, ejecutar:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --compare
```

Salida nueva: `~/OpenFOAM/C3D02_NATIVE_SMOOTH_01/CANDIDATE_COMPARISON_CORRECTED.tsv`. Se preserva la tabla defectuosa original para auditoría, no se sobrescriben logs, no se modifica C14 ni se ejecuta OpenFOAM/CFD. **Aún no se ha ejecutado este modo corregido en Ubuntu del investigador.**

### Próxima decisión técnica

Revisar espacialmente los VTK de celdas cóncavas, celdas con determinantes bajos y cara tetraédrica defectuosa en ParaView **antes** de adoptar ajustes de refinamiento o snapping. Mantener ambos experimentos como baseline/candidato rechazado. No relajar `checkMesh` para superar la puerta.
