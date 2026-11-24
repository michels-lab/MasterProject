# C3D05 B — Comparación inicial C14 2D / 3D-B
Fecha: 2026-11-24. Etapa 3/7; avance 2/7 = 29% de hitos técnicos, no de tesis.

## Fuentes reales
- [C14 2D, postProcessing/metal](https://github.com/michels-lab/MasterProject/tree/main/cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/postProcessing/metal).
- [C14 B corregido, postProcessing/metal](https://github.com/michels-lab/MasterProject/tree/results/c3d05-b-c14-corrected-20261124-162048/analysis_results/C3D05_B_C14/corrected-20261124-162048/postProcessing/metal).
- [Reporte de recuperación](https://github.com/michels-lab/MasterProject/blob/results/c3d05-b-c14-corrected-20261124-162048/analysis_results/C3D05_B_C14/corrected-20261124-162048/C3D05_B_C14_CORRECTED_SAMPLING_REPORT.json): 17 perfiles, 101 estados básicos y 100 estados de densidad; evidencia original comprobada sin cambio.

Sondas originales 2D (20,20,5) mm y 3D B (25.9,-20,25.9) mm, alturas relativas centrales equivalentes, no dominios geométricos idénticos. Series T,U,alpha1,p_rgh de 10001 muestras nativas 2D y 101 muestras archivadas B (0.1 s); rho B 100. No se interpolan tiempos faltantes ni se atribuye precisión de 1 ms a B. Los máximos son máximos observados en cada cadencia.

## Series centrales (T K; Uy mm/s; alpha1 líquida)
| t s | T 2D | T B | Uy 2D | Uy B | alpha1 2D | alpha1 B |
|---:|---:|---:|---:|---:|---:|---:|
|0|1500|1500|0|0|1|1|
|1|1499.98|1499.98|1.50755|4.00763|1|1|
|2|1499.96|1498.90|4.70969|13.6342|1|1|
|3|1496.49|1475.36|7.36258|22.776|1|1|
|4|1477.40|1472.60|7.15821|19.0367|1|.998464|
|5|1471.81|1471.93|7.62046|9.36787|.995451|.995754|
|6|1467.79|1471.49|10.5657|5.48217|.979262|.99399|
|7|1466.53|1470.84|10.6255|3.92816|.974163|.9914|
|8|1465.71|1469.92|9.94951|3.28961|.970876|.987738|
|9|1464.96|1468.86|8.92508|2.90853|.967869|.983494|
|10|1464.19|1467.76|7.92855|2.53731|.964815|.979094|

Primer T <1473 K: 2D 4.720 s, B 3.6 s (intervalo 3.5–3.6 s). Primer alpha1 <.999: 2D 4.803 s, B 3.9 s (3.8–3.9 s). Máximo |U| observado: 2D 10.7558 mm/s a 6.464 s, B 23.0661 mm/s a 3.3 s. En B no cambio de signo de Uy entre muestras consecutivas no nulas; en 2D se detectó cambio a .002 s, no interpretado como inversión desarrollada. rho=6820 kg/m3 en todas las muestras disponibles. p_rgh inicial 2D en sonda 1321.36 Pa vs B 100000 Pa; investigar referencia y procedencia inicial de campos, no atribuir diferencias exclusivamente a dimensionalidad. Al final 99999.5 y 100000 Pa, respectivamente; la precisión de salida limita interpretación de diferencias pequeñas.

## Perfiles horizontales completos a 10 s
Uy en mm/s; T en K; conteo de puntos nativos; estos rangos se calculan en cada soporte espacial propio, no como error punto a punto.
|Altura mm|Caso|n|Uy min|Uy max|n negativo (Uy < -1e-8 m/s)|T min|T max|
|---:|---|---:|---:|---:|---:|---:|---:|
|10|2D|80|-5.75604|5.93710|44|1441.84|1469.54|
|10|B|68|.0827142|2.10653|0|1421.96|1456.83|
|20|2D|80|-7.81949|7.90323|42|1451.73|1472.84|
|20|B|70|.0818777|2.76278|0|1432.92|1467.87|
|30|2D|80|-7.57406|3.71175|24|1458.15|1476.36|
|30|B|72|-.0575135|2.87362|3|1440.75|1471.13|

## B: perfiles angulares a altura 20 mm
|t s|ángulo|n|Uy min mm/s|Uy max mm/s|n negativo|RMSE especular Uy mm/s|
|---:|---:|---:|---:|---:|---:|---:|
|3|0|70|-18.2669|22.9162|18|.922586|
|3|45|80|-26.879|22.9546|26|.989053|
|3|90|70|-19.9273|23.0081|18|2.531703|
|3|135|80|-26.1037|23.0195|24|.830596|
|10|0|70|.0818777|2.76278|0|.454882|
|10|45|80|-4.29666|3.05260|56|.807247|
|10|90|70|.0882518|2.88619|0|.982351|
|10|135|80|-4.32146|2.63354|57|.278725|

RMSE especular calculada entre pares opuestos de puntos ordenados en cada línea; no equivale a métrica de simetría volumétrica. Diagonales conservan proyección X según metadatos; reconstruir distancia firmada antes de comparar con perfiles de eje X/Z. No confundir medias de líneas con flujo neto de sección. Descenso periférico diagonal persiste a 10 s, aunque los perfiles centrales de 0/90 grados muestran sólo ascenso. Es compatible con retorno de circulación en sectores diagonales, no prueba topología global ni causalidad Darcy. La fracción sólida local B 2.0906% no equivale a 10.8297% volumétrica del inventario anterior.

## Alcance y siguientes trabajos
Se leyeron series completas de cinco campos por caso y perfiles seleccionados de 3 y 10 s; no se auditó todavía cada perfil en todos los tiempos ni se calcularon integrales de sección. No hubo ejecución de solver, remallado, modificación del CFD ni importación FoamLens comprobada. Siguiente: series espaciales de los 101 estados, componentes radial/tangencial, métricas de inversión temporal con umbral y soporte común, perfil vertical y balance físico, preservando datos nativos. G3/G4/G5 y validación experimental permanecen abiertos; no se demuestra recalescencia ni causalidad exclusivamente geométrica.
