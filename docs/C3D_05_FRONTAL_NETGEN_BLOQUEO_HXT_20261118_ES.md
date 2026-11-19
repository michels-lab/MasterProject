# Caso B — C3D-05: ensayo Frontal bloqueado por Netgen y alternativa HXT (18-11-2026)

**Evidencia:** salida de terminal Ubuntu WSL compartida por el investigador. **Estado real:** Gmsh Frontal no produjo malla volumétrica; el intento no evaluó `checkMesh`, parches ni transferencia térmica. **No hay CFD.**

## Corrida Frontal realmente ejecutada

Invocación desde `MasterProject/main` (sin omitir el `git pull`):

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_frontal_pilot.sh
```

Sincronización confirmada al commit `2fbe20aff`; pruebas estáticas y unitarias **correctas** (4 + 2 tests de los diagnósticos). Gmsh importó el STEP y trianguló las superficies CAD: mensajes `Meshing surface ...` y `Done meshing 2D`. Justo al iniciar `Meshing 3D`, abortó:

```text
Info    : Meshing 3D...
Error   : Frontal algorithm requires Netgen
Exception: Frontal algorithm requires Netgen
REJECTED / stage=gmsh3d / See log.gmsh3d / NO_CFD
Preserved: /home/michel/OpenFOAM/C3D05_STEP_GMSH_FRONTAL_01
Candidate was NOT accepted (runner exit 5).
```

**Clasificación científica correcta: `BLOCKED_GMSH_FRONTAL_REQUIRES_NETGEN`, no `REJECTED_CHECKMESH`.** No hay malla 3D Frontal, celdas volumétricas Frontal, métricas de determinante ni mejoras demostradas. El texto `REJECTED` en el ejecutor identifica que el pipeline abortó, no que `checkMesh` haya rechazado celdas Frontal.

**La instalación local de Gmsh con bindings Python funciona** para el método Delaunay previo, pero ese binario **no tiene el soporte Netgen requerido por su algoritmo Frontal 3D**. Instalar simplemente otro paquete de Python o repetir el mismo `run_frontal_pilot.sh` no prueba que habilite un Gmsh compilado con ese soporte. No pedirle al investigador reinstalaciones innecesarias sin diagnóstico de compilación.

**Preservación verificada por diseño:**
- `~/OpenFOAM/C3D05_STEP_GMSH_PILOT_01`: malla control Delaunay/STEP, 525,706 tetraedros, `checkMesh` de padre/regiones rechazado únicamente por determinante menor de 0.001 (306 padre, 96 metal y 402 arena), contacto 16,218 caras/lado y áreas idénticas 6348.10669 mm²; no se alteró.
- `~/OpenFOAM/C3D05_STEP_GMSH_FRONTAL_01`: **solo los archivos/evidencias parciales de una importación+mallado superficial Frontal**, con `log.gmsh3d` de error, preservados. **No `checkMesh` Frontal.**

## Candidato HXT, alternativa independiente de Netgen (a probar)

El manual de Gmsh identifica `Mesh.Algorithm3D=10` como **HXT**, implementación paralela de un método Delaunay, frente a `Mesh.Algorithm3D=4` (**Frontal**, requiere Netgen en el Gmsh instalado). [Manual oficial de Gmsh](https://gmsh.info/doc/texinfo/gmsh.html).

La ruta HXT es un **experimento falsable**, no una garantía de corregir el determinante: todos los `underdeterminedCells` originales están en tetraedros de las **aristas de frontera** y tienen exactamente 2 caras internas + 2 caras de frontera. Un método HXT también produce tetraedros y podría reproducir ese patrón. Si vuelve a fallar por el mismo fenómeno, **detener la exploración de algoritmos volumétricos tetraédricos** y plantear mallado con **capas prismáticas/hexaédricas de frontera o hibridación topológica** con verificación `checkMesh`; no bajar el umbral ni falsear `Mesh OK`.

**Control de una variable:** iguales STEP (SHA256 verificados), mismo `occ.fragment`, `Mesh.MeshSizeMax=1.8 mm`, `Mesh.MeshSizeMin=0.9 mm`, mismo mallado superficial por configuración de Gmsh, MSH2 ASCII convertido a metros una sola vez, mismos patches `mappedWall` y criterios de aceptación; variar solo `Mesh.Algorithm3D` de 1 a 10.

**Preflight seguro**: [`preflight_hxt.py`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/preflight_hxt.py) verifica en memoria que los bindings de Gmsh puedan generar elementos 3D usando HXT sobre un pequeño cubo OCC **sin cargar el QuickCup, generar archivos o ejecutar CFD**. Si falla, el orquestador aborta antes de crear salida candidata.

**Un solo comando** conforme al protocolo del investigador: [`run_hxt_pilot.sh`](../cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hxt_pilot.sh) ejecuta verificaciones estáticas/pytest-like unittest, preflight, producción en **carpeta nueva** `~/OpenFOAM/C3D05_STEP_GMSH_HXT_01`, calidad nativa padre/metal/arena, postmortem y área de contacto. Evita sobrescribir original y Frontal. Si HXT no pasa las pruebas nativas, registra los logs y **NO ejecuta CFD**.

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hxt_pilot.sh
```

**Estado al escribir este documento:** código HXT y preflight **preparados en GitHub, NO ejecutados en WSL**. No reportar celdas, área ni calidad HXT hasta recibir salida real. La alternativa del Caso A `C3D-04` se desarrolla en otro chat y no se modifica aquí.

[Informe del mallado original](C3D_05_AREA_ARISTAS_Y_ENSAYO_FRONTAL_20261118_ES.md) · [Regla de instrucciones unificadas](REGLA_INSTRUCCIONES_UNIFICADAS_ES.md).
