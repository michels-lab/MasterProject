# CASE_NOTES — C12_topFixedValue_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** CANÓNICO DIAGNÓSTICO — RUN-VERIFIED + ANALYSIS-VERIFIED; NO baseline impermeable
**Familia:** C  
**Caso padre / referencia:** `C11_topFixedFlux_airGapOF14`

## Objetivo de esta versión

Probar p_rgh fijo en metalTop manteniendo el resto idéntico a V11.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/p_rgh` | metalTop = fixedValue; value uniform 2676.168 Pa, inicialmente consistente con p=1e5 Pa y rho=6820 kg/m3 |

## Qué debe permanecer igual

Salvo los cambios enumerados arriba, el caso debe conservar del padre: geometría/malla, propiedades no mencionadas, estado inicial, modelo de cambio de fase, condiciones térmicas no mencionadas, gravedad, configuración laminar, probes y diagnósticos comunes.

## Formulación física de la familia C

- `constant/metal/materials/castIron`: `rhoConst`.
- `constant/metal/fvModels`: `beta = 1.13e-4 1/K`, `rhoRef = 6820 kg/m3`.
- La buoyancy se introduce mediante la fuente explícita de `solidificationMeltingSource`.

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

- En C, rho es constante y la tapa está a altura constante; V12 y V13 deberían imponer condiciones de presión reducida muy cercanas.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.

## Resultado de la corrida — 2026-09-29

La simulación completó 10 s sin errores fatales.

Resultados principales:
- max `|sum(phi)|` NETO en `metalTop`: **4.901e-10 kg/s**;
- masa neta integrada: **-1.441e-10 kg**;
- energía advectiva integrada por top: **+6.293718 J**;
- calor no advectivo integrado por top: **+374.672263 J**;
- T central final: **1464.30 K**;
- cruce descendente de 1473 K: **4.642 s**;
- alphaL central final: **0.965235**;
- alphaL media final: **0.9620239**;
- max Co: **0.06632859**;
- mediana `R_p_outer`: **7.579e-4**;
- `R_p_outer>1`: **0%**;
- continuidad acumulada final: **1.47638e-6**.

### Interpretación

C12 y C13 resultan indistinguibles dentro de la precisión almacenada, como se esperaba para `rhoConst` y tapa horizontal.

Sin embargo, `sum(phi)` es una suma NETa del patch. Su valor casi cero no garantiza `phi=0` cara por cara. La energía advectiva integrada no nula (+6.29 J) demuestra intercambio advectivo local que no se cancela energéticamente.

### Decisión

Conservar C12 como control diagnóstico de `fixedValue p_rgh`. No usarlo como demostración de impermeabilidad estricta. V11 permanece como baseline físico del top fijo.
