# Caso A — análisis científico de la réplica fiel C14
24-11-2026. Etapa 09/10; 8/10 hitos (80%). Fuente: datos reales publicados en C14_3D_A_faithful y C14_topFixedFlux_explicitRef. Archivo inicial: 3726 archivos de inventario (176484972 bytes); análisis derivado posterior, no modifica el manifiesto de publicación original.

## A3. Análisis térmico y fluidodinámico
Probe nativo 10001 muestras por variable a dt=.001 s, sin faltantes. T central 2D/3D a 10s 1464.19/1466.36 K; RMSE temporal 6.7058704 K, sesgo -1.7761714 K, diferencia máxima absoluta 21.25 K. Primer T<1473 K 4.720/3.451 s, primer alpha<1 4.720/3.449 s; fracción sólida central final 0.035185/0.026506. Velocidad central máxima 0.0107557915 m/s a 6.464 s (2D), 0.0224076370 m/s a 3.238 s (A). T del probe monótona no creciente; recalescencia no observada. p_rgh en t0 1321.36/-1388.19 Pa, primer paso 99995.9/99994.4 Pa; investigar inicialización de presión, no asumir error de física por signo de p_rgh.
 
| Magnitud | 2D | 3D-A fiel |
|---|---:|---:|
| T media a 10 s reconstruida de deltaH (K) | 1465.159331 | 1450.727323 |
| Fracción sólida media por volumen a 10 s | 0.0379407 | 0.102755 |
| Primer alpha medio <1 registrado (s) | 0.2 | 0.3 |
| Máxima potencia latente guardada (W) | 138.0709 (10s) | 1038.793 (7.3s) |
| Tasa media enfriamiento final (K/s) | 1.949246 | 2.32838 |
| Tasa media enfriamiento máxima (K/s) | 7.370134 | 11.89826 |
| Máximo gradiente T guardado (K/m) | 18735.58 (0.1s) | 20740.22 (5.1s) |
| Potencia de frontera metálica a 10s (W) | 313.975 | 1641.914 |

La media T reconstruida parte de 1500 K y divide deltaH por rho Cp V; no equiparar con lectura directa del campo T. La réplica A tiene fracción sólida y H final prácticamente iguales a la primera corrida (H final 311527.6 J en ambas, alpha final 0.897245 en las reducciones). Esto NO demuestra igualdad celda a celda.
 
Perfiles nativos a 10 s: y relativo 20 mm, referencia 2D x-20 mm; 3D x o z respecto al centro 25.9 mm, diagonales X proyectadas multiplicadas por sqrt(2); vertical y relativo a base. Interpolación solo en soporte común, sin extrapolación; tolerancia 0.00001 mm por redondeo de coordenadas.
| Dirección | puntos comunes | RMSE T K | RMSE magnitud U m/s | RMSE magGradT K/m |
|---|---:|---:|---:|---:|
| 0° |70|14.94924|0.00346496|1995.63|
| 45° |80|10.63144|0.00308229|888.88|
| 90° |70|14.94995|0.00346504|1995.67|
| 135° |80|10.69187|0.00313075|871.72|
| vertical central |80|3.75078|0.00333234|567.21|

Para comparación estrictamente homogénea de las cuatro direcciones, los mismos 70 puntos comunes arrojan RMSE T 14.94924,9.87068,14.94995,9.90346 K respectivamente. Diferencia entre perfiles 0° y 90° RMSE 0.002673 K; diagonales 45°/135° 0.07208 K. No implica axisimetría global. Diagonales comparan magnitudes, no componentes globales de vectores. Máxima velocidad a 10s en líneas y20: 0°/90° 0.00264603 m/s, 45° 0.00367392, 135° 0.00362982; vertical 0.00343172. No son máximos volumétricos. 
## A4. Balance diagnóstico del metal
R = Q_out - (H(t0)-H(t)) - calor latente liberado. Positivo = salida superior a la disminución estimada de almacenamiento. Integración trapezoidal de 101 valores espaciados 0.1s; calor latente por inventario rho L V (alpha0-alpha) o por integral de potencia nativa. V=1.6e-5 m³ 2D, 4.7921447006662436e-5 m³ A, rho=6820, Cp=827, L=228600. No energía discreta completa ni integración a dt=.001s.
| Caso / intervalo | Q_out J | delta H liberado J | latente inventario J | latente potencia J | R inventario J | R potencia J |
|---|---:|---:|---:|---:|---:|---:|
|2D 0–10|4055.57983|3144.1|946.424387|945.298779|-34.944557|-33.818949|
|2D .1–10|4022.32496|3075.5|946.424387|945.298779|0.400573|1.526181|
|A 0–10|20830.5438|13317.6|7677.034416|7681.477265|-164.090616|-168.533465|
|A .1–10|20669.7485|12991.2|7677.034416|7681.477265|1.514084|-2.928765|

R/Q A .1–10: +0.007325% y -0.014169%; 0–10: -0.787740% y -0.809069%. 2D .1–10: +0.009959% y +0.037943%; 0–10: -0.861641% y -0.833887%. No excluir silenciosamente el primer intervalo: ambos flujos guardados en t0 son cero; la diferencia es compatible con transitorio inicial submuestreado, no prueba de su única causa. Latente potencia vs inventario A difiere 4.442848 J (0.0579% del inventario). A Q contacto 19616.8472 J, top 1213.696385 J desde t0; todos los valores nativos de flujo advectivo y phi sumados en top son cero. Este balance no cuantifica flujo bilateral del molde en la nueva corrida.
 
CSV derivado versionado: cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful/analysis_results/faithful_native_analysis_20261124/thermal_energy_101.csv (101 filas, commit 0b1063648c1e517b62ce102629e039a7e0c301e2). Fuentes Git blobs en orden alpha/H/potencia latente/potencia frontera: 2D b47a098efabe021aaf8ce556317092f0bc9e4c75, 02cb3d0a03d09bbd67eb99910c273b8d83d9a503, 30eb996599a46d64d71af65dedd4877704cab73f, 96edae3ca6581d6947acd522bc3536e5c58d8c2c; A bdb8f647fbb4a40b2b45265d066f84520426c381, 70e7db34c2f3c805375d2088af14dce044c880fa, e6dc77e1d554484a6786def0da4647023fd586b6, 43a8230da2df4359166cdcd471804da87da0f273.
 
## Pendiente estrictamente local
Ejecutor audit_faithful_a_fields_and_energy.py compara T,U,p,p_rgh,alpha metal y T molde de las dos corridas sobre idénticas celdas, 101 estados, volúmenes, estadísticas y balance bilateral metal/molde. Reutiliza reconstrucción q previa únicamente con igualdad exacta de archivos primarios y entradas físicas; de lo contrario usa el extractor C++ ya probado sobre copia temporal aislada, sin solver CFD. Produce CSV y JSON en C3D04_A_C14_FAITHFUL_RUNTIME_10S_01/analysis_results/field_and_energy_audit_01. Código publicado; ejecución local pendiente.
 
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
source /opt/openfoam14/etc/bashrc
export HWLOC_COMPONENTS=-gl
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/audit_faithful_a_fields_and_energy.py"
```
 
A3 comparaciones archivadas y A4 balance diagnóstico del metal completos en Git; campo volumétrico y balance bilateral de réplica pendientes WSL. No afirmar cierre discreto, independencia ni QuickCup. Etapa 09/10, 8/10=80%.