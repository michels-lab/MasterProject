# Operación Granada — Caso B: acoplamiento térmico transitorio de dos sólidos con OpenFOAM Foundation 14

**20 de noviembre de 2026.** Caso B: **etapa 3/7 y 2/7 hitos técnicos = 29 %** (NO porcentaje de tesis ni calidad física). G1 CAD y G2 malla aceptados; G3 materialización física y G4 ejecución/energía en la malla real **sin cerrar**.

## Problema de fondo

El [bloque anterior](C3D05_F14_POSTPROCESS_SMOKE_Y_EVIDENCIA_UNICA_20261120_ES.md) pasó **10/10 diccionarios de producción** y postprocesamiento `foamPostProcess` verdadero en dos regiones **desacopladas** de una celda. El [extractor C++](C3D05_F14_WMAKE_REAL_20261120_ES.md) también compiló y arrancó con Foundation 14 real. No obstante, estos PASS no verificaban la construcción simultánea de termodinámica multirregión, los parches `mappedWall`, la condición `coupledTemperature`, ni la integración en tiempo con `foamMultiRun`: exactamente el tramo previo al cálculo térmico 3D en la WSL.

## Nueva verificación nativa de mayor nivel

Se agregó [`smoke_native_foundation14_solver.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/smoke_native_foundation14_solver.py) y su [workflow de CI](../../.github/workflows/c3d05-foundation14-two-solid-solver-smoke.yml):

- **OpenFOAM Foundation14 auténtico**, Ubuntu 24.04; no mock del solver.
- Dos regiones **sólidas separadas** `metal` y `mold`, una celda HEX8 de lado **0.01 m** cada una, geometría contigua a través de una pared común, con `blockMesh -region`. Los dos parches de interfaz son `mappedWall` recíprocos `metal_to_mold` ↔ `mold_to_metal`, declarados mediante `neighbourRegion` y `neighbourPatch`.
- **No se reemplazan parámetros**: los 10 archivos `controlDict`, `fvSchemes`, `fvSolution`, `physicalProperties` y temperaturas iniciales se generan con **el mismo** `prepare_t0.file_map()` que se usaría para la malla real, y `c14_numerical_reference.build()` remite a los archivos archivados de C14 con fuentes verificadas. La referencia C14 contiene `Cv≈Cp` y `k=Cp μ/Pr`, **no propiedades medidas de hierro/arena**.
- `foamMultiRun` tiene que construir ambas regiones, resolver el modelo `solid/solid` y avanzar del tiempo 0 al tiempo final del candidato **0.1 s** con sus opciones productivas. No basta con que los diccionarios sean legibles.
- La misma prueba comprueba **dos campos de temperatura finales** escritos y lee las historias `volAverage(T)` con el postprocesador original en las dos regiones. Requiere la serie completa, volumen `10^-6 m³` por región, campos iniciales iguales a la referencia C14 y valores finitos. Ningún resultado se confunde con las 270,788 celdas reales ni con curvas QuickCup.
- La prueba ocurre **solo en un directorio temporal** del runner. No puede leer ni modificar el STEP original, `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`, C14 archivado, los 12,636 contactos reales, ni `T0_INPUTS.json` con datos físicos pendientes.

## Criterio de aceptación

**Evidencia nativa de software:** PASS requiere tanto `foamMultiRun` real como campos de temperatura de ambas regiones, y `foamPostProcess` de ambos materiales. Si `mappedWall` o `coupledTemperature` fallan, se registra el error nativo y **NO se marca aprobado** hasta corregir su causa raíz.

**Evidencia científica:** aun cuando el smoke sea verde, **no constituye validación física**. Los dos cubos no replican la geometría, la severa no ortogonalidad (1,826 caras >70°) ni el comportamiento térmico/metalúrgico de la fundición QuickCup. Quedan pendientes la ejecución nativa **en la WSL del usuario**, verificación energética e interfacial real, sensibilidad de tamaño de paso y malla, propiedades JMatPro y validación experimental.

**Estado de esta entrega:** consultar [Actions](https://github.com/michels-lab/MasterProject/actions/workflows/c3d05-foundation14-two-solid-solver-smoke.yml) para verificar el resultado final; código y workflow se publicaron. No inferir PASS de que exista este documento.
