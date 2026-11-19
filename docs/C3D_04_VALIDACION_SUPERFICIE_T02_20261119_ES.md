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

## Resultado real de validación muestral V4/T02 — WSL 19-11-2026

**Estado actualizado: `SAMPLED_BIDIRECTIONAL_SURFACE_DISTANCE_COMPLETED / FAVORABLE_MEASURED_RESIDUALS / NOT_RIGOROUS_HAUSDORFF / NO_CFD`.**

El investigador ejecutó en WSL el autodignóstico sintético, el lector de STL binario y el auditor nativo de superficie sobre la malla aceptada preliminarmente `C3D04_V4_TRANSITION_REPAIR_01/T02`. El programa imprimió `SELF_TEST_OK: point-to-triangle, BVH, STL binary parser and auto unit scale`, confirmó la identidad SHA-256 de ambos STL y creó:

```text
/home/michel/OpenFOAM/C3D04_V4_T02_CAD_SURFACE_AUDIT_01/SAMPLED_CAD_SURFACE_REPORT.json
```

**Estos datos son puntos muestreados frente a triángulos continuos de la superficie opuesta, no Hausdorff exacto ni error máximo garantizado.** Las dos direcciones malla/STL se informan por separado.

| Material | Dirección | Muestras | Máximo [mm] | P95 [mm] | P99 [mm] | RMS [mm] | Muestras >0.5 mm |
|---|---|---:|---:|---:|---:|---:|---:|
| Hierro | STL → malla | 4,421 | **0.104768977** | 0.084237137 | 0.100467258 | 0.045467291 | 0 % |
| Hierro | malla → STL | 2,910 | **0.102346260** | 0.051427115 | 0.075091194 | 0.022718477 | 0 % |
| Arena | STL → malla | 3,897 | **0.104973015** | 0.079895382 | 0.098208442 | 0.041813787 | 0 % |
| Arena | malla → STL | 4,311 | **0.099903895** | 0.042798513 | 0.057900141 | 0.018156947 | 0 % |

El muestreo compara **5,504 triángulos nativos metal** contra **4,628 triángulos STL metal** y **13,568 triángulos nativos arena** contra **3,716 triángulos STL arena**. Ambos STL se escalaron **0.001 (mm → m)**. Diferencia relativa máxima de dimensiones bounding box entre CAD y malla: **6.532015871879646e−8 para hierro**, **5.89142434697673e−8 para arena**. Hashes de fuentes verificados:

- Metal STL: `f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf`.
- Arena STL: `ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32`.

**Conclusión:** el máximo observado en estas muestras es **0.104973015 mm**, sin ninguna muestra >0.5 mm. Resultado favorable para la aproximación geométrica de ambas superficies al STL aprobado, pero **NO establecer un gate de precisión no acordado, no afirmar coincidencia absoluta con STEP ni validación geométrica global**. Los mayores residuos podrían estar localizados cerca de las transiciones Y−40..−39 mm; no se probó dónde están las distancias máximas con el resumen actual.

**Siguiente auditoría read-only:** inspeccionar no ortogonalidad severa de T02 mediante `log.checkMesh.parent/metal/mold` y la geometría ya exportada como `nonOrthoFaces.vtk`. Los máximos nativos siguen en 82.92036178° padre, 77.9303929° metal y 82.058116° arena. Se requiere caracterizar localización y cantidad de caras antes de elegir esquemas numéricos y eventual prueba de sensibilidad de malla. No volver a ejecutar el auditor superficial en el mismo directorio, pues se negará a sobrescribir su evidencia. **No CFD.**
