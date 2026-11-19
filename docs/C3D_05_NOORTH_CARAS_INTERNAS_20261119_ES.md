# Caso B C3D-05 — Las 1,826 caras de alta no ortogonalidad están en el interior

**Fecha de registro:** 19/11/2026. **Evidencia primaria:** salida WSL real del investigador ejecutando `run_nonorth_face_audit.sh` sobre `/home/michel/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`. **Malla HEX8 ya validada geométricamente; no hubo nuevo mallado ni CFD.**

## Hallazgo observado, confirmado por conjuntos nativos

El script comparó los `nonOrthoFaces` guardados por OpenFOAM 14 con los recuentos `checkMesh` de padre, metal y arena. El resultado real fue:

```text
METAL: severe=595 internal=595 boundary=0 contact-adjacent=0 outer-adjacent=0
  native severe faces by boundary patch: {}
MOLD: severe=1231 internal=1231 boundary=0 contact-adjacent=0 outer-adjacent=0
  native severe faces by boundary patch: {}
NATIVE_FACESET_AUDIT: PASSED (metal+mold=1826 / parent=1826). NO REMESH, NO SOLVER.
```

La ejecución pasó los chequeos estáticos del repo, **2 regresiones de nombres Python + 3 regresiones del localizador de caras**, y antes del diagnóstico confirmó de nuevo `OVERALL_GEOMETRY_TOPOLOGY: PASSED` con los siete predicados originales SHA256/STEP/HEX8. El nuevo JSON de evidencia guardado en WSL es:

`~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02/NONORTH_FACESET_TOPOLOGY_AUDIT_20261119.json`.

**Interpretación rigurosa:**
- Las **595** caras de alta no ortogonalidad del metal, y las **1,231** de la arena, son **100 % caras internas**, no caras de frontera. Suman **1,826**, exactamente el recuento de la malla padre.
- **Ninguna** cara severa es incidente a una celda que posea una cara de interfaz `metal_to_mold` / `mold_to_metal`; ninguna es incidente a una celda que posea una cara externa `metalTop` / `moldOuterUnclassified`. Esta es una medición por conectividad directa, **no** una distancia física ni una prueba de que estén lejos del contacto.
- Por ello, no hay fundamento para señalar un defecto en las caras `mappedWall` o en las celdas que las tocan **como causa directa de las 1,826 caras severas**. Sigue habiendo riesgo de precisión de los términos de difusión/gradiente en celdas interiores, incluida la evolución del frente de solidificación.
- El mayor ángulo de no ortogonalidad **76.7989°** y las **1,826 caras >70°** NO son un fallo de `checkMesh` en este ensayo (`Mesh OK` padre/metal/arena); esto **no implica** que el esquema temporal o de gradiente sea suficientemente estable. Sin solver térmico no puede afirmarse estabilidad ni conservación energética.
- **No remallar todavía por suposición**. Primero medir dónde se agrupan las caras en relación con las capas celulares de las paredes/interfaz; después elegir si optimizar malla o evaluar esquemas correctivos bajo condiciones térmicas reales.

## Siguiente diagnóstico diseñado sin remallar: distancia por capas de celdas

Se añadió [`scripts/audit_nonorth_hop_distance.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/audit_nonorth_hop_distance.py) que construye, en **memoria CSR**, el grafo de adyacencia `owner/neighbour`. Ejecuta dos BFS independientes por material: desde celdas que tocan **interfaz metal–arena** y desde celdas que tocan la **frontera exterior**. Para cada cara severa, informa el menor número de *saltos entre celdas* desde sus dos celdas incidentes hasta cada clase de frontera; entrega histogramas, mínimos, medianas, p90 y máximos.

**Importante:** la métrica está expresada en **capas topológicas (hops)**, NO milímetros ni distancia euclidiana. No se infiere error numérico ni campo térmico. Se verifican los conteos nativos, `Mesh OK` independiente, el informe de cara previa y los parches; nunca se reemplaza la malla ni se fuerza aceptación. Tiene tope de memoria disponible en WSL antes de construir el grafo y prueba sintética de cadenas de celdas, salto 0 (pared), índices incorrectos y estadísticos.

[El orquestador de una sola ejecución](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_hop_distance.sh) preserva todos los archivos anteriores y crea el JSON **solo si todavía no existe**:

`~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02/NONORTH_CELL_HOP_DISTANCE_20261119.json`

**Comando único, cuando se ejecute en WSL:**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_hop_distance.sh
```

**Estatus al escribir:** herramienta nueva **PREPARADA EN GITHUB, NO EJECUTADA en la malla real**. La distancia por saltos aún no tiene resultados; no inventarlos.

## Posterior a la distribución espacial/topológica

La prioridad de modelado es definir (y auditar por separado) condiciones térmicas físicas en `metal`, `mold`, `metalTop`, `moldOuterUnclassified` y contacto `mappedWall`; propiedades térmicas dependientes de T, calor latente, esquema de resolución para alta no ortogonalidad y estudio de sensibilidad de malla. No lanzar simulación de solidificación por el mero hecho de que `Mesh OK` esté aprobado.

**Estado validado**: `CASE_B_C3D05_HEX8_GEOMETRY_TOPOLOGY_PROVENANCE_AND_CONTACT_PASSED; HIGH_NONORTH_INTERNAL; CFD_NOT_RUN`.

[Informe de validación CAD/HEX8](C3D_05_HEX8_VALIDACION_INDEPENDIENTE_FINAL_20261119_ES.md) · [Norma de una sola instrucción](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
