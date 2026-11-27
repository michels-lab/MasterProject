# Uva + Granada — comparación C14-2D / A / B por estaciones comunes

Corte 27-11-2026. C14 fijo 10 s, no campaña adaptativa 200 s. A réplica fiel, B postproceso corregido de los 101 estados originales, 2D C14 referencia. Sin nueva ejecución CFD. A 8/10 hitos, B 2/7, sin cambio.

## Método
Lectura directa de 29 archivos XY en GitHub. Todas las columnas de las filas leídas son finitas y tienen el número esperado de entradas según su encabezado. Coordenadas X en m: para comparar con A/B, x_2D + .0059; altura física de 20 mm corresponde a y=-.020 en 3D (base -.040). Emparejamiento por x redondeada a 1e-7 m, sin interpolar ni extrapolar. Para diagonales 45° A/B se compara la proyección X sobre la misma línea nominal, no distancia radial. Las estadísticas son aritméticas por estaciones coincidentes, no integrales de volumen, área ni masa. Clasificación Uy: descendente < -0.1 mm/s, ascendente > +0.1 mm/s, resto banda muerta. No se deduce independencia de malla de geometrías distintas.

## Línea horizontal 0°, altura 20 mm, 70 estaciones comunes
| t s | T 2D K | T A K | T B K | alpha 2D | alpha A | alpha B | N descendente 2D/A/B |
|---:|---:|---:|---:|---:|---:|---:|---|
|0|1500|1500|1500|1|1|1|0/0/0|
|4|1484.861143|1472.044571|1472.091429|1|.996153329|.996290486|12/18/20|
|5|1477.138857|1469.060143|1468.422429|.999032500|.985301129|.982267100|24/16/0|
|7|1472.068286|1463.958571|1464.293143|.993113486|.964745771|.965635986|34/0/0|
|10|1469.629143|1458.806714|1459.253429|.986556571|.944015300|.945427671|32/0/0|

| t s | RMSE T A/B K | A/2D K | B/2D K | RMSE Uy A/B mm/s | A/2D | B/2D |
|---:|---:|---:|---:|---:|---:|---:|
|0|0|0|0|0|0|0|
|4|.329770|13.991453|14.001079|1.022961|9.578120|9.681395|
|5|1.583845|11.387221|12.824143|2.384663|4.867676|4.827257|
|7|1.309499|12.393153|13.087665|.794463|5.389106|6.003413|
|10|.941046|14.949238|15.101628|.299008|4.692784|4.667677|

## Alturas a t=10 s, línea 0°
| altura mm | N común | T 2D K | T A K | T B K | alpha 2D | alpha A | alpha B | N descendente 2D/A/B | RMSE T A/B K |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
|10|68|1464.176176|1448.674706|1447.723676|.964780000|.903461176|.898766309|32/0/0|1.129497|
|20|70|1469.629143|1458.806714|1459.253429|.986556571|.944015300|.945427671|32/0/0|.941046|
|30|72|1473.825556|1463.652500|1463.457639|.998037833|.963465847|.962279819|10/12/0|1.255459|

## Diagonal 45°, altura 20 mm, 80 estaciones A/B
|t s|Uy min A mm/s|Uy min B mm/s|N descendente A/B|T A K|T B K|RMSE T A/B K|
|---:|---:|---:|---|---:|---:|---:|
|4|-16.0528|-20.9181|26/28|1473.644125|1473.784000|.363622|
|5|-10.6995|-14.1315|28/26|1471.030500|1471.638875|.776317|
|7|-5.47729|-6.62018|44/54|1466.419750|1467.388000|1.031442|
|10|-3.27682|-4.29666|56/56|1459.633875|1459.776500|.914916|

En los tiempos examinados, ambos 3D tienen temperatura media de línea cercana y menor que 2D para t>0 a 20mm. A 10s el complemento de alpha medio de línea a 20mm es 1.3443% (2D), 5.5985% (A), 5.4572% (B). No equivale a fracción sólida de todo el metal. A 10s, 0° y altura 20mm no tienen puntos descendentes en A/B, pero 45° tiene 56/80 en cada uno. Esto demuestra dependencia direccional de las muestras; no demuestra una inversión global de circulación. A 30mm A conserva 12 puntos descendentes y B ninguno bajo el umbral a 10s. No atribuir diferencias exclusivamente a malla, geometría, BC ni transferencia térmica sin diseño controlado.

## Procedencia SHA Git por perfil
A: cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful/postProcessing/metal/C14CanonicalProfiles/
B: rama results/c3d05-b-c14-corrected-20261124-162048, commit 8f8135876275434363f8cd37a32f73190417f578, prefijo analysis_results/C3D05_B_C14/corrected-20261124-162048/postProcessing/metal/
2D: commit 03c543cad38bbc033a44d7d6c62b788f943116ed, cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/postProcessing/metal/

| perfil / tiempo | A blob | B blob | 2D blob |
|---|---|---|---|
|0° h20 / 0|2e959165bc3b742ce0ffee9af47e68e8932f4ebd|f2ef637065286c43f2091ee4f24505b5d51f122d|f65535ef6af2675355e555b8d5d8477396a8cd07|
|0° h20 / 4|309abcfa693d8737a2f537a130ed2b714e8c06e3|19e8e6f5386e262fe9386ed762042d65758a370c|59f2ca3febd454e5106d1ea43e6192885d649dd1|
|0° h20 / 5|af3f942ffe4354650b7ab495e46f71e9fbefa8ec|42b3314450897111e6da6dcdddc53fe561d6767d|c24de0946c23c3f2661e9e2b68aca5d8f1d8d899|
|0° h20 / 7|bc7377c463bc221b26989d68a500501e2037434c|65389b34845a02d01571f9c7226205f47ac34f6b|843dafed57f2f89c300b0fcd785cd8719158dfd5|
|0° h20 / 10|a5c68b08e9ea965296933aa5b8e7f7247c001f95|e7f751b5a941f637741bd4d41ecef13702816526|4252c80ccbb91da24bf59d92082c14534e4d08c6|
|0° h10 / 10|a2555311f36d050bf6022e2586c33c6d5366fe3d|ea88c13e1295bf6fe5daab39d07161abd13a9446|254a03b4b94eb23ca3b9b0f3df9283641eda7d15|
|0° h30 / 10|33bda5e27d4b5a1e24fb993afa1401a4dc837d5e|4ea43115f55b5e0a57318512f8332f54d96dd5fc|39c9ccaca18f0b9299928582c084dd0be8f927bf|
|45° h20 / 4|8bab1b38eb2f95ed807ffc589211a07d63b82a38|8de40f246e419ef06becbda91cc4ed8f49cc88d9|—|
|45° h20 / 5|3e574065f5e1e15cd49618271374d774db4dca06|8a0d1312f8164b1c052bd7760664c733f5b0b6a1|—|
|45° h20 / 7|3de234279ee5ca445a3d620cb4658cf072b45658|4e07ee0d9d0164f381f04155a328cdec80167df1|—|
|45° h20 / 10|6d5ed6525a961f006edf82afb6f1448b2563a249|7a52f2f44bff9589194caed5a0fabc8713fc740b|—|

Horizontales: horizontalProfiles (A/2D) y C14CanonicalhorizontalProfilesB3D (B), archivo <tiempo>/line_y<altura>mm.xy. Diagonal: additional3DProfiles (A), C14Canonicaladditional3DProfilesB (B), <tiempo>/height20_angle45.xy. Reporte B blob 483ffaa77a24e3fbbda6f6e3b28d564dfed08e0b; no recupera la cadencia de 1ms. No se localizaron sondas B en la ruta supuesta; no sustituir con medias de línea. Quedan pendientes las 101 muestras de todas las líneas, series de sonda A/2D, balance energético, incertidumbre y comparación experimental. No modificación de resultados originales.
