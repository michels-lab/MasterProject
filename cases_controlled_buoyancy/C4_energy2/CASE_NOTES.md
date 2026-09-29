# CASE_NOTES — C4_energy2

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** histórico — sensibilidad numérica  
**Familia:** C  
**Caso padre / referencia:** `C3_reference`

## Objetivo de esta versión

Aislar el efecto de duplicar la corrección de energía.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `system/fvSolution` | nEnergyCorrectors = 2; el resto hereda C3 |

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

- Mantiene totalPressure en metalTop y air gap con sintaxis heredada OF13.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.
