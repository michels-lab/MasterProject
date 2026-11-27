# Catálogo de evidencia de MasterProject — 27-11-2026 (Uva + Granada)

51 filas de RUN_CASE_REGISTRY.csv (blob 9ebacf7e5c9c864b6e10dbe7ba31713fcafdacf6), 31 con alguna métrica importada: las 26 históricas más B14, C14, C11-energy2, A y B. 20 filas conservan estado y referencia sin importar métricas todavía; celdas vacías no son ceros ni ausencia de resultados. Este catálogo NO modifica el consolidado histórico ni el registro ni equivale a 51 casos validados. No fusionar campañas de 10 y 200 s, contracción ni sustitutos térmicos.

Fuentes adicionales (todas en main al corte, revisión c348fcdf30417c94d594e541e1974a55de4703ee):
- case_metrics.csv histórico: blob 084210e0fc6184a023faa0feb13ef8dbd4526d1f; métricas archivadas sin recalcular las 26 filas completas.
- V14 summary.md: cdeed9dcb55aff00c65f32b5e2506574476cac5f.
- C11-energy2 summary.md: 44072e7018a455f2b89b75a2d039a1692bb15247.
- A: docs/review/C14_A_2D_NATIVE_PROBES_20261127_ES.md (e6fbbb6b5e54f938d6616352076fe2ed3fec9330).
- B: cases_3d/C3D_05_step_gmsh_conformal/c14_physics/README.md (49e584a5e12043a4e1a2b6f3786df39bfd97e8e7); alpha1 volumétrico 10 s reportado; no sonda equivalente a 1 ms.

Las columnas *_last indican último registro disponible de cada magnitud, no necesariamente idéntico tiempo. probe_last_s se refiere exclusivamente a la sonda. Los estados se importan literalmente del registro, no se promueven por este catálogo. No sustituye la revisión de logs, campos ni validación experimental.

## Hallazgos nuevos: auditoría de comparación histórica

bc_pair_metrics.csv blob fea218c1c97d6bfaa6c98419a4b557d12ba1be93: 13 pares; V6/V8 T solo 13/12 tiempos exactamente comunes hasta 4.91714/3.98888 s; alpha media solo t=0 en ambos, RMSE cero sin capacidad discriminante. bc_profile_metrics.csv blob a915e803dc09366ab035079fce8cf0f3a40a0c49: 260 filas, 40 con tiempos distintos; p.ej. V6 B=9.946515 y C=9.182456 s. No usar como comparación a tiempo común. profile_inventory.csv blob 72b8eec99ea752c86c0da94c30eae466b28907f9: 104 disponibles. status.tsv blob 9ab2ee43d3186a08d0cfe639bd7849a714874138: 26 filas. El generador legacy compara perfiles por posición de fila y columna fija, no verifica coordenadas ni encabezado; omite filas no numéricas, sobreescribe duplicados en series y puede integrar intervalos faltantes. Se mantiene su algoritmo únicamente para reproducibilidad histórica, protegido con --out obligatorio e independiente. Los 26 estados de corrida se conservan.

## Recalculo de sensibilidad V6 y V8

Ocho series completas leídas de la revisión fijada anterior. Dos columnas finitas, eje estrictamente creciente. Comparación lineal interpolada sobre cuadrícula de 0.01 s dentro de la intersección de soportes; sin extrapolación. El sesgo y diferencia son C-B. Las muestras interpoladas no son nuevos resultados CFD independientes.

| Par | Magnitud | Soporte evaluado s | N | RMSE | Sesgo | Máxima abs | Diferencia último tiempo común |
|---|---|---|---:|---:|---:|---:|---:|
| V6 | T K | 0–9.99 | 1000 | 14.928459535 | -7.528485983 | 32.030000 | -0.078157895 |
| V8 | T K | 0–9.99 | 1000 | 14.923145394 | -7.525511764 | 32.022903226 | -0.070000000 |
| V6 | alpha1 volumen medio | 0–9.18 | 919 | .003524492 | -.002470482 | .005622833 | -.002849867 |
| V8 | alpha1 volumen medio | 0–9.18 | 919 | .003523894 | -.002470232 | .005622965 | -.002849768 |

T fuentes B6/C6 2811/1585 muestras hasta 9.99966/10.0034 s; B8/C8 2811/1585 hasta 9.9997/10.004 s. Alpha media B6/C6 29/16 muestras hasta 9.946515/9.182456 s; B8/C8 29/16 hasta 9.946556/9.182888 s. El paso de análisis 0.01 s no representa resolución física adicional de esas 16–29 muestras. No afirmar resultados comparativos de alpha media a 10 s.

| Caso | T blob | Alpha media blob |
|---|---|---|
|B6_adaptiveDt|2a4dfadc1fb011fdc682a58cc6179801f87abfb8|fb13c0c52be5343052ef83b96de388a8e4b80de9|
|C6_adaptiveDt|b04148a0683f53df1f115786efd4376f099bfbcc|1b793f820171304d142fde44761f73cb1d86f217|
|B8_adaptiveOuter4|c8b5815f1270b4e6bb4cd42cae5b88d323933554|764a868bd7dd97dd7ffaf65394c1674930c224ab|
|C8_adaptiveOuter4|2f8426273584fddcb8df2a0f6f39ac1c0a5d6dde|fc5ab15c8184013e450b08aae7348ae8b412eaa0|

Rutas: cases_controlled_buoyancy/<caso>/postProcessing/metal/temperatureProbe/0/T y metalMeanLiquidFraction/0/volFieldValue.dat. Recalculo directo en lectura de datos GitHub, sin OpenFOAM. No se reejecutó el generador legacy modificado; no se corrigieron aún sus algoritmos ni se verificó la semántica de todos los campos históricos. Mantener originales intactos.
