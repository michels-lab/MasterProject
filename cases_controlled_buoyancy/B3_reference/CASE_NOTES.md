# CASE_NOTES — B3_reference

> Este archivo documenta la intención y genealogía del caso. No modifica la simulación.

**Estado:** histórico — referencia numérica  
**Familia:** B  
**Caso padre / referencia:** `baseline controlado`

## Objetivo de esta versión

Referencia B con 2 outer correctors.

## Cambios respecto al padre

| Ubicación exacta | Cambio |
|---|---|
| `system/fvSolution` | nOuterCorrectors = 2 (referencia raíz multi-región) |
| `constant/metal/materials/castIron` | icoTabulated con rho(T) |
| `constant/metal/fvModels` | beta = 0 en solidificationMeltingSource |
| `0/metal/p_rgh` | metalTop = totalPressure |
| `0/metal/T y 0/mold/T` | air gap escrito con sintaxis heredada OF13; bajo OF14 la resistencia pretendida no queda aplicada |

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

- No usar como baseline térmico OF14 final: air gap heredado no está expresado con la sintaxis OF14.
- Caso histórico: no corregir retroactivamente; conservarlo como evidencia de convergencia.

## Comparación correcta

Comparar este caso contra su padre/referencia indicado arriba y contra el caso de la otra familia con el mismo número/objetivo. No atribuir diferencias B/C a la formulación de buoyancy si también cambió alguna condición numérica, térmica o de frontera.
