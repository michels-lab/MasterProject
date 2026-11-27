# Uva + Granada — comparación de sondas nativas A / C14-2D

27-11-2026. Comparación directa de cuatro series originales completas, sin CFD. Fuentes fijadas: A 1ac7269161ce7f12c73d109571efbf35f572481a, 2D 03c543cad38bbc033a44d7d6c62b788f943116ed. Directorios cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful y cases_controlled_buoyancy/C14_topFixedFlux_explicitRef, ambos postProcessing/metal/temperatureProbe/0/.

| Modelo | T blob | alpha1 blob | Coordenada m |
|---|---|---|---|
|A|f12ed43f6eb859653ffb7302d5838095e519fd45|0f8dd3512da8916ff06f457893264e4cc4444191|(.0259,-.02,.0259)|
|2D|fd158909490dfd7de7a368096cc6017a91f307e9|383995c6ab8153d6f21cf1bb5a0b7ad45e406a9e|(.02,.02,.005)|

Cada serie tiene 10001 filas de dos columnas finitas, eje 0..10 s a .001 s (tolerancia 1e-9 s); no interpolación. Puntos nominales centrales a 20 mm de altura, no medias espaciales. T inicial 1500 K, alpha1 inicial 1. Valores finales A/2D: T 1466.36/1464.19 K, alpha1 .973494/.964815. Ninguna de las cuatro series tiene incrementos positivos consecutivos en los valores archivados. No implica ausencia de recalescencia en todo el dominio ni valida física experimental.

Primer registro T<1473 K: A 3.451 s, 2D 4.720 s. Primer registro alpha1<.999: A 3.672 s, 2D 4.803 s. Son cruces de umbral de muestra, no tiempos exactos de nucleación.
RMSE T 6.70587043568 K; sesgo A-2D -1.77617138286 K; diferencia absoluta máxima 21.25 K. RMSE alpha1 .00679043872209; sesgo A-2D .00388870862914; diferencia absoluta máxima .01102. A cruza antes el liquidus pero acaba más caliente en el punto central. No confundir con el promedio de línea inferior registrado en C14_2D_A_B_COMMON_STATIONS_20261127_ES.md.

| t s | T A K | T 2D K | alpha1 A | alpha1 2D |
|---:|---:|---:|---:|---:|
|0|1500|1500|1|1|
|2|1498.09|1499.96|1|1|
|4|1472.26|1477.40|.997113|1|
|5|1471.12|1471.81|.992510|.995451|
|6|1470.23|1467.79|.988965|.979262|
|8|1468.24|1465.71|.981002|.970876|
|10|1466.36|1464.19|.973494|.964815|

## Automatización integral preparada
analysis_tools/compare_c14_three_models.py y test_compare_c14_three_models.py, workflow manual .github/workflows/c14-three-model-comparison.yml. Fija tres commits, verifica coordenadas nominales de A/2D y reporte B, rechaza colisiones y datos no físicos, usa intersecciones sin interpolación. Objetivo 3838 archivos de perfil y filas de métricas (17*101 por A/B + 4*101 de 2D), 2525 filas comparativas (17*101 A/B + 2*4*101 frente a 2D). Exporta dos CSV y JSON SHA256 de fuentes/salidas a destino independiente. Seis pruebas de software añadidas, no ejecutadas en esta sesión. No existe aún resultado verificado de la campaña integral. El workflow solo postprocesa archivos publicados; no requiere OpenFOAM. La sonda B de 1 ms no está recuperada; no inventar una serie equivalente. Estados A 8/10, B 2/7 y campaña adaptativa 6/8 no cambian.
