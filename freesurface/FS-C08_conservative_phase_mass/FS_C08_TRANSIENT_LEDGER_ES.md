# FS-C08 | Operación Granada: transporte transitorio y balance
Fecha: 2026-11-25. Rama de investigación independiente.

## Evidencia real hasta este punto
- eac7f2af: paso de 1 µs aprobado, cierre volumétrico 6.66e-16, discrepancia EOS 5.75e-16.
- d24ca8b2: intento de diez pasos; primer estado guardado, segundo paso rechazado por transporte líquido en celda 16457.
- 96e82a62: nuevo limitador del predictor; compilación detenida por surfaceMesh/fvMesh. fbc55d4c corrige el acceso a la malla. No nueva corrida confirmada.
- El caso B14 es una referencia de propiedades, no un modelo calibrado de expansión grafítica.

## Nuevo diagnóstico por paso
FS_C08_ACCEPTED_STATE_LEDGER integra las masas y volúmenes independientes de las fases, el volumen total de dominio, volumen metálico previo (geometría aceptada), cambio de volumen y fuentes volumétricas; también extremos de T, presión y rapidez. FS_C08_LOCAL_ENERGY_LEDGER integra el valor absoluto del defecto local de la ecuación de energía interna, usando el flujo advectivo y conductivo realmente ensamblados y el trabajo mecánico registrado. La suma absoluta evita ocultar cancelaciones entre celdas. El cociente local usa un piso de escala de 1 J/m3; no es un umbral de aceptación físico.

El runner conserva FS_C08_TRANSIENT_LEDGER.csv y .json incluso si la corrida termina con error, si el solver produjo un log. El archivo incluye el historial de masas, volúmenes y energía, errores de continuidad temporal y banderas de registros incompletos. La presencia de un registro de presión por sí sola no implica un estado completo.

## Interpretación y límites
- Los flujos limitados conservan masa por cara, pero el limitador de capacidad es conservador en sentido numérico y puede inhibir transferencias físicamente posibles si se ignora entrada simultánea.
- La fuente térmica y de cambio de fase son diagnósticos de la formulación actual; su integral no se interpreta como una descomposición global exacta de volumen con advección, cambios de temperatura y alimentación.
- El residuo de energía corresponde al fluido, no a la primera ley conjunta fluido+molde. El campo histórico pressureCorrectionEnergyGap_J se conserva por compatibilidad; su cálculo actual es la diferencia de reconstrucción postSolve, no una medida independiente de trabajo de presión.
- No se altera el cierre de presión, ecuaciones de energía, propiedades B14 ni casos A/B en el bloque de diagnóstico.
- Nuevos cambios C++ y pruebas Python requieren ejecución; no se afirma estabilidad multistep, contracción validada ni balance energético global.

## Siguiente ejecución
Repetir diez pasos desde t=0 en la copia aislada con --laminar-reference --startup-probe-dt 1e-6 --startup-probe-steps 10. Si pasa, revisar ledger, balance y continuidad de historias antes de aumentar horizonte. Si falla, localizar el primer paso y etapa exacta con los registros. Mantener todos los casos previos.
