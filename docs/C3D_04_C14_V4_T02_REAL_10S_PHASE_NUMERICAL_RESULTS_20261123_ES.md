# Caso 3D-A — C14 original en V4/T02: resultados térmicos, fracción líquida y diagnósticos de 10 s

**Fecha de análisis:** 23 de noviembre de 2026. **Origen exacto:** JSON impreso por el investigador al ejecutar `analyze_existing_c14_3d_results.py` sobre la corrida ya preservada en `/home/michel/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01`. La salida es `/home/michel/OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_ANALYSIS_01`. Se han visto los valores **del resumen publicado por el investigador**, no el archivo completo `C3D04_A_C14_10S_TIME_SERIES.csv` ni los 28 MB del log ni la malla WSL.

**Regla científica:** todo el modelo original 2D C14 — hierro fluido, arena sólida, entalpía, momento, presión, solidificación, temperatura inicial y parámetros — **se mantiene**. Solo dimensionalidad, malla y parches 3D de V4/T02. Ninguna modificación física se justifica a partir de estos resultados sin autorización del investigador.

## Identidad y cobertura del análisis ya ejecutado

| Señal | Evidencia del analizador REAL WSL |
|---|---:|
| Estado | `EXISTING_REAL_V4_T02_C14_10S_FIELDS_AND_LOG_AUDITED_NOT_PHYSICALLY_VALIDATED` |
| Tiempo físico | 10 s |
| Pasos transitorios en log | 10 000 |
| Estados guardados | 101 (t=0 y cada 0.1 s hasta t=10 s) |
| Muestra de Courant metal | 10 000 |
| Registros de continuidad | 60 000 |
| Resoluciones de `h` | 30 000 |
| Resoluciones de `e` | 30 000 |
| Resoluciones de `p_rgh` | 60 000 |
| Selección nativa del modelo C14 `fluid`/`solid`/`solidificationMeltingSource` | true |
| Terminación nativa `End` | true |

## Resultados a t=10 s — **promedios por celda, no ponderados por volumen**

| Campo / umbral | Resultado |
|---|---:|
| T hierro mínimo | 1401.91 K |
| T hierro **promedio por celda** | **1444.7184787946428 K** |
| T hierro máximo | 1471.07 K |
| T arena mínimo | 300.006 K |
| T arena promedio por celda | 531.3307448186529 K |
| T arena máximo | 918.764 K |
| Hierro bajo C14 `Tliq=1473 K` | **8 960/8 960 = 100 % de celdas** |
| Hierro bajo C14 `Tsol=1423 K` | **1 158/8 960 = 12.924107142857142 % de celdas** |
| `phaseChangeSource:alpha1` mínimo | **0.0** |
| `phaseChangeSource:alpha1` medio | **0.8367355017427456** |
| `phaseChangeSource:alpha1` máximo | **0.992311** |
| Celdas con `alpha1<0.999` | **8 960/8 960** |
| `p_rgh` mínimo | 99 999.8 Pa |
| `p_rgh` promedio | 99 999.91190848213 Pa |
| `p_rgh` máximo | 100 000.0 Pa |

**Interpretación respaldada:** entre el estado inicial (`metal T=1500 K`, `alpha1=1` en C14) y t=10 s el metal se enfrió y el campo de fracción líquida dejó de ser uniforme en 1; **hubo avance de solidificación según el modelo**. A t=10 s, todas las celdas estaban por debajo del liquidus original; 1 158 estaban además por debajo del solidus. La fracción líquida media por celda fue 0.8367355; `1 - media(alpha1) = 0.1632644982572544` es el **promedio no ponderado de la fracción no líquida** en las celdas, **NO una fracción sólida de volumen total ni de masa total**. Tampoco establece por sí sola cuál fue el calor latente integrado transferido.

La temperatura promedio del hierro pasó de 1500 K iniciales a 1444.7185 K, diferencia de **−55.2815 K en promedio por celda**. La arena pasó de 300 K a 531.3307 K, diferencia **+231.3307 K por celda**. Los gradientes reales requieren perfiles espaciales y, para energía física, integración por volúmenes y flujos; NO se infiere conservación a partir de estas medias.

## Diagnósticos del log completo

| Diagnóstico | Resultado |
|---|---:|
| Courant máximo **de los 10 000 pasos** | **0.0240415** |
| `maxCo` histórico configurado C14 | 0.25 |
| Courant medio en último paso | 0.00157478 |
| Courant máximo en último paso | 0.00450431 |
| `global` continuidad máxima absoluta registrada | 4.21562 × 10⁻¹⁸ |
| `cumulative` continuidad del último registro | −6.5319 × 10⁻¹⁴ |
| `h` residuo inicial máximo encontrado | 1.0 |
| `h` residuo final máximo encontrado | 0.000265533 |
| `h` último residuo final | 1.69416 × 10⁻¹¹ |
| `e` residuo inicial máximo encontrado | 1.0 |
| `e` residuo final máximo encontrado | 0.0000431133 |
| `e` último residuo final | 6.03586 × 10⁻¹⁰ |
| `p_rgh` residuo inicial máximo encontrado | 0.946686 |
| `p_rgh` residuo final máximo encontrado | **0.00776125** |
| `p_rgh` último residuo final | 5.19776 × 10⁻⁸ |

El Courant máximo **sobre todo el registro** 0.0240415 es inferior al límite configurado 0.25; observar esto es un indicador favorable, pero no prueba convergencia temporal/espacial, exactitud o ausencia de oscilaciones locales. El **máximo residuo final de `p_rgh` llegó a 0.00776125 en algún paso o iteración**; debe localizarse temporalmente y contrastarse con controles numéricos C14. La continuidad `global` y `cumulative` son diagnósticos de la ecuación implementada, **no** equivalentes al cierre termoenergético. No se calculó un balance de energía.

## Declaraciones verificadas y pendientes

**Observación verdadera del modelo, sobre la malla real:** `foamMultiRun` terminó 10 s; se escribieron 101 estados; se obtuvieron T del metal/arena, p_rgh y `alpha1`; el modelo alcanzó temperaturas dentro y por debajo del intervalo `Tsol=1423`, `Tliq=1473` y `alpha1` varió; existe seguimiento de Courant en los 10 000 pasos.

**Aún no demostrado:** (i) temperatura y fracción **ponderadas por volumen o masa**, (ii) flujo térmico de la interfaz y fronteras exteriores, (iii) calor sensible y latente integrados y cierre de energía, (iv) instante **exacto** de primera solidificación (solo disponemos del resumen a t=10 s y el CSV completo quedó en WSL), (v) localización temporal de los máximos de residuales y/o validación de tolerancia, (vi) independencia de malla y de `deltaT`, (vii) concordancia experimental QuickCup.

**Etapa canónica:** hito 06/10 cerrado; **hito 07/10 EN PROGRESO**, 6/10=**60 % de avance operativo**. Aunque ya hay evidencia de cambio de fase para preparar el hito 08, no se marca completo mientras no se documente la secuencia temporal de `alpha1`, análisis de calor latente y Darcy. `CFD_run=true`, `physical_validation=false`, `numerical_accuracy_validated=false`, `grid_independence=false`.

**Siguiente trabajo sin reejecutar CFD:** usar el CSV/JSON existentes en `~/OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_ANALYSIS_01` para reconstruir curvas de enfriamiento, primer estado guardado bajo liquidus y solidus, y evolución de `alpha1`; después auditar conservación usando volúmenes y flujos. Preservar los archivos originales C14 y V4/T02 sin cambios.
