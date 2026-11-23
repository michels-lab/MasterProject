# Caso A C3D04 · Revisión científica real del postprocesamiento nativo

**23 de noviembre de 2026. Estado: etapa 07/10 EN PROGRESO; 6/10=60 % de hitos operativos.** No es un porcentaje de validación física de la tesis.

## Evidencia real observada en WSL

El investigador ejecutó en el **worktree A exclusivo** `recover_existing_c14_3d_stage07.py` después de `git fetch && git merge --ff-only origin/main` sin actualizar los otros árboles extraídos. La salida real fue:

- `status = NEW_101_STATE_DIAGNOSTIC_PUBLISHED_NO_CFD`.
- `source_volume_mode = EXISTING_VOLUME_CSV_AND_JSON_FOUND`: el análisis volumétrico anterior sí contenía sus archivos; **NO fue preciso reconstruirlo**.
- El **primer descenso observado** de la fracción líquida del modelo `phaseChangeSource:alpha1` ocurre en el estado guardado `t=0.3 s`, después de `0.2 s`. **No sabemos el instante exacto de inicio ni el estado microestructural real.**
- `max_saved_interval_latent_power_W = 1038.881301373963`, durante `7.2–7.3 s`. **Estimación por diferencia finita de inventarios modelo** a Δt_guardado=0.1 s, no potencia instantánea nativa ni balance conservativo del paso de solver 0.001 s.
- `final_metal_T_volume_mean_K = 1450.7091627651344` al tiempo de simulación `10 s`.
- `final_metal_solid_inventory_kg_model = 0.03358283580064463` (33.58 g nominales, fórmula C14 con rho y alpha1).
- `native_copy_forensic_status = NATIVE_REPORT_SOURCE_VERIFIED_NOT_PHYSICAL_VALIDATION`: el informe de copia nativa pertenece al mismo CFD original.
- `native_commands_verified = false` y `energy_conservation_verified = false`: **faltan diagnósticos nativos; la procedencia SHA no acredita ejecución completa**.
- Salidas WSL originales, conservadas:
  - `~/OpenFOAM/C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01/C3D04_A_STAGE07_RECOVERY_REPORT.json`
  - `~/OpenFOAM/C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01/C3D04_A_STAGE07_KINETICS_101_STATES.csv`

**Procedencia:** salida de terminal aportada por el investigador, **no** lectura de archivos WSL privados desde GitHub. No se realizó nueva CFD ni se modificó el caso fuente, el C14 2D, la malla, o los worktrees B/FS.

## Causa operacional ya demostrada y límite científicamente insalvable offline

El wrapper original `run_c14_3d_complete_postprocess.py` registró cuatro subprocesos (`c14_functions`, `momentum`, `top_surface`, `foamLog`), errores de funciones originales, métricas de perfiles 80 puntos, lista de campos derivados faltantes e intento de energía nominal. El resumen anterior solo indicó `native_commands_verified=false`; no se suministraron sus códigos ni logs. Por ello **no es lícito atribuir el error nativo concreto a una causa particular todavía**.

El C14 original en `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/researchDiagnostics` **documenta expresamente** que los functionObjects `temperatureTimeDerivative` y `liquidFractionTimeDerivative` de tipo `ddt` requieren ejecución del solver y **no admiten reconstrucción retrospectiva con `foamPostProcess`**. Esto explica una incompatibilidad de diseño entre la ambición de paridad completa 2D y los 101 snapshots 3D, pero **no prueba que esos objetos hayan sido el error específico de esta ejecución**. No inventar 10 001 sondas de pasos de 0.001 s, no falsificar recalescencia ni modificar la física original.

El C14 además calcula `metalSensibleEnthalpy`, `metalLatentHeatPower`, `metalTopEnergyPower`, `metalMoldEnergyPower` y `metalBoundaryEnergyPower`. Para analizar conservación deben estar las **tablas nativas reales**, con su muestra temporal y orientación verificadas. Incluso un residual nominal del metal no demuestra el balance global metal+arena.

## Entrega: auditoría integrada, rigurosa, sin repetir solver

`cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/audit_existing_native_c14_stage07.py`

En **una sola ejecución** y con orígenes autenticados por SHA, inspecciona:
1. **Identidad absoluta** de `system/controlDict` C14 (original/CFD/copia) y SHA exacto de `log.foamMultiRun`; el reporte previo de 101 estados y el reporte nativo deben referir a las **mismas** carpetas y al mismo log.
2. **Los cuatro comandos reales**: lee de la evidencia original sus `exit_code`, comprueba la consistencia booleana `passed` y el resultado agregado. No inventa éxito solo porque existe el log. Localiza señales de FATAL IO, campo inexistente, compilación/coded functionObject o fallo real; **ignora** el anuncio normal de `FOAM_SIGFPE`.
3. **Cobertura contra C14 2D**: identifica familias `postProcessing` faltantes, campos calculados que no aparecieron en `10/metal`, perfiles de 80 puntos faltantes o no finitos.
4. **Auditoría energética nativa en lectura**: si las seis tablas requeridas existen y son consistentes, calcula un residual **NOMINAL** metal-only mediante el código existente `c14_3d_native_energy_closure.calculate()`, sin escribir ni presentar conservación verificada. Si faltan, devuelve error real y clasificación honesta.
5. Documenta los dos objetos `ddt` C14 incapaces de recuperar los 10 001 pasos como `KNOWN_OFFLINE_LIMITATION`, sin afirmar que sean el error observado.

**Salida única en una carpeta nueva, no sobrescribible:** `~/OpenFOAM/C3D04_A_C14_NATIVE_STAGE07_FORENSICS_01/C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json`. Consola JSON resume nombres/códigos de subprocesos fallidos, extractos literales de firmas de error, familias/campos/perfiles ausentes y estado de energía. Si la evidencia cambia, exige un destino de reporte diferente. No realiza `foamPostProcess`, `foamMultiRun`, remallado, Git, copia del CFD ni cambios de `postProcessing`. No reutilizar resultado nativo anterior como si fuera nuevo.

## Ejecución únicamente en worktree A

Tras integrar la entrega en `main`, desde WSL:

```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/audit_existing_native_c14_stage07.py"
```

No ejecutar `git pull` sobre `~/OpenFOAM/MasterProject`, ni cambiar FS o B. Esta comprobación es necesaria para distinguir qué diagnóstico puede **recuperarse offline de forma científicamente válida** y qué función C14 exigiría **un nuevo estudio transitorio controlado**, sin repetir la corrida existente solo por conveniencia. El siguiente bloque integrado será corrección selectiva de las funciones compatibles con WSL Foundation14, **únicamente en nueva copia**, después de observar los errores reales; sin sobrescribir la copia actual.

**Estado del hito:** todavía 7/10, **6/10 = 60 %**, balance energético/solidificación y comparación experimental pendientes. QA sintética de esta herramienta no es ejecución real WSL.
