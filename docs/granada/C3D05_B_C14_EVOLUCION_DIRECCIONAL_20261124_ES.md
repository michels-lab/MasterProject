# C3D05 B — Evolución direccional de Uy y velocidad radial/tangencial
24-11-2026. Etapa 3/7; 2/7 = 29% de hitos técnicos. Sin cambio de validación física.

Fuente: rama results/c3d05-b-c14-corrected-20261124-162048, analysis_results/C3D05_B_C14/corrected-20261124-162048/postProcessing/metal/C14CanonicalhorizontalProfilesB3D y C14Canonicaladditional3DProfilesB. Perfil a altura 20 mm (Y=-20 mm). Datos reales leídos por el agente; sin nuevo CFD.

## Evolución observada
Umbral descendente Uy < -0.1 mm/s; ascendente Uy > +0.1 mm/s. N=70 en 0° y 80 en 45°. No interpretar proporciones de puntos como áreas ni volúmenes.
|t s|Uy min 0° mm/s|n descendente 0°|Uy min 45° mm/s|n descendente 45°|RMS Ur 0° mm/s|RMS Utheta 0° mm/s|RMS Ur 45° mm/s|RMS Utheta 45° mm/s|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|4|-8.2509|20|-20.9181|28|5.00871|.660324|5.34833|.411860|
|5|.245485|0|-14.1315|26|2.70735|.557393|4.07576|.604934|
|6|.18785|0|-9.28171|39|1.64660|.559397|3.06350|.628035|
|7|.156001|0|-6.62018|54|1.92820|.644145|2.25341|.541545|
|8|.143088|0|-5.79366|57|1.70773|.566155|1.78838|.371183|
|9|.11454|0|-5.13707|56|1.36982|.458874|1.56113|.279589|

## Transición con cadencia nativa B
|t s|Uy min 0° mm/s|n descendente 0°|
|---:|---:|---:|
|4.0|-8.2509|20|
|4.1|-6.86816|20|
|4.2|-5.44975|19|
|4.3|-4.01439|19|
|4.4|-2.65332|16|
|4.5|-1.41986|12|
|4.6|-.353132|2|
|4.7|.149775|0|
|4.8|.196764|0|
|4.9|.227072|0|
|5.0|.245485|0|

A 4.7 s todos los puntos de 0° son ascendentes bajo el umbral elegido; la última muestra descendente de este intervalo está a 4.6 s. No se demuestra permanencia en todos los instantes posteriores hasta auditar los 101 estados. El descenso diagonal persiste en tiempos enteros comprobados, con aumento de proporción descendente 5–8 s mientras baja su velocidad máxima descendente. Compatible con redistribución de circulación, no prueba de causalidad o topología volumétrica.

Ur=(Ux dx+Uz dz)/r; Utheta=(-Ux dz+Uz dx)/r, dx=X-0.0259, dz=Z-0.0259. RMS no ponderada por área; las líneas no son superficies. La componente radial/tangencial no está definida en el eje; no se inventan ceros.

## Automatización
analysis_tools/analyze_c3d05_b_corrected_profiles.py: analiza los 17 perfiles x 101 estados; reconstruye XYZ a partir de coordenadas nativas y extremos, genera XY direccionales en árbol de postProcessing separado, CSV temporal, comparación C14 2D en estaciones físicas comunes sin extrapolar, eventos de signos opuestos entre muestras consecutivas, hashes SHA de fuentes. El perfil vertical central no tiene Ur/Utheta definidos; se conserva en métricas y en datos originales. Se excluyen cambios de signo mediados por banda muerta de los eventos directos.
Workflow .github/workflows/c3d05-b-published-profile-analysis.yml, con fuentes reales en GitHub, permiso de lectura, sin OpenFOAM/WSL. Primera ejecución [45504719498](https://github.com/michels-lab/MasterProject/actions/runs/45504719498) observada en cola; no afirmar análisis integral concluido ni importación FoamLens hasta verificar los resultados. Artefacto de salida C3D05-B-directional-analysis. No modifica fuentes ni la rama de resultados original. No se ha verificado conservación, contracción, independencia ni QuickCup/JMatPro.
