# FS-C07 — Transitorio térmico nativo previo al modelo de contracción

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
