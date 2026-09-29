# CASE_NOTES — B13_prghPressure_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** CANÓNICO DIAGNÓSTICO — RUN-VERIFIED + ANALYSIS-VERIFIED; NO baseline impermeable  
**Familia:** B  
**Caso padre / referencia:** `B11_topFixedFlux_airGapOF14`

## Objetivo de esta versión

Imponer presión estática atmosférica a través de prghPressure, permitiendo que p_rgh se actualice con rho(T) y altura.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/p_rgh` | metalTop = prghPressure; p uniform 0 gauge relativo a pRef=1e5 Pa; rho rho; value inicial 2667.739248 Pa |

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

- La BC actualiza p_rgh con rho; en B esto la distingue físicamente de V12 fixedValue.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.

## Resultado de la corrida — 2026-09-29

La simulación completó 10 s sin errores fatales.

Resultados principales:
- max `|sum(phi)|` en `metalTop`: **9.771e-5 kg/s**;
- masa integrada por top: **-5.799e-4 kg**, magnitud equivalente a **0.533%** de la masa inicial B;
- energía advectiva integrada por top: **-559.53 J**;
- calor no advectivo integrado por top: **+374.77 J**;
- energía total integrada por top: **-184.75 J**;
- cruce central descendente de 1473 K: **4.291 s**;
- T central final: **1469.23 K**;
- alphaL central final: **0.985082**;
- alphaL media final: **0.9591660**;
- max Co: **0.06910705**;
- mediana `R_p_outer`: **7.346e-4**;
- `R_p_outer>1`: **0%**;
- continuidad acumulada final: **9.88004e-7**.

### Interpretación

`prghPressure + slip` mantiene la presión estática atmosférica objetivo, pero no produce una tapa impermeable en B. Existe entrada de masa y entalpía sensible por `metalTop`.

El probe central presenta un rebound de **+4.00 K**:
- Tmin local: **1471.28 K @ 5.167 s**;
- máximo posterior: **1475.28 K @ 7.237 s**.

La fracción líquida presenta:
- mínimo alphaL: **0.993108 @ 5.231 s**;
- recuperación a **alphaL=1.0 @ 6.222 s**.

Esto es **remelting local dentro del modelo**, coincidente con la entrada advectiva de frontera. No debe describirse como recalescencia metalúrgica por nucleación.

### Decisión

Conservar B13 como prueba diagnóstica de presión estática atmosférica. **No adoptarlo como baseline impermeable.** V11 permanece como referencia física del modelo actual.
