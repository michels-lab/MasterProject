> **23-11-2026 | CASO B C14 PHASE ACTUAL EN WSL (101 estados):** `alpha1<.999` primer estado guardado **0.3s**, anterior **0.2s**; media final por celdas **0.8424205632624837**, mínimo sobre 101 estados **0**; Courant máximo sobre log **0.267133**. Físicamente validado **NO**. El analizador nativo previo **SÍ** se ejecutó; nueva cronología independiente `summarize_existing_case_b_c14_phase_timeline.py` y 9 tests publicados, **aún NO corridos en la WSL**. Nunca repetir `--run-full`, no remallar. Caso B G3/G4/G5 físicos abiertos, 2/7 hitos aceptados. [Informe nuevo](../../../docs/granada/C3D05_B_C14_101_ESTADOS_ALPHA1_OBSERVADO_Y_TIMELINE_20261123_ES.md).

> **23-11-2026 | CASO B C3D-05 — CFD C14 REAL 10 S COMPLETADO; AUDITORÍA DE ALPHA1 PREPARADA (AÚN NO CORRIDA EN WSL):** el investigador compartió el mensaje nativo `C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED` con `native_C14_F14_solver_run=true`. El C14 metal `fluid`, arena `solid`, `solidificationMeltingSource` concluyó 10 s en la malla STEP/Gmsh HEX8 real (92,200 + 178,588 celdas); **NO** repetir `--run-full`. Publicados `c14_physics/analyze_existing_case_b_c14.py` y 9 pruebas fuente/negativas para leer en **solo lectura** el log original, SHA, `T`, `phaseChangeSource:alpha1`, `p_rgh`, cruces Tliq/Tsol y el primer cambio de fase guardado, sin solver/remallado. Hasta ejecutar este análisis **NO se sabe el resultado de alpha1(t)**; no se ha verificado calor latente, energía, JMatPro/QuickCup ni convergencia. **Caso B etapa 3/7, 2/7=29 % hitos técnicos.** [Informe](../../../docs/granada/C3D05_B_C14_10S_CFD_REAL_COMPLETADO_Y_ANALISIS_SOLO_LECTURA_20261123_ES.md).

> **23-11-2026 | CASO B C3D-05 — FIX DEL ARRANQUE FOUNDATION14, NO CFD EJECUTADO:** primer intento WSL de `run_case_b_c14_native.sh --run-full` abortó en `/opt/openfoam14/etc/bashrc: line 46: ZSH_NAME: unbound variable` por `set -u` de nuestro wrapper antes de cargar la configuración oficial. **Ningún Python materializador, malla copiada ni foamMultiRun se ejecutaron.** Corregido: `set +u` exclusivamente durante `source bashrc`, luego `set -u`; añadido `bash -n` y regresión shell con `ZSH_NAME` sin definir (CI aún no verificado). Estado Caso B **3/7; 2/7=29% hitos técnicos**, G3–G5 físicos abiertos. [Bitácora de causa y reparación](../../../docs/granada/C3D05_B_C14_SOLIDIFICACION_3D_FASE_FISICA_20261123_ES.md).

# Caso B C3D-05 — Física C14 original de solidificación sobre HEX8 real

**No confundir con T0 C14 numérico de dos sólidos:** `~/OpenFOAM/C3D05_T0_C14_SHK_01` ya terminó una conducción simplificada de 0.1 s. Esta carpeta contiene un nuevo modelo **metal fluido + arena sólida + `solidificationMeltingSource`**, físicamente fiel al **C14 original de 2D** y geométricamente adaptado al Caso B. **No incorpora datos JMatPro QuickCup, contracción ni convergencia de malla.**

## Fuente y malla

- A partir del original `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef` y del verificador de fidelidad C14 probado en `cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/c14_source_fidelity.py`.
- Malla B aceptada **solo lectura**: `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`, exactamente **270,788 HEX8**, 92,200 metal y 178,588 arena; contacto `mappedWall` 12,636 caras por lado; alto riesgo de no ortogonalidad.
- Se preserva el modelo original, las condiciones físicas y los controles `endTime=10`, `deltaT=0.001`, `writeInterval=100`. Los únicos cambios son el nombre/cantidad geométrica de parches exteriores del molde con **BC idénticas**, `pRefCell=0` con celda nativa comprobada y zona completa `metal` en la copia.

## Acciones

Una orden integrada WSL, desde el checkout actualizado:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/run_case_b_c14_native.sh --run-full
```

Usar **`--materialize` en lugar de `--run-full`** para detenerse después de producir y analizar los archivos nativos sin resolver aún el CFD; el modo `--preflight` es solo lectura. No encadenar `--materialize` y `--run-full` sobre el **mismo destino**: el bloqueo de sobreescritura es intencional. Si ya se materializó y luego se desea correr esa misma carpeta, se requiere una ruta de ejecución específica que reutilice la evidencia y la modele como una decisión separada; **no borrar ni volver a generar** la carpeta para evitar alteraciones inadvertidas.

**Destino aislado:** `~/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01`. Nada de la geometría original, T0 de 0.1 s o Caso A se edita. Un fallo se preserva como evidencia en la carpeta candidata o de solver, sin reintento automático.

## Evidencias

El ejecutor genera `C3D05_B_C14_FLUID_SOLID_STAGE_REPORT.json` con huellas originales, selección de celda y zonas, hashes de cinco elementos `polyMesh` de cada región, los 22 diccionarios de modelo y la salida de `foamDictionary` nativo. Cuando se lanza `--run-full`, el informe sólo marca `native_solver_run=true` si existen **log `End`/10 s/modelos `fluid`+`solid`+`solidificationMeltingSource` y archivos finales nativos**. La existencia de `phaseChangeSource:alpha1` no demuestra por sí sola solidificación; requiere una línea temporal.

Se incluyen ocho pruebas de código y workflow estático sin CFD. **La publicación del código no demuestra que hayan pasado ni que el ejecutor haya funcionado en la WSL real.**

Para detalles y límites: [informe canónico del 23-nov](../../../docs/granada/C3D05_B_C14_SOLIDIFICACION_3D_FASE_FISICA_20261123_ES.md).

**Estado:** Caso B etapa **3/7**; **2/7=29% hitos técnicos**, G3/G4/G5 abiertos, sin solidificación del B real observada todavía.
