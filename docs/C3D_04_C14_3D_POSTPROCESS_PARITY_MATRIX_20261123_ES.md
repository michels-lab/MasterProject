# Caso 3D-A C3D-04 — contrato de paridad con el postprocesamiento C14 original

Fecha: 2026-11-23. Estado: ETAPA 07/10 EN PROGRESO. Avance operativo 6/10 = 60 %. CFD real original 10 s completado. Conservación energética, independencia de malla, QuickCup y paridad funcional sin validar.

## Mandato del investigador

El Caso A debe calcular y guardar como mínimo las mismas familias de magnitudes que el 2D C14, y además las integrales y perfiles relevantes para la geometría 3D. No basta con medias T, alpha1 y Courant. La física C14, sus parámetros, la malla aprobada y los resultados numéricos ya existentes son inmutables. No mezclar el Caso B, contracción ni T0 auxiliar.

## Referencia completa de C14

- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/functions
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/researchDiagnostics
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/lineProfiles
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/momentumPostProcessing
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/Allrun
- analysis_tools/topSurfaceFlowPostProcessing
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/logs/
- cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/postProcessing/metal/

## Cobertura obligatoria

| Cálculo C14 | Estado Caso A 3D |
|---|---|
| Campos T metal/arena, alpha1, p_rgh 0..10s | Comprobados en WSL, 101 estados, medias por celda |
| Log Courant, continuidad, residuos h/e/p_rgh | Comprobado; localización temporal de picos preparada |
| Sonda (U,T,p_rgh,rho,alpha1) | PENDIENTE; no se pueden regenerar 10,001 valores originales con solo 101 fotogramas |
| Perfiles horizontales y verticales U,T,p_rgh,rho,alpha1 | PENDIENTE adaptar a interior 3D y validar coordenadas |
| vorticity, flowType, magSqrDevGradU | PENDIENTE native |
| gradT, magGradT, dTdt, coolingRate | PENDIENTE native; tasas medias de 0.1s preparadas |
| gradRho, magGradRho | PENDIENTE native |
| dAlphaLdt, solidificationRate, latentHeatRateVol | PENDIENTE native; inventario/tasa promedio discretos preparados |
| CoCell, máximos de gradientes | PENDIENTE espacial, Courant global del log conocido |
| metalMeanLiquidFraction, metalSensibleEnthalpy, metalLatentHeatPower | PARCIAL: integrales 3D de alpha y estimados de almacenamiento |
| energyAdvectiveFlux, heatFlux, energyFlux | PENDIENTE flujos reales por caras |
| metalTopPhiSum, topFlow, topPhiAbsolute, topPhiNet, topPhiMaximum, topPhiMinimum, topPatchFaceFields, nearTopInternalLine | PENDIENTE mapeo 3D para impermeabilidad cara por cara |
| metalMoldEnergyPower, metalTopEnergyPower, metalBoundaryEnergyPower | PENDIENTE sumas verdaderas de potencia en interfaces y exteriores |
| phaseChangeSolidFraction, phaseChangeDarcyCoeff, phaseChangeModelDeltaT, aceleraciones Darcy/buoyancy/pRgh y ratios | PENDIENTE diagnóstico nativo del modelo C14 exacto |
| momentumMean, momentumMax, momentumHorizontalProfiles, momentumVerticalProfiles | PENDIENTE postprocesado nativo |
| Integrales por volumen de T, alpha, velocidad, presión y energía; pico residual fechado | CÓDIGO NUEVO, aún no corrido sobre WSL |
| Independencia de malla/timestep y comparación QuickCup | PENDIENTES, sin validación científica |

## Primer bloque desarrollado

La herramienta cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/c14_3d_postprocess_parity.py lee el JSON/CSV nativos auditados y las mallas originales de ambas regiones. Calcula el volumen de CADA celda por geometría de caras owner/neighbour y lo comprueba contra el volumen geométrico de frontera. Para 101 estados, estima temperatura media volumétrica metal/arena, fracción líquida/sólida volumétrica, porcentajes de volumen bajo Tliq/Tsol, velocidad media/RMS/máxima, presión media volumétrica y variaciones almacenadas de energía sensible y de inventario latente. Se emplean exclusivamente rho, Cp, Cv, L y temperaturas iniciales del contrato científico original. No se declara cierre de energía. Examina el instante guardado correspondiente al mayor residuo final de h, e y p_rgh.

Salida en carpeta NUEVA:
- C3D04_A_C14_3D_VOLUMETRIC_101_STATES.csv
- C3D04_A_C14_3D_POSTPROCESS_REPORT.json (más inventario SHA-256 exacto de diccionarios C14 originales)

Una única orden WSL posterior desde MasterProject con los cambios integrados, sin nueva CFD:

    python3 cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/c14_3d_postprocess_parity.py

El analizador no invoca foamMultiRun, foamPostProcess, blockMesh o checkMesh. Ante inconsistencia bloquea el cálculo sin alterar insumos ni inventar números.

## Límites científicos y próximos entregables

1. C14 original escribió sondas en cada paso de 0.001 s; la corrida 3D guardó campos cada 0.1 s. Los 10,001 valores de sonda no pueden recuperarse retroactivamente de 101 estados.
2. Coordenadas 2D C14 (x=0.02, y=0.02, z=0.005) no pueden asignarse a ciegas a 3D; verificar dentro de malla con los puntos/celdas reales.
3. Cambios de almacenamiento energético deltaE NO prueban conservación. Falta integrar potencias nativas por superficies externas y acoplamiento metal/arena, corregir orientación de ambas regiones, y contabilizar ecuaciones y fuentes del solver.
4. Aplicar derivadas ddt a fotogramas 0.1s no equivale a resultados del functionObject durante cada paso 0.001s. Etiquetar explícitamente las derivadas de estados guardados.
5. Para paridad completa, ejecutar native foamPostProcess en COPIA MATERIAL aislada del caso final, usar diccionarios originales C14 sin cambios físicos, adaptar solo ubicaciones de muestreo geométricamente verificadas y auditar la salida por objeto. Nunca ejecutar Allrun del C14 sobre el caso real, porque remalla y corre solver.
6. Aún no hay evidencia local WSL de ejecución de este analizador nuevo. El avance operativo permanece 6/10=60%; Hito 7 no se cierra por escribir código.

Este documento es contrato de cobertura, no declaración de cálculo ejecutado ni validación.


## Segundo bloque: postprocesamiento OpenFOAM Foundation14 sobre copia física

Se añadió run_c14_3d_complete_postprocess.py como orquestador integral **preparado, NO EJECUTADO en WSL**. Su diseño:
1. valida contra la auditoría anterior la identidad de 101 estados, SHA del log y bytes intactos del controlDict C14;
2. calcula las integrales volumétricas y deja informe separado;
3. deriva coordenadas de sondas/perfiles mediante centroides geométricos de celdas metálicas REALES, normalizando los tres niveles horizontales a 25/50/75 % de altura para no copiar puntos 2D que pueden estar fuera de la 3D (registra coordenadas verdaderas);
4. crea una COPIA completa independiente del run original, copia los cinco diccionarios de función C14 y el postproceso de superficie, cambiando exclusivamente probeLocations/sets en la copia;
5. ejecuta foamPostProcess para functions, momentum y topSurfaceFlow y después foamLog, sin invocar solver, checkMesh o blockMesh;
6. compara carpetas postProcessing realmente producidas contra la lista de carpetas postProcessing que existen en C14 2D y emite JSON PASS/FAIL por bloque, faltantes y límites de muestreo.

Advertencias de aceptación: los puntos elegidos por centroides garantizan base geométrica real, pero los segmentos entre ellos **NO** garantizan estar enteramente dentro de una geometría cóncava: se requiere comprobar las salidas nativas. Además, campos de fuente de solidificación escritos ex post podrían no reconstruir el mismo resultado de ddt/latente que el functionObject durante la corrida; no asumir equivalencia sin comparación. La existencia de una carpeta por objeto no acredita precisión numérica ni cierre energético.

Cuando la rama esté integrada y CI aprobado, la **única orden** para intentar el análisis íntegro en el entorno real es:

    python3 cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_3d_complete_postprocess.py

El runner llama internamente al cálculo volumétrico, genera copia aislada, intenta todos los postprocesos y guarda logs individuales. Si algún native postprocess falla, NO borra ni sobrescribe el CFD de investigación y reporta el bloque incompleto. El avance sigue 6/10=60 % hasta obtener evidencia de ejecución y revisar los flujos/energía y estabilidad.


## Tercer bloque: balance térmico nativo trazable a C14 (código listo, WSL pendiente)

La herramienta c14_physics/c14_3d_native_energy_closure.py utiliza exactamente las columnas reales publicadas por los objetos originales C14 en:
- metalSensibleEnthalpy: volIntegrate(rho,h), energía sensible integral de metal [J].
- metalLatentHeatPower: volIntegrate(latentHeatRateVol), potencia volumétrica integrada de solidificación [W].
- metalTopEnergyPower, metalMoldEnergyPower y metalBoundaryEnergyPower: sum(energyFlux), sum(heatFlux) y sum(energyAdvectiveFlux), expresadas como potencia de caras [W].
- metalMeanLiquidFraction: volAverage(phaseChangeSource:alpha1), para contraste con integrales de la malla 3D.

Primero se exige que potencia de todas las fronteras metálicas coincida con la suma metalTop + metal_to_mold, aceptando únicamente tolerancia por formato de escritura. Luego se calcula la integral trapezoidal de P_salida y P_latente sobre los estados guardados de 0.1 a 10 s; el t=0 se excluye de la integral porque el functionObject puede registrar flujos iniciales no evaluados. La expresión diagnóstica es:

    residual_J = [H(t)-H(0.1)] + integral(P_energyFlux_out dt) - integral(P_latentRelease dt)

El signo positivo de latentRelease procede de solidificationRate = -dAlphaLdt y latentHeatRateVol = rho * solidificationRate * L de los diccionarios originales. Este residual es una **prueba de coherencia nominal**, no la identidad discretizada exacta del solver ni una validación física de conservación. Falta el balance regional de la arena y la verificación de fuentes y temporalidad nativa. El resultado se reporta sin imponer artificialmente que el residuo sea cero. La regresión se prueba contra los archivos postProcessing REALES archivados del C14 2D.

El ejecutor integral invoca el auditor de energía cuando los objetos nativos han producido sus tablas, conserva todos los logs, declara cualquier ausencia y sigue sin ejecutar CFD. Todo el proceso respeta **etapa 07/10, 6/10=60%** hasta comprobarlo sobre WSL y revisar críticamente el balance.
