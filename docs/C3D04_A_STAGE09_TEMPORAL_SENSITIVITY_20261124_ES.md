# Caso A — A5.1 sensibilidad temporal C14 fiel
24-11-2026. Etapa 09/10; 8/10 hitos operativos (80%). A3/A4 diagnóstico de estados guardados concluido; 606 archivos primarios idénticos entre las dos ejecuciones A. La referencia es C3D04_A_C14_FAITHFUL_RUNTIME_10S_01. No repetirla.

## Diseño controlado
Malla V4/T02 8960 metal,12352 molde; propiedades, modelos, BC, algoritmos, esquemas, tolerancias, condiciones iniciales y coordenadas idénticos al C14 fiel. Únicas modificaciones ejecutables de controlDict: deltaT y writeInterval, manteniendo 0.1 s entre estados guardados, endTime=10 y adjustTimeStep=no. 
|Nivel|dt s|pasos|writeInterval|probe muestras|
|---|---:|---:|---:|---:|
|Referencia|0.001|10000|100|10001|
|Medio|0.0005|20000|200|20001|
|Fino|0.00025|40000|400|40001|

Ejecutor run_c14_a_temporal_sensitivity.py crea casos separados a partir del generador inicial probado, con idéntica malla/hash y diccionarios físicos de la referencia. Copia los cuatro diccionarios nativos de diagnóstico. Ejecuta los dos niveles nuevos secuencialmente; reutiliza niveles completos con informe/hash válido, bloquea incompletos sin borrarlos. Verifica tiempos reales del solver, ausencia de FATAL, cobertura nativa, logs, 101 estados y preservación de la referencia. No modifica B ni FS. No altera las frecuencias físicas de escritura de las reducciones; por ello no acredita conservación discreta por cada paso.

## Análisis
CSV probe_common_10001.csv (T, magnitud U, alpha1,p_rgh,rho) compara en instantes coincidentes sin interpolación; cruces térmicos/alpha se delimitan además en cada resolución nativa. thermal_common_101.csv compara H, alpha, tasas, potencias, T media reconstruida y fracción sólida. cellwise_common_101.csv cuantifica diferencias de T,U,p,p_rgh,alpha y T molde, ponderadas por los volúmenes reales, sobre celdas idénticas. JSON reporta RMSE, sesgo, máximo y diferencia final por pareja; orden aparente solo si convergencia monótona y positiva. Balance metal por inventario y potencia latente desde 0 y 0.1 s, no cierre discreto. 
Criterios provisionales de cribado medio/fino: RMSE/max abs T probe 0.5/1 K; T media reconstruida 0.25/0.5 K; sólido volumétrico 0.001/0.002; velocidad probe 0.00025/0.001 m/s. No son tolerancias aprobadas de tesis, ni bastan para afirmar independencia de referencia. Analizar convergencia de las dos parejas, campos y tasas, y sensibilidad del transitorio inicial. 
## A5.2 espacial
V4/T02 aceptada usa 180 bloques y conserva contorno curvilíneo. Su blockMeshDict contiene subdivisiones pequeñas, incluso 1, 2 y 3; no aplicar factores fraccionarios con redondeo arbitrario. Derivar niveles a partir del diccionario T02 realmente aceptado, manteniendo vértices, arcos, regiones, grading y parches; considerar multiplicadores enteros y coste real, o diseño anisótropo justificado con ratios efectivos. Verificar conformidad de interfaces, volúmenes/áreas/CAD y calidad nativa antes de CFD; no confundir A/B o 2D/3D con refinamiento. La nueva malla aún no se ha generado. Seleccionar dt para aislar sensibilidad espacial después de resultados temporales. 
## Única ejecución local A5.1
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
source /opt/openfoam14/etc/bashrc
export HWLOC_COMPONENTS=-gl
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/run_c14_a_temporal_sensitivity.py"
```
Salida: ~/OpenFOAM/C3D04_A_C14_TEMPORAL_SENSITIVITY_01, casos dt_00005 y dt_000025, analysis_results/C14_A_TEMPORAL_SENSITIVITY_REPORT.json. Código publicado (cc602ba150881374a877bbf5f0d3ca0bacc24ba5); sin ejecución WSL, no afirmar independencia. CSV de auditoría A3/A4 local aún pendientes de archivo Git. No cambiar porcentaje hasta evidencia. 
