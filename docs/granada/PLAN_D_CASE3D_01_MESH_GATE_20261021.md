# Operación Granada Grande — Plan D / case3d-01: evidencia de geometría y malla

**Fecha 21-oct-2026 — Estado: desarrollo de herramientas y pruebas, no ejecución OpenFOAM.**

## Identificación sin ambigüedad

El nombre científico y de caso acordado es exactamente **case3d-01**, dentro del **Plan D**. Su directorio de entrada histórico es `cases_3d/C3D_01_metal_mold`, porque los PR #18 (refinamiento) y #19 (barreras de ciencia) siguen editando el modelo. No se ha renombrado ni eliminado ese árbol sin resolver primero dichos PR. Existe un punto de entrada/documentación y script independiente en `cases_3d/case3d-01/` que puede preparar una copia de ejecución con ese nombre.

No confundir con `freesurface/FS-C01/`: es la rama científica B de interfaz libre, sin solidificación validada. Plan D aquí significa tridimensional metal–arena.

## Triple alcance

**A — Geometría y fuentes reales:** `analysis_tools/granada_plan_d_case3d01_mesh_gate.py` inspecciona el verdadero `blockMeshDict` versionado de la geometría, sus unidades OpenFOAM Foundation14 `units [mm];`, vértices, 29×36×29 celdas y límites reales 58×72×58 mm, y contrasta contra la referencia `geometry_reference.json`. Valida que las cajas envolventes metal/molde estén dentro de la malla de fondo; esta prueba AABB es insuficiente para demostrar que la superficie está cerrada o que los puntos semilla están realmente dentro de los STL. Cuando el investigador proporciona sus dos STL locales originales, comprueba exactamente los SHA-256 del SolidWorks original sin convertir ni publicar archivos. Registra en el reporte los hashes de todas las entradas accesibles.

**B — Gate de evidencias de mallado:** sin logs originales, el resultado del parser es `NOT_RUN_LOGS_NOT_SUPPLIED`. Con rutas a `log.blockMesh` y `log.checkMesh.background`, comprueba que no exista fallo fatal, que blockMesh termine normalmente y que checkMesh reporte `Mesh OK.`, 30276 celdas y bounding box en metros consistente con la malla. Captura SHA-256 de cada log y jamás ejecuta comandos de OpenFOAM o toca `polyMesh`. Incluso con logs correctos el estado es deliberadamente `SUPPLIED_LOG_SCREEN_PASSED_NOT_INDEPENDENT_MESH_CHECK`: texto aportado por el investigador NO constituye verificación independiente de la malla.

**C — Preparación segura con nombre canónico:** script `cases_3d/case3d-01/scripts/stage_mesh_only.sh`. En una carpeta nueva y externa a Git, verifica ambos archivos STL de SolidWorks, copia nativa `mm` sin transformaciones, incorpora el `blockMeshDict` existente y el script de `blockMesh`/ `checkMesh`, y declara el estado `BACKGROUND_MESH_INPUTS_ONLY_NOT_RUN`. Se niega a sobrescribir carpeta existente, publicar STL en el repositorio o correr CFD. La ruta histórica no se altera.

## Diferencia entre política de refinamiento y certeza científica

El PR #18 documenta una **decisión solicitada**: volumen completo de metal y arena nominalmente a 0.5 mm, dos niveles de refinamiento desde celdas de fondo de 2 mm. El PR #19 plantea una **suspensión como requisito científico** hasta analizar magnitudes macroscópicas, escala dendrítica y convergencia. Ambos documentos pueden coexistir únicamente si se distingue la preferencia de configuración de la hipótesis científica. Aquí el estado queda: `OPEN_0.5MM_NOT_AUTOMATICALLY_APPROVED`.

Para estimar costo, con volúmenes CAD de 47.987490 cm³ metal y 102.843165 cm³ arena, el equivalente uniforme ideal de cubos de 0.5 mm es `ceil((Vmetal+Vmolde)/(0.0005³))`, aproximadamente 1.207 millones de celdas. Ese número es **estimación geométrica ideal**, no resultado de `snappyHexMesh`, ni un límite total real de celdas, memoria, ortogonalidad, celda máxima o resolución dendrítica. El gate emite CSV comparativo para 2, 1, 0.5 y 0.25 mm.

## Ejecución y aceptación

Ver uso detallado y comandos en `cases_3d/case3d-01/README.md`.

- En GitHub CI: Python syntax, regresiones sintéticas y análisis read-only de los archivos CAD/mesh de referencia versionados. Nunca se ejecuta OpenFOAM. La ausencia deliberada de STL/logs privados debe quedar explícita.
- En Ubuntu local: preparar una copia con STL SHA esperados y ejecutar solamente `blockMesh` y `checkMesh`; guardar logs y auditar con `--require-stls --require-mesh-logs`.
- Luego, como fase **no cubierta** por este bloque, diseñar y ejecutar `snappyHexMeshDict` completo v14, interfaces metal/molde, refinamiento por volumen, patches y splitMeshRegions, verificar fracciones de volumen por región y tamaños físicos reales. Evitar acoplamiento térmico aparente por usar una sola región.
- Finalmente, formular CHT y solidificación con el solver real, termofísica JMatPro (J0 abierto), composición del hierro fundido, grafito/microestructura y validación de curvas experimentales (G1 abierta); ninguna afirmación sobre recalescencia sin modelo que la represente.

## Evidencia oficial sobre la arquitectura

Foundation 14 incluye tutorial de **CHT no isotérmico acoplado a un solver VOF** en `tutorials/multiRegion/CHT/VoFcoolingCylinder2D`. Su `system/controlDict` contiene `regionSolvers { fluid compressibleVoF; solid solid; }`. Referencia: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/VoFcoolingCylinder2D/system/controlDict . Esto demuestra la existencia de esa combinación en un tutorial oficial, **no** que nuestro STL/malla Plan D implemente ya las condiciones de frontera. Plan D no adopta VOF sin justificación; las rutas B y D siguen independientes.

Sintaxis del refinamiento volumétrico `mode inside; level`, superficies y `insidePoint` del ejemplo oficial `tutorials/mesh/snappyHexMesh/flange/system/snappyHexMeshDict`: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/mesh/snappyHexMesh/flange/system/snappyHexMeshDict . Esa sintaxis no sustituye un `snappyHexMeshDict` completo, ni verifica el mallado de dos materiales.

## No interferencia / bitácora permanente

Este bloque solo añade archivos de análisis, tests, workflow y carpeta canónica de entrada. No edita `NEXT_RESEARCH_ROADMAP_ES.md`, `PROJECT_AUDIT_LOG_ES/EN`, `cases_3d/C3D_01_metal_mold/`, ni fuentes pertenecientes a los PR #18, #19 y #20. Tampoco modifica datos históricos C14/B14, las salidas de V15/V16, STL privados ni FS-C01.

Próximo Granada: revisar los PR de malla en conjunto con director/costo computacional y, cuando se puedan ejecutar las primeras mallas en Ubuntu, importar logs checkMesh/surfaceCheck, diseñar y validar interfaces térmicas multi-región sin falsificar el estado científico.
