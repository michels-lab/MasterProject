# FS-C07 — 20 estados nativos: solidificación observada y defecto de asignación metal/sólido

Fecha 2026-11-23. **Reporte sobre evidencia real generada en WSL**, entregada por el investigador como salida de `diagnose_fs_c07_phase_allocation.py --compact`. SHA-256 del texto compartido en la conversación: `8a3b1c31bcbcfddec65815c52f4f3a8a6e5d41f162bba41ed653bd9ca7e2b45e`; este hash corresponde a la copia de texto recibida, **no a archivos OpenFOAM nativos**. Los campos CFD originales y sus hashes siguen en la laptop del investigador.

## Conclusión sin alterar el modelo

**El solver Foundation14 COMPLETÓ realmente 1.0 s y guardó 20 estados completos de `alpha.metal`, `alpha.metal.solid`, `T.metal`.** La fase sólida absoluta `alpha.metal.solid` alcanza `0.500401199262` en alguna celda a `t=1s`, y `1160` celdas con `alpha.metal >= 0.5` registran `T.metal <=1473 K`. Esto constituye **evidencia de cambio de fase NUMÉRICO NATIVO** en el modelo provisional de C14, no prueba calibración JMatPro, porcentajes físicos globales ni contracción.

El analizador científico original falló legítimamente porque existen celdas con `alpha.metal.solid > alpha.metal + 1e-8`. Esto es principalmente una **violación del encaje de fase sólido–metal**, no un gran VOF global menor que cero ni metal por encima de uno. No justificar clip global ni “reparar” campos archivados.

`alpha.metal.solid` es fracción absoluta **respecto a volumen de celda**, no la fracción sólida condicional de su metal. `max(alpha.metal.solid)=0.500401...` NO significa 50.04 % del volumen metálico global solidificado. Más de treinta mil celdas con `alpha.metal.solid>0` incluye cantidades trazas en aire/interfaz; no contar esas celdas como material metálico efectivamente sólido.

## Evolución real de los 20 campos nativos

Criterio `core=` celdas con `alpha.metal>=0.5`; liquidus **solo de cribado** C14 `1473 K`. No se midieron volúmenes integrados con estos datos todavía.

| t [s] | max(alpha.metal.solid) | core metal T<=1473 K [celdas] | celdas con violación >1e-8 | violación máxima absoluta |
|---:|---:|---:|---:|---:|
| 0.05 | 0.00103272 | 0 | 39 | 1.12e-7 |
| 0.10 | 0.00278749 | 4 | 65 | 5.40e-7 |
| 0.15 | 0.0490283 | 12 | 211 | 1.26e-6 |
| 0.20 | 0.0994852 | 168 | 187 | **6.1813429e-6** |
| 0.25 | 0.141880 | 252 | 550 | 4.38e-6 |
| 0.30 | 0.177429 | 276 | 612 | 5.04e-6 |
| 0.35 | 0.208515 | 324 | **641** | 3.18e-6 |
| 0.40 | 0.236601 | 392 | 598 | 4.07e-6 |
| 0.45 | 0.262568 | 488 | 390 | 9.13e-7 |
| 0.50 | 0.286961 | 676 | 423 | 5.35e-7 |
| 0.55 | 0.310126 | 760 | 420 | 4.74e-7 |
| 0.60 | 0.332296 | 856 | 462 | 5.80e-7 |
| 0.65 | 0.353522 | 1016 | 439 | 5.60e-7 |
| 0.70 | 0.373799 | 1128 | 376 | 5.36e-7 |
| 0.75 | 0.393167 | 1128 | 368 | 6.03e-7 |
| 0.80 | 0.411693 | 1132 | 360 | 5.35e-7 |
| 0.85 | 0.435340 | 1136 | 349 | 5.74e-7 |
| 0.90 | 0.459506 | 1136 | 424 | 5.77e-7 |
| 0.95 | 0.481042 | 1156 | 400 | 5.16e-7 |
| 1.00 | **0.500401** | **1160** | **378** | 4.96712638e-7 |

**El primer instante GUARDADO con al menos una celda de núcleo bajo Tliq es 0.10 s.** Por resolución temporal, el cruce ocurrió en algún momento entre 0.05 y 0.10 s, **no** necesariamente exactamente 0.1 s. A `t=1s`, `T.metal` en núcleo varía entre `1447.96242737` y `1491.54833384 K`.

## Ubicación y magnitud exacta del defecto (sin inferir geometría)

- Primer estado almacenado, `t=0.05 s`: celda **19072**, `alpha.metal=3.71157060936e-6`, `alpha.metal.solid=3.82400195266e-6`; exceso `1.1243134329999986e-7`. Se observaron `39` celdas por encima de `1e-8`.
- Peor violación absoluta entre 20 estados, `t=0.20 s`: celda **30580**, `alpha.metal=0.00134523317659`, `alpha.metal.solid=0.00135141451949`; exceso `6.181342900000129e-6` (`0.4595%` respecto a `alpha.metal` de esa celda). Aunque pequeña en fracción de volumen de celda, **excede 618 veces el umbral 1e-8**.
- Máximo número de celdas por encima del umbral: `641` a `t=0.35 s` (`1.865%` de las 34,368 celdas).
- Último estado, `t=1.0 s`: celda **12400**, `alpha.metal=3.47762515e-6`, `alpha.metal.solid=3.97433778811e-6`; exceso `4.967126381099997e-7` (`14.28%` relativo respecto al metal **local muy pequeño**). `378` celdas por encima del umbral (`1.10%` de 34,368).
- `20,459` celdas incumplen desigualdad matemática estricta a `t=1s` (contando infinitesimales), pero **solo 378** superan la tolerancia `1e-8`. Esta distinción es fundamental. No hay evidencia de `alpha.metal>1`: el máximo registrado en los 20 estados fue `1.0`.

La tabla anterior no contiene integrales volumétricas absolutas: de los números máximos, conteos y temperaturas **no es posible derivar** el `V_s` global o masa sólida total sin el campo por celda y los volúmenes de la malla. El primer analizador abortó precisamente antes de obtener esas integrales.

## Hipótesis técnica (NO demostrada todavía)

La implementación Foundation14 `VoFSolidificationMelting::correct()` limita `alphaSolid_ = min(...,alphaVoF)` **cuando ese método se ejecuta**; la fase `alpha.metal` también se transporta por VOF. Si después de actualizar `alphaSolid` cambia `alpha.metal`, puede quedar `alphaSolid > alphaVoF` en algunos estados guardados. Es plausible que este sea un desfase de actualización/advección, especialmente en celdas interfaciales con `alpha.metal` minúsculo, pero **requiere verificar el orden temporal del solver y localización física**. La solución científica no es recortar el `alphaSolid` de archivos originales, sino diseñar una evolución conservativa del metal líquido/sólido, idealmente vinculada a sus densidades reales y a la superficie libre.

## Recuperación cuantitativa: sin nueva CFD, sin alterar evidencias

Archivo nuevo:

- [`analysis_tools/recover_fs_c07_native_phase_metrics.py`](../../analysis_tools/recover_fs_c07_native_phase_metrics.py). Integra **las 20 instantáneas nativas por volumen geométrico** de las 34,368 celdas. Reporta **separadamente y sin clip**:
  - `V_metal_raw=ΣVc·alpha.metal`;
  - `V_solid_raw=ΣVc·alpha.metal.solid`;
  - `V_liquid_raw=ΣVc·(alpha.metal-alpha.metal.solid)`;
  - volumen integrado de desbordamiento local `ΣVc·max(alpha.metal.solid-alpha.metal,0)`;
  - magnitud de contribuciones negativas de metal/sólido y de metal >1;
  - volúmenes y celdas metálicas del núcleo por debajo de liquidus numérico de cribado;
  - comparación de las integrales por celdas con monitores nativos `volFieldValue.dat` si existen y coinciden temporalmente, guardando el residuo sin maquillar resultados;
  - SHA-256 de las tres variables originales por instante.
- Siete pruebas sintéticas independientes [`test_recover_fs_c07_native_phase_metrics.py`](../../analysis_tools/test_recover_fs_c07_native_phase_metrics.py), y CI estático añadido; **aún no verificados en la laptop**.
- La etiqueta `raw` significa que los valores son sumas numéricas del campo **sin corregir violaciones**. Se calculan para medir el tamaño del problema y recuperar la evolución térmica, **no para otorgar validez física al volumen sólido con `s>a`**.

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
git fetch origin research/fs-c02-metal-air-vof-20261117
git switch --detach FETCH_HEAD
python3 analysis_tools/recover_fs_c07_native_phase_metrics.py --compact \
  ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
```

**No repetir `foamMultiRun`, no borrar las 10,868 carpetas de tiempo de un caso archivado, no modificar campos `alpha.metal` o `alpha.metal.solid` de la corrida aceptada como origen de datos.**

## Puerta de aceptación

- **PASS demostrado:** solver Foundation14 1.0 s, veinte estados completos, producción de un campo sólido positivo y celdas metálicas por debajo de liquidus C14 de cribado.
- **FAIL comprobado:** restricción `0<=alpha.metal.solid<=alpha.metal<=1` en todas las celdas con margen 1e-8.
- **PENDIENTE:** magnitud integrada de exceso por volumen, auditoría de masa por fase y salida de metal, energía sensible+latente, calibración JMatPro por composición, evolución conservativa y alimentación, contraste QuickCup, malla/Δt convergidos.
