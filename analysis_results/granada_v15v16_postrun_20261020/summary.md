# Granada Grande — auditoría numérica read-only V15/V16 (2026-10-20)

**Origen real:** workflow CI [39390605406](https://github.com/michels-lab/QuickCup-Solidification/actions/runs/39390605406), sobre head de PR #20 `47c6dcd04c725bce97232b430dd0b0ddfaa54cfe`. El job ejecutó 6 pruebas sintéticas (PASS), luego inspeccionó seis casos originales versionados y cuatro parejas térmicas (PASS de presencia de fuentes y cálculo). Los informes `evidence.json` y `pair_metrics.csv` están en el artefacto de ese run, no se publican como salida de solver.

**No se ejecutó OpenFOAM en CI.** Esta es una auditoría de muestras/series almacenadas, no nueva corrida, validación física, cierre de energía ni validación experimental. Los datos del investigador, malla y casos originales quedan intactos. El auditor sigue como **PR borrador**, no fusionado a main.

## Diagnóstico de Courant y continuidad almacenada

| Caso | max Courant observado | Registros > maxCo 0.25 | Último contCumulative disponible |
|---|---:|---:|---:|
| B14 | 0.0673434 | 0 | -0.031019 |
| B15 | **0.255553** | **34** | -0.0311059 |
| B16 | 0.0674108 | 0 | -0.0310064 |
| C14 | 0.0650864 | 0 | 4.44346e-13 |
| C15 | **0.258115** | **35** | 2.05427e-14 |
| C16 | 0.0651054 | 0 | 4.44212e-13 |

La última continuidad se informa desde el **último renglón realmente disponible** en el archivo `logs/contCumulative_0`, no necesariamente del instante físico 10 s; comparar su hora y las series completas antes de etiquetar los números «a 10 s». Un Courant que excede 0.25 es alerta para estudiar el controlador adaptativo, **no evidencia suficiente de divergencia**. La continuidad acumulada de la familia B de aproximadamente −0.031 sigue abierta como problema físico/numerico de dominio cerrado.

## Comparación de temperaturas centrales por tiempo físico

Grilla común de 0.01 s, interpolación lineal solo dentro del intervalo compartido, sin extrapolación; datos de `postProcessing/metal/temperatureProbe/0/T` y sus identificadores SHA-256 en el JSON del workflow.

| Pareja hijo - padre | RMSE (K) | máximo absoluto de ΔT (K) |
|---|---:|---:|
| B15 – B14 | 0.137902 | 0.280 |
| C15 – C14 | 0.140024 | 0.308 |
| B16 – B14 | 0.015632 | 0.030 |
| C16 – C14 | 0.020080 | 0.050 |

Las diferencias son de **una sonda**; no prueban equivalencia de perfiles, velocidad, energía, fracción líquida, ni frentes metalúrgicos. Comparar contra la revisión preliminar anterior no cierra las puertas J0/G1.

## Incidente del flujo de evidencia y reparación

La primera ejecución del PR informó seis alertas falsas al tratar como fila de dos columnas un marcador original aislado `0` al inicio de cada archivo `CourantMax_0`. Se limitó el reconocimiento a **un único** primer marcador en archivos Courant y se añadió una prueba que rechaza dos marcadores. En el run final quedan **dos alertas científicas reales**, las 34/35 excedencias de los casos adaptativos B15/C15.

## Estado y siguiente bloque

- Estado del auditor: **candidato PR #20; seis tests PASS y CI de fuente real PASS en head 47c6dcd**. El workflow exige seis fuentes de T/Courant/continuidad y cuatro comparaciones válidas; sus alertas físicas se reportan, no ocultan.
- Registros `RUN_CASE_REGISTRY.csv`, `CASE_NOTES`, J0/JMatPro, G1/experimento y auditoría física V15/V16: **no cerrados** ni cambiados por este cribado.
- Siguiente trabajo independiente: análisis termodinámico/multirregión de calor sensible + latente, potencia en metalTop y metal/molde, revisión de conservación y eventos de fase; solo a partir de campos/flujos dimensionalmente correctos. C3D-01 continúa en PR #18/#19 con owner propio.
- FoamLens será consumidor científico potencial del contrato JSON/CSV del PR #20 solo cuando exista importador explícito, probado; no confundir documentación de protocolo con funcionalidad disponible en la aplicación.
