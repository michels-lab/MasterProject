# Caso A — Validación geométrica superficial de la malla C3D-04 V4/T02

**19 de noviembre de 2026 — Estado: `HERRAMIENTA_PREPARADA / AUDITORÍA_AÚN_NO_EJECUTADA / NO_CFD`.**

## Contexto real

La malla `C3D04_V4_TRANSITION_REPAIR_01/T02` del QuickCup **pasó nativamente** las tres pruebas `checkMesh` de OpenFOAM 14 (padre, hierro y arena) y los controles de volumen e interfaz. Está formada por 8,960 celdas metal + 12,352 arena, parches recíprocos `mappedWall` de 2,496 caras y área de contacto **6,343.771874 mm²**. Determinante mínimo de hierro **0.001566024926**, no ortogonalidad máxima padre **82.92036178°**, metal **77.9303929°** y arena **82.058116°**. Esto **NO prueba coincidencia superficial 3D** con el CAD real; la alta no ortogonalidad debe analizarse antes de producción numérica.

## Nuevo instrumento de auditoría

`cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_accepted_surface_fit.py`

- Lee exclusivamente la malla **preservada** en `constant/metal/polyMesh` y `constant/mold/polyMesh`, y las superficies originales verificadas por SHA256 `metal_v2.stl` / `mold_v2.stl` del proyecto.
- Requiere previamente estado de **malla y área aceptadas** en `NATIVE_BUILD_STATUS.txt`, para no confundir el caso V4/T02 con ensayos rechazados.
- Convierte caras poligonales nativas en triángulos de superficie, lee el STL binario y deduce únicamente la escala compatible entre metros y milímetros comprobando el bounding box. No adivina traslaciones ni rotaciones CAD.
- Construye un índice espacial BVH; evalúa distancias euclidianas punto→triángulo en las dos direcciones: **malla→STL y STL→malla**, para **hierro y arena por separado**.
- Muestrea vértices y centroides de triángulos repartidos por bandas axiales Y, incluyendo las bandas del redondeo basal; reporta máximo, RMS, percentil 95, percentil 99 y porcentaje de distancias superiores a 0.5 mm en cada dirección. Los 0.5 mm son un **umbral descriptivo de reporte**, no criterio de aceptación científica ya acordado.
- Usa solo Python estándar, sin Gmsh ni solver. Es **solo lectura** sobre malla/STL: el reporte se escribe en **un directorio nuevo**, protegido contra sobrescritura, bajo `~/OpenFOAM/C3D04_V4_T02_CAD_SURFACE_AUDIT_01`.
- Incluye prueba sintética `--self-test` para distancias punto-triángulo, árbol BVH, STL binario y conversión de unidades.

**Advertencia metodológica obligatoria:** las distancias se calculan sobre un **muestreo finito** de la superficie y **NO constituyen cotas superiores rigurosas de la distancia de Hausdorff**. Los cuadriláteros no planos se aproximan mediante triángulos y el STL puede tener su propio error de tessellation frente al STEP de SolidWorks. Un valor pequeño observado no certifica error máximo real pequeño. Si los residuos muestran desviaciones localizadas relevantes, realizar auditoría CAD B-Rep/STEP o triangulación más refinada antes de CFD; no introducir un corte de error arbitrario solo para aprobar.

## Único comando de ejecución WSL (sin CFD)

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && \
python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_accepted_surface_fit.py --self-test && \
python3 cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_accepted_surface_fit.py
```

La salida preservada será `~/OpenFOAM/C3D04_V4_T02_CAD_SURFACE_AUDIT_01/SAMPLED_CAD_SURFACE_REPORT.json`. El script informa **rechazo/errores de lectura o de SHA** en vez de generar una conclusión numérica ficticia.

## Criterio de transición a física

No confundir malla nativa aceptada con CFD listo. Mantener como pendientes: desviación superficial CAD (ambos materiales), evaluación de los rangos de no ortogonalidad con los esquemas discretos elegidos, estudio de independencia de malla, condiciones térmicas `metalTop/moldTop/moldExterior/moldBottom/moldRecessWall/moldRecessRoof`, continuidad de flujo/conjugación `metal_to_mold/mold_to_metal`, y reproducción de comportamiento térmico/solidificación de C14 en 3D. **No se ejecuta `foamMultiRun` en esta etapa.**

Referencia de origen: [V1–V4, evidencia nativa T02](C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md).
