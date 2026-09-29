# CASE_NOTES — B5_airGapOF14

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** transición / control de air gap  
**Familia:** B  
**Caso padre / referencia:** `B5_outer3`

## Objetivo de esta versión

Repetir la línea V5 con resistencia de air gap expresada correctamente para OF14.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `0/metal/T` | metal_to_mold añade h { type wallLayersHeatTransferCoefficient; thicknessLayers (2e-4); kappaLayers (1e-1); } |
| `0/mold/T` | se eliminan thicknessLayers/kappaLayers del lado molde para no duplicar la misma resistencia |
| `constant/metal/materials/castIron` | usa la tabla B extendida hasta 2273.15 K para igualar el rango con la rama V9 |

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

- Nombre transicional; la versión numerada equivalente es B10_airGapOF14.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.
