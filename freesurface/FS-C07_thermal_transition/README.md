# FS-C07 — Transitorio térmico nativo previo al modelo de contracción


> **23-11-2026 — DIAGNÓSTICO DEFINITIVO DE EJECUCIÓN, PENDIENTE DE ACEPTACIÓN DE FASES.** El log nativo de la corrida `...183217Z_72da1bf4` llegó a **`Time=1s` y `End`**, después de **2355 s** de reloj. Hay **10868 directorios de tiempo** y **20 estados con campos VOF/sólido/T completos**. `FS_C07_REPORT.json` quedó `INCOMPLETE` únicamente porque `phase_volume_metrics` rechazó la asignación `alpha.metal.solid <= alpha.metal` en alguna celda bajo la **primera** tolerancia 1e-8: mensaje exacto `FS-C03 STATIC GATE: invalid VOF / absolute-solid phase allocation`. Ese mensaje no se explica solo por el mínimo VOF `-9.766e-46` observado a 0.114 s; se necesitan mínimos/máximos y celda exacta de los 20 estados. **No repetir CFD ni recortar campos hasta medir la gravedad real.** Potencia interfacial al final: `Q_fluid=-7184.75867563 W`, `Q_mold=+7184.84637194 W` (residuo `+0.08769631 W`, `0.00122058 %`). Se detecta `alphaRhoPhi.metal=+7.54288884513e-6 kg/s` en `atmosphereLowerSides` a 1 s, por lo que tampoco hay evidencia de confinamiento metálico perfecto. [Informe fuente y límites científicos](../../docs/granada/FS_C07_NATIVE_1S_SOLVER_COMPLETADO_POSTPROCESO_BLOQUEADO_20261123_ES.md).

> **FORENSIC FS-C07 SIN SOLVER, SOBRE EL MISMO CASO EXISTENTE:**
>
> ```bash
> cd ~/OpenFOAM/FS_C02_WORKTREE
> git fetch origin research/fs-c02-metal-air-vof-20261117
> git switch --detach FETCH_HEAD
> python3 analysis_tools/diagnose_fs_c07_phase_allocation.py --compact \
>   ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
> ```
>
> Este inspector no invoca `foamMultiRun`, no modifica ningún archivo original y cuantifica por cada instante las celdas que violan las restricciones en tolerancias `1e-12`, `1e-10`, `1e-8`. Recupera el primer/peor caso y presenta temperaturas de cribado y hashes de los campos; esas temperaturas **no** validan JMatPro ni contracción.



> **23-11-2026 — CORRIDA PRIMERA TERMINÓ CON EVIDENCIA PRESERVADA; CAUSA NO IDENTIFICADA.** El investigador aportó `FS-C07 EVIDENCE PRESERVED: /home/michel/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4`, pero **no** la línea precedente de error, el JSON `last_error` ni el final del log. Esto **no permite** inferir error del solver: el mismo mensaje se imprime cuando falla la auditoría Python tras un `foamMultiRun` exitoso, cuando el solver devuelve código no cero o ante timeout. Se observó antes `t=0.1142694919 s`, **no** se ha establecido el tiempo final. El investigador aportó `df -h`: `/dev/sdd`, 1007 GB capacidad, 62 GB usados, **895 GB libres, 7 % utilizado**. No hay evidencia de agotamiento de disco. **No relanzar ni editar la corrida antes de recuperar la causa exacta**.

> Para leer la evidencia **sin CFD ni escritura en el caso**, se incorporó [`analysis_tools/inspect_existing_fs_c07.py`](../../analysis_tools/inspect_existing_fs_c07.py):
>
> ```bash
> cd ~/OpenFOAM/FS_C02_WORKTREE
> git fetch origin research/fs-c02-metal-air-vof-20261117
> git switch --detach FETCH_HEAD
> python3 analysis_tools/inspect_existing_fs_c07.py \
>   ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
> ```
>
> Imprime `FS_C07_REPORT.json.status` y `last_error`, los últimos tiempos nativos `Time =`, el mayor directorio físico por valor numérico (no `sort -V`), el último estado que tenga **alpha.metal, alpha.metal.solid y T.metal** y el final del log para diferenciar fallas del solver y de auditoría. Incluye seis pruebas sintéticas de no modificación de archivos (CI aún no verificado). El ejecutor quedó corregido para que en **futuros** fallos imprima nuevamente `ROOT CAUSE` y último tiempo CFD, sin cambiar la corrida guardada.



> **23-11-2026 — FS-C07 PRIMER TRANSITORIO NATIVO CONFIRMADO EN EJECUCIÓN (NO COMPLETADO).** Diagnóstico WSL del investigador: PID `7761` (`foamMultiRun`), CPU `99.6%`, tiempo físico `t=0.1142694919 s` tras 5 min 15 s, `deltaT=8.5072638377e-5 s`, `maxCo=0.0999378380216`, `maxAlphaCo=0.0629947162022`, tamaño del caso `203 MB`. Los monitores nativos de pared aportan `Q_fluid=-13857.4604404 W` y `Q_mold=+13860.3677049 W` (`R_Q=+2.9072645 W`, desajuste relativo `0.0209776 %`). El `alpha.metal` de OpenFOAM continúa acotado salvo un residuo negativo ~`1e-45` sin significado físico. **No hay evidencia de que haya terminado ni de que se haya formado metal sólido**.

> **CAUSA DE SALIDA EXCESIVA INVESTIGADA:** existen carpetas de tiempo por cada paso físico, a pesar de `controlDict.writeControl=adjustableRunTime` y `writeInterval=0.05 s`. El FS-C07 inicialmente heredó los diez `system/functions` FS-C06 con `writeControl timeStep; writeInterval 1`; en Foundation14 `wallHeatFlux::write` invoca `writeLocalObjects::write()`, por lo que esta ruta puede emitir volFields incluso cuando la escritura principal es infrecuente. Se versionó un **nuevo** [`native/system/functions`](native/system/functions) exclusivo de FS-C07: los diez monitores conservan `executeControl` nativo pero cambian a `writeControl writeTime; writeInterval 1` para emitir resultados cuando escribe el caso principal (cada 0.05 s). El stager ahora verifica que el FS-C06 original siga intacto y coloca SOLO en la nueva copia los monitores FS-C07 con menor frecuencia. **Esta solución no afecta al proceso ya activo y todavía debe validarse en WSL**. No hacer `git fetch`/reiniciar otro solver para arreglar a mitad de ejecución.

> Referencias Foundation14: [controles independientes por function object](https://cpp.openfoam.org/v14/namespaceFoam_1_1functionObjects.html), [fuente C++ del wallHeatFlux](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/functionObjects/field/wallHeatFlux/wallHeatFlux.C). Proyección solo orientativa: 203 MB a 0.114 s equivale a ~1.8 GB si el crecimiento fuese lineal; el consumo final puede variar. **Comprobar espacio disponible antes de continuar durante horas** (`df -h "$CASE"`), no eliminar carpetas de un cálculo en marcha.



> **23-11-2026 — PRIMER INTENTO NATIVO INICIADO POR INVESTIGADOR, RESULTADO AÚN DESCONOCIDO.** `FS_C07_THERMAL_20261123T183217Z_72da1bf4` mostró `FS-C07 starting native 1s thermal screening (not shrinkage)...` y quedó sin salida visible. **No afirmar congelamiento ni finalización**: el ejecutor anterior enviaba toda la salida de `foamMultiRun` a `log.FS_C07_foamMultiRun` y mantenía bloqueado el terminal hasta el final (o su timeout). La cota `maxDeltaT=1e-4 s` exige al menos **10,000 intervalos** para `endTime=1s` si se llega al paso máximo; Courant puede imponer muchos más. El nuevo ejecutor (commit posterior al intento ya lanzado) muestra cada 15 s el tiempo `Time =` nativo, el tamaño del log y el tiempo de pared; conserva las salidas y trata Ctrl+C/timeout. **No afecta ni interrumpe automáticamente al solver ya en ejecución**.

> **DIAGNÓSTICO DE SOLO LECTURA SOBRE ESA CORRIDA (en otra terminal WSL):**
>
> ```bash
> CASE="$HOME/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4"
> ps -eo pid,etime,pcpu,pmem,stat,args | grep -E '[f]oamMultiRun|[f]oamRun'
> ls -lh "$CASE/log.FS_C07_foamMultiRun"
> tail -n 35 "$CASE/log.FS_C07_foamMultiRun"
> find "$CASE" -maxdepth 1 -type d -printf '%f\n' | sort -V | tail -n 12
> ```
>
> No iniciar un segundo proceso para el mismo caso; no destruir ni reemplazar archivos. Si se confirma CPU a cero, `Time` congelado o fallos repetidos, interrumpir desde la terminal original con Ctrl+C para conservar el caso y revisar el log. Si `Time` y CPU avanzan, el cálculo está funcionando, aunque puede ser costoso. No etiquetar FS-C07 como validado hasta revisar campos de sólido, liquidus y diez monitores.


**Estado (23-11-2026): CÓDIGO PREPARADO. No ejecutado todavía en WSL ni aprobado por CI.**
Esta etapa implementa **un caso OpenFOAM Foundation 14 real** que deja de
limitarse a los `2×1e-7 s` de arranque de FS-C06 y desarrolla el enfriamiento
de metal–aire (`fluid/compressibleVoF`) y arena (`mold/solid`) con la misma
`VoFSolidificationMelting` (entalpía y amortiguamiento Darcy) y los
**diez monitores nativos comprobados**. **No implementa contracción
volumétrica, alimentación, densidades distintas sólido/líquido ni efectos
de grafitización; tampoco atribuye datos JMatPro.**

## Procedencia y aislamiento

**Fuente aceptada real:**
`~/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091`.

El preparador `analysis_tools/stage_fs_c07_native.py` verifica:
- informe `FS_C06_REPORT.json` con ejecución nativa de dos pasos y campo sólido;
- malla y archivos iniciales `0/fluid`, `0/mold`;
- `constant/fluid/fvModels` idéntico al diccionario FS-C06 versionado;
- `system/functions` idéntico a la instrumentación aceptada;
- 10 archivos de función objeto reales (`.dat`) en `postProcessing`, bajo
  cualquier subcarpeta de región;
- ningún tiempo previo adicional o enlace simbólico que comprometa la copia.

Clona a una carpeta nueva `~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_...`.
**Nunca elimina, sobrescribe ni reanuda** el caso FS-C06 de origen. En la
copia solamente, retira los antiguos tiempos 1e-7 y 2e-7 y sus
`postProcessing`, preserva `0` y las mallas, conserva el reporte original
como `FS_C06_PARENT_REPORT.json`, instala el `controlDict` nuevo y
la instrumentación nativa sin transformarla, y escribe
`FS_C07_REPORT.json` con hashes de procedencia.

## Control nativo preparado

| Parámetro | Valor de pantalla FS-C07 | Interpretación |
|---|---:|---|
| `endTime` | 1 s | Horizonte de enfriamiento **a probar**, no garantía de cruzar liquidus |
| `deltaT` inicial | 1e-7 s | Conserva arranque prudente |
| `maxDeltaT` | 1e-4 s | Cota superior, no paso fijo |
| `maxCo`, `maxAlphaCo` | 0.1 | Control de advección/interfaz |
| `writeControl` | `adjustableRunTime` | Guardar campos físicos comparables |
| `writeInterval` | 0.05 s | Hasta ~20 snapshots si el solver completa 1 s |
| `purgeWrite` | 0 | No destruye evidencia anterior |
| `system/functions` | 10 function objects FS-C06 | Inventario metal/sólido/rho, masa atmósfera, flujos y calor en arena |

Los valores de C14 `Tsol=1423 K`, `Tliq=1473 K`, `L=228600 J/kg`
y la función de fracción sólida continúan siendo **parámetros de cribado**
heredados, no propiedades aceptadas de las ocho fundiciones de la tesis.
Temperaturas y fracciones se leen de campos nativos `T.metal`,
`alpha.metal`, `alpha.metal.solid`, nunca de un ajuste predictivo inventado.
El diagnóstico distingue la fracción sólida **absoluta por celda** de la
fracción condicional respecto al metal.

### Preparar solamente (sin CFD)

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
git fetch origin research/fs-c02-metal-air-vof-20261117
git switch --detach FETCH_HEAD
python3 analysis_tools/stage_fs_c07_native.py \
  --source ~/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091
```

### Correr un transitorio real Foundation 14 en otra copia

Con el entorno OpenFOAM 14 cargado:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/stage_fs_c07_native.py --native --timeout-minutes 120 \
  --source ~/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091
```

`--native` crea **su propia copia nueva**; nunca corre el caso preparado
previamente, por diseño. La corrida está sujeta a límite de tiempo de reloj
de 120 min (configurable 1–240) y preserva su directorio/log si falla,
se agota el tiempo o no cruza el liquidus. **No se promete que complete 1 s,
cruce la temperatura crítica o forme sólido**: el reporte debe dar
`liquidus_crossing_observed`, `positive_solid_fraction_observed` desde
campos reales. Si no hay solidificación, queda como pantalla térmica
insuficiente, no un resultado aceptado.

## Física no resuelta aquí: derivación obligatoria del modelo de contracción

En la descripción con metal líquido `l`, metal sólido `s` y aire `a`,
las fracciones ocupadas cumplen:
`alpha_l + alpha_s + alpha_a = 1`;
`alpha_m = alpha_l + alpha_s`.
Como `alpha.metal.solid` es una **fracción volumétrica absoluta** dentro
de la celda, `alpha_l=alpha.metal-alpha.metal.solid` y la densidad metálica
efectiva sería `rho_m=(alpha_l*rho_l+alpha_s*rho_s)/alpha_m` cuando
`alpha_m>0`. No usar aquí la fórmula armónica que corresponde a
fracciones másicas (ni transformar sólidos en densidad de aire).

Para una cinética de solidificación `Gamma` en kg/(m³·s), las dos
ecuaciones conservativas mínimas deben cancelarse al sumarlas:

```text
d(alpha_l rho_l)/dt + div(alpha_l rho_l u_l) = -Gamma
d(alpha_s rho_s)/dt + div(alpha_s rho_s u_s) = +Gamma
----------------------------------------------------------
d(rho_m alpha_m)/dt + div(alpha_l rho_l u_l
                           + alpha_s rho_s u_s) = 0
```

La variación volumétrica idealizada debida al intercambio de fases
local satisface `S_V = Gamma*(1/rho_s - 1/rho_l)` (1/s), **antes** de
agregar dilataciones térmicas, desplazamiento del sólido y condiciones
de alimentación. Con `rho_s > rho_l` produce una demanda volumétrica
negativa; la grafitización puede reducirla o invertir el signo. **No
introducir `massSource` neto negativo para fabricar contracción**:
eso extrae metal y rompe el propósito conservativo.

Revisión precisa del código de OpenFOAM Foundation 14 (consultado el
23-11-2026):

- `compressibleVoF::prePredictor` construye `alphaRhoPhi1`,
  `alphaRhoPhi2`, `rhoPhi`, `contErr1` y `contErr2`.
- `compressibleVoF::alphaSuSp` trata las fuentes de fase y dilatación.
- `compressibleVoF::pressureCorrector` resuelve la presión usando
  `rho1`, `rho2`, `psi1`, `psi2`, y reajusta `phi` y densidades.
- `compressibleVoF::thermophysicalPredictor` transporta entalpía con
  `alphaRhoPhi1/2`, `contErr1/2` y fuentes `fvModels`.
- `VoFSolidificationMelting::correct()` cambia la fracción sólida
  según `T.metal`, con relajación, pero no es una ecuación conservativa
  de masa sólida transportada. Su `addSup` actúa en energía y momento.

Es necesario un desarrollo nativo específico que vincule **las cuatro
ecuaciones** (masa líquida, masa sólida, VOF/aire y energía) con la presión.
No basta con sustituir `rho` en un `postProcessing` ni con calibrar
`Cu`, `relax` o `q`. Datos faltantes para las composiciones reales:
`rho_l(T,composición)`, `rho_s(T,composición,fracción de grafito)`,
`f_s(T)` aceptada, entalpía/latente y su procedencia JMatPro/laboratorio.

## Puertas de aceptación

1. **FS-C07 térmico**: solver real completo; liquidus cruzado en celdas de
   metal y `alpha.metal.solid>0` en al menos un volumen metálico; perfiles
   temporales con paso/malla y flujo `Q` revisados. Si no, NO PASS.
2. **FS-C07 conservativo (pendiente implementar)**: transporte positivo de
   masa por fase, compensación `Gamma`, estado del sólido y alimentación,
   masa metálica conservada con sus flujos abiertos y nueva densidad nativa.
3. **FS-C07 VOF**: superficie libre que responda al signo y magnitud del
   cambio físico de volumen; sin extracción ficticia de masa.
4. **Validación científica**: convergencia, energía sensible+latente,
   condiciones de arena y curvas experimentales QuickCup por composición.

No mezclar con `main`, FS-C05, FS-C06, ni la línea 3D-A/B.
Fuentes OpenFOAM GPLv3: https://github.com/OpenFOAM/OpenFOAM-14/tree/master/applications/modules/compressibleVoF
