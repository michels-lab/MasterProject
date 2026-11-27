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

## Actualización 27-11-2026: campañas 200 s (catálogo de metadatos separado)

[campaign_200s_manifest_metrics.csv](campaign_200s_manifest_metrics.csv) contiene las 13 filas externas del registro, separadas de las métricas físicas de las 31 filas anteriores. Nueve manifiestos completos reabiertos en commits inmutables, con 104 partes declaradas y 3,361,897,523 bytes en total. Se verificó la igualdad del blob Git con el índice, los nombres de las partes consecutivos, los tamaños positivos y su suma exacta con archive_bytes, y la sintaxis de los SHA256 de partes. No se descargaron ni recalcularon los hashes de los binarios, ni se verificó el contenido interno de los reportes o logs. Los nueve declaran cobertura nativa completa y ausencia de campos volumétricos en el archivo. No se presume validación física.

- Adaptativa laptop: seis publicaciones completas, dos fallos A al intentar .68/.70 s. B14 MPI8 14276/14275 pasos con/sin tope; C14-3DB MPI8 15013/15012; C14-2D 11029 MPI8 con tope y 11028 serial sin tope (comparación confundida por modo de ejecución). Diferencia de un paso no demuestra trayectorias equivalentes, ni garantiza estabilidad, independencia temporal o velocidad de ejecución.
- Laboratorio fijo: tres manifiestos confirmados, 200000 pasos por caso a .001 s. C14-3DA reportado completo/auditado, rama v2 sin MANIFEST.json al consultar; no repetir CFD. Laptop fijo A reportado completo, auditoría pendiente. Actualizado RUN_CASE_REGISTRY.csv y catálogo general para las tres filas fijas verificadas como RUN_VERIFIED/AUDIT_MANIFEST_VERIFIED, no ANALYSIS_VERIFIED. El índice de manifiestos fija ahora las tres revisiones. Los 26 casos históricos y sus banderas no cambian.
- La media de paso 200/solver_steps es solo una magnitud derivada de los metadatos para las corridas completas. Los tiempos de fallo no representan último estado aceptado. No inferir pasos a partir de tiempos de fallo. No se importaron temperaturas, solidificación, velocidades ni conservación de los archivos compactos sin inspección de su contenido.
- Las tres corridas fijas reportan tiempos de pared en MAESTRIA_STATUS.json (B14-2D 2937.269257 s, C14-2D 35482.560214 s, C14-3DB 58392.772611 s); para A no existe cifra allí. No constituyen un benchmark controlado entre máquinas, mallas y condiciones. La comparación de pasos frente a adaptativo no es speedup medido.

Próximo: validar los archivos compactos por descarga local y SHA256, extraer sus reportes y series, distinguir diagnósticos nativos de perfiles recuperados, alinear tiempos guardados y coordenadas sin extrapolación; no convertir disponibilidad en cierre de energía/masa ni en independencia de malla. El catálogo general conserva métricas físicas vacías para las campañas 200 s hasta contar con sus fuentes internas.

## Uva + Granada: comparación física disponible de alpha1 y recuperación selectiva

Se localizaron las vistas analysis_preview en las nueve publicaciones completas fijadas. Se leyeron 9 series de metalMeanLiquidFraction/0/volFieldValue.dat, 2001 filas de dos columnas finitas por serie, eje exacto 0..200 s a .1 s con tolerancia 1e-7 s, alpha1 en [0,1] y ningún incremento positivo consecutivo. Total 18009 muestras, sin interpolación. Resultados y blobs en [alpha200s_comparison.csv](alpha200s_comparison.csv). La fuente exacta de cada fila es analysis_preview/postProcessing/metal/metalMeanLiquidFraction/0/volFieldValue.dat en source_commit. Se comparó cada adaptativo con su fijo laboratorio del mismo caso por tiempo físico común: RMSE en fracción 0.001275–0.002373 (0.128–0.237 puntos porcentuales), diferencias máximas 0.002546–0.0054534. Sesgo adaptativo menos fijo positivo en los seis. Los tres B3D alcanzan alpha1 medio registrado igual a cero a 129.4 (fijo) o 130 (ambos adaptativos) s; ninguno de los 2D llega a cero. No inferir contracción geométrica, validación QuickCup, energía discreta ni equivalencia de campos a partir de una media. C14-2D serial sin tope no es contraste MPI homogéneo. Las vistas previas no equivalen a comprobación del archivo binario ni a cobertura completa de sondas adaptativas a .1 s: el exportador selecciona exclusivamente tiempos exactos disponibles. Las nueve vistas de reportes indican solver_completed y cobertura nativa; SHA-256 del contenido aún no contrastado con los manifiestos.

El transferidor previo get-results solo consultaba el prefijo histórico y dependía de insumos locales. Nuevo tools/recover_published_200s.py: lista revisiones elegibles sin descarga por defecto; con --commit y --out recupera un único archivo publicado por SHA inmutable, verifica blob del manifiesto, tamaño y SHA256 de cada parte y archivo concatenado, miembros regulares bajo el caso esperado, límite de extracción (20 GiB por defecto), espacio disponible, hash del reporte y log y criterio de cobertura. Conserva originales, no reconstituye mallas ni campos volumétricos omitidos, no ejecuta solver. Cuatro pruebas de software publicadas; no se ejecutaron ni se descargaron archivos en esta sesión. Decisión: destino nuevo explícito, ninguna recuperación masiva automática. Consultar listados mediante python3 tools/recover_published_200s.py desde el checkout actualizado. El Caso A fijo no tiene publicación verificable con commit/manifiesto completo; no repetir CFD.

## Uva + Granada: temperatura, flujo, enfriamiento y energía a 200 s

[thermal_flow_energy200s_comparison.csv](thermal_flow_energy200s_comparison.csv) registra nueve publicaciones fijadas y seis archivos de diagnóstico por publicación (54 series, 108054 filas temporales). Se verificaron columnas finitas, 2001 registros por serie, eje 0..200 s a .1 s con tolerancia 1e-7 s; las comparaciones T/U usan tiempos coincidentes, sin interpolación. Las rutas fuente bajo analysis_preview/postProcessing/metal/ son temperatureProbe/0/T, temperatureProbe/0/U, metalBoundaryEnergyPower/0/surfaceFieldValue.dat, metalMeanCoolingRate/0/volFieldValue.dat, metalSensibleEnthalpy/0/volFieldValue.dat y metalTopPhiSum/0/surfaceFieldValue.dat. Los blobs respectivos se registran en el CSV; son vistas Git, no comprobación de archivos binarios completos. Las filas T y U corresponden a sonda central; enfriamiento a promedio volumétrico; potencia a frontera del metal (metalTop + metal_to_mold), no frontera externa metal+molde. No se evalúa aquí conservación discreta completa.

- RMSE T adaptativo vs fijo del mismo caso: B14 ~.2322 K, C14 MPI .7198 K, C14 serial .8717 K, 3DB ~.7746 K. T central final 1423 K en 2D y 1237.46/1237.55 K fijo/adaptativo 3DB. En 3DB primer T registrado estrictamente <1423 K: fijo 107.8 s, adaptativos 81 s; máxima diferencia 4.48 K. El cruce depende de precisión publicada y meseta térmica: no es nucleación, solidificación global ni tiempo experimental. B14 tiene 20 incrementos positivos consecutivos en las tres series muestreadas; no identificar recalescencia sin evidencia adicional.
- RMSE vectorial de U = sqrt(media(||U_adapt-U_fijo||²)), no RMSE de magnitudes; rango .0888–.2001 mm/s. Máximos de magnitud en sonda fija B14/C14/3DB: 8.15467/10.40743/23.06589 mm/s. No máximos de todo el dominio. La velocidad residual a 200 s en 2D adaptativos excede la fija; no afirmar equivalencia relativa en velocidades pequeñas.
- Enfriamiento medio volumétrico a 200 s fijo B14/C14/3DB: .1993246/.222582/1.455496 K/s. Máximo muestreado a .1 s: 7.351813/7.370135/12.44617 K/s. No confundir con derivada de sonda central.
- Cuadratura trapezoidal de potencia total de frontera metálica en .1 s: fijo B14 29033.04524 J, C14 28911.13300 J, 3DB 149329.47889 J. Diferencia adaptativo vs fijo relativa entre -.02368 y -.00639 %. Integrales advectivas registradas nulas o ~1e-13 J; máximo desacuerdo absoluto de columnas adv+heat vs total <=2.274e-13 W en las nueve tablas. No es balance global, no es integral al paso solver, no implica que el flujo térmico local esté verificado. Comparar geometrías requiere considerar áreas/volúmenes y no solo energía total.
- Cambios de entalpía sensible almacenada reportada (volIntegrate(rho,h)), fijo B14/C14/3DB -6816.3/-8404.2/-74708.7 J. No sumar directamente fracción volumétrica a energía sin densidad, calor latente y contrato de fase. No llamar a la diferencia con la energía de frontera residual de conservación.
- Flujo neto superior sum(phi) a .1 s: C14 2D y 3DB exactamente cero en todas las series; B14 máximo absoluto 7.623297e-20 kg/s entre variantes, integral firmada <=2.822e-20 kg en magnitud. Esto no prueba impermeabilidad cara a cara ni conservación global de masa.

No se ejecutó CFD ni se alteraron archivos originales. Se reintentaron dos consultas interrumpidas y se completaron las seis familias de series. C14-3DA sigue excluido de esta comparación por falta de publicación completa. Pendiente: inspección de campos cara a cara, energía latente y balance global metal/molde, datos solver-step y verificación de binarios. No se modifican hitos de validación física.
