> **ADENDA 20-11-2026 | GRANADA_C3D05_NATIVE_ENERGY_20261120:** el posprocesamiento de T0 usa `foamPostProcess` F14 por región, `volAverage(T)`, energías sensibles `ρCvV⟨T⟩` y discrepancia global/intercambio efectivo bajo el comando único `--solve`; no hay aún campos nativos ni continuidad de flujo directa por interfaz. **G3/G4 ABIERTOS, Caso B etapa 3/7, 2/7 hitos=29% técnico**. [Reporte](granada/C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md).

> **ADENDA 19-11-2026 | GRANADA_C3D05_C14_NUMERIC_SHK_20261119:** para evitar múltiples preflights se agregó paquete Granada C14 numérico de fuente SHA con un comando que prepara la copia de la malla aceptada, valida 10 diccionarios, calcula referencia matemática de conservación y (solamente con `--solve`) ejecuta 100 pasos aislados, auditando log. **No se ha ejecutado en WSL**: el ejemplo de C14 no se confunde con propiedades experimentales. Caso B **etapa 3/7, 2/7 hitos (29% técnico)**. [Paquete y límites](granada/C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md).

> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119 — ADENDA DE TRABAJO INTEGRAL:** ya no se considera un preflight aislado como una entrega completa. Caso B etapa 3/7, 2/7 hitos técnicos = 29%; T0 aún sin propiedades trazables ni materialización/solver. Al cerrar propiedades se debe preparar un solo bloque de configuración, comprobación y corrida local controlada, sin repetir auditorías STEP/HEX8 aceptadas. [Política](POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md), [estado](PROJECT_STAGE_STATUS.json). La descripción técnica previa de T0 se mantiene sin alterar.

# C3D-05 Caso B — Etapa T0: conducción transitoria metal–arena, estructura Foundation 14 preparada

**Fecha:** 19 de noviembre de 2026. **Estado al crear:** archivos reales de configuración T0, plantillas y verificadores publicados en el repositorio; **NO se ha ejecutado el nuevo preflight en WSL**, **no se ha materializado ningún caso térmico con datos físicos**, **NO CFD**.

## 1. Entrada ya validada y protección de evidencia

La malla geométrica de entrada es **`~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`**, con 270,788 HEX8 (92,200 metal, 178,588 arena), tres `Mesh OK` nativos OpenFOAM 14 y contacto metal↔arena recíproco `mappedWall` de 12,636 caras y 6,349.07567760369 mm² por lado. Procedencia STEP SHA256 y geometría pasaron la auditoría independiente `OVERALL_GEOMETRY_TOPOLOGY: PASSED`. Los 1,826 rostros con no ortogonalidad >70° son internos; 226 caras metal a 1 salto del contacto, 235 arena a 1 salto del contacto y 398 arena a 1 salto de pared externa. **Los saltos son topológicos, NO distancias en mm.**

El futuro cálculo se alojará exclusivamente en **`~/OpenFOAM/C3D05_T0_CONDUCTION_01`**, carpeta separada que nunca se sobrescribe. Las mallas regionales se **copiarán** (sin symlinks) solo cuando estén aprobados los parámetros y sus fuentes. Ni la geometría original, ni sus diccionarios, ni sus reportes existentes se modifican.

## 2. Modelo T0 definido — NO equivale a solidificación

T0 resuelve solo la **conducción transitoria** en dos **sólidos estacionarios** unidos idealmente, sin movimiento ni solidificación:

\[
\rho_i C_{v,i}\,\frac{\partial T_i}{\partial t}
= \nabla\!\cdot\left(k_i\nabla T_i\right),\qquad i\in\{\mathrm{metal},\mathrm{arena}\}.
\]

En la interfaz, como **hipótesis de verificación numérica** se exige continuidad de temperatura y de flujo normal (contacto perfecto, sin resistencia), implementada por `coupledTemperature` en `metal_to_mold` y `mold_to_metal` sobre `mappedWall` recíprocos. En `metalTop` y `moldOuterUnclassified` se ha elegido **`zeroGradient` (adiabático)** para probar un sistema térmico cerrado y balance energético. **No refleja** la transferencia física del QuickCup al ambiente: eso debe sustituirse posteriormente por una condición justificada (convección/radiación/resistencia/interfaz real).

T0 no incorpora `alpha`, latente, eutéctico, austenita primaria/proeutéctica, evolución de fracción sólida, recalescencia, flujo del hierro, `enthalpyPorosity` ni convección. Es únicamente la etapa de **verificación de acoplamiento y conservación**. No se atribuye al material el comportamiento de un hierro líquido.

## 3. Esquema exacto de archivos creados

Nueva ruta de fuente: `cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/`.

| Archivo versionado | Función |
|---|---|
| `T0_INPUTS.json` | Datos pendientes y sus fuentes; todos los valores físicos aparecen `null`, no inventados |
| `templates/constant/{metal,mold}/physicalProperties.tpl` | `heSolidThermo`, `constIsoSolid`, `rhoConst`, `eConst`, `sensibleInternalEnergy`, `Cv` |
| `templates/0/{metal,mold}/T.tpl` | Temperaturas iniciales distintas; `coupledTemperature` recíproca y exterior adiabático |
| `templates/system/{metal,mold}/fvSchemes.tpl` | Euler, Gauss linear, `Gauss linear corrected`, `snGrad corrected`, sin convección |
| `templates/system/{metal,mold}/fvSolution.tpl` | Solver de `e` GAMG; 2 correctores no ortogonales **propuestos, no validados** |
| `templates/system/controlDict.tpl` | `foamMultiRun`, `regionSolvers { metal solid; mold solid; }`, tiempo explícito y salidas |
| `scripts/prepare_t0.py` | Valida TODAS las propiedades, unidades, procedencia, campos T y parámetros temporales; luego copia malla a carpeta nueva y renderiza diccionarios |
| `scripts/run_t0_preflight.sh` | **Una sola instrucción**: pruebas, revisión geométrica nativa preservada, entorno Foundation 14, validación de entradas **SIN crear caso ni CFD** |
| `scripts/run_t0_materialize.sh` | **Etapa posterior**, copia y crea diccionarios solo si todas las entradas y evidencias se completaron; `foamDictionary` para parseo, nunca ejecuta solver |
| `tests/test_prepare_t0.py` | Pruebas aisladas de bloqueo de entradas faltantes, fuentes, parches, sustituciones y esquema (los números de fixtures son solo sintéticos) |

**Importante:** `Cv` en `eConst` no puede sustituirse sin explicación por el `cp(T)` de la tesis. Para un material modelado como incompresible, `Cp\approx Cv` podría constituir una hipótesis documentada, pero **no se autoriza asumirlo en silencio**.

### Datos requeridos antes de materializar

Cada región necesita `rho_kg_m3`, `Cv_J_kg_K`, `kappa_W_m_K`, `molWeight_g_mol` de convención del modelo, `T_initial_K` y una **fuente explícita por campo**. Tiempo: `deltaT_s`, `endTime_s`, `writeEverySteps` y justificación de su elección. Las temperaturas iniciales deben diferir para activar intercambio de energía entre regiones. El campo `molWeight` del `pureMixture` no representa por sí solo la composición real de la arena/aleación; documentar la convención.

Faltan datos documentados de ambas regiones en la fuente de parámetros: el preflight imprimirá `T0_BLOCKED_MISSING_PHYSICAL_INPUTS_OR_EVIDENCE` y **NO habrá archivo ejecutable ni intento de solver**. Pueden usarse propiedades provisionales solo en un experimento identificado inequívocamente como *verificación numérica no física*, con procedencia y justificación; **no presentar dichos resultados como datos experimentales o validación de tesis**.

## 4. Compatibilidad verificada con documentación oficial — NO probada aún en WSL

Se contrastó la arquitectura contra **OpenFOAM Foundation 14**, no contra distribuciones OpenCFD:

- `foamMultiRun` y su diccionario `regionSolvers`: https://cpp.openfoam.org/v14/foamMultiRun_8C.html
- BC Foundation v14 `coupledTemperature`: https://doc.cfd.direct/openfoam/user-guide-v14/thermal-boundary-conditions
- `0/metal/T` ejemplo real: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/0/metal/T
- `constant/metal/physicalProperties` exacto: https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiRegion/CHT/heatedDuct/constant/metal/physicalProperties
- `system/metal/fvSchemes`, `fvSolution`, `controlDict` oficiales en `tutorials/multiRegion/CHT/heatedDuct/` de OpenFOAM-14.

El archivo `fvSolution` propone `nNonOrthogonalCorrectors 2`, frente a **0 en el ejemplo oficial**. Es una opción numérica *por evaluar* a la luz de ángulos máximos de 76.8°, no garantía de estabilidad. Deberán compararse opciones y errores de balance/flujo. `deltaT` está sin rellenar: nadie ha medido estabilidad o errores temporales T0.

## 5. Primera instrucción WSL — solo preflight

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_preflight.sh
```

La orden revisa las regresiones y el caso HEX8 de origen, comprueba que Foundation 14 y `foamMultiRun`/`foamDictionary` estén disponibles y enumera los parámetros no establecidos. **No genera ni modifica mallas, no ejecuta `foamMultiRun`, no crea el caso T0 si los parámetros siguen nulos**.

**Criterios de la próxima etapa:** completar la matriz de parámetros, seleccionar hipótesis de contacto ideal versus resistencia finita y exterior, verificar diccionarios nativos, realizar una simulación sintética explícitamente autorizada, medir (E(t)), flujos integrados `metal↔mold`, gradientes y estabilidad; después solidificación T1, incertidumbres y malla/tiempo. No asignar la etiqueta `CFD_VERIFIED` por un preflight.

**Estado canónico:** `T0_MODEL_AND_GUARDS_COMMITTED`, `T0_WSL_PREFLIGHT_NOT_RUN`, `MATERIAL_DATA_MISSING`, `T0_THERMAL_CASE_NOT_MATERIALIZED`, `CFD_NOT_RUN`.
