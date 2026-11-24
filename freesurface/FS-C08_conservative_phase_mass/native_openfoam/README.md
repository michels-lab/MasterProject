# FS-C08: puente de campos nativos Foundation 14 — primera integración `wmake`


## Ejecución recomendada: un solo comando de diagnóstico

El worktree `FS_C08_WORKTREE` **ya fue creado y comprobado por el investigador en WSL**, por lo que **NO vuelvas a ejecutar `git worktree add`**. Actualiza el mismo árbol:

```bash
cd ~/OpenFOAM/FS_C08_WORKTREE && \
git fetch origin research/fs-c08-conservative-phase-mass-20261123 && \
git switch --detach FETCH_HEAD && \
python3 -B analysis_tools/run_fs_c08_native_bridge.py \
  --case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
```

Este script [`run_fs_c08_native_bridge.py`](../../../analysis_tools/run_fs_c08_native_bridge.py) verifica que `WM_PROJECT_VERSION=14` y `FOAM_USER_APPBIN` estén configurados, compila con `wmake`, ejecuta la herramienta de **solo lectura** en los tiempos 0.2/0.4/1 s, aplica el comparador de evidencia nativa y comprueba SHA-256 antes y después de **seis archivos originales**. Toda la evidencia queda en una carpeta *nueva* de `~/OpenFOAM/FS_C08_DIAGNOSTICS/`; el caso original permanece fuera. Si falla compilación, ejecución, paridad o integridad, conserva el motivo en `FS_C08_NATIVE_BRIDGE_REPORT.json` y los logs `wmake.log` y `fsC08NativeInventory.log`. **No invoca `foamMultiRun`.**

La utilidad nativa y el workflow aún deben **compilarse/ejecutarse por primera vez en WSL**; solo está demostrada previamente la parte C++17 independiente con 18 pruebas Python y binario C++ sin `wmake`.



Es una **utilidad OpenFOAM real**, que carga `fvMesh` de la región `fluid`, campos `alpha.metal` y `alpha.metal.solid` de los tiempos pedidos y el volumen exacto de cada celda **sin modificar** ni los campos ni el caso. A partir de esos campos calcula las mismas integrales RAW del análisis FS-C07, errores locales `alpha_s>alpha_m+1e-8`, y si se solicitan explícitamente **densidades constantes con procedencia**, convierte las celdas de núcleo estrictamente válidas (`alpha_m≥0.5`, `0≤alpha_s≤alpha_m≤1`) a masas y ejecuta el núcleo independiente `ConservativePhaseExchange.H` con **Γ=0 y flujo=0**. Se trata de **interoperabilidad de API/malla**, no una nueva simulación de física.

**Estado antes de prueba en tu WSL:** código y `Make/files`+`Make/options` incorporados al repositorio, **no compilados todavía con OpenFOAM 14** (el contenedor de desarrollo no tiene `wmake`). Si falla, se registra el diagnóstico y se corrige sobre esta misma rama. El compilador C++17 independiente sí pasó en la laptop, pero no demuestra compatibilidad con `fvMesh`.

## Compilar y probar con el caso FS-C07 original de solo lectura

El worktree FS-C08 ya existe; actualiza **ese** árbol, no FS-C07:

```bash
cd ~/OpenFOAM/FS_C08_WORKTREE
git fetch origin research/fs-c08-conservative-phase-mass-20261123
git switch --detach FETCH_HEAD

# Cargar el entorno Foundation14 en una consola donde funcione foamMultiRun.
# Si ya está cargado, no hace falta volver a hacer source.
command -v wmake
command -v foamMultiRun

cd freesurface/FS-C08_conservative_phase_mass/native_openfoam
wmake

# Variante 1: sin densidades, puro inventario VOF/solid (NO usa Γ ni masa).
fsC08NativeInventory \
  -case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4 \
  -region fluid -time '0.2,0.4,1' \
  | tee /tmp/FS_C08_NATIVE_INVENTORY.log

# Comparar DIRECTAMENTE con los conteos e integrales originales 20/20.
# Ejecutar desde la raíz del worktree FS-C08:
cd ~/OpenFOAM/FS_C08_WORKTREE
python3 -B analysis_tools/verify_fs_c08_openfoam_inventory.py \
  --log /tmp/FS_C08_NATIVE_INVENTORY.log --times 0.2 0.4 1.0

# Variante 2: comprobar la interoperabilidad con núcleo C++17 con parámetros
# puramente SINTÉTICOS: no representan rho_l/rho_s de hierro real.
fsC08NativeInventory \
  -case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4 \
  -region fluid -latestTime \
  -rhoLiquid 7000 -rhoSolid 7300 -provenance SYNTHETIC_NOT_JMATPRO
```

**Importante:** el ejecutable exige `-latestTime` o `-time` explícito para no iterar por los más de diez mil directorios de tiempo creados por monitores. No hay `runTime.write()`, `mesh.write()` ni `field.write()`, no se invoca `foamMultiRun`. Si `fvMesh` encuentra un tiempo sin `alpha.metal.solid`, el programa debe fallar y no reemplazarlo con ceros.

El inventario OpenFOAM nativo tiene que reproducir, por ejemplo, los siguientes valores; el verificador independiente compara los conteos y excesos con el JSON real de FS-C07:

| t [s] | `V_metal_raw` [m³] | `V_solid_raw` [m³] | `V_exceso` [m³] | celdas fuera de 1e-8 |
|---|---:|---:|---:|---:|
| 0.20 | 4.801190828e-5 aprox. | 3.376485e-8 aprox. | 2.9743834396e-12 | 187 |
| 0.40 | 4.801179796e-5 aprox. | 4.4459296e-7 aprox. | 6.12728937157e-12 | 598 |
| 1.00 | 4.8011038266835194e-5 | 2.403591085462431e-6 | 1.7680724185913767e-12 | 378 |

Los valores 0.20/0.40 de las dos primeras columnas son **aproximaciones de la transcripción del postproceso previo**; la comparación deberá aceptar tolerancia, no tratarlos como exactos de origen.

## Qué NO hace

- No resuelve continuidad líquido/sólido/acoplada del gas; solo lee los campos históricos.
- No actualiza VOF, superficie libre, presión, energía, ni el término `Γ`; la llamada al kernel se hace **con Γ=0 y flujos=0**.
- No corrige las 7,692 incidencias de asignación de fase de FS-C07 ni recorta fracciones.
- No usa JMatPro, no implementa contracción, alimentación o porosidad real.
- No cuenta una variación de `V_metal` como contracción por cambio de densidad.

Este puente establece la primera barrera técnica **Foundation14 wmake → fvMesh/fields → kernel C++17**, necesaria antes de escribir un módulo conservativo `compressibleVoF` auténtico. La siguiente barrera será el transporte de masa por fase con `±Γ` y fuentes en las ecuaciones de presión y energía sobre un caso nuevo aislado.

## Aceptación automatizada sin corrida de CFD

[`verify_fs_c08_openfoam_inventory.py`](../../../analysis_tools/verify_fs_c08_openfoam_inventory.py) compara **independientemente** el log del ejecutable `wmake` con [20 estados nativos registrados](../../FS-C07_thermal_transition/evidence/FS_C07_PHASE_ALLOCATION_20_NATIVE_STATES_20261123.json); rechaza duplicados, faltantes, error en conteos/volúmenes, final metal/sólido y ausencia de un pie de log de solo lectura. Sus [seis tests sintéticos](../../../analysis_tools/test_verify_fs_c08_openfoam_inventory.py) están añadidos al CI, sin afirmar que la utilidad `wmake` haya compilado en WSL.

La salida con estado `PASS` **solo significa** que una utilidad OpenFOAM14 leyó sin alteración los campos y las integrales de FS-C07. **No** significa que exista `Γ` nativa distinta de cero, contracción física, cierre de energía ni movimiento de metal líquido.
