> **Operación Uva + Granada — corte vigente 27-11-2026.** El estado canónico es [STATUS.json](STATUS.json) de esta rama. El lote 12 de arranque nativo Foundation14 (7b3ed1ff4) registró compilación y ejecución WSL, 4/4 variantes y 75/75 pasos aceptados a 5 μs, según las salidas de terminal del investigador; la réplica no se suma. No hay independencia temporal, cierre energético global CHT ni validación física de contracción. Las afirmaciones fechadas 23–24 de noviembre sobre ausencia de compilación/CFD, el EOS incompresible y los comandos shadow describen etapas históricas, no la siguiente acción. El candidato activo usa K provisional de hierro puro (83.761 GPa), no calibración CE/S. Mantener los gates estrictos, no relanzar FS-C07 ni pruebas shadow; investigar dependencia temporal y aceleración de arranque antes de avanzar el horizonte. Los archivos de resultados WSL no se inspeccionaron directamente en esta auditoría.

> **26-11 UTC / 25-11 local — lote 12 verificado (7b3ed1ff4):** candidato de geometría sincronizada compiló y completó 4/4 variantes, 75/75 pasos a 5 μs (dt fijo 1/.5/.25/.125 μs, 5/10/20/40 pasos), todas las auditorías finales acopladas aprobadas. Lote FS_C08_BATCH_20261126T032157Z_1a7731a8, réplica 20261126T042933Z_0c0d778e con mismas métricas reportadas, no sumar dos veces; biblioteca SHA256 2b47f54fec6e429b6e7484c4440de718eca8d7611c2b90d1f938838faab82887. K=83.761 GPa provisional, tolerancia 1e-12. Umax=75.278332/65.608821/36.642851/12.822502 m/s; pMax=207.815914/176.681719/141.862471/115.526940 kPa; L1=5.7046e-9/2.3342e-8/2.6350e-8/1.0925e-7. No independencia temporal, no validación de contracción, no energía global CHT aceptada. Acumulado 501/757 pasos, 36/48 variantes únicas según registro anterior; no porcentaje de tesis. [Historia integrada](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md). Evidencia: consola WSL aportada por investigador, no disco inspeccionado.

# FS-C08 — Primer núcleo conservativo líquido–sólido–gas

> **24-11-2026 — AVANCE OPERATIVO REAL:** [nuevo workflow de compilación física Foundation14](../../.github/workflows/fs-c08-native-cfd-build.yml), no otro test sintético; auditoría de energía por las fronteras (advección y calor hacia la arena) en [solver nativo](coupled_solver/native/README.md), con etiqueta explícita de **balance parcial** hasta integrar trabajo de presión/energía cinética y gas. Reparado el preparador que tenía regex inválidas para seleccionar equilibrio/cinética. **No hay confirmación de build, CFD ni rechupe real.**


> **24-11-2026 — FS-C08: ENERGÍA POR FASE Y CONDUCCIÓN POR FASE EN EL SOLVER REAL.** El predictor térmico [nativo](coupled_solver/native/README.md) ya está reformulado en código como inventario conservativo de energías internas de líquido, sólido y gas; integra Cv_l(T)/Cv_s(T) de fuentes materiales, coloca calor latente solo en u_l(Tref)-u_s(Tref), transporta energía líquida/gaseosa por caras FV y retiene conducción CHT y trabajo de presión. Además corrige las conductividades moleculares k_l(T)/k_s(T) en celdas y superficies con molde. Hay campos de energía J/m³ y flujos energéticos frontera W, y se sincroniza el gas tras el corrector de presión. **CÓDIGO EN GITHUB, NO COMPILADO en Foundation14 WSL, NO CFD ejecutada ni balances gas/energía o rechupe validados.** No volver a pedir pruebas shadow.


> **AVANCE REAL DE ECUACIONES — 24-11-2026:** el [nuevo módulo CFD](coupled_solver/native/README.md) ahora ordena advección líquida → fuente Γ exactamente conservativa, reinicia cada corrector PIMPLE desde `oldTime` para evitar dobles conversiones, traslada los balances a `postSolve`, rechaza reinicios parciales, obliga a un EOS metálico coherente (incompresible respecto a presión, ρ_l(T)/ρ_s(T)) y recupera [Darcy de zona pastosa dentro de momento](coupled_solver/native/fsC08MushyMomentum.C). **El cierre de solidificación ya no usa un factor por Δt**: se elige equilibrio de fracción sólida por masa o cinética física con `tauPhaseChangeT(T)`; todas las propiedades, Cu y q requieren procedencia. **Aún NO está compilado con `wmake` ni validado como CFD de contracción.** Persisten pendientes el cierre exacto de entalpía/gas y la alimentación metalúrgica. No repetir las pruebas shadow/lectura.


> **ACTUALIZACIÓN DE IMPLEMENTACIÓN 24-11-2026 — Código de SOLVER CFD real (sin corrida todavía).** Se añadieron [módulo nativo fsC08ConservativeVoF](coupled_solver/native/README.md) y [preparador de caso aislado](../../analysis_tools/stage_fs_c08_coupled.py): ecuaciones FV de masa líquido/sólido con Γ(T), propiedades diferenciadas ρ(T) exigidas, presión PIMPLE con densidad efectiva del metal, energía con una fuente latente ΓL y diagnóstico del flujo de metal por fronteras. En el documento de arquitectura, las rutas relativas del módulo se encuentran en `native/README.md` y el preparador en `../../../analysis_tools/stage_fs_c08_coupled.py`. **NO fue compilado con wmake en WSL, NO se usaron datos reales de JMatPro, NO se validó cierre entálpico estricto/EOS/feeding/rechupe.** Lo anterior que dice código de solver no implementado describe la fase histórica antes de estos commits; revisar [STATUS.json](STATUS.json) para límites actuales. **Los PASS sintéticos y shadow ya están cerrados.**


> **ESTADO VIGENTE 24-11-2026 — NO MÁS COMANDOS DE PRUEBAS SINTÉTICAS.** El investigador completó `FS_C08_NATIVE_GAMMA_FV_SHADOW_PASS__SYNTHETIC_NO_CFD` sobre malla real Foundation14; ese resultado se registra como infraestructura numérica, **NO** contracción simulada ni validación de hierro. La ruta de lectura + shadow queda CERRADA. **Prioridad única: [implementación de solver físico con continuidad de metal líquido/sólido/gas, densidades distintas, presión, VOF y energía](coupled_solver/FS_C08_CAMBIO_DE_RUMBO_SOLVER_FISICO_20261124_ES.md)**. El documento contiene las ecuaciones y los archivos nativos Foundation14 localizados. **El solver acoplado aún NO está implementado**; no presentar los bloques históricos de comandos de abajo como pasos siguientes.



> **24-11-2026 — NUEVO AVANCE CON Γ NO NULA:** después del hito de lectura nativa OpenFOAM14 con PASS en WSL, se incorporó una segunda utilidad [fsC08NativeShadowStep](native_openfoam/shadow_step/README.md) que usa el **fvMesh real de FS-C07** (volumen, owner, neighbour) y, **solo en memoria**, aplica un paso transitorio explícito de **tres masas conservativas** con fuentes opuestas ±Γ no nulas, flujos internos de las tres fases y entalpía con calor latente una sola vez. La fixture es enteramente **SYNTHETIC_ONLY_NOT_JMATPRO** y las condiciones iniciales son artificiales: se usa la malla real pero **NO los campos reales como estado físico nuevo**. El [núcleo C++17 multi-celda](native_cpp/ConservativePhaseNetwork.H) compiló y pasó en el entorno Linux del asistente; el **nuevo wmake Foundation14 continúa pendiente de prueba en WSL**. No se implementa presión, velocidad, CFD-VOF, alimentación ni contracción física.
>
> **Próxima ejecución, sobre el worktree FS-C08 existente:** 
>
>     cd ~/OpenFOAM/FS_C08_WORKTREE
>     git fetch origin research/fs-c08-conservative-phase-mass-20261123
>     git switch --detach FETCH_HEAD
>     python3 -B analysis_tools/run_fs_c08_native_shadow.py --case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
>
> El nuevo comando [run_fs_c08_native_shadow.py](../../analysis_tools/run_fs_c08_native_shadow.py) crea un reporte independiente en FS_C08_DIAGNOSTICS, exige 3 flujos de fase y Γ local no nula, comprueba balances de metal/gas/entalpía y conserva SHA-256 de los seis archivos FS-C07. Solo imprimirá **FS_C08_NATIVE_GAMMA_FV_SHADOW_PASS__SYNTHETIC_NO_CFD** después de compilar, ejecutar y validar cada condición.




> **24-11-2026 — HITO NATIVO WSL CONFIRMADO POR EL INVESTIGADOR.** Al actualizar el worktree a `90117e3b8` y ejecutar `run_fs_c08_native_bridge.py`, la consola confirmó **`FS_C08_NATIVE_FVMESH_READ_ONLY_BRIDGE_PASS__NO_CFD`**. Reporte:
> `~/OpenFOAM/FS_C08_DIAGNOSTICS/FS_C08_NATIVE_FIELD_BRIDGE_20261124T073954Z_1d35c584/FS_C08_NATIVE_BRIDGE_REPORT.json`.
> El retorno PASS del [ejecutor versionado](../../analysis_tools/run_fs_c08_native_bridge.py) solo se alcanza si pasan `wmake`, lectura real de `fvMesh`/`alpha.metal`/`alpha.metal.solid`, paridad con el conjunto FS-C07 de 20 estados y **SHA256 idéntico** antes/después de seis campos originales. La evidencia de esta ejecución consta del **estado de terminal suministrado por el investigador**; el contenido del JSON nativo no fue inspeccionado independientemente desde este entorno.
>
> **LÍMITE:** primer puente de **interoperabilidad/OpenFOAM14, sin ejecutar CFD**, `Γ=0` en las comprobaciones opcionales del kernel. No hay todavía continuidad triple-fase, acoplamiento `p`, `p·dV`, alimentación/porosidad ni predicción de contracción de hierro. No repetir el análisis FS-C07 para justificar física no implementada. Próximo hito: **fuentes `±Γ` conservativas dentro de ecuaciones de transporte reales y enlace con energía y presión**.



> **24-11-2026 — WSL REAL VERIFICADO Y PUENTE OpenFOAM14 PREPARADO.** El investigador ejecutó en Ubuntu/WSL los **18/18 tests Python OK** (0.072 s), compiló con `c++ -std=c++17 -Wall -Wextra -Werror -pedantic` y obtuvo `FS-C08 C++17 ... PASS`. El escenario sintético de equilibrio produjo `m_metal=0.042 kg` constante, `m_solid=0.008049301974720929 kg`, `T=1463.417497649 K`, `Gamma=804.930197472 kg/(m³·s)` y residuo `E=-5.82076609e-11 J`. **Esa evidencia ya es de la laptop, no solo del contenedor del asistente.**
>
> **NUEVO BLOQUE FS-C08 `wmake` — AÚN POR VALIDAR EN WSL:** [puente nativo Foundation14 `fvMesh`→`alpha.metal`/`alpha.metal.solid`→kernel C++17](native_openfoam/README.md). Incluye `Make/files` y `Make/options`, siete pruebas de contrato/paridad, y [un ejecutor único](../../analysis_tools/run_fs_c08_native_bridge.py) con cinco pruebas de orquestación que compila con `wmake`, lee tres tiempos FS-C07, compara las integrales con la evidencia histórica **y comprueba SHA256 de seis campos originales** antes/después. Los logs se preservan en `~/OpenFOAM/FS_C08_DIAGNOSTICS`. **Esto NO vuelve a ejecutar `foamMultiRun`, ni resuelve masa/energía/presión de forma acoplada.**
>
> ```bash
> cd ~/OpenFOAM/FS_C08_WORKTREE
> git fetch origin research/fs-c08-conservative-phase-mass-20261123
> git switch --detach FETCH_HEAD
> python3 -B analysis_tools/run_fs_c08_native_bridge.py \
>   --case ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
> ```
>
> El siguiente hito aún es **solver nativo de masa conservativa no nula con fuentes ±Γ y acoplamiento de presión/energía/interfaz**; ni esta integración de API ni las propiedades sintéticas suplen eso.


**Estado:** implementación ejecutable de **referencia de volúmenes finitos**, probada localmente en el contenedor del asistente (18/18 tests sintéticos). **Todavía NO es un módulo del solver OpenFOAM Foundation14**, NO ha sido compilada con `wmake` en WSL, NO es una corrida de contracción 3D de QuickCup ni fue alimentada con tablas reales JMatPro. Separación explícita de los hitos de código y de la validación física.

**Rama:** `research/fs-c08-conservative-phase-mass-20261123`, creada desde `research/fs-c02-metal-air-vof-20261117`. **FS-C07 y sus campos originales permanecen intactos**. No relanzar el antiguo `foamMultiRun` para validar este prototipo.

## Qué se implementó realmente

[`analysis_tools/fs_c08_conservative_reference.py`](../../analysis_tools/fs_c08_conservative_reference.py) es un paso temporal FV conservativo (dominio arbitrario de celdas con caras internas y flujos por frontera suministrados). Actualiza las **masas físicas** `m_liquid`, `m_solid`, `m_gas`, y no solo una fracción sólida no conservativa:

```text
m_liquid^(n+1) = m_liquid^n − Δt Σ(F_liquid outward)
                 − Δt Vcell Γ
m_solid^(n+1)  = m_solid^n  − Δt Σ(F_solid outward)
                 + Δt Vcell Γ
m_gas^(n+1)    = m_gas^n    − Δt Σ(F_gas outward)
```

`Γ` se expresa en kg/(m³·s), **positivo para líquido→sólido**, negativo para fusión. Se calcula `m_liquid + m_solid` con fuentes opuestas, de modo que la solidificación **no crea ni destruye masa metálica**. Las caras internas transportan flujos opuestos a ambos lados; en caras abiertas se exige temperatura de fase entrante para conservar el flujo entálpico. `Γ` y las velocidades/flujos son *entradas*, no una ley termocinética que ya hayamos calibrado.

`rho_l(T)`, `rho_s(T)`, `cp_l(T)`, `cp_s(T)`, `cp_g(T)` son curvas tabuladas en SI, con interpolación lineal **sin extrapolación fuera de rango**. El salto de entalpía `L` se representa una sola vez como `h_liquid(T)=∫cp_l(T)dT+L`; `h_solid(T)=∫cp_s(T)dT`, y la temperatura se recupera por inversión numérica monotónica del presupuesto de entalpía de la celda. Por tanto, convertir masa líquida en sólida conserva la energía del ledger y puede redistribuir energía latente en sensible **sin añadir una segunda fuente ficticia `ΓL`**.

Volúmenes físicos y cierre geométrico:

```text
V_l = m_l / rho_l(T)
V_s = m_s / rho_s(T)
V_g = Vcell − V_l − V_s
alpha_l = V_l/Vcell ; alpha_s = V_s/Vcell ; alpha_g = V_g/Vcell

ΔV_metal|Γ,ρ≈const = Δt Vcell Γ (1/rho_s − 1/rho_l)
```

`rho_s > rho_l` da contracción del volumen metálico por conversión a masa fija; `rho_s < rho_l` expansión. Para densidades dependientes de T, el programa reporta por separado el **cambio geométrico total** (incluye efecto térmico y transporte) y la estimación de conversión a temperatura inicial, sin confundir ambas. Rechaza masas negativas, volumen metálico superior al volumen disponible, propiedades no finitas, temperaturas fuera de tabla, influjos sin entalpía definida, fuente excesiva, y gas atrapado en volumen nulo.

Se calcula además la presión idealizada `p_g=m_g R_g T/V_g` como **diagnóstico de celda a volumen fijo**. **NO se resuelve presión de la mezcla, ecuación de momento, trabajo mecánico `p,dV`, movimiento de interfaz ni alimentación**. El cierre de entalpía implementado es **algebraico** del volumen de control; gas ideal + `cp_g` no constituye por sí solo el cierre termo-mecánico total. Por eso los resultados dicen `pressure_velocity_and_interface_not_solved=true` y `physical_3d_shrinkage_validated=false`.

### Prueba reproducible (no CFD)

```bash
# Usar la rama FS-C08 en un worktree propio para no mover FS-C07
cd ~/OpenFOAM/MasterProject
git fetch origin research/fs-c08-conservative-phase-mass-20261123
git worktree add --detach ~/OpenFOAM/FS_C08_WORKTREE FETCH_HEAD

cd ~/OpenFOAM/FS_C08_WORKTREE
python3 -B -m unittest discover -s analysis_tools -p 'test_fs_c08_conservative_reference.py' -v
python3 -B analysis_tools/fs_c08_conservative_reference.py \
  freesurface/FS-C08_conservative_phase_mass/fixtures/SYNTHETIC_TWO_CELL_REFERENCE.json
```

La configuración de ejemplo está marcada **`purpose=SYNTHETIC_TEST_ONLY`**; `rho_l=7000`, `rho_s=7300 kg/m³`, `L=200000 J/kg` y `Γ=[120,80] kg/(m³·s)` son **números arbitrarios de prueba, NO propiedades de tu hierro, NINGÚN dato JMatPro ni coeficientes físicos validados**. La salida debe preservar los límites `physical_3d_shrinkage_validated=false`, `openfoam_14_solver_executed=false`.

**Ejecución real en el contenedor del asistente (2026-11-23):** `python3 -m unittest discover` informó 18 pruebas, todas `OK`, duración ≈0.03 s. La ejecución del escenario sintético con CLI produjo balances relativos a errores de punto flotante:

```text
initial metal mass = 0.042 kg
final metal mass   = 0.042 kg
liquid → solid     = 0.0002 kg
metal mass residual= 0.0 kg
enthalpy residual  ≈ 2.91e-12 J
ΔV_metal           = −1.1741683e-9 m³  (escenario sintético)
```

Los números anteriores son resultados de **prueba de software**, no evidencia de colada real ni contracción QuickCup.

## Segundo modo implementado: equilibrio térmico con Γ implícita

Además del ledger con fuentes y flujos prescritos, el núcleo FV contiene **`LinearMushyMassClosure`** y **`solve_closed_cell_mushy_equilibrium`**: para **una celda cerrada sin advección** se determina simultáneamente `T`, `m_s` y `Γ=(m_s^(n+1)-m_s^n)/(V Δt)` a partir de un presupuesto de entalpía y un modelo explícito de fracción sólida **por masa**:

```text
f_s(T) = 1                       si T <= T_solidus
       = (T_liquidus - T) / (T_liquidus - T_solidus)
                                 si T_solidus < T < T_liquidus
       = 0                       si T >= T_liquidus

E(T,f_s) = m_metal [(1-f_s) h_l(T) + f_s h_s(T)] + m_g h_g(T)
E(T^(n+1), f_s^(n+1)) = E^n + Q Δt
Γ = (m_s^(n+1)-m_s^n) / (V Δt)
```

No se adiciona `ΓL` otra vez: `h_l` **ya incorpora `L`**. El método revisa monotonicidad energética, rechaza solidus/liquidus fuera de tablas y limita el uso del modelo a una celda sin transporte (todavía no ofrece el cierre discreto de energía de la solución CFD con advección, presión y trabajo mecánico).

**ATENCIÓN:** la interpolación lineal `f_s(T)` es una **ley artificial para pruebas**, no la ruta de austenita proeutéctica, grafito/ledeburita ni un diagrama termodinámico calibrado para tus ocho composiciones CE/S. El ejemplo no debe describirse como solidificación real de hierro, aunque su contabilidad de masa y entalpía es conservativa.

```bash
cd ~/OpenFOAM/FS_C08_WORKTREE
python3 -B analysis_tools/fs_c08_conservative_reference.py \
  --mode closed-cell-mushy-equilibrium \
  freesurface/FS-C08_conservative_phase_mass/fixtures/SYNTHETIC_ONE_CELL_MUSHY_EQUILIBRIUM.json
```

Resultados **verificados localmente en escenario sintético** con calor extraído `Q=-3000 W` por 1 s, y valores totalmente ilustrativos:

```text
m_metal inicial = 0.042 kg; m_metal final = 0.042 kg
m_solid final = 0.008049301974720929 kg
T_final = 1463.4174976491418 K
f_s (de masa metálica) = 0.1916500470  [19.165 %, NO valor de hierro real]
Γ inferida = 804.9301974720928 kg/(m3 s)   [synthetic only]
E_final - E_target = -5.82077e-11 J
ΔV_metal = -4.72561759768e-8 m³  [synthetic only, ≈ -0.0472562 mm³]
```

También se comprobaron en **18 tests sintéticos locales** inversión adiabática del proceso, **refusión** con `Γ<0`, expansión por `ρ_s<ρ_l`, dos celdas con caras internas, fronteras abiertas, propiedades `ρ(T),cp(T)` y bloqueos de entradas inválidas. El **workflow GitHub Actions** los ejecutará en la rama nueva, pero el estado de CI aún debe verificarse; sin `wmake` ni `foamMultiRun` para FS-C08.

## Núcleo C++17 probado: transición hacia implementación nativa

Se añadieron [`native_cpp/ConservativePhaseExchange.H`](native_cpp/ConservativePhaseExchange.H) y [su programa de pruebas](native_cpp/test_ConservativePhaseExchange.C). Es **C++17 compilable sin dependencias externas** que recibe masas por fase, densidades, volumen de control, `Γ`, flujos salientes y `Δt`, y produce `m_l,m_s,m_g`, volumen líquido, sólido y gas, `ΔV_metal` y residuo de masa:

```bash
cd ~/OpenFOAM/FS_C08_WORKTREE
c++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic \
    -o /tmp/fs_c08_cpp_exchange_test \
    freesurface/FS-C08_conservative_phase_mass/native_cpp/test_ConservativePhaseExchange.C
/tmp/fs_c08_cpp_exchange_test
```

**Validación real hecha en el contenedor Linux del asistente:** el compilador `g++ 14.2.0` emitió un binario y el test imprimió `PASS (synthetic only, NOT OpenFOAM CFD)`. Comprueba conservación local/global de metal bajo conversión, fusionar de nuevo el sólido, flujo entre dos celdas, flujo saliente al exterior, expansión cuando `ρ_s<ρ_l` y bloqueos de estados inválidos. El workflow FS-C08 vuelve a compilar y probarlo en CI; **CI y WSL todavía no comprobados**.

El núcleo C++ deliberadamente **NO** incluye presión, temperatura ni energía: esas partes existen en la versión de referencia Python y hay que integrarlas en una sola formulación nativa de `compressibleVoF` con `fvModel` y continuidad propia antes de una corrida real. El nombre del directorio `native_cpp` indica el lenguaje, **no un ejecutable OpenFOAM certificado**. No se proporciona `Make/files`/`Make/options` para fingir que ya puede compilarse con `wmake`.

## Bloques pendientes: paso de ledger a CFD Foundation14

| Hito | Estado |
|---|---|
| Ledger por celda de `m_l/m_s/m_g` y fuentes `±Γ` | **IMPLEMENTADO + 18 pruebas Python locales OK; kernel C++17 compilado y probado** |
| Transporte entre celdas y flujos abiertos con entalpía | **IMPLEMENTADO en referencia FV** |
| `ρ_l(T),ρ_s(T),cp(T)` tabulados y rechazo de extrapolaciones | **IMPLEMENTADO en referencia FV** |
| Volumen de vacío/gas y EOS idealizada | **DIAGNÓSTICO implementado** |
| Cierre de equilibrio lineal pastoso con `Γ` derivada de entalpía | **IMPLEMENTADO SOLO PARA UNA CELDA SINTÉTICA CERRADA** |
| Flujos `Γ` para hierro real (nucleación, austenita/grafito, composiciones y datos experimentales) | **PENDIENTE** |
| Propiedades por CE/S/JMatPro y trazabilidad de composición | **PENDIENTE: no inventar valores** |
| 3D `compressibleVoF` + nueva ecuación `α_sρ_s` con transporte conservativo | **PENDIENTE: no compilado/integrado** |
| Presión/velocidad/free-surface, `p,dV`, alimentación/porosidad | **PENDIENTE** |
| Acoplamiento energía CHT + calor latente sin doble conteo | **PENDIENTE nativo** |
| Integración de `alphaRhoPhi.metal` por todas las fronteras | **PENDIENTE nativo** |
| Refinamiento malla/Δt, convergencia, curvas QuickCup | **PENDIENTE** |

### Criterio de integración futuro

El `VoFSolidificationMelting` original actualiza `alpha.metal.solid` antes de `alphaPredictor`, mientras el metal VOF puede transportarse después. FS-C07 confirmó en 20/20 estados **cero violaciones `alpha_s>alpha_m+1e-8` en núcleo (alpha_m≥0.5)**, pero 7,692 incidencias en metal residual, y su **gate físico global FAIL**. La nueva versión nativa NO debe limitarse a introducir un `min(alphaSolid,alphaVoF)` tras el transporte: la conversión debe mantener `Γ` cancelando exactamente en continuidad líquido/sólido, sumar las fracciones de volumen hasta `α_a=1-α_l-α_s`, y recuperar presión/interfaz y entalpía coherentemente. Hasta entonces es **prototipo de balances FV, no CFD de contracción**.

Referencia: [FS-C07 gate 20/20](../../docs/granada/FS_C07_GATE_20DE20_VOF_Y_RUTA_MODELO_CONSERVATIVO_20261123_ES.md).
