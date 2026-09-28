# Matriz de validación — QuickCup Solidification

## Objetivo

Determinar la **mínima física adicional necesaria** para explicar la evidencia experimental sin confundir:

1. error / sensibilidad numérica;
2. diferencias de implementación de buoyancy;
3. diferencias de parámetros térmicos y condiciones de frontera;
4. limitaciones del modelo de solidificación de equilibrio;
5. necesidad real de una ley cinética con subenfriamiento y recalescencia.

Esta matriz congela V3–V7 como evidencia numérica y evita modificar esos casos históricos para introducir física nueva.

---

## 1. Lo que V3–V7 ya establecen

### Sensibilidad numérica

Los resultados versionados muestran:

- B3 → B5 → B7: mediana del cociente de coupling de `p_rgh` (R) = 0.6054 → 0.5975 → 0.6032.
- C3 → C5 → C7: 0.8127 → 0.8010 → 0.8088.
- Outer4 no produce una mejora monotónica respecto a outer3.
- El costo de outer4 aumenta aproximadamente 89% en B y 86% en C respecto al baseline outer2.
- B4/C4 con dos energy correctors no modifican materialmente la solución central respecto a B3/C3.
- V6 adaptive reduce fuertemente el costo, pero todavía requiere comparación física antes de aceptarse como sustituto del timestep fijo.

**Estado:** la diferencia B/C no se explica por falta de más outer/energy correctors dentro del rango probado.

### Comportamiento térmico/fase central

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

**Interpretación aceptada:** el rebound C es robusto frente a los cambios numéricos probados, pero en el modelo actual coincide con **remelting local**. No debe etiquetarse por sí solo como recalescencia metalúrgica por nucleación.

---

## 2. Auditoría contra el benchmark Quick-Cup hipereutéctico/hipoeutéctico de Chiumenti et al.

Referencia de trabajo:

M. Chiumenti, M. Cervera, E. Salsi, A. Zonato, *A phenomenological model for the solidification of eutectic and hypoeutectic alloys including recalescence and undercooling*.

El paper usa el Quick-Cup hipereutéctico/hipoeutéctico para calibrar/validar una ley cinética capaz de reproducir crecimiento dendrítico, transformación eutéctica, subenfriamiento y recalescencia.

### Comparación de condiciones

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

### Hallazgo crítico

El caso actual empieza a **1500 K (1226.85 °C)**, mientras el benchmark hipereutéctico/hipoeutéctico del paper inicia a 1300 °C y usa **1260 °C como inicio de la transformación dendrítica**.

Por tanto, si se usa ese experimento como objetivo de validación, la simulación actual empieza aproximadamente **33 °C por debajo del T_start_L del paper**. No es científicamente válido atribuir una discrepancia con la curva experimental únicamente a la ausencia de recalescencia cinética antes de alinear estas condiciones.

---

## 3. Qué contiene el modelo del paper que no contiene solidificationMelting

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

## 4. Puertas de decisión

### G0 — Paridad de benchmark

Antes de calibrar o crear una ley cinética:

- usar temperatura inicial del experimento objetivo;
- reproducir temperatura inicial del molde;
- reproducir resistencia/HTC metal–molde;
- reproducir HTC exterior;
- usar propiedades térmicas consistentes con el experimento;
- fijar ubicación equivalente del termopar;
- documentar incertidumbre de cada parámetro.

**Estado actual: NO cumplida.**

### G1 — Caso de equilibrio alineado

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

### G2 — Modelo cinético

Se abre únicamente si el caso G1 alineado no puede reproducir simultáneamente:

- subenfriamiento;
- onset de austenita primaria;
- onset eutéctico;
- recalescencia;
- duración de solidificación;

sin usar parámetros térmicos no defendibles.

En ese caso se implementará un nuevo `fvModel`, no un solver completo, manteniendo intacto el solver multi-región y separando la nueva física de las formulaciones B/C de buoyancy.

---

## 5. Diseño propuesto del fvModel cinético — solo después de G1

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

## 6. Datos que faltan para completar la validación cuantitativa

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

## Decisión actual

1. **V3–V7 permanecen congelados como estudio numérico/buoyancy.**
2. **No se modifica todavía `solidificationMelting` para forzar recalescencia.**
3. El siguiente caso científico debe ser un **benchmark de equilibrio alineado con el experimento**.
4. Si ese benchmark demuestra una limitación estructural del modelo de equilibrio, se implementará el `fvModel` cinético de dos transformaciones.


---

## Regla permanente de revisión numérica — residuos de presión

A partir del 28 de septiembre de 2026, **todo caso controlado B/C nuevo o reejecutado** debe incluir una auditoría explícita de la evolución de los residuos de presión antes de considerarse numéricamente revisado.

La revisión mínima obligatoria es:

1. evolución temporal del residual inicial de cada solve de `p_rgh`;
2. evolución temporal de `p_rghFinalRes`;
3. las mismas series respecto al índice de timestep, además del tiempo físico;
4. contracción lineal por solve:
   `C_p = p_rghFinal / p_rghInitial`;
5. contracción del acoplamiento exterior presión–velocidad:
   `R_p_outer = r_p(first solve, last outer) / r_p(first solve, first outer)`;
6. fracción de timesteps con `R_p_outer > 1`;
7. continuidad acumulada/global;
8. Courant máximo;
9. costo computacional;
10. comparación de los campos físicos para confirmar que una mejora aparente de residuos no cambia indebidamente la solución.

Un paso de tiempo menor **no se considera automáticamente mejor**. Si `p_rgh` y/o `p_rghFinalRes` muestran una meseta mientras aumenta el número de timesteps y el costo, debe reportarse como posible estancamiento del acoplamiento presión–velocidad.

El script oficial para esta auditoría es:

`analysis_tools/pressure_stagnation_analysis.py`

El script descubre automáticamente todos los directorios B/C que contengan `logs/`, por lo que la regla se extiende a casos futuros sin necesidad de añadirlos manualmente.

La etiqueta `plateau_candidate` del script es únicamente un indicador de cribado: significa que la mediana del residual cambia menos de 0.25 décadas log10 durante el 25 % final de las muestras disponibles. **No constituye por sí sola un criterio de convergencia.** La magnitud del residual, las curvas completas, la continuidad y la solución física deben revisarse conjuntamente.
