# CASE_NOTES — B11_topFixedFlux_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** CANÓNICO — BASELINE físico actual para `metalTop` fijo e impermeable — RUN-VERIFIED + ANALYSIS-VERIFIED
**Familia:** B  
**Caso padre / referencia:** `B9_topFixedFlux / B9_airGapOF14`

## Objetivo de esta versión

Combinar tapa fixedFluxPressure de V9 con air gap correcto OF14 y tabla B extendida.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/p_rgh` | metalTop = fixedFluxPressure |
| `0/metal/T` | air gap OF14 mediante wallLayersHeatTransferCoefficient |
| `0/mold/T` | sin duplicación del air gap |
| `constant/metal/materials/castIron` | tabla rho(T) extendida hasta 2273.15 K |
| `system/researchDiagnostics` | incluye metalTopPhiSum y energyAdvectiveFlux |

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

- Base inmediata de las pruebas de presión V12/V13.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.

## Estado después del cierre V10–V13 — baseline verificada directamente

La corrida V11 con air gap OF14 ya está versionada y auditada directamente.

Resultados B11:
- max `|sum(phi)|` en `metalTop` = **1.694066e-21 kg/s**;
- `∫phi dt = -1.27055e-22 kg`;
- energía advectiva integrada por el top = **-1.22e-16 J**;
- T central final = **1470.07 K**;
- alphaL central final = **0.988421**;
- alphaL media final = **0.9606902**;
- max Co = **0.0673434**;
- mediana `R_p_outer = 0.001981`;
- `R_p_outer>1` = **0%**;
- cumulative continuity final = **-0.0310209**.

B10, con la tapa previa, tuvo `Eadv,top=-629.63 J`. Al cerrar la tapa en B11 el transporte advectivo desaparece, mientras el heat transfer metal→molde permanece prácticamente igual (**3686.64 J vs 3687.23 J**). La diferencia de T central B10→B11 tiene RMSE **8.53 K** y los perfiles de `Uy` se reorganizan fuertemente.

La cumulative continuity de B11 no representa pérdida de masa por el top: el flujo directo es ~0. Es la tensión conocida entre `rho(T)`, volumen geométrico fijo e inexistencia de shrinkage/free-surface/feeding.

### Decisión

Mantener B11 como baseline impermeable de diagnóstico para familia B. No reabrir el top para “mejorar” continuidad. Si se quiere conservar contracción térmica física, el siguiente modelo debe representar cambio de volumen/alimentación/superficie libre.

Resumen reproducible:
- `analysis_results/v10_v13_closure/summary.md`
- `analysis_results/v10_v13_closure/case_metrics.csv`
- `analysis_results/v10_v13_closure/pair_metrics.csv`
- `analysis_results/v10_v13_closure/profile_metrics.csv`
