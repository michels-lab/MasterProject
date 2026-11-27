# Uva + Granada — integridad temporal de los diagnósticos FS-C08

Corte 27-11-2026. Rama de investigación independiente. No nuevas corridas ni cambios de ecuaciones, propiedades, tolerancias o estrategia temporal.

## Hallazgos y correcciones
- Confirmado por lectura: startup_probe_dt está en la firma de execute; REQUIRED_FINAL_FIELDS es una tupla indexable. No se modifican por sospechas anteriores.
- fs_c08_transient_ledger.py: una fecha con solo marcadores inválidos ahora se conserva como fila incompleta; antes podía desaparecer. Se rechazan claves duplicadas y dt no positivo. El contraste de inventarios previos solo se calcula si la separación temporal coincide con el dt nativo del estado actual (tolerancia max(1e-14,1e-6*dt)); no cruzar pasos totalmente ausentes ni filas incompletas. Un registro completo aislado no se convierte en una trayectoria continua.
- run_fs_c08_real_cfd.py: comparación de estados guardados rechaza marcas de presión no convergida aunque exista otra convergida al mismo tiempo, marcas de aceptación sin timestamp inequívoco y snapshots duplicados. Es un filtro de elegibilidad, no una validación de campos ni un balance independiente.
- Sintaxis cotejada con emisiones nativas en fsC08PressureCorrector.C (blob bfcdcb8dac5a...; SHA completo bfcdcb8dac5b04f7d3f1d6dfe44f5c690842e34c) y fsC08ConservativeVoF.C (644d771c61f3e6cf1c039b481328463e9bc8a75f): time_s, dt_s, cierre de presión =1, energía final y gate de masa. No se modifican C++.
- Tres regresiones nuevas de ledger y tres aserciones de rechazo en la prueba de elegibilidad; no ejecutadas en esta sesión. Corrección de documentación: -4.72561759768e-8 m³ equivale a -47.2561759768 mm³, no -0.0472562 mm³. Es un ejemplo sintético histórico, no contracción CFD observada.

## Estado científico
STATUS.json blob ecba6becf44deb55b813466f98144add83bfc100, bloque synchronized_geometry_energy_candidate: lote 12 reportado 4/4 variantes y 75/75 pasos a 5 μs, 36/48 variantes y 501/757 pasos históricos únicos, no progreso porcentual de tesis. La réplica no se cuenta. A 5 μs, Umax varía 75.2783 a 12.8225 m/s al refinar dt de 1 a .125 μs. Masa sólida 9.43942e-7 a 9.63238e-8 kg. No independencia temporal ni validación física; K provisional puro Fe 83.761 GPa. Fuente terminal del investigador, no archivos WSL crudos inspeccionados.

Prioridad: analizar los balances locales de aceleración y las contribuciones de presión/interfaz/momento con evidencia nativa existente; no reducir umbrales ni proponer horizonte largo como resuelto. Cierre CHT global, propiedades CE/S y contracción física siguen pendientes. Los nuevos filtros no recalifican los resultados históricos.
