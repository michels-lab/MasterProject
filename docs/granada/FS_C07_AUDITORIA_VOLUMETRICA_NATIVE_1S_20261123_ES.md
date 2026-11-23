# FS-C07 — auditoría volumétrica nativa de 1 s (20 estados, datos reales)

**Fecha:** 23-11-2026. **Clasificación:** CFD nativo completado; cambio de fase numérico observado; auditoría geométrica *raw* recuperada; **acotamiento de fase no aprobado**; ninguna contracción física implementada.

## Procedencia y límites

Fuente primaria: salida de terminal del investigador de `python3 analysis_tools/recover_fs_c07_native_phase_metrics.py --compact` sobre el caso existente:

`/home/michel/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4`.

La salida muestra `native_solved_to_time_s=1.0`, `native_solver_completed=true`, `complete_saved_native_phase_snapshots=20`, `read_only=true`, `any_native_field_edited=false`, `native_solver_was_reexecuted=false`. Se detectaron **ambos** monitores originales, `FS_C06_metalVoFVolume` y `FS_C06_solidMetalVolume`, y se compararon con integrales independientes de los 34,368 volúmenes de celda. No se modificaron campos originales ni se ejecutó el solver en esta auditoría.

**No debe confundirse el inventario volumétrico bruto con volumen sólido físicamente validado:** hay celdas con `alpha.metal.solid > alpha.metal` por encima de `1e-8`; las sumas se reportan **sin clip**, de forma independiente, para evaluar magnitud del defecto y tendencia de fase. Tampoco la variación de volumen VOF es por sí misma contracción de solidificación: FS-C07 no contiene `rho_l/rho_s`, fuente conservativa de cambio de fase ni alimentación acoplada.

## Hallazgos cuantitativos principales

| Magnitud | Valor | Alcance |
|---|---:|---|
| Volumen inicial `ΣV α.metal` | 4.801191628e-5 m³ = **48.01191628 cm³** | Inventario VOF inicial |
| Volumen `ΣV α.metal` a 1.00 s | 4.8011038266835194e-5 m³ = **48.01103827 cm³** | Integral raw |
| Volumen `ΣV α.metal.solid` a 1.00 s | 2.403591085462431e-6 m³ = **2.40359109 cm³** | Integral raw, no aceptación de fases |
| Volumen `ΣV(α.metal−α.metal.solid)` a 1.00 s | 4.560744718137276e-5 m³ = **45.60744718 cm³** | Diferencia raw, puede incluir asignaciones líquidas locales negativas |
| Razón bruta sólido/metal a 1.00 s | **5.006330152878137 %** | Proporción geométrica numérica, no fracción sólida validada |
| `ΔV_metal=V(1)-V(0)` | **−8.7801316480e-10 m³ = −0.878013 mm³** | **−0.00182874 %** del volumen inicial; no equivale a contracción física |
| Exceso integrado `ΣV max(α_s−α_m,0)` a 1.00 s | **1.7680724185913767e-12 m³ = 0.00176807 mm³** | **0.0000735596 %** del volumen sólido raw; NO cero |
| Exceso integrado máximo entre estados | **6.127289371568527e-12 m³ = 0.00612729 mm³** | Ocurrió a **0.40 s** |
| Máximo exceso local de fracción entre estados | **6.1813429e-6** | Ocurrió a **0.20 s**, celda 30580; distinto del instante de mayor integral |
| Celdas con error local >1e-8 al final | **378/34368 (1.10 %)** | Sigue fallando gate de acotamiento |
| Celdas núcleo `α_m>=0.5` bajo 1473 K a 1s | **1160** | Primer instante guardado no nulo **0.10 s**; 1473 K es C14 provisional |
| Volumen de metal núcleo por debajo de Tliq a 1s | **2.3021914743112273e-5 m³** | **48.19955593 %** del inventario metálico *núcleo*, no sólido global |
| Volumen sólido raw integrado solo en núcleo a 1s | **2.3839739866602345e-6 m³** | Parte de la suma sólida raw total, no solidificación aprobada |

A `t=1s` la mínima temperatura del metal núcleo es `1447.96242737 K` y la máxima `1491.54833384 K`. El máximo local de `alpha.metal.solid` es `0.500401199262`, que **no significa 50 % global**. El conteo `32933` celdas con `alpha.metal.solid>0` incluye cantidades ínfimas en aire/interfaz.

### Serie temporal reproducida desde los datos entregados

Las unidades de `V_m` y `V_s` son **cm³**. `E_{s>m}` es el exceso integrado en **mm³**. **No son fracciones corregidas**.

| t [s] | V_m raw [cm³] | V_s raw [cm³] | 100·V_s/V_m [%] | E_s>m [mm³] | Celdas >1e-8 |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 48.01196597 | 0.00124650 | 0.002596 | 0.00006215 | 39 |
| 0.10 | 48.01196786 | 0.00054637 | 0.001138 | 0.00029913 | 65 |
| 0.15 | 48.01188490 | 0.00647426 | 0.013485 | 0.00080714 | 211 |
| 0.20 | 48.01190828 | 0.03376485 | 0.070326 | 0.00297438 | 187 |
| 0.25 | 48.01195496 | 0.12382418 | 0.257903 | 0.00411403 | 550 |
| 0.30 | 48.01194058 | 0.22360325 | 0.465724 | 0.00570169 | 612 |
| 0.35 | 48.01179451 | 0.33123148 | 0.689896 | 0.00604462 | 641 |
| 0.40 | 48.01179796 | 0.44459296 | 0.926008 | **0.00612729** | 598 |
| 0.45 | 48.01150540 | 0.56596022 | 1.178801 | 0.00196256 | 390 |
| 0.50 | 48.01144735 | 0.70364378 | 1.465575 | 0.00143139 | 423 |
| 0.55 | 48.01143044 | 0.85430427 | 1.779377 | 0.00171019 | 420 |
| 0.60 | 48.01138992 | 1.01228459 | 2.108426 | 0.00188354 | 462 |
| 0.65 | 48.01135507 | 1.18250743 | 2.462974 | 0.00185649 | 439 |
| 0.70 | 48.01130799 | 1.36150939 | 2.835810 | 0.00181933 | 376 |
| 0.75 | 48.01126494 | 1.54172775 | 3.211179 | 0.00169584 | 368 |
| 0.80 | 48.01121710 | 1.71953987 | 3.581538 | 0.00162712 | 360 |
| 0.85 | 48.01117598 | 1.89462449 | 3.946216 | 0.00168597 | 349 |
| 0.90 | 48.01113008 | 2.06694285 | 4.305133 | 0.00179863 | 424 |
| 0.95 | 48.01108134 | 2.23654898 | 4.658402 | 0.00165528 | 400 |
| 1.00 | 48.01103827 | **2.40359109** | **5.006330** | 0.00176807 | 378 |

**Importante:** la integral `V_s` **disminuyó** entre los primeros dos estados 0.05 y 0.10 s (`0.00124650→0.00054637 cm³`) antes de crecer después. Por tanto, decir que “creció de modo monótono en todos los tiempos” sería falso. Esto justifica una auditoría de inicialización y secuencia de actualización del modelo.

### Concordancia con los monitores nativos

El reporte independiente confirma `native_volFieldValue_metal_monitor_found=true` y `native_volFieldValue_solid_monitor_found=true`. Al último estado, OpenFOAM registró:

```text
Native FS_C06_metalVoFVolume = 4.801103826683e-05 m3
Geometric independent ΣV alpha.metal = 4.8011038266835194e-05 m3
Difference = 5.197394164352387e-18 m3

Native FS_C06_solidMetalVolume = 2.403591082361e-06 m3
Geometric independent ΣV alpha.metal.solid = 2.403591085462431e-06 m3
Difference = 3.101431041645881e-15 m3
```

Los monitores son coherentes con las integrales independientes dentro de la precisión reportada. La mayor discrepancia relativa de los **20 estados** es aproximadamente `1.18e-10` para inventario VOF y `1.18e-8` para sólido raw. Esto es un control de reproducibilidad de postproceso, **no un balance de masa**.

El `V_​metal` perdió 0.878013 mm³ en 1 s; no confundir ese cambio con volumen que se contrajo por diferencia de densidad. Hay flujo de metal no nulo por fronteras abiertas (en `atmosphereLowerSides` al último instante `+7.54288884513e-6 kg/s`); falta integrar todos los `alphaRhoPhi.metal` con orientación correcta, comparar con masa metálica auténtica (no `volIntegrate(rho)` de mezcla) y distinguir compresibilidad/advección de contracción.

### Calidad/aceptación

- **PASS con evidencia**: `foamMultiRun` Foundation14 a t=1 s; 20 estados ASCII completos; integrales nativas de volumen metal/sólido reproducidas; `alpha.metal.solid` positivo y cruce de Tliq C14 de cribado observados.
- **FAIL con evidencia**: restricción local `0<=alpha_solid<=alpha_metal<=1` con `1e-8` de tolerancia: celdas en todos los 20 estados. El error volumétrico integrado es pequeño, pero **no habilita declarar consistencia estricta**.
- **NO PROBADO**: masa metal conservada respecto a la salida/entrada de metal, energía sensible+latente, independencia de `Δt`/malla, Tliq y propiedades por CE/S/JMatPro, formación de cavidad, alimentación, metal sólido estacionario/móvil, curvas QuickCup.

**Próximo bloque físico**: caracterizar espacialmente las celdas `alpha_solid>alpha_metal` (interfaz y momento de actualización), y diseñar acoplamiento de `Gamma`, `rho_s(T)`, `rho_l(T)`, presión, energía y superficie libre; no borrar el fallo con `clip` del archivo histórico.

### Fuente y hashes de campos reales a t=1 s

- `alpha.metal`: `578a317dba2ac906cd76156257397131a15a73aa6406a9d4b30078dea48598a6`.
- `alpha.metal.solid`: `a591efdb79b4a4a1ed09fa8a7f4d8bfc19c082fadae0b9105806e6f78f033575`.
- `T.metal`: `5d67c4b58cea009b8ab6824a50ed2aa4cb70f4905782a537d425620a05c3c240`.

No se recibió copia de los archivos nativos en este turno; los hashes son los valores que reportó en la salida del analizador real el investigador. La transcripción integra resultados observados, no simula ni sustituye el archivo de origen.
