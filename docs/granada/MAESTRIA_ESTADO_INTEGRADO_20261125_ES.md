> **FS-C08 — sexto lote verificado:** compilación corregida; 3/4 variantes completas, 7/15 pasos; atribución inicial en las cuatro. Término volumétrico metálico domina, aproximadamente 1/Δt (−20.79 a −167.09 kPa para 2 a 0.25 μs); superposición <0.01 Pa. Acumulado 201/250 pasos, 21/24 variantes de seis lotes únicos, réplica excluida. Nuevo diagnóstico auxiliar de compresibilidad finita con referencia bibliográfica Fe puro, no propiedad calibrada de fundición ni cambio de EOS. Pendiente compilación/ejecución; B14, A/B y validación intactos. [Bitácora](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md).

> **FS-C08 — sexto lote:** compilación rechazada antes de CFD (List.C:211, distance(int&, int&)); candidato de corrección dac7a456 con inicialización escalar explícita y eliminación de lista no utilizada, pendiente de verificación WSL. El acumulado verificado continúa en 194/235 pasos y 18/20 variantes. Sin cambios físicos o de hitos A/B. [Bitácora](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md).

> **Actualización FS-C08, quinto lote:** sensibilidad temporal 3/4 variantes completas, 35/75 pasos, acumulado 194/235 pasos y 18/20 variantes. A 10 μs, U máxima 160.819/143.896/118.656 m/s con Δt=2/1/0.5 μs; 0.25 μs rechazado en primer paso por positividad de presión, dp mínimo −164226 Pa. No independencia temporal. Próximo bloque: atribución lineal de la presión inicial a cuatro fuentes de volumen, sin modificar ecuaciones físicas ni B14, cuatro casos fijos hasta 2 μs; ejecución pendiente. [Bitácora FS-C08](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md).

> **Actualización FS-C08, cuarto lote:** soporte de transporte 4/4 variantes completas, 40/40 pasos; acumulado de los cuatro lotes 159/160 pasos, 15/16 variantes. Eliminar flujos de gas fuera del soporte previo no reduce U máxima (143.896 m/s a 10 μs). Siguiente lote: sensibilidad temporal a horizonte físico común de 10 μs, cuatro pasos fijos (2, 1, 0.5 y 0.25 μs), no adaptativo; código publicado, ejecución pendiente. No cambios de física, hitos A/B o validación experimental. [Bitácora FS-C08](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md).

> **25-11-2026 | Actualización FS-C08:** tercer lote (energía) compilado y ejecutado, 4/4 variantes completas, 40/40 pasos; tres lotes acumulados 119/120 pasos, 11/12 variantes completas. Cambiar nivel temporal de advección no elimina aceleración; referencia retenida 143.896 m/s a 10 μs. Nuevo lote de soporte de transporte de presión (trial/oldLiquid/oldGas/oldBoth) publicado en rama independiente, compilación y CFD pendientes. Sin validación física ni cambio de hitos A/B. [Bitácora FS-C08](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md).

# Estado integrado de investigación — 25 de noviembre de 2026

Actualización documental, no corrida nueva. Conserva la [bitácora del 24-11](MAESTRIA_ESTADO_INTEGRADO_20261124_ES.md) como historia; esta página prevalece para el alcance aquí documentado. Fuentes: estados canónicos de A/B del repositorio, consola WSL de FS-C08 de los lotes y observaciones del investigador en conversaciones de campaña. Los archivos remotos de laboratorio no se han inspeccionado directamente en esta actualización.

| Línea | Estado vigente | Bloqueo |
|---|---|---|
| 2D histórica C/B | 26/26 corridas; C14 referencia de solidificación; B14 referencia de propiedades rho(T) para contracción | JMatPro/QuickCup y validación experimental |
| 3D-A C3D04 | Etapa 9/10, 8/10 = 80% de hitos operativos; C14 fiel de 10 s archivado; corrida fija compacta de 200 s reportada completa | Publicación de corrida de laboratorio pendiente de autenticación; conservación discreta, independencia y experimento |
| 3D-B C3D05 | Etapa 3/7, 2/7 = 29% técnico; C14 original 10 s, 101 estados; piloto MPI adaptativo de 3 s reportado | No CFD de 200 s completo confirmado; cierre físico, conservación, malla y tiempo |
| FS-C08 | Solver nativo compilado y ejecutado en WSL; lotes movilidad 4/4 y flujo 3/4 completos | Aceleración del gas, energía global CHT y propiedades calibradas; lote energético aún pendiente |
No existe porcentaje total de tesis. No intercambiar hitos, mallas, materiales ni estados de ramas.

## Campaña 200 s: distinguir ejecuciones

**Fija compacta (laboratorio):** el investigador reportó C14-3DA-200s `SOLVER_COMPLETE_COMPACT_AUDITED`, solver_completed=true, 200000 pasos, tiempo final 200.0 s; publicación GitHub falló por autenticación. Es ejecución reportada completa, no archivo publicado ni validación física. C14-2D, B14-2D y C14-3DB fueron reportados preparados sin corrida al registrar ese resultado; posteriormente se observó C14-2D serial en ejecución en laboratorio, sin final confirmado. Lanzamiento MPI de laboratorio posterior falló por `RuntimeError: load Foundation14` antes de ejecutar nuevas corridas. No reejecutar A ni limpiar salida para subsanar publicación.

**Adaptativa independiente (PC):** C14-3DA falló (temperatura inicial negativa reportada a 0.7 s); preservar intento, no confundir con A fijo 200 s completo. C14-2D último registro recuperado 14 s/1728 pasos, dt=.02 s, auditoría de cadencia inicial aprobada; no final confirmado. B14-2D bloqueado/fallido preservado. C14-3DB serial interrumpido por el investigador cerca de 2.41 s; piloto MPI de 3 s con 8 procesos reportado completo, 2042 pasos, 872.54 s, Co_max=.248564, maxCo=.25, maxDeltaT=.025 s (piloto específico, no política de todas las campañas). No es corrida de 200 s. Los resultados se consignan como observaciones reportadas, no auditoría independiente de logs o archivos.
Solo cuatro casos autorizados: C14-3DA, C14-2D, B14-2D, C14-3DB. B14 3D excluido. Mantener fixed/adaptive/MPI independientes.

## FS-C08: evidencia nueva que sustituye el bloqueo histórico de compilación
[Bitácora de cada variante](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md) · [Estado canónico](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/STATUS.json) · [PR #79](https://github.com/michels-lab/MasterProject/pull/79) (rama separada, no merge).

- Propiedades de ingeniería derivadas de B14 (no curvas auténticas de fases calibradas). Δt fijo 1e-6 s, pruebas 10 pasos, no adaptativo por decisión del investigador. FS-C07 original preservado.
- Lote movilidad: 40/40 pasos aceptados; referencia refresh_separate 143.896 m/s y 183.428 kPa a 10 μs; ponderada combinada 279.879 m/s y 294.452 kPa. No seleccionada.
- Lote flujo: 39/40 pasos aceptados; 3/4 variantes completas, upwind aislado falla en décimo paso por masa gaseosa inadmisible (celda 99). A 9 μs referencia 136.152 m/s, upwind 128.839, sin ddtCorr 138.933, combinado 131.864. Ninguna elimina aceleración; no seleccionar por velocidad sola. Referencia refresh/separate/linear/incremental retenida.
- Próximo lote energético: código f8e356f4, cuatro combinaciones de niveles temporales de energía advectada; compilación y CFD pendientes. 79/80 pasos de los dos lotes, no 98.75% de investigación. Energía global CHT y contracción física NO verificadas.
- Operación Granada: una compilación, 2 casos independientes simultáneos por defecto, reportes CSV/JSON, comando con tee y clip.exe para pegar resultados sin ratón (también fallos). No micropruebas individuales.

## Registros principales
- [C14 2D](../../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/CASE_NOTES.md), [B14 2D](../../cases_controlled_buoyancy/B14_topFixedFlux_explicitRef/CASE_NOTES.md).
- [Caso A](../../cases_3d/C3D_04_rounded_multiblock_pilot/README.md), [estado A](../C3D04_CASE_A_STATUS.json).
- [Caso B](../../cases_3d/C3D_05_step_gmsh_conformal/README.md), [estado B](../PROJECT_STAGE_STATUS.json).
- [Comparación C14 2D/A/B](C14_COMPARATIVO_2D_3DA_3DB_SONDAS_20261124_ES.md): 10.76/22.41/23.07 mm/s máximos centrales en 10 s; no confundir con máximos locales FS-C08. C3D01/02/03, B14 y C14 históricos preservados.
