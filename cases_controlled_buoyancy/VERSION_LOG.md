> **27-11-2026 — Estado vigente:** campaña laptop adaptativa 6/8 calculadas y publicadas, 0 recuperaciones 2D pendientes, 2 variantes A fallidas; A 8/10=80% y B 2/7=29% hitos, no validación física. FS-C08 lote 12: 75/75 pasos de arranque. La campaña fija del laboratorio permanece separada. [Historia científica](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Estado vigente](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json). Los estados anteriores son históricos.

> **27-11-2026 — Estado vigente:** A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29% hitos. Campaña histórica 2D 26/26, V14 aparte. Laptop adaptativa 6/8 calculadas, 5/8 publicadas, B14-2D sin tope pendiente, A fallida en ambas variantes. FS-C08 lote 12 75/75 pasos, 4/4 variantes, no independencia temporal ni validación física. Los estados anteriores son históricos. [Historia](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Estado](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json) · [Evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md).

V15/V16 permanecen preparados/no corrida verificada en el registro histórico. La campaña 200 s adaptativa es distinta de V15/V16: no renombrar ni sobreescribir generaciones. El inventario conserva las 34 carpetas B/C.

# VERSION_LOG — casos controlados B/C

Este índice resume la genealogía de `cases_controlled_buoyancy`. El detalle exacto de cada caso está dentro de su propio `CASE_NOTES.md`.

## Serie numerada canónica

| Versión | Casos | Objetivo | Cambio principal |
|---|---|---|---|
| V3 | `B3_reference / C3_reference` | Referencia numérica | outer=2; totalPressure; air gap heredado OF13 |
| V4 | `B4_energy2 / C4_energy2` | Sensibilidad energía | nEnergyCorrectors=2 |
| V5 | `B5_outer3 / C5_outer3` | Sensibilidad outer | outer=3 |
| V6 | `B6_adaptiveDt / C6_adaptiveDt` | Sensibilidad timestep | adaptive dt, maxCo=0.25 |
| V7 | `B7_outer4 / C7_outer4` | Sensibilidad outer | outer=4, dt fijo |
| V8 | `B8_adaptiveOuter4 / C8_adaptiveOuter4` | Diagnóstico adaptive+outer4 | V6 + outer=4 |
| V9 | `B9_topFixedFlux / C9_topFixedFlux` | Corrección de tapa | metalTop p_rgh=fixedFluxPressure; top phi diagnostic |
| V10 | `B10_airGapOF14 / C10_airGapOF14` | V5 + air gap OF14 | totalPressure + gap correcto |
| V11 | `B11_topFixedFlux_airGapOF14 / C11_topFixedFlux_airGapOF14` | V9 + air gap OF14 | fixedFluxPressure + gap correcto |
| V12 | `B12_topFixedValue_airGapOF14 / C12_topFixedValue_airGapOF14` | Propuesta doctor | fixedValue de p_rgh inicialmente consistente |
| V13 | `B13_prghPressure_airGapOF14 / C13_prghPressure_airGapOF14` | Presión estática atmosférica | prghPressure con p=0 gauge relativo a pRef |
| V14 | `B14_topFixedFlux_explicitRef / C14_topFixedFlux_explicitRef` | Referencia explícita de presión sobre baseline V11 | fixedFluxPressure + slip; pRefPoint (0.02 0.04 0.005); pRefValue 1e5; diagnóstico face-wise U/phi |

## Casos transicionales no numerados

- `B5_airGapOF14 / C5_airGapOF14`: control intermedio V5 + air gap OF14; antecedente directo de V10.
- `B9_airGapOF14 / C9_airGapOF14`: control intermedio V9 + air gap OF14; antecedente directo de V11.

## Duplicados/provisionales V12/V13

No borrar sin revisar historial, pero **no tratarlos como la versión canónica**:

- `B12_fixedValueP_rgh / C12_fixedValueP_rgh`: primer intento V12 con `p_rgh=fixedValue 0`.
- `B13_prghPressureAtmosphere / C13_prghPressureAtmosphere`: primer intento V13 con `prghPressure` y `value 0`.

Las versiones canónicas son:
- V12: `B12_topFixedValue_airGapOF14 / C12_topFixedValue_airGapOF14`.
- V13: `B13_prghPressure_airGapOF14 / C13_prghPressure_airGapOF14`.

## Dos advertencias históricas que deben acompañar cualquier interpretación

1. **Air gap:** V3–V9 históricos conservan la sintaxis heredada OF13 (`thicknessLayers/kappaLayers` directamente en `coupledTemperature`). En OF14 esa forma no representa la resistencia pretendida. V10/V11/V12/V13/V14 usan `h { type wallLayersHeatTransferCoefficient; ... }` una sola vez en la interfaz.
2. **B9:** además del cambio de `metalTop`, B9 necesitó extensión diagnóstica de la tabla `rho(T)` hasta 2273.15 K y se añadió referencia regional de presión. Por ello B9-vs-B5 no es estrictamente una comparación de un solo cambio.

## Regla de mantenimiento

Cada nuevo caso B/C debe incluir desde su creación un `CASE_NOTES.md` que especifique:
- padre;
- hipótesis;
- archivos/entradas cambiados;
- variables deliberadamente mantenidas;
- advertencias;
- comparación de control;
- estado canónico/provisional.

Si un caso cambia después de haber sido corrido, la nota debe registrar el cambio y distinguir qué commit produjo cada dataset.
