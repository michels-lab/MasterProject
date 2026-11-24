# C3D04-A — visualización y análisis de solidificación real, etapa 08

24-11-2026. Evidencia: stdout WSL aportado por el investigador, desde commit d9cddf895, estado VISUALIZATION_AND_SOLIDIFICATION_READY. Los CSV y el caso local no se han descargado al repositorio; la apertura gráfica aún no se ha observado. No se relanzó el solver; SHA del caso original intactos.

## Resultados a 10 s (promedios ponderados por volumen)
| Magnitud | Valor |
|---|---:|
| T metal mínima / media / máxima [K] | 1401.91 / 1450.709162765 / 1471.07 |
| T arena media [K] | 481.745941375 |
| Fracción líquida / sólida de modelo | 0.8972449753 / 0.1027550247 |
| Masa sólida nominal [kg] | 0.0335828358 |
| Inventario latente liberado nominal [J] | 7677.0362640 |
| Fracción de volumen bajo Tsol | 0.0482952119 |
| Fracción de volumen entre Tsol y Tliq | 0.9517047881 |
| Fracción de volumen desde Tliq | 0 |
| Velocidad media / RMS / máxima [m/s] | 0.0018239872 / 0.0022349906 / 0.0060135896 |
| Darcy medio / máximo [1/s] | 1052742.2096 / 100000000 |
| Magnitud aceleración Darcy media / máxima [m/s²] | 2.037619665 / 611.332 |
| Magnitud aceleración flotación media / máxima [m/s²] | 0.000134919531 / 0.0233789 |
| Magnitud aceleración presión media / máxima [m/s²] | 0.02808266047 / 0.692569 |
| Tasa media de enfriamiento último intervalo [K/s] | 2.3382092912 |
| Potencia latente nominal último intervalo [W] | 1012.4512302 |

Primer incremento observado de fracción sólida en 0.2–0.3 s; máximo de potencia latente nominal 1038.8813014 W entre 7.2 y 7.3 s; máximo de velocidad guardado 0.025338495 m/s a 2.8 s. Las diferencias temporales de 0.1 s no reconstruyen las derivadas de cada paso de 0.001 s. No identifican austenita primaria ni recalescencia sin evidencia adicional.

Categorías descriptivas alpha>=0.99, 0.01<alpha<0.99 y alpha<=0.01: volumen final 1.5510%, 97.4423%, 1.0067%; velocidades medias respectivas 0.00320698954, 0.00182081066, 0.0000006102217023 m/s. No son fracciones de especies metalúrgicas. El frenado Darcy concuerda cualitativamente con el comportamiento del modelo, no constituye validación experimental.

## Entrega funcional
Caso local: ~/OpenFOAM/C3D04_A_C14_VISUALIZATION_01, archivo C3D04_A_C14.foam. 28 campos metal presentes en los 101 estados, T en arena, 21 familias postProcessing; phi y rho figuran en estado final pero no en todos los tiempos. Perfiles verticales corregidos 101×80 en tramo interior, no altura 2D equivalente. CSV analysis/solidification_101.csv, energy_inventory_101.csv, boundary_native_q_101.csv, boundary_native_q_faces_t10.csv. Residuo global nominal previo 0.1305158505 J; no conservación discreta demostrada.

## Estado
Etapa 08 operativa DONE (evolución de solidificación y flujo demostrada y analizada, caso visual creado). Etapa 09 IN_PROGRESS, 8/10=80% de hitos operativos, no avance de tesis ni exactitud física. Pendientes: conservación discreta, sensibilidad temporal y espacial sobre geometría comparable, QuickCup. Los casos A y B no constituyen automáticamente un estudio de independencia de malla porque difieren en geometría y topología. No repetir CFD base ni diagnósticos ya recuperados. No imponer pruebas unitarias manuales al investigador.
