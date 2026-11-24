# Caso B C3D-05 — ejecución C14 original: sondas reales cada 0.001 s

**24 de noviembre de 2026.** El usuario abrió y visualizó correctamente el Caso B 3D anterior y solicita **ejecutar el posprocesamiento con exactamente la configuración C14 original**, sin nuevas tandas de pruebas.

## Diferencia esencial: posprocesamiento ex post vs. en tiempo de solver

La primera simulación del Caso B, ya realizada, calculó de 0 a 10 s con `deltaT 0.001`, `writeControl timeStep`, `writeInterval 100`: conserva **101 estados** cada 0.1 s. No se pueden regenerar retrospectivamente los 10,000 instantes intermedios de sondas mediante ese conjunto archivado. Para capturar el mismo `temperatureProbe` del C14 (`executeInterval=1`, `writeInterval=1`, cada paso), es **necesaria una nueva ejecución del solver**.

## Entrega de nueva ejecución realmente independiente

Archivo publicado en el repositorio:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/EJECUTAR_CASO_B_C14_COMPLETO.sh`

**Comando único en WSL desde `~/OpenFOAM/MasterProject`:**

```bash
git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/EJECUTAR_CASO_B_C14_COMPLETO.sh
```

Crea una carpeta **nueva**:

`~/OpenFOAM/C3D05_B_C14_FUNCIONES_C14_COMPLETAS_10S_01`

Solamente copia físicamente `0/`, `constant/` y `system/` del **CFD original 3D-B**. Las 101 instantáneas originales y toda su visualización permanecen intactas; no hay enlaces simbólicos de escritura hacia el CFD original. Los diccionarios del C14 original se copian sin cambiar sus bytes:

- `system/controlDict` (igual al C14 original y al Caso B): `application foamMultiRun;`, `startTime 0;`, `endTime 10;`, `deltaT 0.001;`, `writeControl timeStep;`, `writeInterval 100;`, `adjustTimeStep no;`, `purgeWrite 0;`.
- `system/functions` con `temperatureProbe` (en cada paso), `topFlow`, y los `#include` originales de `researchDiagnostics` y `lineProfiles`.
- `system/researchDiagnostics`: gradientes, vorticidad, topología, Courant, flujos de energía, tasas térmicas y de fase, indicadores de energía/solidificación del modelo.
- `system/lineProfiles`: perfiles horizontales y verticales, con **coordenadas originales del C14 2D sin ajustar**.
- `system/momentumPostProcessing` y el original `analysis_tools/topSurfaceFlowPostProcessing`, ejecutados con `foamPostProcess` al terminar `foamMultiRun`.
- `foamLog` como en el `Allrun` original, para continuidad, residuales y Courant.

**No se lanza `blockMesh` ni `splitMeshRegions`**: son pasos del `Allrun` 2D que NO se deben repetir sobre la malla 3D aceptada de metal (92,200 HEX8) y arena (178,588 HEX8).

OpenFOAM Foundation14 lee los functionObjects del archivo independiente `system/functions` de manera nativa. No es necesario cambiar el `controlDict`.

**Precaución de geometría:** conservar exactamente las coordenadas 2D C14 de las sondas/perfiles podría ubicar algún punto fuera del metal 3D del Caso B. No se ajustan silenciosamente para cumplir el pedido de «tal cual». Revisar log y datos de `temperatureProbe` y `horizontalProfiles`/ `verticalProfiles` después de ejecutar.

La ejecución es real: el lanzador usa `foamMultiRun` Foundation14, muestra el log del solver en pantalla y lo guarda en el directorio nuevo. Ninguna herramienta de este chat puede ejecutar directamente `foamMultiRun` en la laptop del usuario, así que **el nuevo cálculo no está confirmado todavía en WSL**. No se han añadido ni lanzado pruebas automatizadas en este bloque.

### Si el solver terminó pero falló una etapa de posprocesamiento

No repetir los 10 segundos. Ejecutar, dentro de `~/OpenFOAM/MasterProject`:

```bash
bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/EJECUTAR_CASO_B_C14_COMPLETO.sh --post-only
```

Conserva logs previos de la etapa fallida y reintenta solamente `foamPostProcess` o `foamLog`. Cada etapa correcta recibe archivo `.DONE`.

### Abrir la nueva solución

Tras terminar, el lanzador imprime:

```bash
paraview --data="$HOME/OpenFOAM/C3D05_B_C14_FUNCIONES_C14_COMPLETAS_10S_01/C3D05_B_C14_FUNCIONES_COMPLETAS.foam"
```

Sondas: `postProcessing/temperatureProbe/`. Perfiles: `postProcessing/horizontalProfiles/` y `postProcessing/verticalProfiles/`. Los demás diagnósticos se crean en `postProcessing/` por los functionObjects originales.

**Estado real observado**: Caso B original 10 s y ParaView ya abiertos; el segundo solver con sondas C14 **pendiente de ejecución WSL**. No se cierra el balance de energía, ni sensibilidad de malla/dt ni QuickCup/JMatPro o contracción por el simple hecho de producir datos de functionObjects. Hitos científicos conservados en 2/7.
