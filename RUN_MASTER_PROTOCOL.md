# QUICKCUP — PROTOCOLO MAESTRO DE CORRIDAS Y SINCRONIZACIÓN

**Versión:** 2026-10-08 · **Alcance:** repositorio `QuickCup-Solidification` (autónomo, no depende de Michel's Lab/main)  
**Autoridad:** este archivo define qué revisar y actualizar antes/durante/después de **cada** corrida o auditoría de OpenFOAM Foundation 14.  
**Regla:** ningún agente ni conversación debe dar por actualizado el proyecto basándose solo en un `git push`, en un `End`, en un termopar que llega a 10 s o en una nota aislada. Usar este protocolo + `RUN_CASE_REGISTRY.csv`.

## Agentes especializados de auditoría (2026-10-08)

Cuatro agentes declarados en .github/agents/: observación local de corrida, interpretación/validación de postProcessing, verificación física/numérica y mantenimiento de documentación. El inventario de campos está en [POSTPROCESSING_FIELD_GUIDE_ES.md](POSTPROCESSING_FIELD_GUIDE_ES.md).

Verificadores ejecutables:
- analysis_tools/live_run_watch.py: lee logs EN VIVO si el usuario lo ejecuta junto a su OpenFOAM local.
- analysis_tools/audit_postprocessing_config.py: verificación estática de functionObjects V14.
- .github/workflows/quickcup-research-audit.yml: ejecuta validación estática si GitHub Actions la programa y puede iniciar runners. Verificar su estado; no asegurar actividad continua si falla. No se controla el proceso local desde GitHub.

Los agentes no deben identificar una declaración en diccionario como prueba de ejecución. Actualizar manuales ES/EN y guía de campos cuando una herramienta/interpretación cambie, manteniendo referencia a implementación y evidencia.

## A. Fotografía inicial, 2026-10-08

- **30 carpetas** en `cases_controlled_buoyancy/`: 26 casos del batch histórico V3–V13 (todos RUN/ANALYSIS-VERIFIED), B14/C14 (ambos RUN/ANALYSIS-VERIFIED), C11-energy2 (RUN/ANALYSIS-VERIFIED), B11-energy2 (solo PREPARED; sus salidas heredadas se retiraron).
- **29 casos verificados, 1 no ejecutado**. El CSV `analysis_results/full_campaign_audit/case_metrics.csv` **solo representa 26**. `bc_pair_metrics.csv` contiene 13 parejas B/C; no incluye B14/C14. `profile_inventory.csv` tiene 104 entradas, solo 26×4.
- V14: `analysis_results/v14_bc_comparison/summary.md`; C11-energy2: `analysis_results/c11_energy2_test/summary.md`. **Estos resultados NO son filas de `full_campaign_audit/`** todavía.
- **Baseline para la futura validación G1:** `C14_topFixedFlux_explicitRef`, con `C11_topFixedFlux_airGapOF14` congelado como referencia histórica. La puerta **J0 JMatPro está abierta**; no crear G1 definitivo sin cerrar trazabilidad termofísica.
- **Separar estado:** `PREPARED_NOT_RUN` ≠ `RUN_VERIFIED` ≠ `ANALYSIS_VERIFIED` ≠ `EXPERIMENTALLY_VALIDATED`.

## B. Documentos de verdad y cuándo cambiarlos

| Registro / archivo | Regla por corrida o análisis |
|---|---|
| **`RUN_MASTER_PROTOCOL.md`** | Consultarlo **antes** de toda acción; modificarlo si cambia el procedimiento, los entregables o la arquitectura científica, no por cada número nuevo. |
| **`RUN_CASE_REGISTRY.csv`** | **SIEMPRE**: añadir caso al prepararlo; cambiar `run_status`, `analysis_status`, fuente, fecha, cobertura de consolidado después de la corrida. Nunca marcar verificado por salidas heredadas. |
| **`cases_controlled_buoyancy/<CASO>/CASE_NOTES.md`** | **SIEMPRE**: pregunta, parentesco, cambio aislado, preflight, prueba, evidencia, métricas, interpretación, resultados, pendientes, conclusión y estado. |
| **`cases_controlled_buoyancy/<CASO>/CASE_VARIANT.md`** | **SIEMPRE** al crear/concluir una variante: diferencia exacta respecto al padre y decisión científica final. No dejar texto desactualizado de «por correr». |
| **`PROJECT_AUDIT_LOG_ES.md` y `PROJECT_AUDIT_LOG_EN.md`** | **SIEMPRE**: la misma entrada cronológica en ambos idiomas, con fecha, hipótesis, archivos, evidencia, hallazgo, costo, decisión, límites y siguiente paso. |
| **`analysis_results/<EXPERIMENTO>/`** | **SIEMPRE** que existan resultados nuevos: `summary.md` y métricas legibles (CSV/TSV) con procedencia, unidades, comparador y script de análisis. |
| **`analysis_results/full_campaign_audit/*.csv` y `summary.md`** | **AL CAMBIAR LA COBERTURA DEL CONSOLIDADO**: regenerar y comprobar **los cinco archivos conjuntamente**. El script actual `analysis_tools/full_campaign_audit.py` está limitado a 26 por sus listas fijas `CASES` y `BC_PAIRS`. No llamar «global completo» a un archivo que omite casos. **Pendiente de integración:** B14, C14 y C11-energy2. B11-energy2 solo al ejecutarse y verificarse. |
| **`VALIDATION_MATRIX_ES.md` / `VALIDATION_MATRIX_EN.md`** | Al cambiar baseline, decisión científica, estado de J0/G1, sensibilidad o conclusión: mantener coherentes ambos. |
| **`CASE_GUIDE_ES.md` + `CASE_GUIDE_INTERACTIVE_ES.html`** | Actualizar si la corrida cambia lo que enseñamos del solver, una condición de frontera, la comparación B/C o la recomendación de baseline. |
| **`OPENFOAM_COMMAND_MANUAL_ES.md` / `OPENFOAM_COMMAND_MANUAL_EN.md`** | Añadir o corregir **procedimientos nuevos reutilizables**, explicando comando y opciones antes de pedir ejecutarlo. |
| **`JMATPRO_OPENFOAM_TRACEABILITY_ES.md`** | Actualizar al incorporar datos reales de JMatPro: composición, propiedades, origen, rango de T y conversiones. No fingir procedencia. |
| **`analysis_tools/` y `.github/agents/openfoam-solidification.agent.md`** | Actualizar cuando cambie el método de cálculo, control automatizado o reglas de auditoría. No permitir que los scripts de análisis y sus reportes contradigan el inventario. |
| **`.gitignore` / archivos trackeados** | Comprobar ausencia de salidas pesadas/temporales y de resultados heredados como prueba falsa; preservar resultados legítimos locales, no borrar físicamente sin autorización. |

**Principio de conservación:** mantener la campaña de 26 como fotografía histórica identificada por alcance. Si se decide transformar `full_campaign_audit/` en el consolidado de todos los casos, extender los analizadores, regenerar **todos** los productos a partir de entradas verificadas y actualizar su fecha/cobertura conjuntamente. Nunca añadir números a mano ni mezclar nuevos resultados con inventarios viejos sin avisarlo.

## C. Ciclo obligatorio para cada nueva corrida (PRE → RUN → MAZAPÁN)

### C1. Antes de ejecutar — PREPARED
- [ ] Decir al usuario **exactamente** qué se cambiará antes de tocar archivos, Git o ejecutar el solver.
- [ ] Identificar hipótesis, objetivo, caso padre, baseline vigente, **única variable** a modificar, predicción y criterio de éxito/fallo.
- [ ] Crear variante limpia: solo `0/`, `constant/`, `system/` y scripts de entrada; **no copiar** tiempos de solución, `logs/`, `postProcessing/` ni `log.*` y tomarlos como una corrida independiente.
- [ ] Comparar entradas contra padre con hash/diff; archivar lista explícita de diferencias activas.
- [ ] Registrar nombre, familia, estado `PREPARED_NOT_RUN`, fecha, pregunta y fuente en `RUN_CASE_REGISTRY.csv` y `CASE_NOTES.md`.
- [ ] Verificar versión **OpenFOAM Foundation v14**; solvers realmente activos, `foamMultiRun`, control PIMPLE global/regional, malla/regiones, campos, unidades y BC.
- [ ] Confirmar `deltaT`, `endTime`, write intervals, output de sonda, perfiles y `functionObjects`; comparar valores reales del directorio, no declaraciones.
- [ ] Para casos de tapa impermeable, preparar evidencia por cara `phi` y velocidad normal; `sum(phi)≈0` solo **no basta**.

### C2. Ejecutar — RUNNING/FAILED/RUN_VERIFIED
- [ ] Guardar fecha/hora, comando efectivo, entorno, versión, revisión Git de entradas, ID de ejecución y ubicación del log.
- [ ] Confirmar `blockMesh`, `splitMeshRegions` y `foamMultiRun`; revisar `checkMesh` si corresponde.
- [ ] Confirmar fin: retorno del runner, tiempo objetivo/último paso y ausencia de `FOAM FATAL`, excepciones, killed/segfault; cuando no hay `End` no inventarlo. Clasificar `RUN_VERIFIED` solo con evidencia.
- [ ] Separar claramente resultados **locales** de datos persistidos en GitHub; no llamar «verificado en Git» a lo que solo existe en el PC.
- [ ] Preservar resultados antes de limpieza; **no** `Allclean`, `git push --force`, `git add -f` ni eliminación destructiva por defecto.

### C3. Auditoría numérica y física — ANALYSIS_VERIFIED
- [ ] **PIMPLE/energía:** número efectivo de solves `h_n/e_n`; residuales iniciales/finales de `p_rgh`, `p_rghFinalRes`, contracción interna/externa `R_p_outer`, mesetas vs costo, continuidad local/global/acumulada, Courant por tiempo y timestep.
- [ ] **Termofísica:** T central `T(t)`, dT/dt, puntos térmicos adicionales, mapas T y U, extremos, media de `alphaL`, `alphaL(t)`, `rho`, balance y cambios de fase.
- [ ] **Fronteras/energía:** `phi` por cara y `sum(abs(phi))` de `metalTop`, `Uy` normal, transporte advectivo, `heatFlux` y `energyFlux` en tapa e interfaz metal–molde, energía/entalpía integrada y revisión de signos/unidades.
- [ ] **Perfiles comparables:** y=10/20/30 mm y x=20 mm, verificar puntos, tiempo, T, U, alphaL, vorticidad/flowType si existen. No inventar perfiles faltantes.
- [ ] **Comparación controlada:** padre vs hijo; B vs C equivalentes cuando proceda; RMSE, máximos, tiempo de eventos, mapas/series y costo computacional; registrar si la diferencia es numérica o física.
- [ ] **Validación experimental:** solo con CSV/serie medida accesible, composición y condiciones realmente alineadas; registrar RMSE/MAE, tiempos de nucleación, recalescencia y solidificación con incertidumbre; **recalentamiento por remelting local ≠ recalescencia metalúrgica demostrada**.
- [ ] Justificar cada afirmación con fuente específica; etiquetas `GIT-VERIFIED`, `RUN-VERIFIED`, `ANALYSIS-VERIFIED`, `INTERPRETATION`, `OPEN`.

### C4. Cierre = **MAZAPÁN**
- [ ] Persistir `logs/`, `postProcessing/`, CSV/TSV, resumen por experimento, notas de caso, variantes y decisiones; sincronizar sin sobrescribir datos locales válidos.
- [ ] Actualizar **registro de casos + bitácoras ES/EN** y todas las guías/matrices afectadas.
- [ ] Revisar la lista de casos incluida en `full_campaign_audit.py` y las 5 salidas de `full_campaign_audit/`. Si los nuevos casos no están integrados, declararlo **PENDIENTE DE CONSOLIDACIÓN** con un informe de brecha, no «actualizado».
- [ ] Confirmar estado y cobertura con `python3 analysis_tools/check_run_registry.py`. La opción `--require-consolidated` es una puerta estricta para cuando el objetivo sea tener **todos** los casos verificados dentro de los CSV globales; **hoy falla justificadamente por tres casos**.
- [ ] Auditar `git status`, `git diff`, `git log`, archivos ignorados/rastreados, enlaces y consistencia documentación↔datos. Comprobar readback tras commit/push.
- [ ] Responder al usuario con **qué corrió**, resultados/conclusión, qué archivos se actualizaron, pendientes reales, commit y **qué NO quedó validado**.

## D. Gates científicos del proyecto

1. **Preservar originales:** `doctor_original/`, C11 histórico y casos históricos congelados; nuevos tests en copias controladas. C14 es baseline para nueva validación de modelo rígido.
2. **J0 antes de G1:** composición, JMatPro raw numérico por condiciones CE/S/Mn; `Tliq/Tsol/L/Cp(T)/k(T)/rho(T)/fL(T)`, criterio `rhoRef+beta`, procedencia y chequeo frente a `alpha1e=0.8`.
3. **G1 = equilibrio alineado contra experimento:** no inventar condiciones ni resultados; comparar curva termopar antes de introducir física adicional.
4. **Cinética/recalescencia solo si G1 lo exige:** no editar `solidificationMelting` para obtener artificialmente un pico.
5. **No versiones por reflejo:** una variante nueva responde una pregunta concreta y no reemplaza baseline solo por converger o minimizar un residual.

## E. Comprobación de cobertura (desde la raíz del repositorio)

`python3 analysis_tools/check_run_registry.py`  
Lee el registro, carpetas de casos y CSV de campaña; informa casos omitidos, discrepancias y estados pendientes **sin ejecutar OpenFOAM ni modificar datos**.

`python3 analysis_tools/check_run_registry.py --require-consolidated`  
Hace la misma lectura pero termina con error si cualquier caso `RUN_VERIFIED + ANALYSIS_VERIFIED` carece de fila en `case_metrics.csv`. Es la condición necesaria para declarar que el consolidado incluye todos los casos.

**Importante:** esta comprobación verifica *cobertura administrativa*, no la validez física de una corrida, la calidad del CSV ni que las métricas sean de una ejecución genuinamente distinta.

## F. Obligación para agentes y futuras sesiones

1. Leer primero `RUN_MASTER_PROTOCOL.md`, `RUN_CASE_REGISTRY.csv`, últimos apartados de `PROJECT_AUDIT_LOG_ES.md`, `VALIDATION_MATRIX_ES.md` y notas del caso.
2. Comparar estado actual Git/runner con el último registro, informar brechas y explicar acción propuesta **antes** de ejecutarla.
3. Cualquier cambio de datos → completar C1–C4; si falta evidencia, dejar estado abierto, sin datos fabricados.
4. Al cambiar el procedimiento, mantener este archivo vivo; **no depender de un repositorio `main` externo ni de la memoria de un chat**.

**MAZAPÁN = ejecutar/comprobar + preservar/sincronizar + analizar + decidir + documentar + actualizar inventarios + verificar coherencia.**
