> **Quinto lote temporal verificado (b2c5cc1, FS_C08_BATCH_20261125T235504Z_f32def1d):** compilación aprobada, 3/4 variantes completas, 35/75 pasos. A 10 μs: Δt=2 μs U=160.818667 m/s, pMax=210905.107 Pa; 1 μs U=143.896184, pMax=183428.425; 0.5 μs U=118.655983, pMax=345312.839. Δt=0.25 μs 0/40, primer dp mínimo −164225.921 Pa, presión inicial 100000 Pa, rechazo no_admissible_descent (residuo 6.1718164e-6); no estado aceptado. No independencia temporal. Cinco lotes: 194/235 pasos aceptados, 18/20 variantes completas. Siguiente diagnóstico: descomponer residuo inicial en material metálico (térmico+conversión), transporte metálico, EOS gas y transporte/fuente gas; resolver por separado con la misma matriz lineal activa congelada y restaurar incrementos completos. Verificar superposición. Lote temporal corto --steps 2, horizonte 2 μs, 15 pasos programados, sin adaptativo ni alteración B14. Compilación y CFD del diagnóstico pendientes.

> **Cuarto lote verificado (78856d6, FS_C08_BATCH_20261125T234635Z_98d2cbf4):** 4/4 variantes, 40/40 pasos, compilación y CFD WSL verificados. A 10 μs, trial/oldLiquid U=143.896183998 m/s, p=183428.424976 Pa; oldGas/oldBoth U=143.896184544 m/s, p=183428.42572 Pa. Gas fuera de soporte anterior suprimido (primer paso referencia 5.80214612348e-19 kg), contraflujos finales 1928→209 caras, volumen 3.44e-29→3.22e-29 m³; líquido fuera de soporte cero en referencia. No resuelve aceleración. Acumulado cuatro lotes 159/160 pasos y 15/16 variantes completas. **Siguiente: temporal**, 2/1/0.5/0.25 μs fijos, 5/10/20/40 pasos a 10 μs, misma física y referencia, no adaptativo. Comparar exclusivamente tiempos guardados comunes y registros de momento y Jacobiano. Nuevo runner pendiente de ejecución. 

> **Actualización posterior 25-11-2026:** lote energético ejecutado y compilado en WSL (f8e356f4, FS_C08_BATCH_20261125T230435Z_b4fb5b69), 4/4 variantes y 40/40 pasos aceptados. A 10 μs: legacy U=143.896184 m/s, p=183.428425 kPa, residual L1=0.0001605273; oldGas U=145.596040, p=184.199143, L1=0.0001217930; currentLiquid U=143.896183, p=183.428424, L1=0.0001605272; oldGasCurrentLiquid U=145.596038, p=184.199142, L1=0.0001217929. Conservamos legacy. Primer paso celda 16511: advección líquida entrante 9320.618 J/m³, conducción 14.788, advección gaseosa 0.299, trabajo mecánico entrante 0.051. No demuestra transporte artificial en todos los casos. Tres lotes: 119/120 pasos aceptados, 11/12 variantes completas; no porcentaje de tesis. Nuevo lote support: trial/oldLiquid/oldGas/oldBoth, restringe experimentalmente movilidad correctora en caras internas con disponibilidad anterior exactamente nula en ambas celdas. No elimina masa ni cambia tolerancias; compilación y CFD pendientes. Ejecutar --suite support con dos jobs, dt fijo, portapapeles. Las entradas de lote energético pendiente más abajo quedan históricas.

# Bitácora científica FS-C08 — 25 de noviembre de 2026

## Alcance y evidencia
Rama independiente `research/fs-c08-conservative-phase-mass-20261123`, PR #79 borrador. Fuente FS-C07_THERMAL_20261123T183217Z_72da1bf4, 34,368 celdas fluidas, pruebas laminares de arranque con Δt fijo 1e-6 s. Material B14_reference procedente de B14 (49c3ede24c0aadfbc9fce9fcb4e9963c87f096ec), partición de densidades y Cv/energía aproximados; no calibración por composición, JMatPro, grafito ni validación física. Evidencia: stdout WSL aportado por investigador, no lectura directa de disco remoto. No fusionar con A/B.

## Cronología de recuperación
- Corrección de inventarios independientes de líquido/sólido/gas, repetición desde oldTime, proyección de volumen, intercambio de fase conservativo, energía interna con latente una vez y limitador de capacidad por donante. Tres pasos iniciales, fallo por masa gaseosa subnormal; arreglo aritmético sin clipping; diez pasos completos (46a5ad211), masa metálica 0.326409973068 kg.
- Lineal vs armónica (ade60ddce): lineal 10/10, 147.716 m/s a 10 μs, armónica 2/10, rechazo de presión positiva en tercer paso. No comparar sus velocidades finales a tiempos distintos.
- Actualización de matriz de momento: primer intento compiló, falló fixedFluxPressure antes del primer paso; corrección de orden (6bb416084) aprobada 10/10. Referencia actual refreshBeforePressure/separate/linear/incremental. Máximo residual de volumen aceptado 8.881784197e-16; máximo error EOS gas 7.78928135938e-16, residual máximo metal 4.99600361081e-15 kg y gas 2.07102028568e-17 kg. U máxima 143.896 m/s, presión máxima 183.428 kPa; aceleración no resuelta.

## Lote 1: movilidad (cuatro casos)
Commit 3ab54d228; FS_C08_BATCH_20261125T094911Z_ae54acc3, compilación única verificada, dos procesos seriales simultáneos, 40/40 pasos. Valores a 10 μs.
| Caso | Pasos | U máx m/s | p máx kPa | m sólida kg |
|---|---:|---:|---:|---:|
| legacy_separate | 10/10 |147.716 |196.827 |1.3088215e-6 |
| refresh_separate |10/10 |143.896 |183.428 |1.2041819e-6 |
| legacy_weighted |10/10 |253.898 |281.911 |5.0319991e-6 |
| refresh_weighted |10/10 |279.879 |294.452 |8.0091342e-6 |
Movilidad ponderada no seleccionada: empeora velocidad/presión, aunque conserva masa y volumen en la prueba.

## Lote 2: flujo predictor y ddtCorr
Commit 8fa88ae32; FS_C08_BATCH_20261125T225342Z_17c4cfb1; compilación verificada, 3/4 variantes completas, 39/40 pasos. Comparación a 9 μs, último tiempo común.
| Caso | Pasos | U máx m/s | p máx kPa |
|---|---:|---:|---:|
| refresh_reference |10/10 |136.152 |186.900 |
| refresh_total_upwind |9/10 |128.839 |186.299 |
| refresh_no_ddt_corr |10/10 |138.933 |188.999 |
| refresh_total_no_ddt_corr |10/10 |131.864 |188.410 |
Upwind aislado rechazado en décimo paso por masa gaseosa inadmisible celda 99. Conservamos referencia incremental. Transferencia bruta de metal a celdas previamente gas puro en primer paso = 6.38221529908e-8 kg en todas las variantes. Cero posterior no prueba ausencia de transporte a la región gaseosa inicial. Contraflujo no es por sí solo defecto.

## Lote 3: energía (código publicado, NO ejecutado)
Commit f8e356f490a46a0461f20d36db704b56b11d2884. Cuatro variantes legacy/oldGas/currentLiquid/oldGasCurrentLiquid; separación de advección gas/líquido, conducción y trabajo mecánico. Pendientes compilación y CFD. Los lotes 1 y 2 suman 79/80 pasos aceptados, no porcentaje de tesis. No ampliar tiempo físico ni validar rechupe por conservación algebraica. Pendientes: consistencia de momento, transporte de interfaz, balance CHT, propiedades auténticas y expansión de grafito, comparación experimental. No paso adaptativo en FS-C08.

## Ejecución y portapapeles
Desde WSL: un solo bloque, guarda stdout/stderr, preserva código de salida y copia con clip.exe aun si hay fallo:
```bash
(cd ~/OpenFOAM/FS_C08_WORKTREE && git fetch origin research/fs-c08-conservative-phase-mass-20261123 && git switch --detach FETCH_HEAD && python3 -B analysis_tools/run_fs_c08_batch.py --suite energy --jobs 2) 2>&1 | tee "$HOME/FS_C08_LATEST_OUTPUT.txt"; rc=${PIPESTATUS[0]}; echo "Codigo de salida: $rc" | tee -a "$HOME/FS_C08_LATEST_OUTPUT.txt"; clip.exe < "$HOME/FS_C08_LATEST_OUTPUT.txt"
```
Archivos individuales y resumen JSON/CSV: ~/OpenFOAM/FS_C08_DIAGNOSTICS/FS_C08_BATCH_*/. No modificar originales ni borrar intentos fallidos.
