# Operación Granada — Caso B 3D: fvSolution derivado del Caso C14

**19 de noviembre de 2026. Estado de investigación: etapa 3/7 (T0), avance 2/7 hitos = 29% técnico — no es porcentaje de tesis ni de validación CFD.**

## Decisión del investigador
Tomar los `fvSolution` auténticos del caso `C14_topFixedFlux_explicitRef` como referencia de la preparación térmica T0 del `C3D_05_step_gmsh_conformal`, en lugar de elegir parámetros sin fuente.

## Procedencia y uso
- **C14 / `system/fvSolution`:** `PIMPLE` global `nOuterCorrectors=3`, `nCorrectors=2`, `nNonOrthogonalCorrectors=1`, y relajación `e/eFinal=1.0`. Se trasladaron al global T0.
- **C14 / `system/mold/fvSolution` (región sólida):** `PCG` + `DIC` para `(h|e)`, tolerancia `1e-6` y `relTol=0.05`, PIMPLE regional `1/2/0`. Se aplicaron a **ambos sólidos T0** (`metal` y `mold`), con clave explícita `e` y `eFinal { $e; relTol 0; }`.
- **C14 / `system/metal/fvSolution` (región fluida):** `nEnergyCorrectors=2` se conserva como intención numérica y se ubica en el `PIMPLE` global de la prueba T0 multirregión. No se copiaron solucionadores `p_rgh`, `U`, `h` ni parámetros de referencia de presión porque la prueba T0 del Caso B contiene **dos sólidos**, no una región fluida.

Los tres archivos originales siguen inalterados. El manifiesto [`C14_FVSOLUTION_PROVENANCE.json`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/C14_FVSOLUTION_PROVENANCE.json) registra sus SHA Git blob. El generador [`prepare_t0.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/prepare_t0.py) exige que esas fuentes coincidan **antes de escribir una copia del caso**. La regresión [`test_c14_fvsolution.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_c14_fvsolution.py) contrasta valores, procedencia y ausencia de solucionadores fluidos.

## Limitaciones técnicas obligatorias
- C14 era `metal fluid` + `mold solid`. T0 del Caso B es `metal solid` + `mold solid`. Se reutilizan ajustes pertinentes, **no** se afirma que ejecutar ambos implique equivalencia de física.
- El papel de `nCorrectors` de presión en un caso sólido es inactivo; el efecto real de `nEnergyCorrectors` trasladado al global debe comprobarse con OpenFOAM Foundation 14.
- El campo de energía en el T0 sólido es `e`. La no ortogonalidad severa (1,826 caras >70°) exige verificar estabilidad y sensibilidad del corrector; copiar `0` del C14 arena regional **no demuestra estabilidad**.
- `foamDictionary` y las pruebas CI verifican sintaxis/consistencia del código, **no** convergencia, cierre de energía, validación con QuickCup ni propiedades reales.

**Estado:** código configurado y con trazabilidad a C14; propiedades físicas T0 aún sin completar, caso térmico no materializado y solver no ejecutado en WSL. Sigue **etapa 3/7, 2/7 hitos (29% técnico)**. No reabrir la revisión STEP/HEX8 ya cerrada ni solicitar micropruebas de manera aislada.
