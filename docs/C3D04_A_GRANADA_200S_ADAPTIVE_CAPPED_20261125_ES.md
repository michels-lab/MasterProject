# Operación Granada — Caso A, campaña 200 s
25-11-2026. Prioridad C14-3DA-200s. La preparación compacta está realizada; autorizados solamente C14-3DA, C14-2D, B14-2D y C14-3DB en campaña general. Este ejecutor interviene exclusivamente A.
 
## Evidencia y decisión
La evidencia de consola del investigador en otra conversación informa fallo de C14-3DA en CAMPAIGN_200S_ADAPTIVE_UNCAPPED_01 a 0.7 s, deltaT=0.02 s, Courant máximo 0.193601, FOAM FATAL ERROR Negative initial temperature T0: -296.103. El informe local se deberá leer directamente mediante el nuevo orquestador; no afirmar causa raíz ni que T0 de inversión termodinámica sea temperatura de celda. El Co está por debajo de .25: criterio advectivo insuficiente para garantizar estabilidad del acoplamiento térmico y fuente de fase. No borrar esa corrida ni alterar C14 físico. Se mantiene elección experimental posterior del investigador: deltaT inicial .001, adjustTimeStep yes, maxCo .25, maxDeltaT .025, 8 MPI. .025 no excluye .02, por lo tanto no se promete corregir el fallo con ese límite. No cambiarlo silenciosamente ni iniciar producción sin evidencia. 
## Entrega
tools/run_case_a_200s_granada.py integra diagnóstico del fallo previo, inspección de intentos existentes, piloto nativo de 3 s con los parámetros acordados, continuación automática a una ejecución independiente de 200 s solamente tras PASS del piloto. Reutiliza piloto o corrida completa compatibles; si existe un intento fallido coincidente, lo preserva, reporta y bloquea sin repetirlo (retry explícito disponible). Usa el ejecutor MPI y archivo compacto verificado existentes; no repite preparación de campaña ni lanza otros casos. Conserva sondas en cada paso adaptativo real, perfiles/reducciones .1 s (2001), volúmenes 1 s (201). No exigir 200001 muestras con dt variable.
 
Análisis tras CFD completo: CSV de probe en tiempos nativos reales, 2001 estados de evolución térmica y solidificación, potencia latente, tiempos de cruce, balance nominal metal desde 0 y .1 s. Publicación por archivo tar.gz fragmentado y manifiesto SHA en rama independiente, con datos nativos y análisis; no incluye campos volumétricos generados, no sobrescribe main. Informe de fallos y estado en ~/OpenFOAM/C3D04_A_GRANADA_200S_01. No afirma cierre discreto, independencia ni validación.
 
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
source /opt/openfoam14/etc/bashrc
export HWLOC_COMPONENTS=-gl
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$A/tools/run_case_a_200s_granada.py" --repo "$A" --ranks 8 --max-dt 0.025 --publish
```
 
Código publicado 495be9d9920d y b29005416b5e, ejecución WSL no observada. Etapa 9/10, 8/10=80% operativo. Sensibilidad temporal/espacial pospuesta. La configuración es experimental, no sustituto de referencia fija ni prueba de estabilidad a 200 s. Si piloto falla, examinar error y decidir reducción de cap o dt fijo con investigador; no cambiar automáticamente.
