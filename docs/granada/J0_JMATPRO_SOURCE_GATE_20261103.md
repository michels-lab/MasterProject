# GRANADA — J0: origen numérico JMatPro y puente OpenFOAM (2026-11-03)

**Alcance:** `MasterProject` (OpenFOAM Foundation v14). Sin simulaciones ni datos experimentales creados. Esta rama **NO** modifica C11/C14, B14, V15/V16, C3D, geometrías, propiedades de casos o registros científicos canónicos.

## Problema reproducible en el puente anterior

`analysis_tools/jmatpro_property_bridge.py` convertía valores no numéricos a texto, toleraba filas inválidas y empleaba *clamping* en `interp`: si se pedía `rhoRef(T)` fuera del intervalo de temperatura medido, devolvía el extremo más cercano. Un valor de `beta` calculado con esa referencia podía parecer trazable sin que hubiera evidencia en ese T. Además no producía una huella SHA-256 del CSV de origen.

## Corrección implementada

1. **Ingesta explícita:** `T_K` obligatorio y único, sin duplicados de temperatura; campos físicos conocidos numéricos finitos; T en kelvin >0; `rho`, `Cp`, `k` positivos, `fL` entre 0 y 1. El orden de filas puede invertirse porque el auditor ordena por T, pero **nunca** deduplica ni corrige temperaturas silenciosamente.
2. **Cálculo sin extrapolación:** `interp` retorna `None` fuera del soporte medido. El ajuste de densidad usa únicamente muestras dentro del rango líquido seleccionado y reporta `rhoRef`, `beta`, pendiente, `R²`, muestra y rango solicitados; sin muestra/ref adecuados, conserva el estado `NOT_EVALUATED`.
3. **Diagnóstico de fase:** `fL` de JMatPro contra la rama superior de equilibrio `solidificationMelting` con `alpha1e`; NO equivale a la evolución de entalpía por paso temporal ni demuestra recalescencia.
4. **Procedencia y salidas:** SHA-256 de bytes CSV, número de filas, rangos y JSON con estados `J0_status=OPEN`, `experimental_validation=false`, `CFD_executed=false`. CSV de comparación solo si existe `fL`. Escrituras de archivos de reportes atómicas en carpeta separada del archivo fuente; rechazo si el origen queda dentro del directorio de salida.
5. **Gates con fallo explícito:** `--require-density` y `--require-phase` impiden aceptar reportes numéricos parciales en flujos estrictos. 12 pruebas sintéticas con casos negativos y un workflow limitado a Python.

## Uso en laptop WSL Ubuntu

Desde el directorio raíz del repositorio **en la rama que contiene este cambio**:

```bash
python3 -m unittest discover -s analysis_tools -p 'test_jmatpro_property_bridge.py' -v
python3 analysis_tools/jmatpro_property_bridge.py /ruta/local/export_jmatpro.csv \
  --out /ruta/local/auditoria_jmatpro \
  --rho-ref-T 1473.15 --beta-min-T 1473.15 --beta-max-T 1773.15 \
  --Tsol 1423 --Tliq 1473 --alpha1e 0.8 \
  --require-density --require-phase
```

Los parámetros por defecto son **referencia histórica de C11/C14**, no valores aprobados para cada composición. Ajustarlos con evidencia de JMatPro y experimental. No subir CSV con composiciones o datos del investigador sin su decisión explícita.

## Gates que siguen abiertos (NO cerrados en esta PR)

- **J0**: composición real CE/S/Mn; archivos de exportación numérica originales por colada, método/versión JMatPro, unidad/rango/cálculo, `Tsol`, `Tliq`, `L`, `Cp(T)`, `k(T)`, `rho(T)`, `fL(T)`, fases metalúrgicas y evaluación física.
- **G1**: QuickCup y termopares experimentales, alineación de condiciones iniciales y fronteras, incertidumbres y curvas de enfriamiento. No se han ajustado valores del solver.
- **V15/V16 / C3D**: avances y PRs independientes; esta auditoría no los ejecuta ni valida.

**Punto de reentrada:** verificar workflow en SHA exacto del PR, revisar importación de los CSV reales localmente, documentar composición/procedencia (sin publicar información sensible), comparar rangos, y solo entonces plantear casos nuevos conservando los históricos. Nada en GitHub Actions instalará OpenFOAM, ejecutará CFD o afirmará validación.
