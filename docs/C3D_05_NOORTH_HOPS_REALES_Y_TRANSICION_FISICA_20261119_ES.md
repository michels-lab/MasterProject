# Caso B C3D-05 — distancia por saltos de caras no ortogonales y transición a diseño térmico 3D

**Registro:** 19 de noviembre de 2026. **Fuente primaria:** salida nativa real de WSL compartida por el investigador tras ejecutar `run_nonorth_hop_distance.sh`. El directorio auditado es `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`. **No se modificó la malla ni se ejecutó solver CFD/transferencia de calor.**

## 1. Estado experimental confirmado

La revisión independiente del mismo caso volvió a reportar `OVERALL_GEOMETRY_TOPOLOGY: PASSED` con la procedencia STEP SHA-256 auténtica, HEX8 y QUAD4, 270,788 celdas (92,200 metal; 178,588 arena), `Mesh OK` para padre/metal/arena, y patches de contacto recíproco `mappedWall`. El análisis `nonOrthoFaces` previo demostró 1,826 caras severamente no ortogonales (>70°), todas **internas**: 595 metal + 1,231 arena, sin incidencia directa sobre celdas de interfaz ni exterior.

La corrida actual validó la conectividad de los conjuntos nativos y ejecutó un análisis BFS sobre `owner/neighbour`, comparando rutas de celdas a `metal_to_mold / mold_to_metal` y a `metalTop / moldOuterUnclassified`. Las pruebas estáticas y las 2+4 unitarias pasaron. Resultado de la ejecución: **`PASS: preserved nonOrthoFaces counts and cell-hop distances, no remesh or solver.`**

**Informe primario local recién generado:** `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02/NONORTH_CELL_HOP_DISTANCE_20261119.json`. Este archivo **no se ha copiado al repo GitHub**, por ser evidencia local del usuario. Todos los ensayos antiguos se preservaron.

## 2. Resultados medidos: distancia TOPOLÓGICA de cada cara severa

| Magnitud | Metal (595 caras) | Arena (1,231 caras) |
|---|---:|---:|
| Saltos mínimos al contacto metal/arena | **1** | **1** |
| Mediana de saltos al contacto | **5** | **9** |
| P90 de saltos al contacto | **15** | **22** |
| Máximo de saltos al contacto | **23** | **43** |
| Caras a **1** salto del contacto | **226** | **235** |
| Caras a **2** saltos del contacto | **30** | **43** |
| Saltos mínimos a pared exterior | **1** | **1** |
| Mediana de saltos a pared exterior | **34** | **5** |
| P90 de saltos a pared exterior | **56** | **12** |
| Máximo de saltos a pared exterior | **62** | **20** |
| Caras a **1** salto de la pared exterior | **8** | **398** |
| Caras a **2** saltos de la pared exterior | **0** | **62** |
| Caras a ≤2 saltos de **cualquier** pared | **260** | **732** |

Derivaciones aritméticas **calculadas del reporte**, no resultados adicionales de OpenFOAM:
- Metal: 226/595 = **37.98%** de las caras severas a solo 1 salto del contacto; 260/595 = **43.70%** a ≤2 saltos de alguna pared.
- Arena: 235/1231 = **19.09%** a solo 1 salto del contacto; 398/1231 = **32.33%** a 1 salto del exterior; 732/1231 = **59.46%** a ≤2 saltos de alguna pared.
- Total: 992/1826 = **54.33%** a ≤2 saltos de alguna pared; 461/1826 = **25.25%** a 1 salto del contacto.

**Interpretación:** la ausencia de incidencia directa **no implica lejanía a una pared**. Una fracción importante de las caras problemáticas aparece una sola capa de conectividad más adentro: especialmente el metal próximo al contacto y la arena próxima a la pared exterior. Por ello, no es correcto declarar que la no ortogonalidad «no afecta a la interfaz» ni que el problema es puramente lejano al frente térmico. La evidencia no confirma un error de flujo térmico todavía, pero justifica prestar atención a gradientes, esquema de difusión y correcciones no ortogonales antes de resolver.

**Advertencia de escala:** un salto equivale a cruzar una cara interna en el grafo de celdas, **no** una distancia fija en mm. Los percentiles son de distancias por saltos, **no** de intensidad del defecto (ángulo por cara). No se han medido gradientes T, estabilidad, distribución cartesiana XYZ ni error energético con este procedimiento.

## 3. Decisión de proceso: cerrar diagnóstico básico y empezar el modelo térmico

El Caso B **cumplió el objetivo de geometría/topología/interfaz** a nivel OpenFOAM 14, con riesgo cuantificado de no ortogonalidad severa. **No repetir un mallado grueso por inercia.** Guardar `_02` como referencia inmutable y cambiar a los siguientes entregables técnicos, que deben construirse en un **nuevo caso de cálculo**, sin sobrescribir la evidencia original:

1. **Etapa T0 — conducción transitoria bicuerpo de comprobación (SIN solidificación):** definir una prueba numérica de conservación y continuidad de flujo entre `metal` y `mold` sobre la misma geometría. Debe distinguirse explícitamente de la tesis de solidificación: la región metal en T0 sería *material de conductividad térmica simplificada*, **no un hierro líquido con convección ni cambio de fase resuelto**. La etapa debe tener IC/BC y coeficientes térmicos con procedencia y unidades, perfiles T y balance de energía. No usar constantes genéricas como si fueran mediciones.
2. **Etapa T1 — propiedades y fase de cambio:** `rho(T), cp(T), k(T)` para el hierro y propiedades de arena con intervalos y fuentes, composición CE/S/Mn por corrida, temperaturas liquidus/solidus y entalpía latente. Determinar explícitamente el tratamiento de la austenita proeutéctica y el término de solidificación, sin inventar recalescencia. Usar temperaturas y condiciones reales del QuickCup cuando estén disponibles.
3. **Etapa T2 — acoplamiento y no ortogonalidad:** estudiar sensibilidad a `snGrad` y correcciones no ortogonales/solución lineal, paso de tiempo, conservación integrada de energía y, después, sensibilidad a resolución. Verificar que cualquier variante numérica realmente exista en la instalación Foundation 14. No presentar `maxCo` configurado como Courant medido.
4. **Etapa T3 — flujo en metal (si la hipótesis de tesis lo requiere):** añadir convección, momento, porosidad de zona pastosa y efectos de fase **solo en un solver/módulo cuya compatibilidad v14 se haya verificado con un caso pequeño**; no suponer que poner `fvModels` en el solver puro de sólido activa enthalpy-porosity.

## 4. Elección de infraestructura OpenFOAM — VERIFICADA DOCUMENTALMENTE, NO EN WSL

Para **OpenFOAM Foundation 14** la herramienta multirregión estándar es **`foamMultiRun`**, con módulos por región en `system/controlDict` mediante `regionSolvers`. Fuente oficial: https://cpp.openfoam.org/v14/foamMultiRun_8C.html y guía https://doc.cfd.direct/openfoam/user-guide-v14/introduction . La versión v14 también ofrece `coupledTemperature` y capacidades de resistencia térmica en interfaces; fuente oficial: https://doc.cfd.direct/openfoam/user-guide-v14/thermal-boundary-conditions y https://openfoam.org/release/14/ .

**NO se han confirmado aún los nombres exactos de módulos disponibles y dictionaries operativos en el WSL del investigador.** La compatibilidad de `coupledTemperature` (ambos lados), la gestión de contacto (ideal, resistencia finita, gap dependiente de tiempo) y la conducción transitoria no deben inferirse únicamente del `type mappedWall` geométrico. Verificar con tutorial oficial del Foundation 14 y configuración específica para cada región antes de un run.

Para proteger la reproducibilidad:
- `constant/metal` y `constant/mold`: materiales y propiedades termofísicas, con referencias; ningún valor físico temporal de relleno.
- `0/metal/T`, `0/mold/T`: IC y BC para `metalTop`, `moldOuterUnclassified`, ambos lados de contacto. Elegir explícitamente el ambiente y mecanismo de transferencia (convección/radiación/aislamiento) según hipótesis y datos, no defaults.
- `system`: módulos, esquemas (especialmente difusión con alta no ortogonalidad), solvers y controles de solución/convergencia, tiempo y salidas. **No copiar a ciegas** diccionarios de la variante OpenCFD (`v23xx`) como si fueran Foundation 14.
- Medir al ejecutar: temperatura extrema, acoplamiento de flujo de calor en ambas caras, residual/convergencia, balance energético y costo. **Hasta hoy ninguno está medido**.

## 5. Próximo entregable propuesto

Crear una **configuración térmica T0 separada y verificable en su propia carpeta**, con campos/BC/propiedades documentados y verificador de completitud/compatibilidad Foundation 14, **sin iniciar solver de CFD automáticamente**. El usuario exige **una sola instrucción ejecutable por etapa**, preparada en GitHub y verificada antes de anunciar resultados. Primero resolver T0 y solo después incorporar entalpía/solidificación y flujo.

**ESTADO CIENTÍFICO ACTUAL:** `C3D05_HEX8_NATIVE_GEOMETRY_TOPOLOGY_CONTACT_AND_SOURCE_ACCEPTED`; `SEVERE_NONORTH_1826_INTERNAL_AND_WALL_PROXIMITY_CHARACTERIZED`; `THERMAL_MODEL_NOT_CONFIGURED`; `CFD_NOT_RUN`; `GRID_INDEPENDENCE_NOT_DEMONSTRATED`.

Referencias internas: [validación geométrica final](C3D_05_HEX8_VALIDACION_INDEPENDIENTE_FINAL_20261119_ES.md), [auditoría cara interna](C3D_05_NOORTH_CARAS_INTERNAS_20261119_ES.md), [regla de un comando](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
