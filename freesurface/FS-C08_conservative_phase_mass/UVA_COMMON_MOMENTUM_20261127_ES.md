# Uva + Granada — unión de momento y balances conservativos a tiempos físicos comunes

27-11-2026. Rama FS-C08 independiente; postproceso de evidencia existente, sin nuevas CFD ni modificación de ecuaciones, EOS, materiales, malla o tolerancias.

## Implementación

analysis_tools/compare_fs_c08_momentum.py usa los logs foamMultiRun.log de cada variante y la presencia de campos guardados en su caso, con el calendario fijo y el contrato estricto de energía que declara el resumen de lote. Reutiliza comparison_ready_times y extract. No usa la mera presencia de un marcador de momento como prueba de aceptación. Exige marcas nativas de masa/presión y, si corresponde, auditoría energética final, campos requeridos, ledger completo, registro único por paso y tres diagnósticos obligatorios: split vectorial, consistencia y extremo de rapidez. Si existen problemas del parser de momento, la variante no aporta tiempos al contraste (criterio conservador). Un defecto de matriz fresco o extremo de calentamiento de gas ausente se conserva como null, no cero.

Dentro de cada variante exige mismo identificador de celda entre split y extremo de rapidez y concordancia de las tres magnitudes de velocidad máxima (tolerancia max(1e-10 m/s,1e-6 por rapidez máxima)). Entre variantes se informa coincidencia de centros de máximos con tolerancia 1 nm, sin afirmar identidad de malla ni restar magnitudes de celdas distintas como fuerzas. Las series de máximos de dominio se conservan explícitamente como tales. El diagnóstico gravedad/capilaridad permanece conjunto y las magnitudes son equivalentes de velocidad, no aceleraciones. Se conservan los balances de masa, volumen y energía en cada estado unido. Registros de atribución inicial sin time_s permanecen separados. No interpolación ni extrapolación. No se calcula orden de convergencia ni se promueve validación.

El runner de lotes genera FS_C08_COMMON_MOMENTUM.json después de ejecutar las variantes; un error de postproceso no cambia la aceptación nativa. La salida de terminal mantiene un resumen compacto. El CLI independiente lee un lote existente y escribe en un directorio nuevo fuera de los originales, con SHA256 del resumen y logs leídos; estos hashes son recibos de lectura, no verificación independiente contra un manifiesto remoto. No reconstruye campos ni ejecuta wmake/foamMultiRun. Requiere los logs y campos guardados originales y las rutas del resumen accesibles. Ejemplo para el lote reportado, sujeto a existencia de los paths en WSL:

```bash
cd "$HOME/OpenFOAM/MasterProject"
python3 -B analysis_tools/compare_fs_c08_momentum.py \
  --batch "$HOME/OpenFOAM/FS_C08_DIAGNOSTICS/FS_C08_BATCH_20261126T032157Z_1a7731a8/FS_C08_BATCH_SUMMARY.json" \
  --out "$HOME/OpenFOAM/FS_C08_DIAGNOSTICS/COMMON_MOMENTUM_BATCH12_01"
```

Si no hay tiempos comunes, conserva un reporte de exclusiones y devuelve código 2. El CLI no altera archivos de entrada. Cinco pruebas sintéticas añadidas y conectadas a CI; no se ejecutaron en esta sesión. No hay acceso a logs WSL completos desde el conector actual. El bloque prepara la comparación, no reporta contribuciones cuantitativas nuevas. El lote 12 reportado (4/4, 75/75 pasos, 5 microsegundos) permanece sin nueva certificación. Independencia temporal, cierre global CHT y contracción física pendientes.
