# C3D-04 Caso A — T0 integrado con valores auténticos de C14


## 20-11-2026 — Corrección del error REAL de inicialización F14: h uniform

La CI nativa de [PR #57](https://github.com/michels-lab/MasterProject/pull/57) logró ejecutar `blockMesh` para ambas regiones y `foamDictionary` para los 10 diccionarios, pero `foamMultiRun` falló al inicializar `metalTop` con: **“expected keyword 'uniform' or 'nonuniform', found constant”**. Se comprobó el contrato real en la fuente Foundation14 de `externalTemperatureFvPatchScalarField.H`: **`Ta` es `Function1` y usa `Ta constant 300;`; `h` es `FunctionalDimensionedField` y usa `h uniform 10;`**. Referencia: https://cpp.openfoam.org/v14/externalTemperatureFvPatchScalarField_8H_source.html. El parser `foamDictionary` no detecta necesariamente incompatibilidades de tipos en tiempo de inicialización.

Se corrigió **el generador T0 de producción**, no únicamente el banco sintético: ahora todas las paredes externas de metal y molde utilizan `h uniform`. Se conservan exactamente h=10 W/(m² K), Ta=300 K, emisividades y contacto C14, los diez diccionarios, geometría, y los originales archivados. La regresión integrada rechaza `h constant` y conserva `Ta constant`. **La prueba nativa posterior todavía debe aprobarse** y el ensayo sintético no cierra el preflight WSL V4/T02. Etapa 6/10, 5/10=50%, sin CFD nativo del Caso A sobre malla real.

## 20-11-2026 — Puerta de inicialización F14 con solver REAL (malla sintética, NO V4/T02)

[PR #57](https://github.com/michels-lab/MasterProject/pull/57) añade a la **misma instalación Foundation14** de la CI una comprobación posterior al análisis nativo de los diez diccionarios T0. En una carpeta descartable del corredor, el script native_f14_coupled_runtime_smoke.py crea por blockMesh **dos cubos 3D independientes de una celda** con un único mappedWall recíproco, cinco paredes externas del molde y metalTop. Inserta **los diez archivos generados por el mismo productor de Caso A** y realiza dos pasos térmicos a deltaT=0.001 s con foamMultiRun para comprobar carga del solver real, externalTemperature, coupledTemperature, termofísica y escritura nativa de T en ambas regiones. En la copia sintética y solo en ella reduce endTime a 0.002 s y writeInterval a 1.

Los resultados se guardan en el artifact del workflow con logs de blockMesh de las dos regiones, diez logs de foamDictionary, el log de foamMultiRun, los campos escritos y C3D04_A_SYNTHETIC_NATIVE_REPORT.json con sus SHA-256. Un log fallido preserva evidencia y **NO autoriza** declarar prueba completa; hasta que CI termine no debe llamarse PASS.

**Evidencia que esta puerta NO proporciona**: no es la malla V4/T02 de 21,312 celdas, no reproduce sus 2,496 pares mappedWall, no prueba estabilidad ante >70 grados de no ortogonalidad, no mide balance de energía sobre las superficies reales y no simula enfriamiento experimental ni solidificación. **Etapa 6/10, avance operativo 5/10=50 %, sin CFD real del Caso A.** El único siguiente trabajo nativo sobre V4/T02 continúa siendo el hito 06 integrado en WSL; está prohibido confundir un ensayo en cubos con ese gate.



> **20-11-2026 | Corrección preventiva de autotest F14 (hito 06 abierto, 5/10 = 50 %).** Se detectó una aserción obsoleta en `scripts/prepare_case_a_t0.py --self-test` que aún exigía `externalWallHeatFluxTemperature` después de adoptar `externalTemperature` en Foundation14. Corregida a cobertura por cantidad de parches exteriores (metal/arena), rechazo de la BC heredada y ejecución obligatoria del autotest desde la suite integrada. **El cambio no modifica diccionarios productivos, geometría V4/T02 ni ejecuta CFD**; la CI del PR y el preflight nativo real deben verificarse por separado.


## Resiliencia de volumen nativo (etapa 6/10, 50 %) — 20-11-2026

El preflight original exigía `PILOT_MESH_REPORT.tsv` en V4/T02, aunque no está garantizado que todos los casos preservados contengan ese resumen auxiliar. **La falta del TSV no debe bloquear el cálculo real ni justificar pedir otra microprueba.** `read_preserved_mesh_volumes()` conserva su validación estricta si existe el archivo; si está ausente, calcula `V` directamente a partir de `polyMesh/points`, `faces` y la cuenta real de caras internas `neighbour`, integrando el **volumen orientado de las caras de frontera** (`sum dot(a, cross(b,c))/6` con triangulación de polígonos). Rechaza volúmenes nulos, negativos, NaN y geometría desorientada; es volumen de **malla nativa**, no STL o STEP.

Se agregaron regresiones para dos cubos cerrados de volumen conocido, un ejemplo de caras invertidas que debe rechazarse y la ausencia deliberada del TSV. Continúa vigente la puerta previa `checkMesh` padre/metal/molde y contacto de V4/T02 guardados. Este fallback evita la dependencia de un reporte opcional, pero **no prueba por sí solo la capacidad de arrancar `foamMultiRun` ni la validez del Cp→Cv efectivo del metal**. No se modifica V4/T02.

## GRANADA NATIVA 20NOV26 | ETAPA 6/10 · AVANCE 5/10 = 50 %

**Estado VIGENTE al 20 de noviembre de 2026 (las notas posteriores de etapa 5/40 % documentan el estado histórico antes del cierre).** [**CI Foundation14 nativo: 10/10 archivos térmicos interpretados con `foamDictionary`**](../../../reports/case-a-t0/CI_NATIVE_F14_20261120.json), junto a **15/15 pruebas de integración**, contrato de entrega y auditoría científica completos. [PR #53 fusionada](https://github.com/michels-lab/MasterProject/pull/53), commit `718bb48167d58218b344cad6eb169fef198b8dbf`. Los diez archivos provienen de C14 original y la malla 3D V4/T02 no estuvo en el corredor CI, por lo que este resultado **cierra únicamente el hito 05 de diseño/preparación de diccionarios**, no el preflight del caso real ni la ejecución del solver.

**Hito activo 06/10**: ejecutar solo cuando proceda **una única entrega integrada sobre V4/T02 original en WSL**, que incluye QA de estado, cotejo de entradas C14, comprobaciones de malla/contacto guardadas, áreas térmicas reales, creación atómica en carpeta distinta, control SHA de mallas copiadas y 10 lecturas de `foamDictionary` nativo. El runner `run_integrated_milestone.sh --materialize` carga OpenFOAM 14 una sola vez y en Ubuntu 26.04 exporta `HWLOC_COMPONENTS=-gl` antes de `/opt/openfoam14/etc/bashrc` para evitar bloqueo conocido de `pvdataserver`. **No invoca `foamMultiRun`: no se ha hecho CFD ni se ha probado la estabilidad de las condiciones de frontera al resolver**.

Estado canónico actualizado: [`docs/C3D04_CASE_A_STATUS.json`](../../../docs/C3D04_CASE_A_STATUS.json) y [registro de hitos](../../../docs/C3D04_CASE_A_MILESTONE_TRACKER.csv).


## Granada de integridad del preflight — 20 de noviembre de 2026

**Etapa Caso A 5/10 · avance de hitos 4/10 = 40%. No CFD.**

La auditoría CI del paquete integral detectó un defecto de contrato: si las entradas T0 eran inválidas, `--preflight` devolvía **código 0**. Ahora **devuelve código 3**, antes de revisar la malla nativa y sin publicar nada. Los test negativos lo verifican; el preflight con parámetros rastreados a C14 conserva código 0 y no toca V4/T02.

La misma CI expuso un defecto de integración en la prueba de **materialización atómica**: el test de malla simulada intentaba volver a leer `polyMesh/points` ficticio al recalcular por segunda vez las áreas térmicas. El flujo se corrigió en su **causa**: `thermal_network_budget` calcula áreas de paredes y contacto **una sola vez** sobre la fuente real como parte del preflight, deja la evidencia en `native_case_gate + c14_source_parity + initial_C14_BC_thermal_budget` y la materialización atómica **reutiliza esa misma evidencia**. No se vuelven a recorrer polígonos al publicar la carpeta. Se rechaza directamente un llamado de materialización que no lleve evidencia de presupuesto térmico validada. Así, pruebas de éxito y de fallo usan datos sintéticos coherentes, sin simular geometría nativa inexistente.

No se incrementa el avance por estos arreglos: **la comprobación estática en CI no sustituye a `foamDictionary` real, el arranque de `foamMultiRun`, conservación de energía ni validación experimental**. La malla T02 y el C14 original siguen inmutables. Esta modificación se entrega como una única revisión/PR integral, en lugar de pedir múltiples órdenes WSL al investigador.


**19-11-2026 · Etapa 5/10 · Avance 4/10 = 40 % de hitos operativos.**  
**Estado: `C14_VALUES_PORTED / SOURCE_PARITY_GUARD_CODE_COMMITTED / CI_NOT_CONFIRMED / WSL_NOT_RUN / NO_CFD`.** Se trata de un paquete 3D de **verificación de conducción térmica entre dos sólidos**, no del modelo C14 original de metal líquido con solidificación. Malla de referencia **solo lectura**: `~/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02`.

## Operación Granada: compatibilidad Foundation14, auditoría térmica e integridad C14

**Corrección preventiva validada contra documentación oficial Foundation 14:** el `0/T` de C14 histórico utilizaba `externalWallHeatFluxTemperature`, sintaxis heredada que **no se debe copiar tal cual a Foundation 14**. El nuevo generador de C3D-04 conserva los valores **h=10, Ta=300 K y emisividad hierro 0.3/arena 0.5**, pero utiliza la condición Foundation14 **`externalTemperature`** con `h uniform 10;`, `Ta constant 300;`, `emissivity 0.3/0.5;` y `value $internalField;` para las seis paredes físicas no vacías de V4/T02. Se elimina de la configuración generada el modo legado `mode coefficient` y `kappaMethod solidThermo`. El contacto `coupledTemperature` con el modelo `wallLayersHeatTransferCoefficient` de 0.2 mm y 0.1 W/(m K) permanece correcto para F14. Fuente oficial: https://doc.cfd.direct/openfoam/user-guide-v14/thermal-boundary-conditions.

**Protección C14 estricta:** el preflight coteja cada archivo ejecutable original C14 con su **Git blob SHA-1** guardado en `C14_PARAMETER_BASELINE.json`, además de cotejar por contenido cada parámetro numérico con `T0_INPUTS.json`. Si cambia cualquiera de los archivos originales, el paquete se **detiene**: no interpreta como verificada una simulación alterada ni reescribe C14. La suite única de regresión incluye perturbación positiva/negativa de parámetros y modificación de bytes del C14 para probar el rechazo.

**Nuevo presupuesto térmico de arranque sobre la geometría nativa 3D:** `thermal_network_budget()` reutiliza el lector previamente aprobado `measure_interface_area.patch_area`, lee `constant/{metal,mold}/polyMesh` de V4/T02 **sin escribirlo**, suma las áreas reales de `metalTop` y de las cinco paredes externas del molde, verifica por separado las 2,496 caras y áreas recíprocas de ambos lados del contacto, y estima escalas iniciales:

```text
C_metal = rho_metal * Cv_eff_metal * V_metal            [J/K]
C_mold  = rho_mold * Cv_mold * V_mold                  [J/K]
G_contact = (kappa_layer/thickness_layer) * A_contact  [W/K]
G_exterior = h_C14 * A_exterior                       [W/K]
P_contact,inicial = G_contact * (1500 - 300)           [W]
P_conv_metal,inicial = G_exterior_metal * (1500 - 300) [W]
P_rad,inicial ~ emissivity * sigma * A * (T^4 - Ta^4)  [W]
```

La expresión del contacto **no representa por sí sola la resistencia efectiva de celdas e interfaz**. Se trata de un **estimador inicial con temperaturas uniformes de los dos sólidos y la geometría mapeada**, no de una solución 3D, potencia medida en OpenFOAM ni un balance de energía cerrado. La malla de origen, las propiedades originales y los casos anteriores no son modificados. La batería de tests incluye áreas recíprocas consistentes y un caso de áreas de contacto incompatibles que debe fallar.

**Estado al cierre de esta implementación:** `CODE_COMMITTED`, pruebas fuente preparadas para CI, **sin confirmación de ejecución exitosa del CI ni de Foundation14 nativo en WSL**, ni una corrida CFD. Continúa **etapa 5/10 y avance 40 % de hitos**. La validez del esquema numérico, las variables térmicas dependientes de temperatura, la solidificación real y la independencia de malla están pendientes. No repetir auditorías de geometría ya resueltas.

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
