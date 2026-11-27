> **27-11-2026 — cierre de esta revisión documental:** 6/8 combinaciones adaptativas laptop calculadas y publicadas con manifiesto completo; B14-2D sin tope 14275 pasos/200 s, commit e066adf9. Las dos A fallaron (.68/.70 s); no hay caso 2D pendiente de recuperación. 97 ramas indexadas (95 del corte inicial + 2 altas), 3815 commits únicos con cadena de padres completa, 273 archivos documentales inventariados en el corte inicial. No validación física nueva. [Manifiestos](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json) · [Historia e índices](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md). Entradas anteriores históricas.

> **27-11-2026 — Corrección de publicación, segundo corte documental:** campaña laptop 6/8 calculadas, 5/8 con manifiesto completo, 1/8 B14-2D sin tope pendiente, 2/8 A adaptativo fallidas. C14-2D MPI con tope (11029 pasos, 3dbcbee4) y B14-2D MPI con tope (14276 pasos, b02ef4a9) ya están publicados y auditados según sus manifiestos, sin nueva validación física. A 8/10=80% hitos, B 2/7=29%, FS-C08 lote 12 75/75 pasos. [Historia completa](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Manifiestos inspeccionados](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json). Las entradas anteriores quedan como historia.

> **27-11-2026 | Estado vigente integrado:** campaña adaptativa laptop 6/8 combinaciones calculadas, 3/8 publicadas con manifiesto completo, 3/8 pendientes de auditoría de perfiles duplicados, 2/8 A fallidas. C14-2D sin tope es serial, no MPI. A fijo laptop llegó a 200 s; publicación laboratorio no confirmada. FS-C08 lote 12: 4/4 variantes, 75/75 pasos a 5 μs, sin independencia temporal ni validación física. A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29%; 2D histórica 26/26. No porcentaje global de tesis. [Historia y evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md) · [Estado JSON](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json). Las entradas previas conservan su valor histórico.

> **25-11-2026 | ESTADO VIGENTE:** C14 2D de 10 s, 10001 muestras nativas, referencia histórica de solidificación intacta. C14-2D-200s pertenece a campaña fija compacta independiente y variante adaptativa PC; adaptativa último registro recuperado 14 s/1728 pasos, dt=.02 s, cadencia inicial PASS, sin final de 200 s confirmado. Fija laboratorio observada serial en ejecución, sin final confirmado. C14 3DA fijo 200 s reportado completo y 3DB piloto MPI de 3 s no sustituyen resultado 2D. [Registro integrado](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261125_ES.md).

> **24-11-2026 | ESTADO VIGENTE — SINCRONIZACIÓN MAESTRÍA:** C14 continúa como referencia 2D verificada: 10,001 muestras nativas a dt=0.001 s. El análisis comparativo B usa 101 estados a 0.1 s y 404 métricas de estaciones comunes; no equiparar cadencias. No se modifican las entradas originales del C14. [Registro integrado](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261124_ES.md).

> **18-11-2026 — Requisito del primer avance del director:** C14 es la referencia CFD verificada para explicar ecuaciones, BC, `deltaT`, PIMPLE, tolerancias, evolución y **Courant máximo realmente obtenido de logs**. `maxCo=0.25` con `adjustTimeStep=no` no es el máximo observado. La comparación de sensibilidad pendiente es **C14 `phaseChangeSource.relax=0.10` vs C16 `0.25`**; no confundir con `relaxationFactors=1.0`. [Plan de entrega, fuentes y checklist](../../docs/PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md).

# CASE_NOTES — C14_topFixedFlux_explicitRef

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** RUN-VERIFIED — ANALYSIS-VERIFIED  
**Familia:** C  
**Caso padre / referencia:** `C11_topFixedFlux_airGapOF14`

## Objetivo de V14

Aplicar de forma controlada la configuración solicitada por el director sobre el baseline impermeable V11, sin modificar la física restante del caso.

## Cambios respecto a C11

| Ubicación exacta | Cambio |
|---|---|
| `system/metal/fvSolution` | `pRefPoint (0.02 0.04 0.005)` |
| `system/metal/fvSolution` | `pRefValue 1e5` se mantiene explícito |
| `system/metal/fvSolution` | se añade `nEnergyCorrectors 2` |
| `system/functions` | se añade `topFlow` para registrar `U` y `phi` cara por cara en `metalTop` con `writeControl writeTime` |

`0/metal/p_rgh` permanece como en V11:

```
metalTop
{
    type  fixedFluxPressure;
    value $internalField;
}
```

## Control científico

Todo lo demás debe permanecer igual a C11: geometría, malla, air gap OF14, propiedades C con rho constante y buoyancy explícita del modelo, `U=slip`, modelo de solidificación, timestep, BC térmicas, gravedad, PIMPLE restante, probes, perfiles y diagnósticos.

La comparación principal es **C14 vs C11**. Si el cambio de `pRefPoint` solo cambia el datum de presión, no debería alterar de forma material `U`, `phi`, T o alphaL.

## Nota OF14 sobre nEnergyCorrectors

La clave se incluye exactamente porque fue solicitada por el director. Sin embargo, el caso usa el solver regional `fluid` de OpenFOAM Foundation v14. La implementación de `fluid::thermophysicalPredictor()` no contiene un bucle `nEnergyCorrectors`; esa opción sí existe en `multiphaseEuler`. Por ello V14 debe auditar el log para comprobar cuántos solves de energía ocurren realmente y no asumir que la clave está activa.

## Riesgo a verificar al arrancar

El `pRefPoint` solicitado está en `y=0.04 m`, sobre el plano superior geométrico. OpenFOAM necesita asociar el punto de referencia de forma unívoca con una celda. El primer criterio de V14 es, por tanto, que OF14 acepte el punto sin error de referencia.

## Criterios de aceptación

- la corrida llega a 10 s sin fatal error;
- `topFlow` escribe `U` y `phi` en cada writeTime;
- `phi` en cada cara de `metalTop` permanece ~0 si la tapa sigue siendo impermeable;
- comparar `sum(phi)`, `sum(abs(phi))`, min/max `phi`, T, alphaL, Courant y continuidad con C11;
- revisar el log para determinar si `nEnergyCorrectors 2` tiene efecto operativo en el solver `fluid`.

## Hipótesis previa

Se espera que `fixedFluxPressure + slip` conserve la impermeabilidad observada en C11. El cambio de punto de referencia debería afectar principalmente el nivel absoluto/datum de presión, no el campo de flujo. Esta hipótesis debe verificarse con la corrida, no asumirse.


## Resultado verificado — 2026-10-03

- Corrida completada a **10 s** sin fatal error.
- El punto de referencia `pRefPoint (0.02 0.04 0.005)` fue aceptado por OpenFOAM 14.
- `topFlow` registró **80 caras** de `metalTop` por writeTime.
- En 0.1, 5 y 10 s, las 80 caras verificadas tienen `U_y = 0` y `phi = 0` a precisión almacenada.
- Sobre los **100 writeTimes de 0.1 a 10 s**, el máximo `sum(abs(phi))` fue **0**. Por tanto no existe cancelación oculta de entradas/salidas: la tapa es impermeable cara por cara.
- La velocidad tangencial permanece activa, consistente con `slip` (max |Ux| = 4.24467e-3 m/s a 10 s).
- Comparación con C11: T del probe central es idéntica en los 10,001 pasos; máxima diferencia alphaL = 1e-6; a 10 s T=1464.19 K y alphaL=0.964815 en ambos.
- La estructura de `foamLog` para energía es idéntica a V11: `h_0..2` y `e_0..2`. El `nEnergyCorrectors 2` añadido en el **fvSolution regional del metal** no introdujo solves de energía adicionales.
- Conclusión: V14 **preserva la física impermeable de V11** y valida la referencia explícita de presión solicitada; no introduce un cambio físico material respecto a V11.


## Aclaración posterior — energy correctors efectivos

La entrada `nEnergyCorrectors 2` de C14 está en `system/metal/fvSolution`, no en el `system/fvSolution` raíz que controla el bucle global de energía de `foamMultiRun`.

Por ello **C14 NO fue una corrida con 2 energy correctors efectivos**. Su log contiene `h_0..2` y `e_0..2`, exactamente como C11 normal.

El test `C11_energy2_test` confirmó que, al colocar `nEnergyCorrectors 2` en el diccionario raíz, aparecen `h_0..5` y `e_0..5`. Ese test también mostró que duplicar los energy correctors no cambia materialmente T, alphaL o U y aumenta el costo computacional.

Por tanto C14 debe interpretarse como **1 energy corrector efectivo**, con la referencia explícita de presión solicitada por el director.
