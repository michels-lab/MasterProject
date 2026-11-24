# FS-C07 — gate 20/20 de reparto metal–sólido y transición hacia física conservativa

**Fecha de recepción de la evidencia:** 2026-11-23/24. **Origen:** salida auténtica del investigador de `locate_fs_c07_phase_violation.py --all-saved --compact`, ejecutada sobre `/home/michel/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4`. Repositorio inspeccionado antes de actualizar: `e960fb6c0`. **No se ejecutó una nueva CFD**, no se modificaron campos de la corrida y no se declaró cierre conservativo.

Archivo estructurado versionado, generado **únicamente** a partir de los 20 renglones de la evidencia:
[`freesurface/FS-C07_thermal_transition/evidence/FS_C07_PHASE_ALLOCATION_20_NATIVE_STATES_20261123.json`](../../freesurface/FS-C07_thermal_transition/evidence/FS_C07_PHASE_ALLOCATION_20_NATIVE_STATES_20261123.json).
SHA256 del archivo de transcripción aportado por el investigador:
`3c0f797708826a58c2fd40bc2c9f0575bc490eb2141d2ede0816d74ed32fb258`.
No confundir ese hash con el de los campos físicos guardados en OpenFOAM.

## Hallazgo cuantitativo definitivo, pero de alcance delimitado

**Los 20 de 20 estados físicos guardados (0.05 a 1.0 s, cada 0.05 s) tienen CERO celdas que incumplan `alpha.metal.solid <= alpha.metal+1e-8` cuando `alpha.metal >= 0.5`.** Cada instante contiene 34,368 celdas fluidas. El umbral de violación es absoluto `alpha.metal.solid - alpha.metal > 1e-8`.

| Rango de `alpha.metal` nativo | Incidencias celda×instante | % de las incidencias |
|---|---:|---:|
| `0 < alpha < 1e-6` | 2,938 | 38.20% |
| `1e-6 <= alpha < 1e-3` | 4,697 | 61.06% |
| `1e-3 <= alpha < 0.5` | 57 | 0.74% |
| `alpha >= 0.5` | **0** | **0%** |
| **Total** | **7,692** | **100%** |

`7,692` son **incidencias celda-tiempo**, no 7,692 celdas distintas ni 7,692 partículas metálicas. `7,635/7,692 = 99.25897036%` de esas incidencias aparecen con `alpha.metal < 0.001`. Las categorías `alpha.metal <= 0` y `alpha.metal > 1` también tuvieron cero eventos por encima de `1e-8` en este diagnóstico.

Los tres máximos temporales **no** son el mismo fenómeno:

| Magnitud | Máximo medido | t del máximo |
|---|---:|---:|
| Celdas con `solid > metal + 1e-8` | **641** | **0.35 s** |
| Mayor diferencia local `alphaSolid-alphaMetal` | **6.1813429e-6** | **0.20 s** |
| Mayor suma geométrica `sum(Vc * max(alphaSolid-alphaMetal,0))` | **6.1272893715684775e-12 m³** = 0.00612729 mm³ | **0.40 s** |

La revisión de 20 estados confirma ahora **la localización en metal de VOF muy bajo durante TODO el segundo guardado**, no solo en tres cortes. Esto **NO** implica que todo exceso esté sobre una misma superficie geométrica ni que `alphaSolid` sea válido en aire. Las celdas de núcleo metálico se definieron operativamente como `alpha>=0.5`, sin afirmar una interfaz geométrica exacta.

## Gate de estado científico

| Prueba | Estado | Lo demostrado y lo pendiente |
|---|---|---|
| Solver real Foundation14 hasta 1.0 s | **PASS** | `Time=1s` y `End` del log OpenFOAM |
| Veinte instantáneas térmicas + fase guardadas | **PASS** | Tres campos nativos completos por instante |
| Existencia de fracción sólida positiva | **PASS numérico** | Integral sólida RAW `2.403591085462431e-6 m³` a 1s, **sin aceptación de acotamiento global** |
| Coincidencia geométrica RAW con los monitores nativos | **PASS de reproducibilidad** | `Vmetal(1)=4.8011038266835194e-5 m³`; residual vs monitor `5.197394164352387e-18 m³` |
| Ausencia de sobreasignación significativa en núcleo, 20/20 tiempos | **PASS limitado** | Ningún `alphaSolid>alphaMetal+1e-8` donde `alphaMetal>=0.5` |
| Acotamiento `0 <= alphaSolid <= alphaMetal <= 1` para TODAS las celdas | **FAIL** | Hay 39 a 641 celdas con excesos >1e-8, dependiendo del tiempo |
| Conservación global de masa por fase y frontera | **PENDIENTE** | Integrar flujos `alphaRhoPhi.metal`, densidad variable y fuentes |
| Conservación global sensible + latente | **PENDIENTE** | Potencias interfaciales opuestas no equivalen a cierre total |
| Contracción, alimentación, porosidad, expansión grafítica | **NO IMPLEMENTADAS** | No inferir de `Delta Vmetal` de VOF |
| Calibración térmica/composición JMatPro, curvas QuickCup | **NO VALIDADA** | Liquidus `1473 K` fue referencia provisional C14 |

El error integrado es pequeño frente al `Vmetal` y `Vsolid` RAW, pero el criterio físico local sigue sin cumplirse. **No se cambió la tolerancia, no se recortaron campos originales y el reporte original no se renombró como aprobado.**

## Causa técnica probable: secuencia nativa de actualización (no prueba causal exclusiva)

En Foundation14:

1. [`foamMultiRun.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/solvers/foamMultiRun/foamMultiRun.C): ejecuta `solvers[i].fvModels().correct()` antes de `solvers[i].prePredictor()` en PIMPLE; después se guardan los campos con `runTime.write()`.
2. [`twoPhaseSolver.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/twoPhaseSolver/twoPhaseSolver.C): en `prePredictor()` se transporta `alpha` mediante `alphaPredictor()`.
3. [`VoFSolidificationMelting.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/compressibleVoF/fvModels/VoFSolidificationMelting/VoFSolidificationMelting.C): `correct()` calcula `alphaSolid_ = min( ... , alphaVoF )` con el VOF del instante de llamada.

Si el VOF metálico desciende por advección *después* del `correct()` y antes de la escritura, `alphaSolid` puede exceder al nuevo `alphaMetal` en la misma celda. La ubicación casi exclusiva en regiones `alphaMetal <0.001` respalda esta posibilidad; **faltan mediciones in-step para atribuirle causalidad exclusiva**.

Una estrategia que reajustara `alphaSolid` justo después de VOF no resolvería, por sí sola, los balances de masa, presión y energía. Además, si se modifica la fracción sólida que participa en el calor latente, **hay que verificar que el intercambio `Gamma L` use exactamente la misma transferencia de fase** para impedir fuentes espurias de calor. Tampoco basta con recortar las instantáneas históricas al rango [0,alphaMetal].

## Paso físico siguiente: definir y después implementar un balance metal líquido–sólido–aire conservativo

Se separará el desarrollo del modelo nativo conservativo en una nueva etapa (FS-C08 o sucesiva), sin reescribir FS-C07. Denotar por `alpha_l` y `alpha_s` **fracciones de volumen de celda** ocupadas por metal líquido y sólido, `alpha_m = alpha_l+alpha_s`, `alpha_a = 1-alpha_m`; `rho_l(T)`, `rho_s(T)` y `Gamma` (kg·m⁻³·s⁻¹) **pendientes de propiedades y cierre físico**.

Con velocidades de fase pertinentes `u_l`, `u_s`, las ecuaciones objetivo son:

```text
d/dt (alpha_l rho_l) + div(alpha_l rho_l u_l) = -Gamma
d/dt (alpha_s rho_s) + div(alpha_s rho_s u_s) = +Gamma

alpha_m = alpha_l + alpha_s
alpha_a = 1 - alpha_m
0 <= alpha_l, alpha_s, alpha_a <= 1

d/dt (alpha_l + alpha_s)
  + div(alpha_l u_l + alpha_s u_s)
  = Gamma * (1/rho_s - 1/rho_l)
  [solo para rho_l y rho_s constantes bajo las hipótesis indicadas]
```

Para densidades dependientes de T/P o transporte/deformación del sólido, el cierre de volumen y presión debe incorporar esos términos; **no reutilizar sin más la igualdad de densidades constantes**. Las dos ecuaciones de masa deben cancelar exactamente `Gamma` al sumarse. El término de calor latente tendrá que corresponder a una energía de referencia y un `Gamma` bien definidos (no sumar `Gamma L` a ciegas si el modelo también aporta calor latente mediante `D_t(alpha_s)`).

**Puertas antes de una corrida C08:**
- propiedades reales de líquido/sólido por composición y temperatura, sin inventar JMatPro;
- malla y paredes/aberturas conservadas en una copia aislada;
- balance discreto local/global de masa y de fase con `Gamma` opuesto;
- corrección VOF–sólido después del transporte que no cree ni destruya masa;
- balance de energía sensible + latente, presión y velocidad normal de interfaz;
- integración de flujos metálicos por todas las fronteras y controles de Courant;
- pruebas unitarias/conservativas y luego smoke CFD Foundation14 de caso aislado.

Hasta que esas puertas se cumplan, **FS-C07 es transitorio térmico y de fase numérico real, no simulación de contracción validada**.

## Acciones realizadas en repositorio

1. Se versionó el JSON estructurado de los 20 estados, conservando los enteros reales aportados por la terminal, su procedencia y SHA256 de transcripción.
2. Se añadieron seis pruebas sintéticas/de consistencia sobre ese archivo, integradas al workflow FS-C07, pero **su ejecución CI no ha sido verificada**.
3. Se registraron las conclusiones delimitadas en `STATUS.json`, README e índice documental.

La salida de diagnóstico proviene de WSL del investigador; **ninguna nueva CFD** fue lanzada por el asistente.
