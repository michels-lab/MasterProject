# CASE_NOTES — C11_topFixedFlux_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** CANÓNICO — BASELINE físico actual para `metalTop` fijo e impermeable — RUN-VERIFIED + ANALYSIS-VERIFIED
**Familia:** C  
**Caso padre / referencia:** `C9_topFixedFlux / C9_airGapOF14`

## Objetivo de esta versión

Combinar fixedFluxPressure de V9 con air gap correcto OF14.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/p_rgh` | metalTop = fixedFluxPressure |
| `0/metal/T` | air gap OF14 |
| `0/mold/T` | sin duplicación del air gap |
| `system/researchDiagnostics` | incluye metalTopPhiSum y energyAdvectiveFlux |

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

- Base inmediata de las pruebas de presión V12/V13.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.

## Estado después del cierre V10–V13 — baseline verificada directamente

La corrida C11 con air gap OF14 ya está versionada y auditada directamente.

Resultados C11:
- `sum(phi)` en `metalTop` = **0** en el diagnóstico almacenado;
- energía advectiva integrada por el top = **0 J**;
- T central final = **1464.19 K**;
- alphaL central final = **0.964815**;
- alphaL media final = **0.9620593**;
- max Co = **0.0650864**;
- mediana `R_p_outer = 0.0005954`;
- `R_p_outer>1` = **0%**;
- cumulative continuity final = **4.45e-13**.

C10 ya tenía poca advección por el top (**+2.976 J**), y cerrarlo en C11 apenas cambia la solución:
- T central RMSE = **0.164 K**;
- cambio final de T = **-0.08 K**;
- `Uy` final NRMSE = **0.52%, 1.70% y 0.44%** en y=20 mm, y=30 mm y x=20 mm.

### Decisión

C11 queda confirmado como **baseline físico preferido para G1/validación experimental** del modelo Quick-Cup de volumen fijo. V12/V13 permanecen como diagnósticos de BC de presión y no sustituyen la tapa impermeable.

Resumen reproducible:
- `analysis_results/v10_v13_closure/summary.md`
- `analysis_results/v10_v13_closure/case_metrics.csv`
- `analysis_results/v10_v13_closure/pair_metrics.csv`
- `analysis_results/v10_v13_closure/profile_metrics.csv`
