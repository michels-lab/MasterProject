# C14 2D / 3D-A fiel / 3D-B — sondas centrales comparables
24-11-2026. A 9/10, 8/10=80% operativo; B 3/7, 2/7=29% técnico; 2D histórico 26/26 corridas (no validación). No solver ni nueva malla.

Fuentes: [C14 2D](https://github.com/michels-lab/MasterProject/tree/main/cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/postProcessing/metal/temperatureProbe/0), [A fiel](https://github.com/michels-lab/MasterProject/tree/main/cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful/postProcessing/metal/temperatureProbe/0), [B corregido](https://github.com/michels-lab/MasterProject/tree/results/c3d05-b-c14-corrected-20261124-162048/analysis_results/C3D05_B_C14/corrected-20261124-162048/postProcessing/metal/temperatureProbeB3D/0).
Lectura completa de T/U/alpha1 de A fiel 10001 registros por campo, comparada con series previamente leídas de C14 2D 10001 y B 101. A/B sondas (25.9,-20,25.9) mm, 2D (20,20,5) mm: centro relativo. Cadencias A/2D .001 s, B .1 s, comparar máximos observados y no inferir resolución ausente.

|t (s)|T 2D K|T A K|T B K|Uy 2D mm/s|Uy A mm/s|Uy B mm/s|alpha1 2D|alpha1 A|alpha1 B|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|0|1500|1500|1500|0|0|0|1|1|1|
|1|1499.98|1499.98|1499.98|1.50755|3.89854|4.00763|1|1|1|
|2|1499.96|1498.09|1498.90|4.70969|12.8081|13.6342|1|1|1|
|3|1496.49|1475.26|1475.36|7.36258|22.1371|22.776|1|1|1|
|4|1477.40|1472.26|1472.60|7.15821|18.2471|19.0367|1|.997113|.998464|
|5|1471.81|1471.12|1471.93|7.62046|9.89537|9.36787|.995451|.99251|.995754|
|6|1467.79|1470.23|1471.49|10.5657|6.20799|5.48217|.979262|.988965|.99399|
|7|1466.53|1469.26|1470.84|10.6255|4.79208|3.92816|.974163|.985077|.9914|
|8|1465.71|1468.24|1469.92|9.94951|3.95018|3.28961|.970876|.981002|.987738|
|9|1464.96|1467.28|1468.86|8.92508|3.27077|2.90853|.967869|.977154|.983494|
|10|1464.19|1466.36|1467.76|7.92855|2.69531|2.53731|.964815|.973494|.979094|

Primer T<1473 K: 2D 4.720 s, A 3.451 s, B 3.6 s (3.5–3.6). Primera alpha1<.999: 2D 4.803 s, A 3.672 s, B 3.9 s (3.8–3.9). Máxima |U| observada: 2D 10.7558 mm/s a 6.464 s; A 22.4076 mm/s a 3.238 s; B 23.0661 mm/s a 3.3 s. A/B diferencias de máximo observado 0.6585 mm/s (~2.94% respecto A), temperaturas finales 1.40 K, fracción sólida local A 2.6506%, B 2.0906%, 2D 3.5185%.

A y B muestran un patrón central similar, distinto del 2D: mayor pico temprano y descenso posterior. Es concordancia entre modelos, NO prueba de independencia (topología, tamaños de malla y discretización distintos), ni causalidad exclusiva de dimensionalidad ni validación experimental. No confundir sondas locales con medias de volumen, ni alpha1 con contracción física. Próximo: perfiles A/B homologados, reducciones/energía y análisis en FoamLens. El registro general mantiene los hitos físicos abiertos.
