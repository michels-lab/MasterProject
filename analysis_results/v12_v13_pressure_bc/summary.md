# V12/V13 — análisis de condiciones de presión en `metalTop`

**Fecha:** 2026-09-29  
**Estado:** `RUN-VERIFIED` + `ANALYSIS-VERIFIED`

## Pregunta controlada

Los cuatro casos descienden de V11 y cambian únicamente la BC de `0/metal/p_rgh` en `metalTop`:

- V12: `fixedValue` de `p_rgh`;
- V13: `prghPressure` con presión estática atmosférica relativa a `pRef`.

Se mantienen iguales malla, `U=slip`, BC térmica superior, air gap, timestep, PIMPLE, propiedades y modelo de solidificación.

La pregunta es si estas BC de presión son compatibles con la interpretación de `metalTop` como una tapa fija e impermeable y cómo alteran la solución B/C.

## 1. Resultado principal

### Familia C

C12 y C13 son indistinguibles dentro de la precisión almacenada.

- max `|sum(phi)|`: ~4.90e-10 kg/s en ambos;
- flujo másico integrado en 10 s: ~-1.44e-10 kg;
- energía advectiva integrada en top: +6.293718 J;
- calor no advectivo integrado en top: 374.672263 J;
- T central final: 1464.30 K;
- cruce descendente de 1473 K: 4.642 s;
- alphaL central final: 0.965235;
- alphaL media final: 0.9620239;
- max Co: 0.06633;
- mediana `R_p_outer`: 7.58e-4;
- fracción de timesteps con `R_p_outer>1`: 0.

Esto confirma la predicción metodológica: con `rhoConst` y una tapa horizontal fija, `fixedValue p_rgh` y `prghPressure` producen esencialmente la misma condición de presión.

### Familia B

B12 y B13 NO son impermeables.

| Métrica | B12 fixedValue | B13 prghPressure |
|---|---:|---:|
| max `|sum(phi)|` [kg/s] | 9.739e-5 | 9.771e-5 |
| `∫sum(phi)dt` [kg] | -5.642e-4 | -5.799e-4 |
| magnitud vs masa inicial | 0.519% | 0.533% |
| `∫P_adv,top dt` [J] | -660.77 | -559.53 |
| `∫P_heat,top dt` [J] | +369.28 | +374.77 |
| `∫P_total,top dt` [J] | -291.49 | -184.75 |
| T central final [K] | 1471.29 | 1469.23 |
| cruce descendente 1473 K [s] | 9.230 | 4.291 |
| alphaL central final | 0.993250 | 0.985082 |
| alphaL media final | 0.962691 | 0.959166 |
| max Co | 0.14469 | 0.06911 |
| mediana `R_p_outer` | 1.432e-3 | 7.346e-4 |
| `R_p_outer>1` | 0% | 0% |

La masa inicial de referencia de B es:

`m0 = rho(1500 K) * V = 6798.52 kg/m3 * 1.6e-5 m3 = 0.10877632 kg`.

Por tanto, el flujo integrado por `metalTop` en B12/B13 equivale a aproximadamente 0.52–0.53% de la masa inicial en solo 10 s.

## 2. Signo del flujo y significado físico

La normal de `metalTop` apunta hacia fuera del dominio metálico.

Durante el intervalo del rebound en B, tanto `sum(phi)` como `energyAdvectiveFlux` son negativos. Por tanto representan flujo de masa y entalpía sensible entrando al dominio a través de la tapa.

Ejemplos:

### B12

A 5 s:
- `sum(phi)=-5.383e-5 kg/s`;
- `P_adv=-63.26 W`;
- `P_heat=+36.96 W`;
- `P_total=-26.30 W`.

A 6 s:
- `sum(phi)=-5.098e-5 kg/s`;
- `P_adv=-57.97 W`;
- `P_heat=+36.82 W`;
- `P_total=-21.15 W`.

### B13

A 5 s:
- `sum(phi)=-5.524e-5 kg/s`;
- `P_adv=-53.77 W`;
- `P_heat=+37.74 W`;
- `P_total=-16.02 W`.

A 6 s:
- `sum(phi)=-5.220e-5 kg/s`;
- `P_adv=-50.58 W`;
- `P_heat=+37.62 W`;
- `P_total=-12.96 W`.

El término advectivo de entrada supera al calor de salida por convección/radiación, de modo que el balance neto del top introduce energía al metal durante ese intervalo.

Esto demuestra que `U=slip` por sí sola no está haciendo impermeable a `metalTop` cuando se combina con estas BC de valor de presión.

## 3. Rebound y remelting

### B12

El mayor rebound central de temperatura es:

- mínimo local: 1478.93 K a 4.639 s;
- máximo posterior: 1483.27 K a 6.249 s;
- aumento: +4.34 K.

Como todo el evento permanece por encima de `Tliq=1473 K`, alphaL permanece en 1. No es cambio de fase; es un rebound térmico asociado al campo de transporte.

### B13

El mayor rebound central es:

- mínimo local: 1471.28 K a 5.167 s;
- máximo posterior: 1475.28 K a 7.237 s;
- aumento: +4.00 K.

La fracción líquida simultáneamente cambia de:

- mínimo alphaL = 0.993108 a 5.231 s;
- alphaL = 1.0 a 6.222 s;
- recuperación = +0.006892.

Por tanto B13 sí presenta **remelting local dentro del modelo**.

No debe llamarse recalescencia metalúrgica por nucleación. El evento coincide con una entrada no física de masa/entalpía a través de `metalTop`, suficiente para proporcionar una explicación de frontera/transporte.

C12 y C13 no muestran rebound de T ni recuperación de alphaL en el probe central.

## 4. La extracción térmica impuesta es prácticamente la misma

La energía de calor no advectiva integrada sobre todas las fronteras del metal es casi idéntica:

- B12: 4059.815 J;
- B13: 4059.793 J;
- C12/C13: 4056.182 J.

La transferencia no advectiva metal→molde también es casi idéntica:

- B12: 3690.534 J;
- B13: 3685.020 J;
- C12/C13: 3681.510 J.

Así, la gran diferencia B12/B13 no proviene de haber cambiado `h`, emisividad, air gap o BC térmica: esas entradas son iguales y la extracción difusiva queda prácticamente igual.

La diferencia adicional aparece a través del término advectivo creado por la BC de presión en el top.

## 5. Presión y convergencia

La fuga NO se explica por falta de convergencia del pressure corrector.

### B12
- mediana residual inicial del primer solve: 5.80e-4;
- mediana `R_p_outer`: 1.43e-3;
- `R_p_outer>1`: 0%;
- continuidad global final: 1.87e-11;
- cumulative continuity final: 1.27e-6.

### B13
- mediana residual inicial del primer solve: 2.49e-4;
- mediana `R_p_outer`: 7.35e-4;
- `R_p_outer>1`: 0%;
- continuidad global final: 4.32e-12;
- cumulative continuity final: 9.88e-7.

### C12/C13
- mediana residual inicial del primer solve: 1.18e-4;
- mediana `R_p_outer`: 7.58e-4;
- `R_p_outer>1`: 0%;
- continuidad global final: ~3.23e-13;
- cumulative continuity final: ~1.48e-6.

Los cuatro casos muestran fuerte contracción del outer coupling.

La conclusión correcta es:

> el solver converge a estas soluciones; el problema es la interpretación física de la frontera, no una divergencia numérica.

## 6. Relación con la formulación B de densidad variable

Este resultado aclara la tensión observada históricamente en B9.

En B, `rho=rho(T)` aumenta al enfriarse. En un volumen geométrico fijo:

- si la tapa es estrictamente impermeable (`fixedFluxPressure + slip`), el modelo no puede acomodar libremente el cambio de densidad mediante cambio de volumen o alimentación, y aparece la conocida discrepancia acumulada de continuidad;
- si la BC de presión permite flujo, como B12/B13, el solver puede satisfacer mejor continuidad importando masa por `metalTop`.

Históricamente B9 con `fixedFluxPressure` mostró:
- max `|sum(phi)|` ~2.54e-21 kg/s;
- energía advectiva de top ~0;
- cumulative continuity ~-0.0460.

En contraste B12/B13 presentan cumulative continuity del orden de 1e-6, pero lo logran mientras entra aproximadamente 0.52–0.53% de la masa inicial por la tapa.

Por tanto la mejor continuidad de B12/B13 no debe interpretarse como evidencia de mayor fidelidad física para un Quick-Cup de volumen fijo e impermeable. Es, en buena medida, consecuencia de haber abierto numéricamente una ruta de masa que el modelo geométrico no representa.

## 7. Interpretación de cada opción

### `fixedFluxPressure + slip`

Representa mejor una tapa fija e impermeable bajo gravedad.

Ventaja:
- hace compatible el flujo de presión con la BC cinemática;
- evidencia histórica V9: flujo de top ~0.

Limitación en B:
- expone la incompatibilidad entre `rho(T)`, volumen fijo y ausencia de shrinkage/free-surface/feeding.

### `fixedValue p_rgh + slip`

Fija directamente la presión reducida.

En C:
- prácticamente equivalente a V13 porque rho es constante.

En B:
- permite un flujo de masa importante;
- la presión estática reconstruida no permanece atmosférica cuando rho cambia;
- produce rebound térmico no asociado a cambio de fase en el probe central.

### `prghPressure + slip`

Mantiene presión estática atmosférica y actualiza p_rgh con rho.

En C:
- indistinguible de fixedValue.

En B:
- también permite flujo de masa importante;
- produce remelting local coincidente con entrada neta de entalpía por el top;
- no representa una superficie libre completa porque U sigue siendo slip y la geometría no puede moverse.

## 8. Conclusión metodológica

Para el modelo ACTUAL de Quick-Cup con geometría fija y top cinemáticamente impermeable:

- V12 y V13 son pruebas diagnósticas útiles, pero no deben adoptarse como baseline impermeable;
- la evidencia favorece mantener `fixedFluxPressure + slip` como formulación coherente de pared/tapa impermeable;
- la familia C es internamente más compatible con esa geometría fija porque no exige cambio de masa/volumen por `rho(T)`;
- si se desea conservar una formulación B con contracción térmica real, el siguiente problema físico no es otra BC de presión: es representar shrinkage, cambio de volumen, alimentación o una superficie libre móvil de forma coherente.

## Archivos fuente usados

Cada caso V12/V13:
- `postProcessing/metal/metalTopPhiSum/0/surfaceFieldValue.dat`;
- `postProcessing/metal/metalTopEnergyPower/0/surfaceFieldValue.dat`;
- `postProcessing/metal/metalBoundaryEnergyPower/0/surfaceFieldValue.dat`;
- `postProcessing/metal/metalMoldEnergyPower/0/surfaceFieldValue.dat`;
- `postProcessing/metal/metalLatentHeatPower/0/volFieldValue.dat`;
- `postProcessing/metal/metalSensibleEnthalpy/0/volFieldValue.dat`;
- `postProcessing/metal/metalMeanLiquidFraction/0/volFieldValue.dat`;
- `postProcessing/metal/metalMaxCourant/0/volFieldValue.dat`;
- `postProcessing/metal/temperatureProbe/0/{T,U,p_rgh,rho,phaseChangeSource:alpha1}`;
- `logs/p_rgh_0`, `p_rgh_4`, `p_rghFinalRes_0`, `p_rghFinalRes_4`;
- `logs/contCumulative_5`, `contGlobal_5`, `contLocal_5`.

Referencia histórica impermeable:
- `PROJECT_AUDIT_LOG_ES.md`, sección V9.
