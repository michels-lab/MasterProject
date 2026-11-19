> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119 — AMPLIACIÓN QUE PREVALECE:** la regla de «un comando» es insuficiente si ese comando solo realiza un preflight. La entrega debe ser el **HITO INTEGRAL**, con pruebas de código internas, sin trabajo fragmentado para el investigador y con reporte obligatorio de **etapa y avance** para TODOS los casos. [Política](POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [Estado](PROJECT_STAGE_STATUS.json). Caso B: etapa 3/7, 2/7 = 29% de hitos técnicos; no CFD.

# Regla permanente del proyecto — instrucciones unificadas

**Fecha de incorporación:** 18-11-2026. **Origen:** instrucción explícita del investigador durante el diagnóstico C3D-05 del caso B 3D. **Ámbito:** todo `michels-lab/MasterProject` (casos A/B, mallado, solver, bitácoras, pruebas, auditorías, Linux WSL y Git).

## Regla obligatoria de interacción

**El investigador NO quiere instrucciones ni comandos separados en múltiples bloques o mensajes.** Siempre que sea posible, entregar **UN ÚNICO bloque de terminal para copiar y pegar**, que resuelva el objetivo completo de la etapa. Dentro del mismo bloque puede haber varias acciones encadenadas con comprobación de errores, pero el usuario solo debe copiar **una vez y ejecutar una vez**, no administrar una lista de fragmentos por separado.

### Convención

1. **Un bloque de código por etapa**, con una ruta de trabajo clara. Si hay varios pasos lógicos, **crear un script orquestador en el repositorio** y ofrecer un único comando de ejecución. Ejemplo: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/.../scripts/run_full_diagnostics.sh`.
2. **No dividir artificialmente** `git pull`, test, análisis y reportes en bloques sucesivos. El orquestador debe verificarlos en el orden correcto y detenerse de forma diagnóstica ante fallos relevantes.
3. El comando combinado debe ser **idempotente o seguro para reintentos**: rechazar sobrescritura de mallas, conservar salidas y logs anteriores, distinguir acciones de solo lectura de acciones que generan nueva evidencia.
4. **No mezclar objetivos:** para diagnóstico de una malla ya existente, **NO** incluir `blockMesh`, `snappyHexMesh`, `gmsh`, `gmshToFoam`, `checkMesh` adicional ni solver de forma innecesaria; leer los archivos nativos preservados. El diagnóstico no implica una nueva corrida.
5. Si una etapa **necesita confirmación o un insumo nuevo** (STEP, ubicación, instalación de paquete, etc.), usar un único bloque por objetivo. No inventar opciones o parámetros desconocidos.
6. **Responder con el resultado y la ruta** del reporte producido. No dar comandos decorativos redundantes ni presentarlos como tareas independientes.
7. Si excepcionalmente son indispensables dos ejecuciones separadas (p. ej., reinicio de WSL o instalación que requiera interacción), **explicar por qué** y minimizar los comandos al mínimo indispensable.
8. **Priorizar la ejecución real sobre planes y respuestas fragmentadas**, sin confundir `PREPARED`, `RUN`, `MESH_OK` y `CFD_VERIFIED`. Mantener evidencia reproducible y origen de valores.

## Implementación inmediata en C3D-05 (Caso B, 3D CAD STEP)

El primer mallado Gmsh de 525,706 tetraedros **falló únicamente el control de determinante**: 306 padre, 96 metal, 402 arena. Para no dar tres bloques de comandos, se implementó [`scripts/run_full_diagnostics.sh`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_full_diagnostics.sh), que integra pruebas, `diagnose_existing_mesh.py`, `audit_underdetermined_topology.py` y `measure_interface_area.py` en una llamada sobre la salida guardada.

**Invocación canónica — un único comando para pegar en WSL:**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_full_diagnostics.sh
```

El orquestador no ejecuta Gmsh ni CFD; respeta el JSON de área si ya existe y no borra logs. Si una puerta de área falla, conserva evidencia y lo comunica como advertencia/rechazo, no aprobación. No se modifican los STEP originales, C3D-03 ni C3D-04.

**Para todo paso nuevo de cualquier rama del proyecto:** cuando la interacción requiera comandos, el asistente primero debe crear/adaptar el orquestador correspondiente y luego presentar **un solo bloque ejecutable** al investigador.
