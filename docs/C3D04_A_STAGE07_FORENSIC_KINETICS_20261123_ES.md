# Caso A 3D C3D04 · Etapa 7/10: recuperación inmutable y cinética térmica de C14

**23 de noviembre de 2026.** Estado operativo: etapa **7/10 EN PROGRESO**, **6/10 = 60 % de hitos**. La corrida 3D original V4/T02 C14 metal fluido + arena sólida 0–10 s en WSL ya existe, con 10 000 pasos y 101 estados separados 0.1 s. Este cambio **no ejecuta CFD ni acredita conservación energética, independencia de malla o validación QuickCup**.

## Evidencia que motivó el cambio

El investigador confirmó mediante la ejecución real del instalador A/B/FS que ya existen simultáneamente:
- `~/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01`: fuente auténtica C14 3D con 101 estados.
- `~/OpenFOAM/C3D04_A_C14_3D_VOLUMETRIC_POSTPROCESS_01`: carpeta del analizador volumétrico 101 estados.
- `~/OpenFOAM/C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01`: copia de postprocesamiento nativo, posiblemente incompleta.

La verificación sólo certificó **existencia de directorios**; no se ha visto todavía desde GitHub el interior de esas dos últimas carpetas. El ejecutor antiguo `run_c14_3d_complete_postprocess.py` requiere tanto `--volume-out` como `--copy` inexistentes y se bloquea con las rutas por defecto. No es correcto pedir borrarlas, volver a copiar el CFD o repetir los 10 s.

## Nuevo hito de análisis sin escritura en CFD ni recuperación especulativa

`cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/recover_existing_c14_3d_stage07.py`

Lee y comprueba **antes de publicar**:
1. `system/controlDict` del CFD real coincide byte por byte con C14 original.
2. `log.foamMultiRun` sigue siendo el SHA que certificó el análisis volumétrico.
3. El informe volumétrico procede del **mismo caso**, es de postprocesamiento y no de CFD nuevo; existen el CSV original y sus **101 estados 0..10 s en saltos de 0.1 s**, todos finitos y coherentes con masas y volúmenes.
4. `metal_alpha1_volMean + metal_solid_fraction_volMean = 1` y porcentaje de volumen bajo solidus no mayor que el bajo liquidus.
5. Para la copia nativa, sólo **lee** presencia/identidad SHA del log y controlDict, log de cada función nativa (sin inferir éxito sólo por ver un log) y, **si existe**, el informe final que registra códigos de salida, objetos ausentes y perfiles incompletos. Si ese informe es ajeno al caso, se clasifica como no confiable.

Calcula sobre los **estados guardados auténticos**: curva de `T` volumétrica metal/arena, evolución de fracción líquida/sólida, volumen bajo `Tliq`/`Tsol`, velocidad media/máxima y un inventario sólido nominal `m_C14(1-alpha1)`. Identifica **intervalos de primer estado guardado** con temperatura bajo los umbrales y primer descenso de alpha1, no el instante exacto de nucleación. Deriva tasas medias por intervalo de 0.1 s de enfriamiento, calentamiento de arena y solidificación, más potencia latente nominal `rho_C14 L_C14 V (-Delta alpha1)/Delta t` y cambios aproximados de energía sensible/latente.

**Importante:** el campo `alpha1` es variable interna del modelo C14 y no medición microestructural ni fracción sólida QuickCup. El calor latente por diferencias entre snapshots no sustituye fuentes nativas del paso CFD de 0.001 s, ni demuestra recalescencia. El cambio de energía almacenada NO es balance de flujo de frontera. Se conserva el máximo residuo final con tiempo de ocurrencia, leído del log original por el análisis previo.

## Salida real nueva, independiente, protegida e idempotente

Destino: `~/OpenFOAM/C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01`, con:
- `C3D04_A_STAGE07_KINETICS_101_STATES.csv`: 101 filas de características + tasas de los 100 intervalos (la primera fila NO tiene derivadas).
- `C3D04_A_STAGE07_RECOVERY_REPORT.json`: identidades SHA de fuente C14/log/CSV/informe originales, variables y umbrales, rango de primer cruce, pico de enfriamiento y de potencia latente nominal, diagnóstico de copia nativa e indicadores explícitos de no validación.

Si el destino existe con la misma procedencia, se preserva y no se sobrescribe; si la procedencia difiere, se bloquea. No corre `foamMultiRun`, `foamPostProcess`, `foamLog`, `checkMesh`, `blockMesh`, Git ni manipula `postProcessing` de la fuente.

El código tiene pruebas con 101 estados **sintéticos** reproducibles (no sustitutos de CFD de investigación): robustez numérica, primeras observaciones, integridad SHA, copia nativa parcial/ajena, rechazo de datos corruptos, bloqueo de ruta superpuesta y reuso no destructivo del resultado previo.

## Una única operación en WSL, exclusiva del worktree A

Después de integrar en `main`, se avanza **solamente la rama local A**, sin tocar `MasterProject`, el worktree B ni `FS_C02_WORKTREE`:

```bash
git -C "$HOME/OpenFOAM/C3D04_A_WORKTREE" fetch origin &&
git -C "$HOME/OpenFOAM/C3D04_A_WORKTREE" merge --ff-only origin/main &&
python3 -B "$HOME/OpenFOAM/C3D04_A_WORKTREE/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/recover_existing_c14_3d_stage07.py"
```

Si la rama A contiene trabajo local no integrado o `merge --ff-only` no es posible, **bloquea sin forzar, resetear ni borrar**. La invocación de Python es SOLO análisis de archivos previos; NO lanza CFD.

**La corrida real y el estado de la copia nativa no se declaran verificados hasta recibir la salida WSL**. Si el directorio volumétrico anterior **existe pero le falta el CSV o el JSON** porque se interrumpió, se reutiliza el análisis nativo anterior de 101 estados y se **recalcula solo el postprocesamiento en una carpeta NUEVA** `~/OpenFOAM/C3D04_A_C14_3D_VOLUMETRIC_RECOVERED_02`, sin borrar/editar el expediente anterior y sin arrancar `foamMultiRun`. Esta recuperación está respaldada por el analizador volumétrico original, con SHA de log/controlDict y 101 campos guardados. Si el CSV/JSON anterior EXISTE pero muestra inconsistencias, tiempos falsos, valores no finitos o SHA divergente, se bloquea sin ocultar el error; no se reinterpreta silenciosamente un resultado corrupto como 'faltante'. Si la carpeta de recuperación también existe y está incompleta, se bloquea sin sobrescribir. El siguiente hito técnico, **después** de la inspección, es recuperar (sin sobrescribir) los resultados de `foamPostProcess` 3D y cerrar las lagunas de flujos/cierre de energía para avanzar hacia etapa 8; no repetir la malla ni la corrida.

**Avance científico sin modificar:** 6/10=60 %, etapa 7/10 abierta; Caso B y contracción no afectados.
