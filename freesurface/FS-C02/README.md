# FS-C02 — hierro fundido–aire (continuación de la familia B)

Caso correcto: **FS-C02 / B-FS-02**. Independiente de **FS-C01** (agua–aire), **B14** (hierro–molde original) y **C3D-02** (malla 3D activa).

Estado: **STAGING IMPLEMENTADO; SIN CFD Y SIN VALIDACIÓN FÍSICA**. El script analysis_tools/run_fs_c02_local.py convierte una COPIA de las entradas congeladas de FS-C01 (probadas con Foundation v14) en un banco VOF metal–aire. Consulta de solo lectura el archivo de material del caso B14 original. Nunca cambia las entradas originales.

## Física y propiedades provisionales

| Aspecto | Valor de prueba | Procedencia/limitación |
| --- | --- | --- |
| Fases | metal y air | VOF, sin fracción sólida |
| Solver | compressibleVoF Foundation 14 | Base FS-C01 |
| Dominio | 40 × 60 × 10 mm; 80 × 120 × 1 | Geometría de FS-C01, NO B14 |
| Metal inicialmente ocupado | 40 mm de altura | V inicial = 1.6e-5 m3 |
| Densidad metal | rhoConst = 6820 kg/m3 | rho0 de B14, NO rho(T,f_s) |
| Calor específico de prueba | eConst Cv = 827 J/(kg K) | Aproxima Cp de B14, NO termodinámica validada |
| Viscosidad metal | 0.0055 Pa s | B14 |
| Pr metal | 0.14 | B14 |
| T inicial | metal 1500 K, aire 300 K | Campo T zonal, sin acoplamiento con arena |
| Tensión superficial | 1.0 N/m | PROVISIONAL SIN VALIDACIÓN |
| Aire | modelo original FS-C01 | Sin alimentación, cavidad, ni gas de molde |
| Modelo de turbulencia | RAS kEpsilon y damping de FS-C01 | No calibrado para hierro |
| Horizonte temporal | 0–0.1 s | Smoke test, no solidificación |

Masa metálica esperada de la configuración: 1.6e-5 m3 × 6820 kg/m3 = **0.10912 kg**. Todavía NO medida desde solución CFD.

**Ausentes intencionalmente:** cambio de fase, calor latente, molde 3D/CHT, contracción, alimentación, microporosidad, recalescencia. No asumir que compressibleVoF junto con B14 implica shrinkage. El modelo térmico eConst utiliza Cv estimado desde Cp a modo de prueba y requerirá termodinámica/JMatPro trazable; la expansión por grafitización del hierro tampoco está representada.

## Procedimiento aislado en Ubuntu/WSL

Abrir otra terminal, no cerrar ni cambiar la rama del checkout ~/OpenFOAM/MasterProject usado por C3D-02. Tampoco reutilizar ~/OpenFOAM/FS_C01_WORKTREE.

    cd ~/OpenFOAM/MasterProject
    git fetch origin research/fs-c02-metal-air-vof-20261117
    git worktree add --detach ~/OpenFOAM/FS_C02_WORKTREE FETCH_HEAD
    cd ~/OpenFOAM/FS_C02_WORKTREE

Asegurar que la variable WM_PROJECT_VERSION sea 14. Si no lo es, activar Foundation 14 desde /opt/openfoam14/etc/bashrc (o la ubicación local real).

Primero preparar únicamente inputs; esto NO ejecuta CFD:

    python3 analysis_tools/run_fs_c02_local.py --stage-only

Para ejecutar smoke test en carpeta NUEVA, sin reciclar ni sobrescribir salidas anteriores:

    python3 analysis_tools/run_fs_c02_local.py

El ejecutor crea ~/OpenFOAM/FS_C02_RUNS/FS-C02_<UTC>_<id>/FS-C02 y logs FS-C02_blockMesh.log, FS-C02_checkMesh.log, FS-C02_foamRun.log; también FS-C02_RUN_STATUS.json. No ejecuta Allclean, ni modifica B14, FS-C01 o C3D-02.

Si falla la lectura de termodinámica o una BC, leer el log FS-C02_foamRun.log de ESA ejecución e identificar la causa; NO parchear los resultados ni afirmar un solver validado.

## Siguientes verificaciones científicas (NO realizadas)

1. Arranque de compressibleVoF con fluidos metal/aire y ecuaciones térmicas.
2. alpha.metal en [0,1], volumen en el tiempo, cambios de interfaz, campos rho/T/U/p_rgh.
3. Balance real de masa de metal por dominio y contornos. La integral de alpha.metal NO es masa.
4. Balance térmico y transferencia con molde en un siguiente caso, verificando compatibilidad con foamMultiRun + solid.
5. Modelo VoFSolidificationMelting y ley fracción sólida vs T validada, sin suponer implementación automática de shrinkage.
6. Introducir densidades por fase o volumen específico dependiente de T y f_s, cerrar masa y seguir eventual expansión por grafitización.
7. Porosidad y feeding son física adicional y requieren validación independiente.

Los tests del repositorio son solo sintéticos; NO ejecutan OpenFOAM ni prueban estos criterios físicos.


## Primera ejecución real FS-C02: 2026-11-17 (hora local), 2026-11-18 (UTC)

Salida textual comunicada por el investigador, con el **código fuente en commit f226913da** y **OpenFOAM 14**:

    /home/michel/OpenFOAM/FS_C02_RUNS/FS-C02_20261118T005412Z_c04dfcf6

Dentro de esa carpeta, el ejecutor FS-C02 imprimió la creación de un caso independiente y registró ejecución de `blockMesh`, `checkMesh`, `foamRun`, finalizando con:

    FS-C02 foamRun completed. MASS, INTERFACE, THERMAL PHYSICS, SHRINKAGE UNVERIFIED.

Los gates del ejecutor exigen salida de proceso 0 y ausencia de error de mallado / marcador final de solver. **Estado documentado: LOCAL_FOAMRUN_COMPLETED_REPORTED; NO análisis de campos ni validación física todavía**. No se dispone aquí de los logs o campos numéricos completos de la laptop; no afirmar valor real de volumen, alpha o Courant.

La corrida se hizo en `~/OpenFOAM/FS_C02_WORKTREE`; **FS-C01, B14 y C3D-02 permanecen separados**. La rama experimentó solo el cambio programático, no el solver local.

## Auditar la corrida FS-C02 existente, sin relanzar CFD

Obtener la última versión de **esta rama** en el worktree FS-C02 existente (no en `~/OpenFOAM/MasterProject`). Confirmar antes que no haya archivos modificados que necesiten conservarse:

    cd ~/OpenFOAM/FS_C02_WORKTREE
    git status --short
    git fetch origin research/fs-c02-metal-air-vof-20261117
    git switch --detach FETCH_HEAD

Leer el caso original y escribir un informe en un directorio completamente separado:

    python3 analysis_tools/audit_fs_c02_local.py       --run ~/OpenFOAM/FS_C02_RUNS/FS-C02_20261118T005412Z_c04dfcf6       --out ~/OpenFOAM/FS_C02_AUDITS/FS-C02_20261118T005412Z_c04dfcf6_screen1

**No repite blockMesh, checkMesh ni foamRun. No escribe dentro de la carpeta de corrida.** El reporte `FS-C02_NUMERICAL_SCREEN.json` contiene: 0–0.1 s del volumen integrado, máxima deriva, alfa mínimo/máximo en campo final y número de celdas, integral espacial de alpha en el mallado uniforme, masa derivada (rhoConst × V), Courant máximo del log completo, checksums de procedencia, alertas y límites científicos. Falla si faltan entradas/campos originales, identidad del caso o manifiesto SHA-256, o si alguna prueba supera tolerancia. Nunca interpreta una superficie equivalente como altura real ni declara shrinkage/mass real, porque no hay fracción sólida ni rho(T,f_s).

Este audit de Python tiene pruebas sintéticas pero requiere el archivo original `0.1/alpha.metal`; si la versión real de OpenFOAM lo representa de un modo distinto, fallará de manera segura y habrá que estudiar el formato sin inventar datos. Guardar resultados completos para revisión de malla, energía y las siguientes etapas B-FS/B-SH.

## 2026-11-17 (hora local) — Primera auditoría numérica real FS-C02: REVIEW por pico de Courant

El investigador compartió el **JSON íntegro** de `FS-C02_20261118T005412Z_c04dfcf6_screen1/FS-C02_NUMERICAL_SCREEN.json`, obtenido de la corrida local `FS-C02_20261118T005412Z_c04dfcf6`. El auditor pudo leer el volumen, un campo final alpha.metal y el log del solver. Estado **REVIEW** (NO `NUMERICAL_SCREEN_PASSED`).

**Resultados aportados**:
- 11 mediciones de volumen entre t=0 y t=0.1 s: V0 = `1.6e-5 m3`; Vf = `1.599999e-5 m3`; deriva máxima relativa `6.25000000043722e-7` (~0.0000625 %), frente al umbral numérico `0.005` (0.5 %).
- Integral independiente del campo alpha.metal al tiempo final `1.5999991405848604e-5 m3`; discrepancia relativa contra salida volFieldValue `8.786553786224931e-8`.
- alpha.metal mínimo `-1.29497e-31` (redondeo cercano a 0) y máximo `1.0`, 9600 celdas, 3208 con `0<alpha<1`. El recuento estricto incluye fracciones arbitrariamente cercanas a 0/1 y **NO demuestra un espesor de interfaz físico**.
- rhoConst 6820 kg/m³: masa nominal `0.10912000000000002 kg`, masa final **derivada** `0.10911993179999999 kg`. NO es balance independiente de masa.
- 5383 observaciones de Courant. **Máximo global `9.41807`**, considerablemente superior al límite `maxCo 0.25`, aunque el último registro máximo sea `0.246551`. Courant máximo de interfaz en toda la ejecución `0.00941131`, último `0.00028081`.
- La única alerta del auditor es `Courant max exceeds configured maxCo .25`. El cribado de volumen **no autoriza** declarar estabilidad ni validez de la interfaz o energía/solidificación.

**Decisión:** preservar esta corrida; buscar en `logs/FS-C02_foamRun.log` el instante, deltaT y contexto numérico del pico 9.41807, y comparar con evolución de Courant/alpha/velocidad antes de alterar `maxCo`, parámetros termodinámicos o esquema numérico. No aumentar `maxCo` para silenciar la alerta. No avanzar todavía a introducir solidificación o shrinkage. B14, FS-C01 y C3D-02 se mantienen intactos.

### Diagnóstico nuevo, sin volver a correr CFD

El script `analysis_tools/diagnose_fs_c02_courant.py` fue añadido para localizar la observación del máximo global de Courant, el número de registros que exceden `maxCo=0.25`, la línea exacta del log, los `Time =` antes/después y el `deltaT` registrado cerca del pico. Los valores de `Time` indican **marcadores que rodean la línea**, no se deben asignar automáticamente como instante físico exacto de ese Courant.

Desde `~/OpenFOAM/FS_C02_WORKTREE` actualizado con la rama FS-C02 correcta, ejecutar:

    python3 analysis_tools/diagnose_fs_c02_courant.py --run ~/OpenFOAM/FS_C02_RUNS/FS-C02_20261118T005412Z_c04dfcf6 --limit 3 --context 8

El diagnóstico solamente **lee el log original FS-C02** y muestra los mayores picos y líneas circundantes. No reescribe el reporte `screen1`, no relanza `foamRun`, no toca B14/FS-C01/C3D-02. Se exige investigar primero el origen del `Co=9.41807`; no subir artificialmente `maxCo` para que pase.

## 2026-11-17 — Diagnóstico localizado del pico de Co (laptop del investigador)

El script `diagnose_fs_c02_courant.py` aplicado a `FS-C02_20261118T005412Z_c04dfcf6` devolvió 5383 observaciones, **1347 valores Co_max >0.25** y **un solo pico Co_max >1**. Pico absoluto `Co_max=9.41807`, `Co_mean=2.19469`, línea 100 del archivo `logs/FS-C02_foamRun.log`; `deltaT` registrado antes `1.19048e-4 s`, después `3.15988e-6 s`. Segundo mayor pico 0.376259 cerca de `Time=0.000126083s`, siguiente salto 0.342451 cerca de `Time=0.00112245s`; último Co_max=0.246551. El Courant de interfaz de estas primeras líneas es cero, sin probar por sí mismo dinámica de interfaz. **El solver terminó pero la auditoría permanece REVIEW.**

Se identificó un bug del diagnóstico, no del CFD: `Time = 0.000122208s` de Foundation 14 se descartaba por el sufijo `s`; los tiempos anteriores/posteriores se mostraban `null`. Corregido el parser y probada la regresión con segundos adjuntos. Los tiempos son **marcadores cercanos**, no asignación causal de un instante exacto.

**Hipótesis:** primer paso relativamente amplio, velocidades iniciales elevadas inducidas por las condiciones de arranque y limitación de paso temporal que reacciona con retraso. Esto es consistente con `setDeltaT.C` de OpenFOAM Foundation 14, pero **NO identifica todavía la causa física** (puede involucrar presión hidrostática inicial, salto térmico metal–aire, tensión superficial, tratamiento de fronteras y turbulencia). Tampoco se deben atribuir los 1347 excedentes moderados al mismo mecanismo sin estudiar su distribución temporal.

### Siguiente prueba confinada: --startup-probe (NO cambia el expediente original)

En un worktree FS_C02_WORKTREE limpio, actualizado a la rama `research/fs-c02-metal-air-vof-20261117`, activar Foundation 14 y ejecutar:

    python3 analysis_tools/run_fs_c02_local.py --startup-probe

El comando prepara una **tercera carpeta aislada nueva**, con prefijo `FS-C02_STARTUP_`, ejecuta `blockMesh`, `checkMesh`, `foamRun` **solo entre 0 y 0.002 s**, con `deltaT inicial=1e-7 s`, `maxDeltaT=1e-6 s`, `maxCo=maxAlphaCo=0.20`, escritura cada `0.0002 s` y `adjustTimeStep on`. Todos los parámetros se guardan en el manifiesto y en el estado. La salida calcula **máximo Courant en todo el log**, su recuento de excedencias y tres picos principales; condición `PROBE_COURANT_SCREEN_PASSED` solo si ninguno supera 0.20. Si sigue alto, `PROBE_REVIEW_COURANT` y exit code 1, SIN afirmar que el solver no terminó ni tratar de elevar el límite. No se usa el auditor completo FS-C02 de 0.1 s sobre esta prueba parcial de 0.002 s.

Se eligió un límite de paso temporal menor al registrado después del pico, como experimento conservador; **no es una prueba científica de que se hayan eliminado todas las inestabilidades**, requiere correr en la laptop y verificar el resultado. No se modifican parámetros térmicos/metalúrgicos de la corrida anterior, ni B14, FS-C01 o C3D-02.

Fuente específica: [OpenFOAM-14 foamRun setDeltaT.C](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/solvers/foamRun/setDeltaT.C), que ajusta el paso basado en `solver.maxDeltaT()` en un proceso transitorio. El valor `maxCo` controla el tamaño de paso de forma adaptativa, pero no es prueba automática de que todos los pasos hayan permanecido por debajo del objetivo.
