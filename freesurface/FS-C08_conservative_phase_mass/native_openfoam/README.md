# FS-C08: puente de campos nativos Foundation 14 — primera integración `wmake`

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
  -region fluid -time '0.2,0.4,1'

# Variante 2: comprobar la interoperabilidad con núcleo C++17 con parámetros
# puramente SINTÉTICOS: no representan rho_l/rho_s de hierro real.
fsC08NativeInventory \
  -case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4 \
  -region fluid -latestTime \
  -rhoLiquid 7000 -rhoSolid 7300 -provenance SYNTHETIC_NOT_JMATPRO
```

**Importante:** el ejecutable exige `-latestTime` o `-time` explícito para no iterar por los más de diez mil directorios de tiempo creados por monitores. No hay `runTime.write()`, `mesh.write()` ni `field.write()`, no se invoca `foamMultiRun`. Si `fvMesh` encuentra un tiempo sin `alpha.metal.solid`, el programa debe fallar y no reemplazarlo con ceros.

El inventario OpenFOAM nativo tiene que reproducir, por ejemplo:

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
