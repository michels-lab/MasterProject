# Guía de postprocesamiento y agentes científicos — QuickCup / Foundation v14

**Actualización:** 2026-10-08 · **Caso inspeccionado:** C14 (y B14 para paridad de configuración)  
**Tipo de evidencia:** configuración inspeccionada en Git; conclusiones de ejecución física citadas en analysis_results/v14_bc_comparison/summary.md.  
**IMPORTANTE:** la sola existencia de un functionObject no demuestra que se haya ejecutado. Los resultados numéricos deben contrastarse con los archivos generados y logs de cada corrida.

## 1. Arquitectura: de las ecuaciones a los resultados

- **system/controlDict**: foamMultiRun, regiones metal/fluid y mold/solid; C14 inicia 0 s y termina 10 s, dt = 0.001 s sin ajuste automático, estados volumétricos cada 100 pasos, equivalentes nominalmente a 0.1 s.
- **system/functions**: temperatureProbe registra cada paso de tiempo el centro metal (0.02,0.02,0.005) m; topFlow registra U y phi *cara por cara* en metalTop en writeTime.
- **#include researchDiagnostics**: define campos de flujo, transferencia de energía, gradientes, cambio de fase y diagnostico de fuerzas en metal.
- **#include lineProfiles**: muestrea 80 puntos cada uno en y=10,20,30 mm y x=20 mm. z=5 mm; interpolación cellPoint. Un perfil no es un campo 3D completo.
- **system/momentumPostProcessing**: reduce campos de fuerzas/cambio de fase ya escritos a medias, máximos y perfiles con foamPostProcess. Es postproceso después de la corrida, no un nuevo cálculo CFD.
- **Allrun**: prepara malla, ejecuta foamMultiRun, reconstruye resultados de momentum y foamLog; también ejecuta postproceso espacial de metalTop. NO modificar ni limpiar case automáticamente mediante agentes.
- **postProcessing/**: productos analíticos reducidos; **logs/**: series extraídas del log por foamLog; **directorios de tiempo**: campos del solver y campos de diagnóstico. La persistencia en Git varía de la disponibilidad local.

## 2. Diccionario técnico de diagnósticos

| Campo / objeto | Cómo se obtiene | Unidad y lectura correcta | Limitación / verificación |
|---|---|---|---|
| temperatureProbe: T, U, p_rgh, rho, phaseChangeSource:alpha1 | probes, centro del metal, cada paso | K; m/s; Pa; kg/m³; fracción líquida adimensional | Solo el punto central, no el promedio del dominio. |
| topFlow (U,phi) | surfaceFieldValue con operation none y writeFields true en metalTop | U m/s; phi (kg/s por cara en configuración del solver) | Verificar número de caras, orientación, valores y su tiempo. NO confundir sum(phi)=0 con impermeabilidad local. |
| metalTopPhiSum | surfaceFieldValue sum(phi) | kg/s neto por tapa | Flujos positivos/negativos pueden cancelarse; complementar topFlow y sum(abs(phi)). |
| metalTopEnergyPower | suma por tapa de energyAdvectiveFlux, heatFlux y energyFlux, **como columnas separadas** | W | **No sumar esas tres columnas entre sí**: energyFlux ya suma advección y flujo térmico. |
| metalMoldEnergyPower / metalBoundaryEnergyPower | sumas por metal_to_mold y bordes relevantes | W | Revisar orientación de normales/signo; no contar dos veces metal/mold. |
| energyAdvectiveFlux | fvc::flux(alphaRhoPhi,hs) en solver Foundation v14; aquí metal monofásico | W/cara, transporte convectivo de entalpía sensible | No es radiación ni conducción; detectar advección a través de tapa. |
| heatFlux | flujo térmico de termofísica multiplicado por área | W/cara | Transferencia térmica sin flujo másico es posible. |
| energyFlux | energyAdvectiveFlux + heatFlux | W/cara | No tratar como tercer mecanismo energético independiente. |
| metalSensibleEnthalpy | volIntegrate(h) ponderado por rho | J | Entalpía **sensible**, no energía total incluyendo latente. |
| metalMeanLiquidFraction | volAverage(phaseChangeSource:alpha1) | 0–1 | Un cambio en el promedio no describe un punto localizado. |
| vorticityField / flowTopology | vorticity y flowType de U | 1/s (vorticidad); flowType índice adimensional | flowType clasifica topología local, no certifica una corriente ni la causa de convección. |
| gradT, magGradT | grad(T) y módulo | K/m | No equivale a flujo de calor sin conductividad/convención. |
| gradRho, magGradRho | grad(rho) y módulo | kg/m⁴ | Para C con rhoConst debe ser cercano a 0; B es otra formulación de flotación. |
| dTdt; coolingRate | ddt(T) en runtime; coolingRate=-dTdt | K/s | Enfriamiento positivo corresponde a dTdt negativo; requiere historia temporal de ejecución. |
| dAlphaLdt; solidificationRate | ddt(alphaL); solidificationRate=-dAlphaLdt | 1/s | Positivo: disminuye alphaL (solidificación). Negativo: aumento local alphaL (refusión). |
| latentHeatRateVol | rho * L * solidificationRate | W/m³ | Signo positivo libera latente; negativo absorbe. L se define también en fvModels; comparar valores para evitar desincronización. |
| metalLatentHeatPower | integración volumétrica de latentHeatRateVol | W | No equiparar a cambio global de entalpía sensible. |
| CoCell; metalMaxCourant | función CourantNo y max de región metal | adimensional | Una Co pequeña no prueba conservación ni precisión absoluta. |
| momentumMean / momentumMax | volFieldValue sobre campos de fase y momentum guardados | según campo | Requiere campos volumétricos disponibles; no supone recalcularlos retrospectivamente. |

## 3. Diagnóstico de momentum: código C++ propio, no un solver nuevo

El objeto **solidificationMeltingMomentumDiagnostics** usa type coded y codeWrite en system/researchDiagnostics. Lee U, T, rho, p_rgh, g y alphaL, además de Cu, q, beta, rhoRef, Tsol, Tliq y alpha1e de constant/metal/fvModels.

Formulaciones presentes en el código del caso:

- phaseChangeSolidFraction = 1 - alphaL.
- phaseChangeDarcyCoeff = Cu (1-alphaL)^2 / (alphaL^3+q), con dimensión 1/s.
- phaseChangeDarcySp = -phaseChangeDarcyCoeff (coeficiente implícito con signo).
- phaseChangeDarcyAcceleration = -phaseChangeDarcyCoeff * U, m/s². Es escala de desaceleración reconstruida para análisis.
- phaseChangeModelDeltaT = T - max[Tsol, Tsol+(Tliq-Tsol)(alphaL-alpha1e)/(1-alpha1e)].
- phaseChangeBuoyancyAcceleration = g*beta*phaseChangeModelDeltaT, m/s², fuente explícita de la formulación C.
- phaseChangeBuoyancySu = rhoRef*phaseChangeBuoyancyAcceleration, en unidades volumétricas de fuerza.
- pRghAcceleration = -grad(p_rgh)/rho, m/s², componente diagnóstica; no equivale a la aceleración total.
- magPhaseChangeDarcyAcceleration, magPhaseChangeBuoyancyAcceleration y magPRghAcceleration son magnitudes no negativas.
- phaseChangeDragToBuoyancy y phaseChangeDragToPressure dividen magnitudes de aceleración usando un piso numérico SMALL; **grandes cocientes con denominador casi nulo requieren revisar términos absolutos antes de extraer física**.

Estos campos se escriben a los tiempos de escritura del caso. No son mediciones experimentales ni sustituyen un cierre de balances. La variable alpha1e=0.8 afecta la relación de fase (no asumir una línea fL(T) completa de 0 a 1 entre Tsol/Tliq).

## 4. Qué puede vigilarse en vivo y qué no

**Vigilante local**: analysis_tools/live_run_watch.py lee log.foamMultiRun (tiempo, Courant, continuidad, residuos p_rgh y fallos). Solo vigila cuando se ejecuta un proceso de Python junto al solver; no hay conexión remota automática a tu PC.

**Auditor de configuración GitHub**: analysis_tools/audit_postprocessing_config.py comprueba V14, definiciones y coherencia de L. GitHub Actions quickcup-research-audit.yml intenta ejecutarlo por push, bajo solicitud y diariamente. No instala OpenFOAM, no ejecuta foamMultiRun y no certifica campos físicos.

**Postproceso de campos**: una simulación puede alcanzar End, pero pueden fallar foamLog o foamPostProcess. Revisar ambos logs, conteo de archivos/tiempos y los diagnósticos faltantes. No hacer afirmación global de estado sin revisar.

**V14 ya analizado:** analysis_results/v14_bc_comparison/summary.md concluye tapa impermeable comprobada cara por cara y continuidad acumulada casi nula en C14; B14 tiene inconsistencia de continuidad del modelo variable-density en volumen fijo. Esto no es una validación experimental.

## 5. Protocolo de alarma científica y manuales

1. Confirmar fecha, versión OpenFOAM, fuente exacta, caso y controlDict: saber **cuándo** debía ejecutarse cada objeto.
2. Confirmar escritura de datos y/o error en log; distinguir CONFIG-VERIFIED de RUN-VERIFIED.
3. Comparar output real con ecuación/unidad esperada y balance; pedir evidencia extra si falta.
4. Evaluar diferencias contra baseline y contra un test B/C equivalente.
5. Registrar anomalías y su significado en CASE_NOTES, PROJECT_AUDIT_LOG_ES/EN y VALIDATION_MATRIX_ES/EN, y actualizar el manual de comandos si hay procedimiento reutilizable.
6. Cada función nueva se agrega a **esta guía** con ecuación, unidad, frecuencia, salida, verificación y limitación antes de cerrar MAZAPÁN.

## 6. Referencias rastreables dentro del repositorio

- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/functions
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/controlDict
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/researchDiagnostics
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/lineProfiles
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/momentumPostProcessing
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/Allrun
- analysis_results/v14_bc_comparison/summary.md
- analysis_results/c11_energy2_test/summary.md

El detalle de clases internas de Foundation v14 se debe comprobar contra el código fuente antes de aceptar cambios en sintaxis o comportamientos nuevos. No rellenar lagunas de implementación con suposiciones.
