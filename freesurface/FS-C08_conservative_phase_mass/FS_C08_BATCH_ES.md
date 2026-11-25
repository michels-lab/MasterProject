# FS-C08: lote fijo de comparación de momento
Ejecutar desde FS_C08_WORKTREE: python3 -B analysis_tools/run_fs_c08_batch.py --jobs 2

La fuente predeterminada es FS_C07_THERMAL_20261123T183217Z_72da1bf4 en ~/OpenFOAM/FS_C07_RUNS; el material predeterminado es B14_reference/fsC08Material. Se pueden sobreescribir con --source y --material. Los cuatro casos comparten malla, t=0, propiedades, laminar, movilidad lineal, dt fijo de 1e-6 s y diez pasos. Las variantes forman un factorial 2x2: legacy/refreshBeforePressure por separate/phaseWeighted. Dos referencias se repiten deliberadamente con el mismo binario para eliminar diferencias de versión. No se repite la variante armónica descartada.

--jobs 2 (predeterminado) ejecuta dos procesos seriales independientes en paralelo; --jobs 4 permite cuatro, si hay RAM suficiente. No usa descomposición MPI ni paso adaptativo. Una sola compilación previa, recibo SHA256 de biblioteca, bloqueo común a los runners y directorios únicos. No ejecutar wmake manualmente ni modificar las fuentes durante el lote. Un fallo de un caso no cancela los demás.

El resumen se escribe incrementalmente en ~/OpenFOAM/FS_C08_DIAGNOSTICS/FS_C08_BATCH_*/FS_C08_BATCH_SUMMARY.json; al finalizar también CSV. Los registros nativos y reportes individuales se conservan por variante. La comparación común incluye únicamente tiempos completos y guardados por todas las variantes. Últimos resultados de cada caso pueden tener tiempos distintos y no son comparación equivalente. El lote devuelve 2 si al menos una variante fue rechazada, aunque termine de ejecutar todas. No afirma validación física.

Estado al publicar: el nuevo lote y phaseWeighted todavía no han sido ejecutados en Foundation14; las dos referencias tienen corridas anteriores aprobadas de diez pasos. La política de paso temporal fijo se conserva.
