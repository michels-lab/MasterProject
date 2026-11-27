> **27-11-2026 — Corrección de publicación, segundo corte documental:** campaña laptop 6/8 calculadas, 5/8 con manifiesto completo, 1/8 B14-2D sin tope pendiente, 2/8 A adaptativo fallidas. C14-2D MPI con tope (11029 pasos, 3dbcbee4) y B14-2D MPI con tope (14276 pasos, b02ef4a9) ya están publicados y auditados según sus manifiestos, sin nueva validación física. A 8/10=80% hitos, B 2/7=29%, FS-C08 lote 12 75/75 pasos. [Historia completa](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Manifiestos inspeccionados](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json). Las entradas anteriores quedan como historia.

> **27-11-2026 — actualización:** B14 2D adaptativo MPI con y sin tope completó 200 s (14276 y 14275 pasos), pendiente auditoría/publicación por duplicado de perfil vertical. B14 3D excluido; FS-C08 separado. [Historia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md). Entradas anteriores históricas.

> **25-11-2026 | ESTADO VIGENTE:** B14 2D original de 10 s intacto y referencia de rho(T) para contracción. B14-2D-200s fijo compacto preparado, sin 200 s confirmados; intento adaptativo PC bloqueado/fallido preservado. B14 3D fuera de campaña autorizada. FS-C08 utiliza tablas de ingeniería derivadas de B14, no es el B14 original ni modelo calibrado de contracción. Solver FS-C08 ya compilado y probado en WSL; lotes de arranque 79/80 pasos aceptados, energía global y contracción física pendientes. [Registro integrado](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261125_ES.md).

# CASE_NOTES — B14_topFixedFlux_explicitRef

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** RUN-VERIFIED — ANALYSIS-VERIFIED  
**Familia:** B  
**Caso padre / referencia:** `B11_topFixedFlux_airGapOF14`

## Objetivo de V14

Aplicar de forma controlada la configuración solicitada por el director sobre el baseline impermeable V11, sin modificar la física restante del caso.

## Cambios respecto a B11

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

Todo lo demás debe permanecer igual a B11: geometría, malla, air gap OF14, propiedades B con rho(T), `U=slip`, modelo de solidificación, timestep, BC térmicas, gravedad, PIMPLE restante, probes, perfiles y diagnósticos.

La comparación principal es **B14 vs B11**. Si el cambio de `pRefPoint` solo cambia el datum de presión, no debería alterar de forma material `U`, `phi`, T o alphaL.

## Nota OF14 sobre nEnergyCorrectors

La clave se incluye exactamente porque fue solicitada por el director. Sin embargo, el caso usa el solver regional `fluid` de OpenFOAM Foundation v14. La implementación de `fluid::thermophysicalPredictor()` no contiene un bucle `nEnergyCorrectors`; esa opción sí existe en `multiphaseEuler`. Por ello V14 debe auditar el log para comprobar cuántos solves de energía ocurren realmente y no asumir que la clave está activa.

## Riesgo a verificar al arrancar

El `pRefPoint` solicitado está en `y=0.04 m`, sobre el plano superior geométrico. OpenFOAM necesita asociar el punto de referencia de forma unívoca con una celda. El primer criterio de V14 es, por tanto, que OF14 acepte el punto sin error de referencia.

## Criterios de aceptación

- la corrida llega a 10 s sin fatal error;
- `topFlow` escribe `U` y `phi` en cada writeTime;
- `phi` en cada cara de `metalTop` permanece ~0 si la tapa sigue siendo impermeable;
- comparar `sum(phi)`, `sum(abs(phi))`, min/max `phi`, T, alphaL, Courant y continuidad con B11;
- revisar el log para determinar si `nEnergyCorrectors 2` tiene efecto operativo en el solver `fluid`.

## Hipótesis previa

Se espera que `fixedFluxPressure + slip` conserve la impermeabilidad observada en B11. El cambio de punto de referencia debería afectar principalmente el nivel absoluto/datum de presión, no el campo de flujo. Esta hipótesis debe verificarse con la corrida, no asumirse.


## Resultado verificado — 2026-10-03

- Corrida completada a **10 s** sin fatal error.
- El punto de referencia `pRefPoint (0.02 0.04 0.005)` fue aceptado por OpenFOAM 14.
- `topFlow` registró **80 caras** de `metalTop` por writeTime.
- En 0.1, 5 y 10 s, las 80 caras verificadas tienen `U_y = 0` y `phi = 0` a precisión almacenada, salvo un residuo de redondeo máximo de `8.47033e-22` en `phi` a 0.1 s.
- Sobre los **100 writeTimes de 0.1 a 10 s**, el máximo `sum(abs(phi))` fue **8.47033e-22**. Por tanto no existe cancelación oculta de entradas/salidas: la tapa es impermeable cara por cara.
- La velocidad tangencial permanece activa, consistente con `slip` (max |Ux| = 7.7934e-3 m/s a 10 s).
- Comparación con B11: máxima diferencia del probe central T = 0.01 K; alphaL = 7e-6; a 10 s T=1470.07 K en ambos y alphaL=0.988421 vs 0.988414.
- La estructura de `foamLog` para energía es idéntica a V11: `h_0..2` y `e_0..2`. El `nEnergyCorrectors 2` añadido en el **fvSolution regional del metal** no introdujo solves de energía adicionales.
- Conclusión: V14 **preserva la física impermeable de V11** y valida la referencia explícita de presión solicitada; no introduce un cambio físico material respecto a V11.
