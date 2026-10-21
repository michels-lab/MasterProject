# Auditoría Granada — B11/C11 `energy2_test` y procedencia de la documentación

**Fecha:** 2026-10-21  
**Estado:** OBSERVED source difference; historical documentation clarified; run-level and experimental meaning **NOT VERIFIED**.  
**Tipo de auditoría:** contraste de archivos Git rastreados (no ejecución de OpenFOAM).

## Hallazgo

El auditor File Steward reportó dos parejas de `CASE_VARIANT.md` **idénticas** pese a nombres de carpetas que denotan experimentos diferentes. La pregunta correcta no era si se podían borrar, sino si los textos describían fielmente la función científica de cada carpeta.

Se cotejaron las cuatro versiones de `CASE_VARIANT.md` y los `system/fvSolution` de B11 y C11. Los dos `*_energy2_test/system/fvSolution` incluyen la entrada activa `PIMPLE { nEnergyCorrectors 2; }`. En las variantes `*_topFixedFlux_airGapOF14/system/fvSolution` esa entrada no existe. Las demás entradas del directorio `system/` listadas por la API son idénticas en los pares al nivel de blob SHA salvo `fvSolution`. Este resultado **no compara automáticamente el resto del caso**, y no demuestra respuesta diferente.

| Familia | Carpeta con valor explícito | Carpeta pareada sin ese valor | Tipo de evidencia |
| --- | --- | --- | --- |
| B11 | `cases_controlled_buoyancy/B11_energy2_test`: `nEnergyCorrectors 2` | `B11_topFixedFlux_airGapOF14` | Texto de `fvSolution` y árbol de archivos de GitHub |
| C11 | `cases_controlled_buoyancy/C11_energy2_test`: `nEnergyCorrectors 2` | `C11_topFixedFlux_airGapOF14` | Texto de `fvSolution` y árbol de archivos de GitHub |

## Problema documental

Los `CASE_VARIANT.md` históricos de las carpetas `energy2_test` estaban copiados del caso V11 de referencia. Afirman cifras de cierre de energía, continuidad, diferencias de campos y `RUN-VERIFIED + ANALYSIS-VERIFIED`. **Esas cifras no pueden transferirse automáticamente a una configuración distinta** por compartir un documento.

## Decisión de preservación

1. **Mantener las cuatro carpetas y sus cuatro `CASE_VARIANT.md`.** Son etiquetas y evidencias históricas valiosas, no archivos sobrantes.
2. Añadir a los dos documentos `energy2_test` una advertencia explícita de configuración, procedencia y limitación, dejando completo el texto histórico debajo.
3. No modificar `fvSolution`, condiciones de frontera, resultados, tiempos, mallas ni etiquetas del registro de corridas.
4. Registrar un criterio independiente de cierre: localizar logs reales asociados a los directorios `energy2_test`, contrastar su SHA/tiempos, y revisar el significado de `nEnergyCorrectors` en la versión de Foundation que realmente los ejecutó. Si faltan datos: marcar `NO_VERIFIED`.
5. Tratar el hallazgo de duplicación como **justificado por copia histórica pero científicamente contextualizado**. Si el auditor sigue reportando duplicados exactos en las variantes base, no autorizan borrado sin revisar referencias.

## Pruebas y límites

La prueba estática `tools/test_energy2_case_provenance.py` comprueba exclusivamente la diferencia del parámetro y que las dos carpetas `energy2_test` llevan advertencia de contexto. Se ejecuta con GitHub Actions por cambio en los documentos/fvSolution. **Un PASS no equivale a una corrida del solver**, estudio de sensibilidad, cumplimiento de residuales, validación experimental ni prueba del visor FoamLens.

**Siguiente investigación de MasterProject:** identificar un paquete real de resultados `energy2_test` y medir, en ejecución local comparable, qué cambió frente a V11 manteniendo las demás variables constantes. Dejar sin resolver hasta disponer de evidencia.
