# CASE_NOTES — B10_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** numerado — control V5 + air gap OF14  
**Familia:** B  
**Caso padre / referencia:** `B5_outer3 / B5_airGapOF14`

## Objetivo de esta versión

V5 con air gap físicamente activo en OF14 y tabla rho(T) común extendida.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/T` | air gap: h/wallLayersHeatTransferCoefficient, δ=0.2 mm, k=0.1 W/(m K) |
| `0/mold/T` | se elimina la declaración duplicada del gap |
| `constant/metal/materials/castIron` | tabla rho(T) extendida hasta 2273.15 K |
| `0/metal/p_rgh` | conserva totalPressure en metalTop |
| `system/researchDiagnostics` | posteriormente se añadió metalTopPhiSum para futuras corridas; corridas iniciadas antes de ese commit no lo contienen en runtime |

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

- Comparar principalmente contra B11 para aislar la BC superior con air gap y tabla rho(T) igualados.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.
