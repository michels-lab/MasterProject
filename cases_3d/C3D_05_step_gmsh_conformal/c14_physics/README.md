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
