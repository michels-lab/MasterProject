# CASE_NOTES — B12_topFixedValue_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** CANÓNICO DIAGNÓSTICO — RUN-VERIFIED + ANALYSIS-VERIFIED; NO baseline impermeable
**Familia:** B  
**Caso padre / referencia:** `B11_topFixedFlux_airGapOF14`

## Objetivo de esta versión

Probar p_rgh fijo en metalTop manteniendo el resto idéntico a V11.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/p_rgh` | metalTop = fixedValue; value uniform 2667.739248 Pa, valor reducido inicialmente consistente con p=1e5 Pa, pRef=1e5 Pa, hRef=0 y rho_B(1500 K)=6798.52 kg/m3 |

## Qué debe permanecer igual

Salvo los cambios enumerados arriba, el caso debe conservar del padre: geometría/malla, propiedades no mencionadas, estado inicial, modelo de cambio de fase, condiciones térmicas no mencionadas, gravedad, configuración laminar, probes y diagnósticos comunes.

## Formulación física de la familia B

- `constant/metal/materials/castIron`: ecuación de estado `icoTabulated`, con densidad dependiente de T.
- `constant/metal/fvModels`: `beta = 0`; la flotación no se introduce por el término Boussinesq de `solidificationMeltingSource`.
- La ruta de buoyancy de B proviene del tratamiento de presión/densidad variable del solver.

## Archivos clave para auditar este caso

- `0/metal/p_rgh` — condición de presión en `metalTop` y acoplamiento con el molde.
- `0/metal/U` — condición cinemática; `metalTop` debe revisarse junto con presión.
- `0/metal/T` y `0/mold/T` — condición térmica superior e interfaz metal–molde.
- `constant/metal/materials/castIron` — EOS / densidad.
- `constant/metal/fvModels` — cambio de fase, Darcy, beta, rhoRef, Tsol/Tliq, L, alpha1e, relax.
- `system/fvSolution` — acoplamiento multi-región raíz.
- `system/metal/fvSolution` — solución regional de U/p_rgh y referencia de presión.
- `system/controlDict` — timestep, tiempo final y escritura.
- `system/researchDiagnostics` — diagnósticos físicos y de frontera.

## Reglas de revisión

Para cualquier rerun de este caso revisar como mínimo:
- `p_rgh` y `p_rghFinalRes` en el tiempo y por timestep;
- contracción de outer coupling y continuidad;
- Courant;
- `sum(phi)` en `metalTop` cuando el diagnóstico exista;
- `energyAdvectiveFlux` en `metalTop`;
- temperatura, fracción líquida y velocidad;
- coherencia entre la condición física pretendida y las BC realmente escritas.

## Advertencias específicas

- El valor queda congelado aunque rho(T) cambie; esa es precisamente la hipótesis que V12 prueba.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.

## Resultado de la corrida — 2026-09-29

La simulación completó 10 s sin errores fatales.

Resultados principales:
- max `|sum(phi)|` en `metalTop`: **9.739e-5 kg/s**;
- masa integrada por top: **-5.642e-4 kg**, magnitud equivalente a **0.519%** de la masa inicial B;
- energía advectiva integrada por top: **-660.77 J**;
- calor no advectivo integrado por top: **+369.28 J**;
- energía total integrada por top: **-291.49 J**;
- cruce central descendente de 1473 K: **9.230 s**;
- T central final: **1471.29 K**;
- alphaL central final: **0.993250**;
- alphaL media final: **0.9626913**;
- max Co: **0.1446901**;
- mediana `R_p_outer`: **1.432e-3**;
- timesteps con `R_p_outer>1`: **0%**;
- continuidad acumulada final: **1.26875e-6**.

### Interpretación

`fixedValue p_rgh + slip` no produce una tapa impermeable en la familia B. El solver introduce masa y entalpía sensible a través de `metalTop`.

El probe central presenta un rebound térmico de **+4.34 K** (1478.93 K @ 4.639 s → 1483.27 K @ 6.249 s), pero permanece por encima de Tliq y alphaL=1 durante el evento; por tanto no representa remelting.

La fuerte contracción del pressure coupling demuestra que esta fuga no es una divergencia numérica: es una consecuencia de la condición de frontera resuelta.

### Decisión

Conservar B12 como prueba diagnóstica de la propuesta `fixedValue`. **No adoptarlo como baseline impermeable.** Para el modelo actual de tapa fija, V11 permanece como referencia física.
