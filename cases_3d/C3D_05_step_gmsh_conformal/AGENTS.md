> **20-11-2026 | REAL_CASE_B_OPENFOAM_RUN_PRIORITY_20261120 — PRIORIDAD ABSOLUTA DEL INVESTIGADOR:** dedicar las próximas Granadas de C3D-05/B a **ejecutar, depurar y analizar campos T/q sobre la malla HEX8 REAL** `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` (270788 celdas, 92200 metal/178588 molde, 12636 caras de contacto por lado, volúmenes reales 4.79754032229e-05/1.02843380345e-04 m3); **NO más cubos de 1 celda/1m3 como sustitutos de progreso científico** ni nuevas CI sintéticas sin un bloqueo nativo observado. El ejecutor `run_t0_granada.py` exige identidad exacta y `audit_t0_numerical_run.py` exige resoluciones reales de energía `e`. El resultado 3D se expone con archivo `.foam` únicamente tras `foamMultiRun` y auditoría completas. El C14 es solo una **referencia de arranque numérico** sobre la malla real, NO parámetros QuickCup/JMatPro. **No afirmar acceso a WSL, no afirmar CFD corrido y no cambiar etapa 3/7, 2/7 hitos=29% técnico sin logs reales.** Comando único autorizado para ese diagnóstico en WSL: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve`.

> **20-11-2026 | GRANADA_C3D05_F14_POSTPROCESS_REAL_20261120 — OBLIGACIÓN PERMANENTE:** F14 real CI confirmó lectura de **10 diccionarios productivos** y `foamPostProcess` nativo para metal/mold de 1 celda [PASS #44830571389](https://github.com/michels-lab/MasterProject/actions/runs/44830571389), tras corregir error `region0` (functionObject requiere `region metal/mold;`). El comando `--solve` consolida SHA de log, volumen, energía y 12,636 pares de q, con estados de aceptación en FALSE. **No confundir cubos sintéticos/CI con corrida 3D en WSL. Caso B 3/7, 2/7=29% técnico; G3/G4 no cerrados.** [Informe](../../docs/granada/C3D05_F14_POSTPROCESS_SMOKE_Y_EVIDENCIA_UNICA_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_REAL_COMPILER_20261120:** extractor C++ `q()` del Caso B para 12,636 caras por lado **compiló, enlazó y arrancó en OpenFOAM Foundation14 real sobre Ubuntu24.04** ([wmake+ldd+-help CI PASS](https://github.com/michels-lab/MasterProject/actions/runs/44828749324)). Flujo de CSV bilateral y análisis ahora transaccional, con SHA y recuperaciones seguras ([QA sintética PASS](https://github.com/michels-lab/MasterProject/actions/runs/44828766415)). **No hubo compilación en WSL del investigador, ni corrida CFD o medición de energía/flujo**; G3/G4 abiertos. **Caso B etapa 3/7, 2/7 hitos = 29% técnico, NO tesis.** [Informe](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D05_F14_WMAKE_REAL_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_PATCH_Q_12636_20261120 — NORMA PERMANENTE:** Caso B 3/7, 2/7 hitos=29% técnico hasta evidencia real. Granada `--solve` incluye compilación aislada de extractor isotrópico de `q()` bilateral, validación de pares 12,636 metal/arena, energía por intervalo y salvaguardas anti-sobrescritura. **Código NO compilado aún en WSL; no marcar continuidad de flujo ni física PASSED**. [Detalle](../../docs/granada/C3D05_T0_FLUJO_INTERFAZ_12636_CARAS_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_NATIVE_ENERGY_20261120 — NORMA PERMANENTE:** toda entrega indicará Caso B etapa 3/7, avance 2/7=29% hitos técnicos hasta evidencia G3/G4. `--solve` integra `foamPostProcess` metal/molde y serie `ΣρCvV⟨T⟩` con SHA; **CI sintética no acredita ejecución WSL, conservación ni flujo directo por interfaz**. Sin pruebas repetidas por pieza. [Análisis](../../docs/granada/C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md).

# Caso B C3D-05 — normas obligatorias de cualquier agente o nueva conversación

**Última revisión: 2026-11-19.** Prioridad: [Política global de entregas integrales](../../docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md), [estado canónico del caso B](../../docs/PROJECT_STAGE_STATUS.json), [protocolo GRANADA](../../.michelslab/GRANADA.md).

## 1. Siempre mostrar etapa y avance

**Caso B, etapa 3/7: configuración T0; 2/7 hitos técnicos completos = 29 %.** El porcentaje NO mide tesis, tiempo restante ni exactitud físico-numérica. G1 CAD/STEP/procedencia y G2 malla HEX8/contacto aceptados; G3 materialización física T0, G4 balance térmico, G5 solidificación, G6 contracción/alimentación y G7 validación permanecen pendientes. **Nunca incrementar hitos por commits, CI verde, pruebas sintéticas, documentación o referencia numérica C14**.

En cada informe: caso y etapa, número de hitos y %, evidencia observada, bloqueo y siguiente paquete técnico completo. Leer JSON en cada reentrada y no congelar el porcentaje por escritura manual.

## 2. Cero ciclos de micropruebas

Trabajar macro-bloques coherentes; **no pedir al investigador checkMesh, preflight, otro script, otra captura repetida** para validar cada modificación. Ejecutar QA de código en GitHub y preservar evidencias previas. Una sola acción WSL cuando realmente se justifique un hito end-to-end.

## 3. Fuentes y límites de C14

- Original aceptado **solo lectura**: `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` (270,788 HEX8, 92,200 metal y 178,588 arena; 12,636 caras de contacto por lado; 1,826 nonorth severas). No remallar, no sobreescribir evidencias de checkMesh ni afirmar estabilidad.
- `fvSolution` T0 ya se trazó a los tres originales C14 con manifiesto [SHA](t0_conduction/C14_FVSOLUTION_PROVENANCE.json). C14 tiene fluido+sólido; T0 es deliberadamente **dos sólidos**. No copiar p_rgh/U.
- Referencia C14 NUMÉRICA independiente en [Granada](../../docs/granada/C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md): `scripts/run_c14_numerical_granada.sh --solve` dentro de `t0_conduction/` es la única futura orden que prepara, valida y ejecuta un diagnóstico aislado de 100 pasos **si el investigador lo ejecuta expresamente**. No se ha ejecutado en su WSL. El generador conserva SHA de cinco archivos, explica la hipótesis **Cp≈Cv** y `k=Cp mu/Pr`; no marcarlo como JMatPro ni hierro líquido real.
- El archivo físico `t0_conduction/T0_INPUTS.json` contiene `null` deliberados: no sustituir valores de ensayo C14 por entradas medidas inexistentes. Una corrida exitosa no sustituye balance de energía, flujo interfacial, independencia de malla, ni validación experimental.

## 4. Cierre auditable

Mantener código + regresiones + README caso + auditorías ES/EN + validaciones ES/EN + hoja de ruta + protocolo + índice + [estado canónico](../../docs/PROJECT_STAGE_STATUS.json) sincronizados en el mismo bloque. Distinguir `CODE_READY`, `WSL_NUMERICAL_RUN`, `ENERGY_VERIFIED`, `EXPERIMENTALLY_VALIDATED`. CI ejecuta pruebas estáticas, no `foamMultiRun`. Antes de cambiar estados, exigir evidencia y versión concreta del caso.

**Regla permanente:** no presentar solo un preflight como entrega Granada, no inventar propiedades termofísicas, no rehacer malla aceptada, no contaminar Caso A ni otros pilotos.
