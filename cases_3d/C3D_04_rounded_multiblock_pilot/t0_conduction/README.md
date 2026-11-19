# C3D-04 Caso A — T0 integrado con valores auténticos de C14

**19-11-2026 · Etapa 5/10 · Avance 4/10 = 40 % de hitos operativos.**  
**Estado: `C14_VALUES_PORTED / SOURCE_PARITY_GUARD_CODE_COMMITTED / CI_NOT_CONFIRMED / WSL_NOT_RUN / NO_CFD`.** Se trata de un paquete 3D de **verificación de conducción térmica entre dos sólidos**, no del modelo C14 original de metal líquido con solidificación. Malla de referencia **solo lectura**: `~/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02`.

## Fuente original C14 — NO confundir con OpenFOAM Foundation 14

La referencia única es `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef`. Los materiales originales también están copiados sin modificación en `cases_3d/C3D_02_metal_sand_clean`. La tabla de procedencia, parámetros de fusión, configuraciones y hashes de fuente se conserva en [`C14_PARAMETER_BASELINE.json`](C14_PARAMETER_BASELINE.json). Los valores operativos que reutiliza la **aproximación T0** están en [`T0_INPUTS.json`](T0_INPUTS.json).

| Parámetro C14 | Metal `castIron` | Molde `silica` |
|---|---:|---:|
| Temperatura inicial | **1500 K** | **300 K** |
| Densidad | **6820 kg/m³** | **1500 kg/m³** |
| Calor específico original | **Cp = 827 J/(kg K)** | **Cv = 700 J/(kg K)** |
| Peso molecular | **56 g/mol** | **28 g/mol** |
| Conductividad original | `const`: deriva de `mu Cp/Pr` | **2 W/(m K)** |
| Otros del transporte original | `mu = 5.5e-3 Pa s`; `Pr = 0.14` | `constIsoSolid` |
| Conductividad calculada solo a partir de C14 | **32.4892857143 W/(m K)** | 2 W/(m K) |

**NO se cambia C14 para que encaje con T0.** El hierro original tiene `heRhoThermo / hConst / sensibleEnthalpy`, **Cp = 827**, y región `fluid`. El T0 numérico existente utiliza `heSolidThermo / eConst / sensibleInternalEnergy` con región `solid`. Su conversión explícita **`Cv_efectivo = Cp_C14 = 827` es una aproximación para ese ensayo de dos sólidos**, no una medición de Cv ni un modelo C14 físicamente idéntico. Se exige declaración del supuesto y el auditor lo compara directamente con el original. No utilizar la simplificación para resultados de solidificación ni presentación de validación experimental.

### Condiciones térmicas reutilizadas de C14

- Metal exterior `metalTop` y las cinco paredes físicas exteriores **3D** del molde (`moldTop`, `moldExterior`, `moldBottom`, `moldRecessWall`, `moldRecessRoof`): `externalWallHeatFluxTemperature`, **h = 10 W/(m² K)**, ambiente **Ta = 300 K**; emisividad **0.3** hierro, **0.5** arena. Los nombres de paredes 3D corresponden a la geometría C3D-04, no a los nombres bidimensionales `frontAndBack`, `moldLeft` o `moldRight` de C14.
- Contacto `metal_to_mold` ↔ `mold_to_metal`: `coupledTemperature`; coeficiente por capa de metal de **espesor 0.0002 m**, `kappaLayers = 0.1 W/(m K)` y conductancia equivalente **500 W/(m² K)**. Parche `mappedWall` recíproco original 3D: **2496 caras por lado**.
- Tiempo: **`deltaT=0.001 s`**, **`endTime=10 s`**, **`writeInterval=100`** del original C14; `adjustTimeStep=no`.
- PIMPLE de la raíz C14: `nOuterCorrectors=3`, `nNonOrthogonalCorrectors=1`. El valor `nEnergyCorrectors=2` está **escrito en `system/metal/fvSolution` regional C14**; no consta como corrección eficaz del módulo fluid C14. El T0 lo registra como **elección numérica explícita diferente en `system/fvSolution` global**, pendiente de comprobar nativamente; no se afirma equivalencia de comportamiento.

C14 conserva en el baseline separado sus parámetros de solidificación **Tsol=1423 K, Tliq=1473 K, L=228600 J/kg, alpha1e=0.8, relax=0.1, Cu=1e5, q=1e-3, beta=1.13e-4, rhoRef=6820**, así como el solver `fluid+solid`, convección, velocidad y presión. **No se utilizan estos modelos fluidos y de fase en T0.** Serán relevantes para T1, que requerirá otra configuración completa, no un cambio silencioso de T0.

## Un solo paquete verificable (no una orden por pieza)

[Preparador integrado](scripts/prepare_case_a_t0.py) + [orquestador único](run_integrated_milestone.sh) incluyen: lectura de parámetros y fuentes; verificación directa de **27 correspondencias** con archivos ejecutables de C14, más hash SHA-256 de cada fuente; `Mesh OK` previo de padre/hierro/arena y contacto del V4/T02; comparación de cada pared activa nativa contra su BC térmica; control global de PIMPLE + los dos regionales; **10 diccionarios** en memoria; y matriz positiva/negativa [`tests/test_integrated_case_a.py`](tests/test_integrated_case_a.py).

El modo de materialización (**solo cuando se autorice**) verifica Foundation14, copia las mallas a **carpeta temporal**, compara hashes SHA-256 contra la fuente, interpreta los **diez diccionarios con `foamDictionary` nativo**, y solo publica una ruta nueva si todos pasan. No sobrescribe la malla T02 ni llama a `foamMultiRun`, `blockMesh` o `checkMesh`.

Existe también una fórmula de equilibrio de dos sólidos **completamente adiabáticos**, útil como límite analítico abstracto. **No es una meta de conservación de energía para este T0 con C14**, pues en él **sí** hay convección exterior `h=10` y pérdida de energía al ambiente; el balance físico correcto requiere integrar los flujos exteriores e interfaciales del solver, aún pendiente.

## Progreso y siguiente hito

La geometría, calidad, contacto y diagnóstico de las 64 caras extra de la interfaz están cerrados (4/10). Este bloque **5/10** incorpora ahora la configuración numérica, valores conocidos del C14 y trazabilidad; falta confirmar las pruebas integrales en CI y el parse/capacidad Foundation14 en tu WSL para materializar un nuevo T0. La simplificación `Cp→Cv` y la diferencia `fluid vs solid` permanecen **claramente documentadas**. T0 no ha corrido, no se ha cuantificado energía real, no hay convergencia temporal/espacial ni independencia de malla; **0 CFD nuevo**.

No es necesario repetir las auditorías de geometría ni ejecutar ningún comando individual ahora. Cualquier futura ejecución se coordinará como **una sola entrega integral**, de conformidad con el [contrato del caso](../AGENTS.md), el [estado canónico](../../../docs/C3D04_CASE_A_STATUS.json) y el [contrato del proyecto](../../../AGENTS.md).
