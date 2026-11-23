# C3D04 Caso A — recuperación nativa C14 con Foundation14 y registros termofísicos

## 23-11-2026 — WSL real: destino _02 ocupado; inspección recuperable sin borrar

En la segunda invocación del programa por el investigador en `~/OpenFOAM/C3D04_A_WORKTREE`, Git informó `Already up to date` y **el programa se detuvo en preflight** con `C3D04_A_NATIVE_RECOVERY_BLOCKED: new isolated copy output occupied; NEVER overwrite previous CFD or postprocessing`.

Esta salida **solo significa que ya existe** `~/OpenFOAM/C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_02`, no identifica si es un proceso terminado, uno parcial o uno actualmente ejecutándose. La invocación que falló **no realizó copia, `foamPostProcess`, CFD, remallado ni cambios en la evidencia**. No borrar `_02`, no inferir sus seis resultados ni lanzar automáticamente otra copia `_03`.

### Corrección permanente implementada

`run_c14_stage07_solver_backed_recovery.py` reconoce ahora que `--out` ya existe, y **cambia automáticamente a inspección estrictamente de solo lectura**:

- Compara `system/controlDict` original C14, CFD y copia `_02`; compara el SHA256 del log original `log.foamMultiRun` con el log de copia.
- Busca el informe `C3D04_A_C14_SOLVER_BACKED_RECOVERY_REPORT.json` **sin crearlo**. Si existe, comprueba su esquema, ruta fuente y destino, hashes del recuperador original/forense, y **las seis** entradas individuales de `core/energy/phase/flow/profiles/momentum` con `exit_code`, `passed` y SHA256 del log correspondiente. Se puede certificar que **la ejecución de los seis grupos terminó** aunque alguno tenga `passed=false`; eso NO valida energía o física.
- Si falta el informe, no se pueden comprobar los hashes, hay logs incompletos o el reporte no corresponde al caso: clasifica `EXISTING_COPY_PARTIAL_OR_POSSIBLY_ACTIVE_PRESERVED`, muestra presencia y extractos de logs, y devuelve código 3. **No asume que sea seguro reanudar ni que ningún otro proceso esté trabajando.** Si está completo, responde `EXISTING_COMPLETE_NATIVE_POSTPROCESS_REPORT_REUSED_NO_NEW_RUN` con grupos aprobados/fallidos y potencia reportada, **sin reejecutar funciones**.
- Symlinks y rutas engañosas continúan bloqueadas; un destino distinto `--out` requiere una elección explícita, y nunca puede sobrescribir `_02`.

El usuario únicamente debe repetir una vez la invocación normal del script actualizado desde worktree A. **No hace falta volver a ejecutar el ejecutor anterior sin corregir.** No cambia el modelo termofísico, la malla V4/T02, los 101 estados C14 ni los worktrees B/FS. Esta corrección de gobernanza de evidencia no suma hitos.

---

**23 de noviembre de 2026 | Etapa 07/10 abierta | 6/10 = 60 % de hitos operativos.** Este documento diferencia evidencias WSL reales, código nuevo y aceptación futura. No supone validación física ni CFD nuevo.

## Causa real observada en el Caso A de investigación

El investigador ejecutó en WSL `audit_existing_native_c14_stage07.py` sobre la copia de diagnóstico `~/OpenFOAM/C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01` y confirmó:

- Sólo `c14_functions` falló de los cuatro subcomandos originales.
- La traza fatal exacta fue `FOAM FATAL ERROR: Field rho not found in database`, originada al escribir `volFieldValue`.
- Antes del aborto había advertencias `metalBoundaryEnergyPower cannot find required object energyAdvectiveFlux`, `heatFlux` y `energyFlux`.
- Faltan 14 familias de objetos nativos originales, 20 campos derivados y al menos 5 perfiles muestreados incompletos (el número de perfiles incompletos se basa en la lista mostrada en stdout).
- `metalBoundaryEnergyPower/0/surfaceFieldValue.dat` no existe en la copia fallida, por lo que el balance energético nativo no se puede calcular todavía.
- La cinética volumétrica 101 estados **sí está preservada**; primer descenso observado de alpha1 en `(0.2,0.3]s`, temperatura metálica final media volumétrica `1450.7091627651344 K`, potencia latente nominal discreta máxima `1038.881301373963 W` en `7.2–7.3 s`, inventario sólido C14 nominal final `0.03358283580064463 kg`. Estos valores no son validación experimental.

**Diagnóstico causal:** el código original lanzó `foamPostProcess -region metal -dict system/functions`, **sin `-solver fluid`**. En esa modalidad, no se construye automáticamente toda la base de modelos termofísicos de un solver fluido. Por eso el `volFieldValue` original pudo no encontrar `rho` y las operaciones de potencia dependientes de los campos de flujo térmico tampoco estaban disponibles. La presencia de dinámica codificada `dynamicCode` / `wmake` en el log no es, por sí misma, prueba de fallo de compilación: la traza fatal demuestra ausencia de `rho`.

**Fuente documental externa:** OpenFOAM Foundation v14 `foamPostProcess -solver fluid -region ...` permite instanciar el solver apropiado sin avanzar el tiempo; manual oficial sección 7.2 y fuente `foamPostProcess.C`, `https://doc.cfd.direct/openfoam/user-guide-v14/post-processing-cli` y `https://cpp.openfoam.org/v14/foamPostProcess_8C_source.html`. El manual distingue campos cargados de disco y objetos reconstruidos en registro por la opción `-solver`. La ejecución del nuevo pipeline en la malla real V4/T02 todavía debe comprobarse; no declarar éxito anticipado.

## Corrección implementada — aislamiento de grupos y copia NUEVA

Nuevo programa:

`cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_solver_backed_recovery.py`

Antes de copiar datos autentica por SHA-256: `system/controlDict` original C14, `log.foamMultiRun` del CFD real y de la copia fallida, informe auténtico de cinética 101 estados, informe forense de 4 subcomandos reales y archivos de entrada del último estado `10/metal`. Si cualquiera no coincide o el destino está ocupado, aborta; no fuerza, no borra ni reescribe nada.

La nueva copia física es `~/OpenFOAM/C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_02`. Solo ahí adapta puntos de sonda/perfiles usando celdas reales 3D (sin cambiar geometría, fuente C14 ni `controlDict`), conserva los directorios `postProcessing` heredados por separado y genera subdiccionarios `system/stage07Offline_*` a partir de los **bloques originales C14**. Cada grupo se ejecuta **independientemente**:

| Grupo | Modalidad | Objetivo y límite |
|---|---|---|
| core | `foamPostProcess -solver fluid -region metal` | `rho,h,U,phi`, sonda en estados guardados, `metalSensibleEnthalpy`, `metalTopPhiSum`. No reconstruye sonda 0.001s |
| energy | `-solver fluid` | `energyAdvectiveFlux`, `heatFlux`, `energyFlux` y potencias de top, contacto metal/arena y frontera total |
| phase | `-fields '(phaseChangeSource:alpha1)'` sin solver | Promedio nativo de fracción líquida, sin asumir que constructor fluido cargó la variable del modelo |
| flow | `-solver fluid` | Vorticidad, gradientes, `flowType`, Courant y máximos originales C14 |
| profiles | `-fields '(U T p_rgh phaseChangeSource:alpha1)'` sin solver | Perfiles horizontales/verticales solo de variables primitivas originalmente guardadas; **excluye** `ddt` y derivados no reconstruibles |
| momentum | `-solver fluid` | Intento aislado de `solidificationMeltingMomentumDiagnostics` original (coded) y sus resúmenes/perfiles; si el modelo no se puede registrar offline, **se informa el fallo sin detener otros grupos** |

**Los grupos fluidos usan el mecanismo `-solver fluid` de Foundation14, no `foamMultiRun`: la función construye datos/modelos para postprocesamiento, sin resolver las ecuaciones por nuevos pasos.** No se ejecutan `Allrun`, `blockMesh`, `checkMesh`, `git pull`, `git reset` ni se ejecuta el CFD 10s de nuevo.

Al final intenta reconciliar las **101 tablas de potencia de superficies** nativas (si existen) en términos `P_bound - P_top - P_contact`, con orientaciones y tiempos registrados. Incluso si estas sumas coinciden, **NO** certifican conservación global: faltan cierre regional de arena y contabilidad discretizada de entalpía y calor latente original. Los objetos `ddt(T)`, `ddt(alpha1)`, `solidificationRate` y `latentHeatRateVol` del C14 original no se falsifican como salida nativa de 0.001s; las diferencias finitas 0.1s del CSV anterior siguen siendo **estimaciones nominales claramente etiquetadas**.

El pipeline escribe `C3D04_A_C14_SOLVER_BACKED_RECOVERY_REPORT.json` en la NUEVA copia con los grupos PASS/FAIL, hashes de diccionarios originales y adaptados, últimos mensajes por grupo, inventario de energía, geometría de muestreo y banderas de conservación/validación **false**. Una falla individual no impide revisar los otros objetos. Para reintentos futuros debe elegirse otra carpeta; jamás reutilizar la copia fallida antigua o destruir pruebas.

## QA y alcance del smoke científico

La regresión Python construye solo expedientes temporales sintéticos, prueba las listas de objetos C14 originales, exclusión de campos `ddt`, comandos `-solver fluid`, bloqueo SHA de casos, balances de potencia de cara de 101 estados ficticios, rechazo de resultados sobrescribibles y faltantes. No acredita comportamiento WSL real.

Se agregó además al workflow nativo C14 en GitHub una comprobación directa de Foundation14 que parte del caso **sintético de 27 celdas por región** después de sus dos pasos CFD y llama `foamPostProcess -solver fluid -latestTime` sobre `metalSensibleEnthalpy` (el objeto original `rho*h`). Es una prueba de interoperabilidad del solucionador F14 real, **NO** resultados de tesis 3D V4/T02.

## Aceptación nativa real en GitHub Actions — PASS (NO malla V4/T02)

**Workflow:** `https://github.com/michels-lab/MasterProject/actions/runs/45263380861`, en el commit de la rama de implementación. OpenFOAM Foundation **14** instaló los módulos originales C14 y ejecutó el smoke nativo de dos pasos sobre dos regiones sintéticas de **27 celdas por región**. Una vez terminado ese CFD sintético, un segundo proceso `foamPostProcess -region metal -solver fluid -latestTime` (sin nuevo `foamMultiRun`) confirmó:

1. `NATIVE_SOLVER_BACKED_RHO_H_REAL_FOUNDATION14_POSTPROCESS_PASS`: registro termodinámico `heRhoThermo` y `rho`, tabla nativa `metalSensibleEnthalpy` integrada correctamente.
2. `NATIVE_SOLVER_BACKED_3_SURFACE_ENERGY_POWER_TABLES_F14_PASS`: `energyAdvectiveFlux`, `heatFlux`, `energyFlux`, `metalTopEnergyPower`, `metalMoldEnergyPower` y `metalBoundaryEnergyPower` reales calculados con códigos de salida cero y archivos de tabla en el directorio `postProcessing/metal` del caso sintético.
3. Este test **no** prueba que la copia V4/T02 de 101 estados haya corrido el nuevo pipeline ni que los objetos opcionales de momentum/perfiles sean reconstruibles. Tampoco valida el balance total metal+arena; las potencias son nativas pero de una malla sintética.

El workflow de regresión Python `C3D04 A Original C14 3D Postprocessing Volume Parity` terminó `success` en el mismo HEAD. Se conserva explícita la diferencia entre QA nativa sobre 27+27 celdas y resultados científicos WSL de 8960+12352 celdas.

## Única siguiente ejecución WSL (después de integrar y pasar CI)

```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_solver_backed_recovery.py"
```

Los worktrees B y FS, el `~/OpenFOAM/MasterProject` principal, el CFD de diez segundos y **la primera copia nativa fallida** son entradas de solo lectura para este cambio. Un `git merge --ff-only origin/main` en A actualiza solo el worktree A, no el trabajo de las otras ramas. Si el informe del nuevo pipeline muestra `groups_failed`, esos son errores reales pendientes, no equivalen a estabilidad/validación física.

**Hitos: etapa 7/10 sigue abierta; 6/10=60 %; cierre energético/recalescencia/onset exacto/independencia/QuickCup NO declarados.**
