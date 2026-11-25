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
