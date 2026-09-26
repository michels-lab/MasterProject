# Validation Matrix — QuickCup Solidification

## Objective

Determine the **minimum additional physics required** to explain experimental evidence while keeping numerical sensitivity, buoyancy implementation, thermal parameters, equilibrium-solidification limitations, and genuine kinetic effects separate.

This matrix freezes V3–V7 as numerical evidence and prevents new physics from being mixed into those historical cases.

---

## 1. What V3–V7 already establish

### Numerical sensitivity

Los resultados versionados muestran:

- B3 → B5 → B7: mediana del cociente de coupling de `p_rgh` (R) = 0.6054 → 0.5975 → 0.6032.
- C3 → C5 → C7: 0.8127 → 0.8010 → 0.8088.
- Outer4 no produce una mejora monotónica respecto a outer3.
- El costo de outer4 aumenta aproximadamente 89% en B y 86% en C respecto al baseline outer2.
- B4/C4 con dos energy correctors no modifican materialmente la solución central respecto a B3/C3.
- V6 adaptive reduce fuertemente el costo, pero todavía requiere comparación física antes de aceptarse como sustituto del timestep fijo.

**Status:** the B/C difference is not explained by insufficient outer/energy correctors within the tested range.

### Central thermal/phase behaviour

En los casos con probes versionados:

| Caso | Cruce descendente 1473 K | Tmin | alpha_l,min | Rebound posterior |
|---|---:|---:|---:|---:|
| B3 | 6.666 s | 1467.45 K @ 10 s | 0.978184 @ 10 s | no |
| B4 | 6.678 s | 1467.53 K @ 10 s | 0.978506 @ 10 s | no |
| B5 | 6.683 s | 1467.52 K @ ~10 s | 0.978433 @ 10 s | no |
| C3 | 3.386 s | 1456.25 K @ 4.822 s | 0.932983 @ 4.878 s | +5.35 K |
| C4 | 3.386 s | 1456.25 K @ 4.822 s | 0.932983 @ 4.878 s | +5.35 K |
| C5 | 3.386 s | 1456.25 K @ 4.822 s | 0.932984 @ 4.876 s | +5.35 K |

C3/C4/C5 también recuperan aproximadamente 0.02141 de fracción líquida después del mínimo.

**Accepted interpretation:** the C rebound is robust to the tested numerical changes, but in the current model it coincides with **local remelting**. It must not by itself be labelled metallurgical nucleation-driven recalescence.

---

## 2. Audit against the Chiumenti et al. hypoeutectic Quick-Cup benchmark

Working reference:

M. Chiumenti, M. Cervera, E. Salsi, A. Zonato, *A phenomenological model for the solidification of eutectic and hypoeutectic alloys including recalescence and undercooling*.

El paper usa el Quick-Cup hipereutéctico/hipoeutéctico para calibrar/validar una ley cinética capaz de reproducir crecimiento dendrítico, transformación eutéctica, subenfriamiento y recalescencia.

### Condition comparison

| Cantidad | Quick-Cup del paper | Caso controlado actual B3/C3 | Estado |
|---|---:|---:|---|
| T inicial metal | 1300 °C = 1573.15 K | 1500 K = 1226.85 °C | diferente |
| T inicial molde | 20 °C ≈ 293.15 K | 300 K | cercana, no idéntica |
| HTC metal–molde | 500 W/m²K | capa: 0.2 mm, k=0.1 W/mK → h_eq≈500 W/m²K | esencialmente equivalente en resistencia |
| HTC exterior | 50 W/m²K | 10 W/m²K | diferente |
| Molde rho | 1550 kg/m³ | 1500 kg/m³ | diferente |
| Molde Cp | 1000 J/kgK | Cv=700 J/kgK | diferente |
| Molde k | 0.8 W/mK | 2 W/mK | diferente |
| L metal | 228097 J/kg | 228600 J/kg | muy cercano |
| T inicio dendritas paper | 1260 °C = 1533.15 K | no existe como variable cinética independiente | física ausente |
| T inicio eutéctico paper | 1180 °C = 1453.15 K | no existe como variable cinética independiente | física ausente |
| Plateau eutéctico paper | ~1150 °C = 1423.15 K | Tsol=1423 K | valor térmico coincidente, significado distinto |
| Relación de fase | dendrítica + eutéctica con cinética independiente | una única alpha_l de equilibrio | modelo distinto |

### Critical finding

The current case starts at **1500 K (1226.85 °C)**, whereas the paper benchmark starts at 1300 °C and uses **1260 °C as the onset of the dendritic transformation**.

Therefore, if that experiment is used as the validation target, the current simulation starts approximately **33 °C below the paper's T_start_L**. A mismatch with the experimental curve cannot scientifically be attributed solely to missing recalescence kinetics before these conditions are aligned.

---

## 3. Physics present in the paper model but absent from solidificationMelting

El modelo hipereutéctico/hipoeutéctico separa:

- fracción dendrítica primaria;
- fracción eutéctica;
- partición del calor latente entre ambas transformaciones;
- subenfriamiento dependiente de temperatura;
- una temperatura liquidus efectiva que cambia con la fracción sólida;
- leyes de evolución temporal tipo Avrami;
- pausa del crecimiento eutéctico durante recalescencia.

Conceptualmente:

`f_s = (1-theta) f_D + theta f_E`

y el término latente depende de las tasas temporales `df_D/dt` y `df_E/dt`, no solo de una relación algebraica instantánea `f_s(T)`.

Esto es exactamente la clase de física que el `solidificationMelting` estándar de OpenFOAM v14 no contiene.

---

## 4. Decision gates

### G0 — Benchmark parity

Antes de calibrar o crear una ley cinética:

- usar temperatura inicial del experimento objetivo;
- reproducir temperatura inicial del molde;
- reproducir resistencia/HTC metal–molde;
- reproducir HTC exterior;
- usar propiedades térmicas consistentes con el experimento;
- fijar ubicación equivalente del termopar;
- documentar incertidumbre de cada parámetro.

**Estado actual: NO cumplida.**

### G1 — Aligned equilibrium case

Crear una nueva rama de validación, separada de V3–V7, usando el mismo solver y un modelo de equilibrio pero con las condiciones experimentales alineadas.

Comparar:

- T(t);
- dT/dt;
- inicio de transformación;
- mínimo térmico antes del rebound;
- amplitud del rebound;
- duración de solidificación;
- energía latente liberada.

Si el modelo de equilibrio reproduce la evidencia dentro de una tolerancia defendible, **no se añade cinética solo por complejidad**.

### G2 — Kinetic model

Se abre únicamente si el caso G1 alineado no puede reproducir simultáneamente:

- subenfriamiento;
- onset de austenita primaria;
- onset eutéctico;
- recalescencia;
- duración de solidificación;

sin usar parámetros térmicos no defendibles.

En ese caso se implementará un nuevo `fvModel`, no un solver completo, manteniendo intacto el solver multi-región y separando la nueva física de las formulaciones B/C de buoyancy.

---

## 5. Proposed kinetic fvModel design — only after G1

Nombre de trabajo:

`hypoeutecticKineticSolidification`

Estado interno mínimo:

- `fD`: fracción dendrítica normalizada;
- `fE`: fracción eutéctica normalizada;
- `fS`: fracción sólida total;
- `alphaL = 1-fS`;
- oldTime para las variables cinéticas.

Parámetros mínimos:

- `TstartL`;
- `TstartE`;
- `dTcritD`;
- `dTcritE`;
- `betaD`, `betaE`;
- `gammaD`, `gammaE`;
- `deltaD`, `deltaE`;
- `f0D`, `f0E`;
- `theta`;
- `L`;
- `Cu`, `q`.

La fuente de energía se basará en la tasa de cambio de la fracción sólida. El momentum seguirá usando penalización por porosidad conforme disminuya `alphaL`.

La implementación debe conservar la posibilidad de elegir por separado la formulación de buoyancy; la cinética no debe mezclarse con la pregunta B-vs-C.

---

## 6. Data still required for quantitative validation

En el repositorio no existe actualmente una serie temporal experimental numérica del Quick-Cup.

En los archivos disponibles se localizó el paper de referencia y su figura experimental/modelo, pero no un CSV/XLSX con los puntos del termopar.

Sin una serie experimental numérica no se reportarán artificialmente RMSE, MAE o errores de tiempo.

Cuando exista la curva digitalizada/raw, las métricas mínimas serán:

- RMSE y MAE de T(t);
- error en T_start_L y T_start_E;
- error de tiempo de onset;
- error de Tmin;
- error de amplitud de recalescencia;
- error de duración de solidificación;
- comparación de dT/dt alrededor de ambos eventos.

---

## Current decision

1. **V3–V7 permanecen congelados como estudio numérico/buoyancy.**
2. **No se modifica todavía `solidificationMelting` para forzar recalescencia.**
3. El siguiente caso científico debe ser un **benchmark de equilibrio alineado con el experimento**.
4. Si ese benchmark demuestra una limitación estructural del modelo de equilibrio, se implementará el `fvModel` cinético de dos transformaciones.
