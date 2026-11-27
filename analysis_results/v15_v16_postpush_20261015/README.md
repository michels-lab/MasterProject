# QuickCup — inspección inicial de los resultados subidos el 15 de octubre de 2026

**Origen:** commit de datos `25e7cf8cb4a30fb0fe5ece5bd9a2e451815ab232` (push desde laptop).  
**Estado científico:** EVIDENCE-PUSHED / PRELIMINARY COMPARISON — sin dar por cerrada la auditoría física ni experimental.

## Presencia de evidencia

El repositorio contiene nuevas carpetas `logs/`, `postProcessing/` y `log.foamMultiRun` para:
`B11_energy2_test`, `B15_adaptiveDt_fromB14`, `B16_phaseRelax025_fromB14`,
`C15_adaptiveDt_fromC14`, `C16_phaseRelax025_fromC14`.

El archivo `logs/Time_0` y la sonda `postProcessing/metal/temperatureProbe/0/T`
alcanzan 10 s en los cinco casos. Esto prueba la presencia de evidencia hasta el
tiempo objetivo, pero una revisión por separado de log final, conservación,
fronteras, física y procedencia debe preceder a cualquier declaración de
`RUN_VERIFIED`/`ANALYSIS_VERIFIED`.

## Cribado numérico reproducible desde los archivos subidos

| Caso | Pasos de tiempo en Time_0 | T central a 10 s (K) | max Courant reportado | Continuidad acumulada a 10 s | clockTime final (s) |
|---|---:|---:|---:|---:|---:|
| B11-energy2 | 10 000 | 1470.07 | 0.0673434 | -0.0310195 | 315 |
| B15 | 1 684 | 1469.98 | 0.255553 | -0.0311197 | 250 |
| B16 | 10 000 | 1470.08 | 0.0674108 | -0.0310084 | 697 |
| C15 | 1 473 | 1463.89 | 0.258115 | 2.04396e-14 | 225 |
| C16 | 10 000 | 1464.22 | 0.0651054 | 4.44248e-13 | 749 |

B15 y C15 sobrepasan ligeramente el `maxCo=0.25` indicado en el archivo de
control (`Co_max≈0.256/0.258`). Revisar control temporal real por timestep,
naturaleza de la medición, y efectos en el balance antes de aceptarlos.

## Comparación de temperatura central con padres

Los pares se alinearon por **tiempo físico**, interpolando linealmente la
temperatura de las series de sonda en una malla uniforme de 0.01 s entre
0 y 10 s (1001 puntos), en lugar de comparar filas de timestep.
Los archivos escritos tienen precisión limitada y no permiten inferir
diferencias menores a esa precisión.

| Par | Delta T a 10 s (hijo - padre, K) | RMSE T(t) (K) | max absoluto ΔT (K) |
|---|---:|---:|---:|
| B11-energy2 vs B11 | 0.00 | 0.000 | 0.000 |
| B15 vs B14 | -0.09 | 0.138 | 0.280 |
| B16 vs B14 | +0.01 | 0.0156 | 0.030 |
| C15 vs C14 | -0.30 | 0.140 | 0.308 |
| C16 vs C14 | +0.03 | 0.0201 | 0.050 |

**Interpretación restringida:** La respuesta térmica en el punto central es
cercana para B16/C16 y muestra una desviación algo mayor con timestep
adaptativo. Esta observación NO demuestra equivalencia de campos, frentes,
latente o velocidad; tampoco justifica validar ningún caso contra experimento.

## Alertas y próximos pasos

1. Revisar log final `End`, retorno de `Allrun`, avisos/fatales, integridad
   de `topFlow` y resultados de `foamPostProcess`.
2. Repetir análisis de continuidad, presión y energía, con la escala y unidades
   de cada función OpenFOAM. **B sigue acumulando continuidad ≈ -0.031**;
   la relajación y el paso temporal no resuelven el problema físico de volumen cerrado.
3. Auditar por cara `metalTop`, calor latente y `alphaL`; ejecutar
   comparación de perfiles y mapas a tiempos físicos idénticos.
4. Comparar costo de ejecución normalizado por hardware/runner; los
   `clockTime` no prueban por sí solos aceleración reproducible en condiciones
   controladas.
5. Actualizar el registro de caso y notas solo tras completar auditoría del
   log y evidencia física. J0 (JMatPro) y G1 experimental siguen abiertos.

**Regla de preservación:** no ejecutar CFD en GitHub ni modificar los datos
numéricos versionados; la auditoría es de solo lectura. El preflight de casos
PREPARED no debe aplicarse sin distinción a estados que ya contienen productos
de ejecución. En modo post-run, la auditoría de paridad excluye `0/` porque
puede recibir campos diagnósticos; esos campos iniciales requieren revisión
aparte, nunca se consideran verificados automáticamente.

## 27-11-2026 — Operación Uva: recálculo independiente de series publicadas

Origen inmutable: `25e7cf8cb4a30fb0fe5ece5bd9a2e451815ab232`. Se leyeron completas ocho sondas T (cinco experimentos y tres padres), cinco series Time_0, cinco contCumulative_5, cinco clockTime_0 y siete CourantMax_0. Todas las sondas tienen tiempos estrictamente crecientes, valores finitos y cobertura 0–10 s. Los recuentos de Time_0 coinciden con muestras de sonda menos uno. Se interpoló linealmente sobre 1001 tiempos físicos 0:0.01:10 s, sin extrapolación.

| Caso | Pasos | T final K | Delta T final K | RMSE K | max abs Delta T K | Co máximo | Etiqueta temporal Co s | contCumulative_5 final | clockTime s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B11-energy2 | 10000 | 1470.07 | 0 | 0 | 0 | 0.0673434 | 2.678 | -0.0310195 | 315 |
| B15 | 1684 | 1469.98 | -0.09 | 0.137902119 | 0.280 | 0.255553 | 0.814286 | -0.0311197 | 250 |
| B16 | 10000 | 1470.08 | +0.01 | 0.015631879 | 0.030 | 0.0674108 | 2.679 | -0.0310084 | 697 |
| C15 | 1473 | 1463.89 | -0.30 | 0.140024091 | 0.308 | 0.258115 | 0.68 | 2.04396e-14 | 225 |
| C16 | 10000 | 1464.22 | +0.03 | 0.020079761 | 0.050 | 0.0651054 | 2.963 | 4.44248e-13 | 749 |

Referencias: B14 Co máximo 0.0673434 (etiqueta 2.678 s); C14 Co máximo 0.0650864 (etiqueta 2.963 s). El primer registro CourantMax_0 tiene columna temporal vacía y valor cero; se interpreta como arranque t=0. Las etiquetas posteriores llevan sufijo s. El último Co precede a 10 s; no se inventa un registro Co a 10 s. Los pasos inferidos de las sondas adaptativas oscilan aproximadamente entre 0.00119048 y 0.02 s, con precisión temporal de escritura limitada.

El cribado de octubre queda reproducido a la precisión de los datos. Estado propuesto para los cinco casos: EVIDENCE_PUSHED / PRELIMINARY_COMPARISON; no RUN_VERIFIED ni ANALYSIS_VERIFIED. El log nativo completo supera el límite de transferencia del conector al intentar leerlo; no se confirmó End, retorno del runner ni ausencia de errores. No se contrastaron aquí todos los diccionarios, perfiles, flujos cara a cara, campos de fase ni cierre energético. No repetir automáticamente CFD: primero recuperar y auditar la evidencia existente. No se modificaron resultados, solver ni configuraciones.
