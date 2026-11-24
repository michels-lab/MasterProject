# FS-C07 — 1 segundo OpenFOAM Foundation 14 completado; falla **posterior** en auditoría de fases

Fecha: **23 de noviembre de 2026**. Evidencia: salida literal de terminal aportada por el investigador y lectura del código FS-C07 actualmente versionado. Los resultados y log crudos siguen en WSL y **no han sido transferidos a GitHub**. La conclusión es de *solver nativo completado según el log*, **no** de aceptación física o auditoría completa.

## Identidad de la corrida

- Rama originalmente lanzada desde `~/OpenFOAM/FS_C02_WORKTREE` en HEAD `7b0626e41`.
- Caso aislado **único**: `/home/michel/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4`.
- Fuente FS-C06 aceptada y no modificada: `/home/michel/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T032645Z_064d3091`.
- Herramienta usada para diagnóstico: `analysis_tools/inspect_existing_fs_c07.py`; ejecución **solo lectura**, `this_diagnostic_executed_solver=false`, `this_diagnostic_modified_case=false`.
- `FS_C07_REPORT.json.status=FS_C07_INCOMPLETE_PRESERVE_EVIDENCE`.
- `FS_C07_REPORT.json.last_error=FS-C03 STATIC GATE: invalid VOF / absolute-solid phase allocation`.

## Evidencia inequívoca sobre ejecución del solver

```text
solver_end_marker_in_recent_log_tail: true
latest_log_Time_s: 1.0
max_time_directory_s: 1.0
time_directories_count: 10868
last_saved_complete_phase_fields_s: 1.0
complete_phase_field_directories_count: 20
log_error_token_count_in_tail: 0
log_size_bytes: 43857357
...
Time = 1s
ExecutionTime = 2344.433662 s  ClockTime = 2355 s
...
End
```

`2355 s = 39 min 15 s` de reloj. Existen veinte directorios de tiempo con los tres campos reales `alpha.metal`, `alpha.metal.solid`, `T.metal`; **no se ha demostrado todavía que sus valores satisfagan las restricciones físicas**. Las otras miles de carpetas proceden de la configuración de monitores originales FS-C06 (`writeControl timeStep; writeInterval 1`), con escrituras locales adicionales. El diccionario nuevo FS-C07 `writeControl writeTime` fue **versionado después** de arrancar este caso y no debe suponerse aplicado retroactivamente.

## Potencias nativas de interfaz al finalizar

```text
fluid_to_mold: Q_fluid = -7184.75867563 W
mold_to_fluid: Q_mold = +7184.84637194 W
```

Residuo firmado `Q_fluid+Q_mold=+0.08769631 W`, residuo relativo `0.00122058%` respecto al promedio de potencias absolutas. Consistente con reciprocidad térmica a la interfaz en `t=1s`, **no** demuestra cierre integral de energía ni exactitud experimental.

## Masa metálica: ¡no afirmar ausencia de flujo abierto!

Salida nativa a `t=1s` para `atmosphereLowerSides`:

```text
sum(alphaRhoPhi.metal) = 7.54288884513e-06 kg/s
sum(alphaRhoPhi.air) = 0.00520963150429 kg/s
sum(rhoPhi) = 0.00521717439313 kg/s
```

Para `atmosphereSides`:

```text
sum(alphaRhoPhi.metal) = 8.51597548632e-20 kg/s
sum(alphaRhoPhi.air) = -0.000443367807681 kg/s
sum(rhoPhi) = -0.000443367807681 kg/s
```

`fluid_to_mold` transportó `alphaRhoPhi.metal≈4.01265854863e-25 kg/s` al último instante (prácticamente nulo). El flujo metálico por `atmosphereLowerSides` no es cero. Hay que integrar **todos** los flujos metálicos de frontera por tiempo y comparar con la masa metálica en el dominio; una sola potencia instantánea no prueba masa perdida acumulada. La orientación y signo dependen de la normal de la frontera.

## Causa exacta del estado INCOMPLETE

El solver alcanzó `Time=1` y `End`. **La aplicación Python falló después**, durante `audit_saved_fields()`, al llamar `phase_volume_metrics()` para integrar datos guardados.

La validación de `phase_volume_metrics` en `analysis_tools/stage_fs_c06_vof_solidification.py` realiza **dos filtros**:

1. Primer filtro: `-1e-8<=alpha.metal<=1+1e-8` y `-1e-8<=alpha.metal.solid<=alpha.metal+1e-8` por celda. Su fallo emite **literalmente** `invalid VOF / absolute-solid phase allocation`.
2. Segundo filtro (solo si pasa el primero): `0<=alpha.metal.solid<=alpha.metal<=1` estrictamente. Tiene **mensaje distinto** (`phase-volume integration requires strict 0<=solid<=metal<=1`).

La primera puerta falló. Por tanto, **al menos una celda incumple el margen 1e-8**. El valor marginal `Min(alpha.metal)≈-9.7664e-46` observado antes a `t≈0.114s` **no basta por sí solo** para explicar este error. Debemos conocer el campo/instante/celda del peor desvío; no está reportado en el JSON original.

**No recortar artificialmente** el campo original ni desactivar la validación, pues eso ocultaría defectos de formulación o transporte de fases. Hasta cuantificar el problema, no declarar liquidus cruzado, solidificación positiva ni contracción. `native_cfd_executed=true` es un hecho del log, pero el reporte de stager quedó en `false` porque esta marca solo se actualizaba tras pasar toda la auditoría de campos; la semántica de ese campo fue insuficiente para una corrida que acabó con error de postproceso.

## Recuperación sin repetición de 39 minutos

Se añadieron:

- [`analysis_tools/diagnose_fs_c07_phase_allocation.py`](../../analysis_tools/diagnose_fs_c07_phase_allocation.py): lee las veinte instantáneas nativas, informa mínimos/máximos de `alpha.metal` y `alpha.metal.solid`, recuentos de celdas que incumplen las restricciones en tolerancias `1e-12`, `1e-10`, `1e-8`, ubicación y valor del primer/peor defecto, número de celdas con metal bajo liquidus de **cribado**, y SHA-256 de cada campo. Modo `--compact` para salida breve, sin cortar información de casos críticos.
- Pruebas sintéticas de violación significativa vs redondeo [`analysis_tools/test_diagnose_fs_c07_phase_allocation.py`](../../analysis_tools/test_diagnose_fs_c07_phase_allocation.py).
- CI estático que compila e importa estos scripts, distinto de ejecutar OpenFOAM. **Todavía sin verificación de CI/WSL**.

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
git fetch origin research/fs-c02-metal-air-vof-20261117
git switch --detach FETCH_HEAD
python3 analysis_tools/diagnose_fs_c07_phase_allocation.py --compact \
  ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
```

Después de leer el defecto real: decidir si se trata de desbordamiento numérico local o inconsistencia seria del modelo de fuente sólida; solo entonces implementar el criterio de integración científicamente válido, sin alterar archivos originales. No reejecutar `foamMultiRun`.

## Caso 3D independiente

El investigador también informó que su postproceso independiente `C3D-05` ejecutado desde `~/OpenFOAM/MasterProject` (`main`) terminó con `SPATIAL_ALREADY_PRESENT_SHA_VERIFIED_NO_RECOMPUTE`, seis tiempos 0–0.1 s, `12636` caras/tiempo, doce bandas, potencias metal/arena exactamente contrapuestas con precisión de salida. Ese caso trata **conducción nativa 3D archivada** y **no debe confundirse** con `FS-C07` metal–aire VOF ni usarse para demostrar contracción.
