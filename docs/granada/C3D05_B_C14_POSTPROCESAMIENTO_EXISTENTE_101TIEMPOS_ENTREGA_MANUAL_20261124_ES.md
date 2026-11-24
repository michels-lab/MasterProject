# Caso B C3D-05 — posprocesamiento C14 recuperable de los 101 estados existentes

**Prioridad acordada:** primero terminar los productos de posprocesamiento disponibles sobre la simulación 3D **ya completada y abierta en ParaView**, sin repetir CFD y sin añadir tandas de pruebas automáticas. La nueva corrida de 10 segundos que permitiría sondas en cada paso de 0.001 s queda **en pausa**.

## Qué se implementó realmente

Se publicó un nuevo ejecutor en `main`:

- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/POSTPROCESAR_CASO_B_C14_EXISTENTE.sh`
- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/POSTPROCESAR_CASO_B_C14_EXISTENTE.py`

Usa la **corrida original ya finalizada** `~/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01` de hierro fluido + arena sólida con 101 estados (0, 0.1, …, 10 s). Lee y conserva los diccionarios y objetos de función del **C14 original** como procedencia. Crea una copia física aislada de malla, `0/`, los otros **100 directorios de tiempos guardados**, `constant/` y `system/`. **No usa enlaces de escritura al CFD original.**

Destino separado:

```text
~/OpenFOAM/C3D05_B_C14_POSTPROCESAMIENTO_C14_101_TIEMPOS_01/
    C3D05_B_C14_POSTPROCESADO_101_TIEMPOS.foam
    C3D05_B_C14_C14_STYLE_POSTPROCESS_REPORT.json
    postProcessing/...
    logs/
    0/ ... 10/
    system/C14_B_OFFLINE/...
    log.C14B.*
```

El método llama `foamPostProcess` de **OpenFOAM Foundation 14** sobre esa copia para recuperar, desde datos realmente guardados, las siguientes familias inspiradas en los diccionarios del C14:

1. Campo de vorticidad, tipología del flujo, gradiente de temperatura, magnitud del gradiente y fracción líquida media.
2. Sondas de temperatura, velocidad, `p_rgh` y `phaseChangeSource:alpha1` sobre los tiempos archivados.
3. Perfiles horizontales y verticales usando las estaciones y `nPoints=80` originales C14; sin inventar un segmento interior si la geometría 3D curva hace que una sección quede fuera del metal. La pertenencia real se constata al abrir la salida.
4. Diagnóstico de gradientes de densidad, Courant, flujo `phi` y perfiles/sondas de `rho` solo donde realmente se hayan guardado `rho` y `phi`. El lector NO inventa su valor en tiempos ausentes.
5. Campos y sumas de la superficie superior `metalTop` a través de los objetos originales del C14, y `foamLog` del log original.
6. Intenta de modo explícito y separado los objetos originales de energía y momentum; si la fuente no incluye `h`, el término interno del modelo de solidificación o la estructura necesaria, registra la falla de la ejecución nativa. No finge que todos esos términos están disponibles.

Cada comando tiene un log propio, el estado real `COMPLETE`, `NATIVE_OPENFOAM_ERROR` o `UNAVAILABLE`, y un manifiesto final. El archivo `.foam` permite revisar los campos derivados **en ParaView** y el `postProcessing/` almacena las curvas/perfiles calculados cuando OpenFOAM tenga información suficiente. No hay etapas que llamen `foamMultiRun`, `blockMesh`, `splitMeshRegions`, `wmake` o `unittest`.

## Única instrucción de uso (desde la terminal del proyecto)

```bash
git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/POSTPROCESAR_CASO_B_C14_EXISTENTE.sh
```

Al terminar se intentará abrir ParaView sobre la **copia de posprocesamiento**, no sobre la corrida ya validada anteriormente. Para calcular sin abrir ventana, pasar `--no-open`.

Si una sesión se interrumpe **después de crear la copia**, no copiar ni ejecutar el solver otra vez; la opción `--resume` intenta continuar únicamente las etapas que no tengan archivo `.DONE`. Un log parcial previo debe examinarse y preservarse antes de reintentarlo (el script no sobrescribe logs fallidos).

### Límites metodológicos importantes

**El paso de cálculo real fue `deltaT=0.001 s`, pero los archivos disponibles para posprocesar son solo cada `0.1 s`.** Las curvas de sondas y perfiles ex post tienen esa resolución. No equivalen a los 10,001 puntos que `temperatureProbe` habría registrado en tiempo real con `writeInterval=1` ni recuperan la derivada `ddt` calculada dentro de cada paso. Esa información requiere nueva corrida completa.

Los campos metal `h/he` y molde `e/he` no se archivaron. Por ello, ni valores reconstruidos de energía total ni código `coded` de `solidificationMeltingMomentumDiagnostics` son automáticamente idénticos al cálculo en tiempo real. Las familias energía/momentum se consideran pendientes hasta mostrar salida nativa auténtica.

Las posiciones de perfiles y sondas del C14 2D se mantienen métricamente para conservar comparabilidad. Aunque haya puntos dentro del volumen que delimita la malla 3D, una línea puede atravesar un vacío en una geometría cóncava: revisar los `*.xy` y conteos, no afirmar 80 puntos si no se produjeron.

Los 101 estados CFD originales del Caso B no se alteran; ni siquiera el directorio de ParaView que el investigador ya abrió. Los resultados existentes de flujo térmico nativo y ΔE de referencia permanecen disponibles por separado. **La comparación `−11.436 J` no representa conservación de energía validada.**

## Estado de entrega

**Código integrado en GitHub; su ejecución por OpenFOAM en la WSL todavía no fue observada.** No se añadieron pruebas automatizadas. El siguiente acto práctico es correr la orden anterior y revisar directamente las salidas `.foam`, `postProcessing/` y el JSON; cualquier falla real se corrige sobre el comando nativo que la produjo.

La segunda corrida de 10 s con functionObjects en cada paso se mantiene **en pausa**. Estado científico Caso B: etapa 3/7, 2/7 hitos aceptados; no equivale a validación experimental QuickCup/JMatPro.
