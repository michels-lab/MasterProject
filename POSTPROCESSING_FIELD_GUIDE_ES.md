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

**Revisión posterior al push**: `analysis_tools/audit_pushed_results.py` inspecciona logs, perfiles y resultados ya almacenados en Git. No supervisa ni controla un proceso local.

**Auditor de configuración GitHub**: `analysis_tools/audit_postprocessing_config.py` revisa declaraciones y cobertura de V14. GitHub Actions ejecuta comprobaciones solamente cuando el workflow puede correr; no inicia OpenFOAM ni certifica automáticamente la física.

**Postproceso de campos ya efectuado por el usuario**: una simulación puede alcanzar End, pero pueden fallar foamLog o foamPostProcess. Revisar ambos logs, conteo de archivos/tiempos y los diagnósticos faltantes. No hacer afirmación global de estado sin revisar.

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


## 7. Flujo post-push de los agentes

1. Michel ejecuta OpenFOAM Foundation 14 en su laptop, junto con los postprocesos de su caso y su validación local.
2. Michel hace commit y push de la evidencia elegida: logs, sondas, perfiles, flujos y notas.
3. GitHub Actions intenta ejecutar `audit_pushed_results.py` y `audit_postprocessing_config.py` sobre los archivos del commit. **No lanza simulaciones ni modifica casos**.
4. Los perfiles especializados de agentes interpretan la evidencia al ser invocados; la automatización Python genera un informe reproducible, pero no ejecuta por sí sola agentes LLM.
5. MAZAPÁN actualiza CASE_NOTES, CASE_VARIANT, el inventario, los informes, las guías/manuales relevantes y las bitácoras ES/EN; no se atribuyen propiedades físicas a datos ausentes.

## 8. Catálogo exhaustivo de functionObjects configurados en C14

Estos son **los 37 nombres declarados** en las cuatro fuentes principales del caso (no todos generan archivos separados; algunos producen campos intermedios). La tabla complementa la descripción de campos anterior. Para una variante distinta, leer sus propios diccionarios; no asumir que usa los mismos objetos.

### system/functions — 2 objetos

| Objeto | Tipo | Función exacta |
|---|---|---|
| temperatureProbe | probes | Muestrea U, T, p_rgh, rho y alphaL en posición central cada timestep; CSV/series bajo temperatureProbe. |
| topFlow | surfaceFieldValue | En writeTime escribe U y phi por cara de metalTop para distinguir penetración local y cancelación neta; NO es suma acumulativa de tiempo. |

### system/researchDiagnostics — 29 objetos

| Objeto | Tipo | Resultado, interpretación y control |
|---|---|---|
| vorticityField | vorticity | Campo vorticity de U [s⁻¹], deriva espacial de velocidades; revisar signo/componente z en perfiles. |
| flowTopology | flowType | Campo adimensional flowType; clasifica cinemática local, no la causa metalúrgica. |
| energyAdvectiveFlux | energyAdvectiveFlux | W/cara de advección de entalpía sensible. |
| heatFlux | heatFlux | W/cara de flujo térmico sin transporte de masa. |
| energyFlux | energyFlux | W/cara, suma de energyAdvectiveFlux y heatFlux; evitar doble conteo. |
| metalTopPhiSum | surfaceFieldValue | Flujo másico neto kg/s sobre metalTop; revisar por cara aparte. |
| metalTopEnergyPower | surfaceFieldValue | Tabla de potencias por metalTop de tres campos relacionados (no se suman entre sí). |
| metalMoldEnergyPower | surfaceFieldValue | Tablas de potencia por interfaz metal-molde; signo de normal según región metal. |
| metalBoundaryEnergyPower | surfaceFieldValue | Suma de potencias por tapa e interfaz con patch set declarado; no equivale a todos los mecanismos del balance global. |
| metalSensibleEnthalpy | volFieldValue | Integral ponderada por rho de h [J]; no incluye automáticamente calor latente. |
| metalMeanLiquidFraction | volFieldValue | Media volumétrica de alphaL; no es punto central. |
| temperatureGradient | grad | Calcula gradT [K/m] a partir de T en el metal. |
| temperatureGradientMagnitude | mag | Calcula magGradT [K/m]; pierde información de dirección. |
| densityGradient | grad | Calcula gradRho [kg/m⁴] a partir de rho. |
| densityGradientMagnitude | mag | Calcula magGradRho [kg/m⁴]; esperar casi 0 si rhoConst. |
| temperatureTimeDerivative | ddt | Calcula dTdt [K/s] en tiempo de solver; no inferir desde único estado. |
| coolingRate | scale | Convierte dTdt en coolingRate=-dTdt [K/s]. |
| liquidFractionTimeDerivative | ddt | Calcula dAlphaLdt [1/s] desde la historia temporal real. |
| solidificationRate | scale | -dAlphaLdt [1/s], positivo solidificación / negativo remelting local. |
| latentHeatField | uniform | Campo latentHeat uniforme con L en J/kg; verificar contra fvModels. |
| latentHeatRateDensity | multiply | Campo latentHeatRateVol = rho*solidificationRate*L [W/m³]. |
| cellCourantNumber | CourantNo | Campo CoCell adimensional, no sustituye residual de presión. |
| metalLatentHeatPower | volFieldValue | Integral espacial latentHeatRateVol [W], potencia latente instantánea. |
| metalMeanCoolingRate | volFieldValue | Promedio de coolingRate [K/s]; puede ocultar puntos que se calientan. |
| metalMeanSolidificationRate | volFieldValue | Promedio de solidificationRate [1/s]; remelting y solidificación pueden compensarse. |
| metalMaxCourant | volFieldValue | Máximo espacial CoCell en metal; es indicador numérico, no sentencia de convergencia. |
| metalMaxThermalGradient | volFieldValue | Máximo espacial magGradT [K/m]; considerar ubicación y estabilidad espacial. |
| metalMaxDensityGradient | volFieldValue | Máximo espacial magGradRho [kg/m⁴]; comparar formulación B/C. |
| solidificationMeltingMomentumDiagnostics | coded | Código C++ que escribe 12 campos de fase, Darcy, aceleraciones y cocientes, explicados en §3. Su compilación/ejecución real debe confirmarse por log y campos. |

### system/lineProfiles — 2 objetos

| Objeto | Tipo | Resultado |
|---|---|---|
| horizontalProfiles | sets | Perfiles de 80 puntos en y=10,20,30 mm a z=5 mm, incluye U, T, p_rgh, rho, alphaL y diagnósticos derivados. |
| verticalProfiles | sets | Perfil de 80 puntos en x=20 mm a z=5 mm; mismas variables para comparación ortogonal. |

### system/momentumPostProcessing — 4 objetos

| Objeto | Tipo | Resultado |
|---|---|---|
| momentumMean | volFieldValue | Medias de fracción sólida, resistencia Darcy, deltaT y magnitudes de aceleración, desde campos guardados. |
| momentumMax | volFieldValue | Máximos y ubicación de los mismos campos; no supone que están activos en la ecuación como una fuente independiente. |
| momentumHorizontalProfiles | sets | Cuatro familias de campos de momentum y fase en líneas y=10/20/30 mm; evalúa dependencias y tiempo disponible. |
| momentumVerticalProfiles | sets | Mismos campos en x=20 mm para comparación vertical. |

**Cuidado metodológico:** algunos nombres designan el objeto que produce otro campo (por ejemplo, temperatureTimeDerivative escribe dTdt). El verificador debe exigir cobertura de nombre y, por separado, comprobar fórmula, unidad, fuente y evidencia de ejecución.
