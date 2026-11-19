# FS-C05 — Primer candidato físico de VOF + transferencia térmica conjugada 3D (OpenFOAM Foundation 14)

**Estado:** herramienta de preparación disponible en el PR #51. **NO se ha creado ni ejecutado el caso FS-C05 en la laptop**, ni se ha comprobado su lectura por los solvers nativos. Los ensayos de FS-C03, FS-C04, `alpha`, `T` e interfaces ya completados permanecen INTACTOS y no se deben volver a ejecutar como sustitutos de avanzar en física.

## Qué aporta realmente

El tutorial **oficial de OpenFOAM Foundation 14**, `$FOAM_TUTORIALS/multiRegion/CHT/VoFcoolingCylinder2D`, utiliza el ejecutable `foamMultiRun` con los módulos `fluid compressibleVoF` y `solid solid`. Fuente directa: `https://github.com/OpenFOAM/OpenFOAM-14/tree/master/tutorials/multiRegion/CHT/VoFcoolingCylinder2D`. Por tanto, **sí existe una arquitectura oficial que puede acoplar VOF + CHT**. Para el QuickCup se adapta el nombre de regiones a `fluid` y `mold`: el fluido único contiene metal líquido y aire, mientras que arena sigue siendo sólido.

```foam
regionSolvers
{
    fluid           compressibleVoF;
    mold            solid;
}
```

El script `analysis_tools/stage_fs_c05_vof_cht.py` toma **la copia FS-C04 con dos campos de T inicial** y exige la aceptación nativa del postprocesamiento de ambas regiones. Comprueba de nuevo el `alpha.metal` (2368 hierro, 32000 aire), los 3136 pares de contacto arena–fluido y la identidad de `T`. Luego copia todo a un **nuevo directorio** `~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_<UTC>_<id>` y agrega, *solo sobre la copia*, los diccionarios y campos del tutorial oficial adaptados.

**El caso físico propuesto contiene:**
- `0/fluid/{alpha.metal,T,T.air,T.metal,p,p_rgh,U,k,epsilon,nut,alphat}`, `0/mold/T`.
- `constant/fluid/{phaseProperties,physicalProperties.metal,physicalProperties.air,momentumTransport,fvModels,g}`; `constant/mold/{physicalProperties,fvModels}`.
- `system/{controlDict,fvSolution,fluid/fvSchemes,fluid/fvSolution,mold/fvSchemes,mold/fvSolution}` derivados de Foundation14.
- Interfaces **`fluid_to_mold` y `mold_to_fluid` con `coupledTemperature`**, en lugar de los `calculated` anteriores. Aire abierto por `atmosphereTop`, `atmosphereSides` y `atmosphereLowerSides`; `T` del aire reentrante provisional 300 K; `p_rgh` `prghTotalPressure`; `U` `pressureInletOutletVelocity`.
- RAS `kEpsilon` + `compressible::VoFTurbulenceDamping` heredados de FS-C01 (se mantiene la intención investigativa de turbulencia, **sin calibración metalúrgica**). El tutorial oficial usa configuración laminar de referencia, que no se importa como modelo final.
- `endTime=5e-6 s`, `deltaT=1e-7 s`, `maxCo=0.1`, `maxAlphaCo=0.1`, `nEnergyCorrectors=2`: **solo una propuesta inicial de estabilidad, NO parámetros validados**.

## Propiedades provisionales y límites

| Material | Valores de prueba que se instalarán | Estado |
|---|---|---|
| Metal | `rho=6820 kg/m³`, `Cv=827 J/(kg·K)`, `mu=0.0055 Pa·s`, `Pr=0.14`, `sigma=1.0 N/m` | Heredados del ensayo FS-C02; **no** JMatPro ni curvas validadas |
| Aire | `perfectGas`, `Cp=1007 J/(kg·K)`, `Pr=0.7` | Propiedades provisionales del ensayo FS-C01 |
| Arena | `rho=1500 kg/m³`, `Cv=700 J/(kg·K)`, `k=2 W/(m·K)` | **Constantes provisionales**, no medidas para el molde |
| Temperaturas iniciales | Metal 1500 K; aire y arena 300 K | Valores de cribado, NO termopares experimentales |

La `alpha.metal` representa fracción VOF metal/gas, **NO fracción sólida**. No hay calor latente, cambio de fase, grafitización, presión de contracción, feeding ni geometría STL fiel. En el molde, `moldBottom` y las caras del hueco inferior se ponen **adiabáticas provisionalmente** con `zeroGradient`; esto NO es la condición física final y puede afectar radicalmente la curva de enfriamiento. Se deberá resolver el contacto con soporte y la exposición real al aire bajo la arena. No extrapolar el pequeño ensayo de 5 microsegundos a curvas QuickCup.

**El script NO invoca `foamMultiRun`, `foamRun`, `blockMesh` ni crea resultados físicos.** Su manifiesto deja `VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD`, `solver_executed=false`, `VOF_CHT_energy_balance_validated=false`. Antes de autorizar el ensayo nativo hay que validar sintaxis/modelos de Foundation14 y revisar flujos de calor en ambos lados de la interfaz, presión del aire y conservación de masa. Este paso de generación de entradas NO se confunde con un solver exitoso.

## Cómo preparar el candidato aislado

Primero, **verificar en Ubuntu que el estado nativo FS-C04 T ya es verde**. Directorios conocidos del investigador:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 -m unittest discover -s analysis_tools -p test_stage_fs_c05_vof_cht.py -v &&
python3 analysis_tools/stage_fs_c05_vof_cht.py \
  --source ~/OpenFOAM/FS_C04_T_INITIAL_RUNS/FS_C04_T_INITIAL_STAGE_20261119T054751Z_b2a08cb7 \
  --native-T-accepted ~/OpenFOAM/FS_C04_T_NATIVE_CHECKS/FS_C04_T_NATIVE_CHECK_20261119T055532Z_7145a68b
```

Opcional `--tutorial <ruta>` para instalaciones cuyo `$FOAM_TUTORIALS` no apunte a la ruta estándar. El script exige que el tutorial **real instalado** contenga `compressibleVoF` y `solid`, y verifica que los archivos críticos estén disponibles. Mantiene el FS-C04 original en modo de solo lectura y rechaza destinos existentes. `FS_C05_PHYSICS_CANDIDATE.json` guarda procedencia, propiedades y banderas de validación.

**No ejecutar directamente `foamMultiRun` sobre este candidato sin pasar una auditoría de entrada de Foundation14.** Aún no se ha comprobado que las constantes heredadas, BC turbulentas, esquema energético y geometría aproximada produzcan una solución estable; podría fallar incluso al cargar los diccionarios. Hay que inspeccionar errores reales y corregir el modelo sin esconderlos.

## Qué constituye avance físico verificable

1. **Gate de lectura/arranque nativo** de ambos módulos y BC, sin trucar campos o relajar errores.
2. **Ensayo CHT de duración corta** con `foamMultiRun` únicamente en copia aislada; confirmar que hay intercambio real (q_{m metalightarrow arena}) y (q_{m arenaightarrow aire}), con continuidad del flujo térmico en interfaces ((q_{m fluid}+q_{m mold}approx0)).
3. **Masa/energía y malla**: conservar `∫ alpha.metal dV` dentro de tolerancias; revisar (T_{m metal}), arena superior/lateral, `Co`, `maxDeltaT`, `p_rgh`, flujos por las fronteras abiertas y sensibilidad en distancia del contorno.
4. **Prueba de CAD y soporte**: no interpretar temperaturas como experimentales antes de usar STL exactos y condiciones reales de apoyo. Después propiedades (ho(T), C_p(T), k(T)) de aleaciones y arena; por último solidificación y contracción.

**Referencia externa de arquitectura (OpenFOAM 14, sin copiar archivos al repo):** tutorial oficial `VoFcoolingCylinder2D` de Foundation14; `foamMultiRun`, `compressibleVoF`, `solid` y `coupledTemperature`. Documentación de Foundation14: `https://doc.cfd.direct/openfoam/user-guide-v14/thermal-boundary-conditions`.

## Resultado de la laptop, 19-11-2026 — entradas FS-C05 preparadas sin ejecutar CFD

El investigador ejecutó `git fetch` y `git switch --detach FETCH_HEAD` al commit `01a417ce7`, con `WM_PROJECT_VERSION=14`, luego `test_stage_fs_c05_vof_cht.py` (**8 de 8 tests OK**) y `stage_fs_c05_vof_cht.py`. Resultado local:

```text
FS-C05: VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD
New untouched copy with physics candidate: /home/michel/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e
Region solvers: {'fluid': 'compressibleVoF', 'mold': 'solid'}
Still UNTESTED: no CFD, no CHT energy/temperature evolution accepted.
```

**HECHO:** diccionarios de solver candidatos y condiciones `coupledTemperature` instalados en una copia, originales preservados. **NO HECHO:** carga efectiva de módulos/propiedades/BC en OpenFOAM, cálculo de paso de tiempo, conservación energética o masa. Antes de cualquier corrida física larga, ejecutar un arranque breve y aislado, detener/rechazar errores reales y conservar logs; no afirmar flujo térmico a partir del éxito de preparación.

## Nuevo ejecutor de primera física: 2 pasos de `foamMultiRun`, SÓLO sobre otra COPIA

Se incorporó `analysis_tools/run_fs_c05_native_smoke.py` y la suite `test_run_fs_c05_native_smoke.py` con 11 pruebas simuladas (no se ejecuta CFD en GitHub Actions). El ejecutor hace un **preflight del candidato FS-C05 completo**: comprueba el manifiesto `VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD`, los hashes de los archivos generados, las 2368 celdas de hierro y 32000 de aire, `T=1500/300 K` coherente con `alpha.metal`, el campo de arena de 7680 celdas a 300 K, las 3136 caras y los `mappedWall` a la arena, los tres parches de atmósfera abiertos, `coupledTemperature` a ambos lados y los nombres de solver y turbulencia RAS `kEpsilon`. Si la fuente fue manipulada, rechaza el ensayo.

Luego crea una carpeta **nueva** bajo `~/OpenFOAM/FS_C05_NATIVE_SMOKE_RUNS/FS_C05_NATIVE_SMOKE_<UTC>_<id>` y acorta exclusivamente en esa copia `endTime` a **2e-7 s**, conserva `deltaT=1e-7 s`, cambia `writeControl` a `timeStep` e `writeInterval` a 1. Conserva originales FS-C04/FS-C05 y registra `FS_C05_NATIVE_SMOKE_REPORT.json`. **Por defecto no arranca OpenFOAM**; `--native` exige OpenFOAM Foundation14 y `foamMultiRun`, ejecuta dos pasos con límite de tiempo, guarda `log.FS_C05_foamMultiRun` y verifica código de salida cero, ausencia de `FOAM FATAL` y presencia de `Time = ...` y `End`. Un fallo deja el caso y el log para revisión sin sobrescribir nada.

Tras comprobar que la rama está actualizada y pasar tests:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 -m unittest discover -s analysis_tools -p test_run_fs_c05_native_smoke.py -v &&
python3 analysis_tools/run_fs_c05_native_smoke.py \
  --source ~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e \
  --native
```

**Resultado esperado si y sólo si el solver termina el arranque con éxito:** `NATIVE_TWO_STEP_VOF_CHT_STARTUP_COMPLETED_NOT_VALIDATED`. Es todavía **SIN RESULTADO REAL**, y aun si pasa NO acredita conservación de masa VOF, continuidad de flujo de calor, estabilidad transitoria ni cambios térmicos físicos: solo prueba carga de módulos e iteración temporal en un primer ensayo con propiedades provisionales. El log y los nuevos campos serán la evidencia para verificar más adelante el balance energético del contacto metal/arena y arena/aire. El aire exterior debe seguir siendo un volumen resuelto, no un coeficiente de convección inventado.

**No confundir con validación para tesis:** necesitamos `∫alpha.metal dV` al final, flujo térmico recíproco de los 3136 pares de caras, termodinámica `Cp/k/rho(T)`, soporte inferior, geometría CAD fiel y finalmente solidificación/contracción.

## 19-11-2026 — Primer arranque REAL de FS-C05: fallo de discretización turbulenta localizado y corrección instalada

El investigador ejecutó con `WM_PROJECT_VERSION=14` el commit `5de56d46b`; **11 de 11 pruebas unitarias iniciales pasaron**. El primer intento REAL `foamMultiRun` se lanzó en nueva copia independiente:

```text
/home/michel/OpenFOAM/FS_C05_NATIVE_SMOKE_RUNS/FS_C05_NATIVE_SMOKE_20261119T065033Z_7503bc2b
```

El log `log.FS_C05_foamMultiRun` confirma carga real de las regiones **`fluid compressibleVoF` y `mold solid`**. En `Time = 1e-07s` el solver resolvió `alpha.metal`/MULES, `T` del fluido, `e` del molde y `p_rgh`, **antes de fallar**. Volumen de fase informado `0.0280838422309` como fracción respecto al volumen fluido; `alpha.metal` permaneció entre 0 y 1 hasta el punto del error. **NO se completó el primer paso, NO se ha demostrado flujo térmico conservativo ni dos pasos completos.**

Error nativo exacto:
```text
FOAM FATAL IO ERROR:
Cannot find scheme for div(rhoPhi,epsilon)
in dictionary "$FOAM_CASE/system/fluid/fvSchemes!divSchemes"
```

**Causa:** la plantilla oficial `VoFcoolingCylinder2D` contiene `div(phi,k) $turbulence` pero, al sustituir el modelo de turbulencia laminar del ejemplo por el RAS compresible `kEpsilon`, este pide los esquemas de **`div(rhoPhi,k)` y `div(rhoPhi,epsilon)`**, no simplemente `div(phi,epsilon)`. La ausencia de uno de ellos NO constituye un fallo de la malla ni valida/desmiente por sí mismo los resultados térmicos.

**Corrección implementada**: la función `ensure_compressible_kepsilon_divergence` del generador `stage_fs_c05_vof_cht.py` instala explícitamente ambos esquemas `$turbulence` para los **nuevos** casos. El ejecutor `run_fs_c05_native_smoke.py` verifica todos los hashes originales del viejo FS-C05 y aplica esa misma corrección **SOLAMENTE dentro de la nueva copia del arranque**, para permitir reutilizar de manera segura el caso `FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e` SIN modificarlo ni reconstruir FS-C04. Registra cuáles esquemas agregó y el nuevo SHA del `fvSchemes`. También se corrigió el lector de tiempos para el formato nativo `Time = 1e-07s` (con sufijo de segundos). Dos suites de pruebas nuevas incluyen reproducción de la ausencia de esos esquemas y resistencia a duplicados.

**Reintento recomendado (solo después de pruebas verdes):**

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
git status --short
git fetch origin research/fs-c02-metal-air-vof-20261117
git switch --detach FETCH_HEAD
python3 -m unittest discover -s analysis_tools -p test_stage_fs_c05_vof_cht.py -v &&
python3 -m unittest discover -s analysis_tools -p test_run_fs_c05_native_smoke.py -v &&
python3 analysis_tools/run_fs_c05_native_smoke.py \
  --source ~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e \
  --native
```

Si hay otro error de OpenFOAM, **no ocultarlo, no usar el anterior directorio fallido**. El ejecutor preserva log, ruta y estado de cada copia. Un eventual `NATIVE_TWO_STEP_VOF_CHT_STARTUP_COMPLETED_NOT_VALIDATED` solo acredita completar dos pasos, NO que las propiedades 1500/300 K, `kEpsilon`, calor `q`, Co, masa, energía ni solidificación estén validados. El apoyo inferior y CAD exacto siguen pendientes.
