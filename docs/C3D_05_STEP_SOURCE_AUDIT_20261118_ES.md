# C3D-05 — Auditoría de los STEP originales de SolidWorks, 18-11-2026

**Estado:** ambos STEP originales fueron recibidos en conversación, inspeccionados directamente con OpenCASCADE/cadquery en el entorno de análisis y **ACEPTADOS como fuentes CAD preliminares** para C3D-05. **NO se ha ejecutado `Gmsh`, `gmshToFoam`, `splitMeshRegions` ni `checkMesh` de C3D-05 en Ubuntu WSL. No hay CFD.** Esta bitácora **no afirma que los STEP estén versionados en el repositorio**: los binarios ASCII permanecen como adjuntos recibidos; el investigador debe tenerlos accesibles localmente al ejecutar `Allmesh`.

## Fuentes originales recibidas

| Propiedad | Metal | Molde |
|---|---|---|
| Nombre adjunto | `metalmm.STEP` | `QuickCupmm.STEP` |
| Tamaño | 38,011 bytes | 71,973 bytes |
| SHA-256 | `ea5f65796c5156e4931eaec29ff656c279120925ebc083767a16b80892d0f475` | `fe126d23bb639196258551fd156591d7fe2b0b4ce1d7c9ece47016e8ad08a40c` |
| Cabecera | `STEP AP214` | `STEP AP214` |
| Exportador | `SolidWorks 2026` | `SolidWorks 2026` |
| Forma | 1 `MANIFOLD_SOLID_BREP`, 1 sólido válido | 1 `MANIFOLD_SOLID_BREP`, 1 sólido válido |
| Volumen CAD exacto leído [mm³] | **47,988.5249983** | **102,843.3208254** |
| Área de superficie total [mm²] | **7,679.7196385** | **23,325.9970609** |
| Extensión X [mm] | 7.65–44.15 | 0–51.8 |
| Extensión Y [mm] | −40–0 | −65.5–0 |
| Extensión Z [mm] | 7.65–44.15 | 0–51.8 |

Las pequeñas tolerancias geométricas (~1e-7 mm en bordes extremos) están relacionadas con la lectura del B-Rep. Las dimensiones se consignan redondeadas a los valores CAD nominales.

**UNIDADES — punto crítico:** el fichero STEP AP214 declara `LENGTH_UNIT ... SI_UNIT($,.METRE.)` y las coordenadas almacenadas son metros (por ejemplo `0.00765`, equivalente a **7.65 mm**). El lector OpenCASCADE/CadQuery devolvió los sólidos en mm por su conversión de unidades; **no asumir que las cifras de coordenadas del texto STEP están directamente en mm**. El pipeline de Gmsh declara `Geometry.OCCTargetUnit = "MM"` al importar y, antes de exportar la malla al formato OpenFOAM, `Mesh.ScalingFactor=0.001`. Estos dos pasos son distintos y deben validarse con bbox/volúmenes nativos en C3D-05. Nunca aplicar escala 0.001 dos veces.

## Contacto efectivo entre sólidos — comprobación CAD de referencia

Se cargaron por separado ambos B-Rep STEP y se aplicó la operación booleana de **unión** mediante OpenCASCADE.

| Magnitud | Resultado |
|---|---:|
| Volumen metal [mm³] | 47,988.52499826381 |
| Volumen arena [mm³] | 102,843.3208254133 |
| Suma metal + arena [mm³] | 150,831.8458236771 |
| Unión booleana [mm³] | **150,831.8458236516** |
| Número de sólidos tras unión | **1** |
| Área total de las superficies antes de unir [mm²] | 31,005.7166994 |
| Área exterior de la unión [mm²] | **18,300.0744617** |
| Área interna compartida estimada [mm²] | **6,352.82111884** |
| Referencia STL de contacto (laterales + base) [mm²] | 6,352.63369377 |
| Diferencia STEP frente a STL [%] | **+0.00295 %** |

Área compartida deducida de la eliminación de superficies internas durante la unión:
`A_contact = (A_metal + A_mold − A_union)/2`.

**Interpretación respaldada:** el volumen de la unión coincide numéricamente con la suma de volúmenes (interpenetración volumétrica por encima del error de las operaciones no apreciable), su resultado consta de un sólido y la reducción de superficie corresponde a un área de contacto real muy cercana al STL metálico. Esto es **evidencia sólida de alineación y contacto CAD**, pero **NO reemplaza** la prueba nativa de conformalidad de malla `gmsh.model.occ.fragment`, `gmshToFoam`, `mappedWall` ni `checkMesh`.

## Variación frente a STL v2

| Variable | STEP | STL v2 aprobado | Diferencia |
|---|---:|---:|---:|
| Volumen metal [mm³] | 47,988.5249983 | 47,987.697 | +0.00173 % |
| Volumen arena [mm³] | 102,843.3208254 | 102,843.333 | −0.000012 % |
| Área contacto metal–arena [mm²] | 6,352.82111884 | 6,352.63369377 | +0.00295 % |

**La referencia de mayor fidelidad geométrica para el camino C3D-05 es el STEP B-Rep, no el STL triangulado.** Las diferencias anteriores son consistentes con una triangulación finita del STL. Se preservan ambas referencias y las tolerancias y no se cambian entradas de C14 ni C3D-04.

## Estado de ejecución y pasos necesarios

- **Hecho:** dos archivos STEP AP214 autenticados por bytes/huella, sólidos válidos, medidas y contacto booleando consistentes.
- **No hecho:** importar/fragmentar mediante Gmsh en WSL; convertir `.msh` a Foundation 14, mallar C3D-05, `checkMesh`, parámetros físicos 3D o CFD.
- **Siguiente:** poner una copia de ambos STEP originales en rutas accesibles para Ubuntu WSL, por ejemplo bajo una carpeta **local de insumos fuera de las carpetas de resultados**, conservar nombres/sha, y ejecutar el `Allmesh` de C3D-05. El pipeline comprobará el preflight CAD nuevamente con Gmsh y abortará antes de mallar si OCC detecta fallos.
- **Paralelo:** ejecutar la ruta C3D-04 curvilínea ya preparada, sin sobrescribir la C3D-03 preliminarmente aceptada.

[Guía de C3D-05](../cases_3d/C3D_05_step_gmsh_conformal/README.md) · [comparación de rutas A/B](C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md) · [evidencia C3D-03](C3D_03_RESULTADO_NATIVO_20261118_ES.md).
