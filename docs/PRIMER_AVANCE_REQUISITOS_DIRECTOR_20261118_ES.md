# Primer avance de maestría — requisitos expresos del director y trazabilidad OpenFOAM

**Registro:** 18-11-2026. **Proyecto:** MasterProject / QuickCup, solidificación de hierro hipoeutéctico en arena. **Carácter:** lista obligatoria para la primera presentación; no indica que todas las pruebas estén concluidas. **Prioridad científica:** distinguir resultados CFD verificados del **caso 2D de referencia C14** de experimentos de **malla 3D C3D-02, todavía rechazados**. Los criterios anteriores de los proyectos B/C y C14 no se reemplazan.

## 1. Solicitud del director — compromiso de presentación

El investigador confirmó que el doctor pidió que **en el primer avance** se presenten:

1. **Ecuaciones empleadas**, con nombres, significado físico de los términos, supuestos, modelo numérico y fuentes OpenFOAM.
2. **Condiciones iniciales y condiciones de frontera efectivas**, distinguiendo metal, molde, interfaz, superficie superior y planos cuasi-2D; idealmente indicar unidades y el archivo real de donde sale cada condición.
3. **Valores numéricos relevantes**, en particular **el Courant máximo realmente alcanzado**, su evolución, `deltaT`, correctores PIMPLE, tolerancias y cifras del modelo térmico y de solidificación.
4. **Análisis de sensibilidad del coeficiente de relajación del cambio de fase**: `phaseChangeSource.relax` en `constant/metal/fvModels`. No confundirlo con `relaxationFactors` del solver ni con `maxCo`.

No existe una fecha de entrega del primer avance confirmada en los materiales inspeccionados. No inventarla.

## 2. Ecuaciones que se deben exponer y revisar contra la implementación

Las expresiones siguientes son un **esquema físico de las ecuaciones gobernantes** para preparar las diapositivas; **no se presentan como transcripción literal de las ecuaciones discretizadas del código fuente Foundation 14**. Antes de entregar una diapositiva definitiva, verificar cada término, tratamiento de densidad, flotación y fuentes frente a `fluid`, `solid` y `solidificationMeltingSource` nativos y la variante C14 ejecutada.

- **Conservación de masa del metal:** `∂ρ/∂t + ∇·(ρ U) = 0`; con densidad constante, forma incompresible `∇·U=0`, sujeto a las hipótesis reales del solver.
- **Cantidad de movimiento:** forma conceptual `∂(ρU)/∂t + ∇·(ρ U⊗U) = −∇p + ∇·τ + ρg + S_mushy`. Documentar `p_rgh`, flotación y modelo de resistencia de zona pastosa; no inventar la forma del término `S_mushy` sin comprobar `solidificationMeltingSource`.
- **Energía del metal con calor latente:** forma esquemática `∂(ρ h)/∂t + ∇·(ρ U h) = ∇·(k∇T) + S_latente + otros términos del solver`. La liberación/absorción del calor latente está acoplada a la actualización de la fracción líquida; verificar signos y términos del código original.
- **Conducción en el molde sólido:** modelo conceptual `ρ_s c_s ∂T/∂t = ∇·(k_s ∇T)`, usando los valores `Cv`, `rho` y `kappa` que corresponden a `heSolidThermo` de C14.
- **Interfaz metal–molde:** conservar el flujo térmico a ambos lados y contemplar la resistencia de capa del `coupledTemperature`, sin asumir continuidad perfecta de temperaturas cuando hay resistencia de contacto.
- **Superficies exteriores:** describir la condición de transferencia al ambiente `externalWallHeatFluxTemperature` y las contribuciones que efectivamente utiliza la entrada configurada (incluida emisividad, cuando aplique).
- **Modelo de fase:** explicar `Tsol`, `Tliq`, `L`, `alpha1`, `Cu`, `q` y `relax`, indicando qué actualización controla la relajación. No afirmar una ley cinética de recalescencia que `solidificationMeltingSource` no implementa.

**Ecuación numérica del Courant:** presentar la forma dimensional aproximada `Co ≈ |U| Δt / Δx`, o, para flujo volumétrico por caras en un volumen finito, `Co_cell ≈ (Δt/(2 V_cell)) Σ_faces |phi_f|` conforme a la definición concreta que reporta el solver. `Co` es adimensional. Las cifras de `maxCo` de `controlDict` y el **máximo medido** del log tienen significados distintos.

## 3. Datos comprobados directamente del caso CFD de referencia C14

**Fuente:** `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef`, inspección de sus diccionarios versionados en GitHub; las cifras aquí no son resultados nuevos de corrida.

### Control temporal y acoplamiento

| Entrada C14 | Valor literal | Significado para la exposición |
|---|---|---|
| `application` | `foamMultiRun` | Solver multirregión |
| `regionSolvers` | `metal fluid`, `mold solid` | Flujo de metal y conducción en arena |
| `startTime` / `endTime` | 0 / 10 s | Intervalo simulado |
| `deltaT` | 0.001 s | Paso temporal fijo |
| `adjustTimeStep` | `no` | **No hay ajuste automático de Δt por Courant** |
| `maxCo` | **0.25** | Parámetro configurado; **NO es el Courant máximo medido** y no actúa como control de adaptación con `adjustTimeStep no` |
| `maxDeltaT` | 0.1 s | Cota configurada para adaptación, inactiva en el modo fijo |
| `writeControl`/`writeInterval` | `timeStep` / 100 | Registro cada 100 pasos = 0.1 s |
| PIMPLE raíz | `nOuterCorrectors 3`, `nCorrectors 2`, `nNonOrthogonalCorrectors 1` | Número de iteraciones del acoplamiento global |
| `nEnergyCorrectors 2` en metal | Declarado en `system/metal/fvSolution` | **No implica dos correctores efectivos en C14**: los logs previamente auditados indican que el solver regional no utilizó esa clave como un doble paso de energía |
| `pRefPoint` / `pRefValue` | `(0.02 0.04 0.005)` m / `1e5` Pa | Referencia de presión solicitada y verificada para C14 |

### Condiciones iniciales y de frontera literales de C14

| Región / campo | Frontera | Entrada configurada | Interpretación |
|---|---|---|---|
| Metal, temperatura `T` | `internalField` | `1500 K` | Temperatura inicial |
| Arena, temperatura `T` | `internalField` | `300 K` | Temperatura inicial |
| Metal, `U` | `internalField` | `(0 0 0) m/s` | Fluido inicialmente en reposo |
| Metal, `metalTop` | `U: slip` y `p_rgh: fixedFluxPressure` | Literal del caso | Superficie sin penetración normal, con deslizamiento tangencial |
| Metal, `metal_to_mold` | `U: noSlip` y `p_rgh: fixedFluxPressure` | Literal del caso | Interfaz sólido–fluido |
| Metal, `metalTop` | `T: externalWallHeatFluxTemperature` | `h=10 W/(m² K)`, `Ta=300 K`, `emissivity=0.3` | Condición de intercambio con ambiente; no sustituir por `h=50` del ejemplo del doctor |
| Metal, `metal_to_mold` | `T: coupledTemperature` con `wallLayersHeatTransferCoefficient` | `thicknessLayers=(2e-4 m)`, `kappaLayers=(0.1 W/(m K))` | Resistencia interfacial; `h_equiv = k/d = 500 W/(m² K)` para una capa simple |
| Arena, `moldTop`, `moldBottom`, `moldLeft`, `moldRight` | `T: externalWallHeatFluxTemperature` | `h=10 W/(m² K)`, `Ta=300 K`, `emissivity=0.5` | Intercambio exterior del molde |
| Arena, `mold_to_metal` | `T: coupledTemperature` | Acoplamiento multirregión | Contraparte del metal |
| Metal/arena, `frontAndBack` | `empty` | Literal del caso | Caso de referencia cuasi-2D; **no trasladar esta BC a 3D completo** |
| Metal, `p_rgh` | `internalField` | `1e5 Pa` | Presión inicial reducida referenciada |

**Requisito adicional del director ya verificado:** `topFlow` y datos de C14 acreditan `U_y=0` y `phi=0` en 80 caras de `metalTop`, con `sum(abs(phi))=0` en los tiempos reportados hasta 10 s. No deducir impermeabilidad solo de `sum(phi)=0`, pues las contribuciones de signos opuestos pueden cancelarse.

### Propiedades y modelo de fase C14

- Metal `castIron`: `rho = 6820 kg/m³`, `Cp=827 J/(kg K)`, `mu=5.5e-3 Pa s`, `Pr=0.14`; `equationOfState rhoConst`, `thermo hConst`, `transport const`.
- Molde `silica`: `rho=1500 kg/m³`, `Cv=700 J/(kg K)`, `kappa=2 W/(m K)`; `rhoConst`, `eConst`, `constIsoSolid`.
- `phaseChangeSource`: `solidificationMeltingSource`, `Tsol=1423 K`, `Tliq=1473 K`, `L=2.286e5 J/kg`, `alpha1e=0.8`, `beta=1.13e-4 K⁻¹`, `rhoRef=6820 kg/m³`, `Cu=1e5`, `q=1e-3`, **`relax=0.1`**.
- Estos son datos efectivos de **C14**, no una afirmación de que `rho(T)`, `Cp(T)` o `k(T)` ya se hayan incorporado; la mejora con datos dependientes de temperatura/JMatPro debe diferenciarse como **trabajo futuro**.

## 4. Courant, tolerancias y estabilidad — cifra pendiente de medir

**Error que no debe aparecer en el primer avance:** poner `Co_max=0.25` como máximo alcanzado. El diccionario fija `maxCo 0.25`, pero con `adjustTimeStep no` la simulación usa `deltaT=0.001 s` y ese 0.25 **no certifica** el número de Courant observado.

**Evidencia a extraer de los registros REALES** de cada caso CFD verificado: mensajes `Courant Number mean: ... max: ...` (o formato real), máximo global de todos los pasos con tiempo de aparición, promedio relevante, evolución en el tiempo; número de correctores, residuos iniciales/finales `p_rgh`, `U`, `h/e`, continuidad, costo CPU/clock y `deltaT` real. Evitar inventar números: sin salida de log auditada, valor actual **PENDIENTE**.

En C14: tolerancias configuradas `p_rgh 1e-7`, `U 1e-8`, `h 1e-9` y `e` en molde `1e-6`, con `relTol` regionales variables (metal presión 0.01, velocidad/energía 0.05; arena energía 0.05). No presentar estas tolerancias como residuos efectivamente alcanzados.

## 5. Sensibilidad obligatoria del coeficiente de relajación del cambio de fase

**Pregunta:** ¿cómo cambia la evolución de temperatura, fracción líquida, front de solidificación, convergencia, conservación y costo cuando se modifica exclusivamente `phaseChangeSource.relax`?

| Caso | `relax` | Estado comprobado | Otros parámetros |
|---|---:|---|---|
| `C14_topFixedFlux_explicitRef` | **0.10** | `RUN_VERIFIED` y `ANALYSIS_VERIFIED` históricos | Referencia |
| `C16_phaseRelax025_fromC14` | **0.25** | **`PREPARED_NOT_RUN`**; no se ha verificado ejecución CFD | Diseñado para cambiar **únicamente** `constant/metal/fvModels`, conservando Δt fijo y BC de C14 |

**Experimento mínimo ya planificado:** ejecutar C16 en la laptop y comparar C14 vs C16 al mismo tiempo físico (hasta 10 s), sin modificar las fuentes originales, solamente después de la verificación preflight habitual. Documentar versiones de OpenFOAM y checksums/diffs de todas las entradas para asegurar cambio de una sola variable. **No afirmar resultados de sensibilidad antes de ejecutar y auditar C16**.

**Mayor solidez experimental (opcional, aún sin casos fuente creados):** evaluar al menos un valor menor, por ejemplo 0.05, y uno mayor, por ejemplo 0.50, si el objetivo es mostrar tendencia y no solo una diferencia entre dos casos. Estos **son valores propuestos, no experimentos realizados ni instrucciones de alterar C14/C16 sin control**.

**Variables y gráficos exigibles:**
1. Temperatura `T(t)` en puntos equivalentes de C14 y C16; `ΔT(t)=T_variant−T_C14`; temperatura a 10 s y tiempo de cruce de `Tliq/Tsol` cuando ocurra en el intervalo observado.
2. `phaseChangeSource:alpha1(t)` (fracción líquida), `Δalpha1(t)`, valores mínimos y oscilaciones; perfiles espaciales y posición/tiempo del frente cuando estén disponibles.
3. `U`, máxima velocidad y presión/continuidad; revisar `phi` en `metalTop` para asegurar tapa impermeable.
4. `Courant mean/max` y **máximo observado** (no `maxCo` nominal); residuos por campo, correctores, estabilidad temporal y costo computacional.
5. Fuente de calor latente, indicadores de balance energético y consistencia termodinámica donde las salidas realmente estén disponibles; no asumir que una recuperación de temperatura es recalescencia por nucleación. Separar remelting del fenómeno metalúrgico.

**Interpretación científica:** la relajación `phaseChangeSource.relax` gobierna la actualización de fase del modelo entalpía-porosidad; **no es** la relajación de `U`, `h` o `p_rgh` definida por `relaxationFactors` del `fvSolution` raíz, cuyos valores C14 están en 1.0. La comparación controlada C16 es una sensibilidad de la respuesta del modelo de fase, **no** simplemente un ajuste cosmético de convergencia.

## 6. Estructura sugerida para el primer avance

1. Pregunta de investigación, QuickCup, hipótesis y ámbito 2D→3D.
2. Geometría y condiciones físicas; distinguir ejemplo cuasi-2D del doctor, C14 2D verificado y QuickCup 3D todavía sin malla aprobada.
3. Ecuaciones gobernantes (masa, momento, energía metal/arena, fuente de fase y acoplamiento térmico) con hipótesis/limitaciones.
4. Condiciones iniciales y de frontera con tabla, esquema y referencias a archivos reales C14.
5. Propiedades y constantes del modelo, especialmente `Tsol`, `Tliq`, `L`, `Cu`, `q` y `relax`.
6. Solución numérica: malla, `deltaT`, PIMPLE, tolerancias; **Courant medido** y residuos/continuidad.
7. Comparación cuantitativa de sensibilidad `C14(relax=0.10)` vs `C16(relax=0.25)` **solo cuando C16 haya corrido y se analicen resultados reales**.
8. Avance 3D: STL original y v2, ablación fallida, estudio de `blockMesh` conformante del doctor como referencia de construcción, limitaciones y próximos experimentos.
9. Conclusiones, límites físicos y próximos pasos; no afirmar CFD 3D.

## 7. Checklist de aceptación documental

- [x] Solicitud del director registrada textualmente en categorías.
- [x] Valores configurados de C14 y C16 extraídos de los diccionarios versionados.
- [x] Separación documentada entre `maxCo=0.25` nominal, `Co_max` realmente observado y `relax=0.1/0.25`.
- [x] BC/IC reales y unidades de C14 documentadas.
- [ ] Verificación término por término de las ecuaciones discretizadas del solver Foundation 14 y su cita académica.
- [ ] Extracción verificable del máximo Courant observado del log C14 (con fecha/tiempo simulado y evolución).
- [ ] Ejecución y auditoría de C16 con `relax=0.25`; curvas comparativas y conclusiones estadísticas/físicas.
- [ ] Tabla de indicadores de residuos, continuidad, costo, energía y convergencia con fuentes de datos explícitas.
- [ ] Preparación del primer avance con gráfica, referencias bibliográficas y notas de alcance; fecha de presentación aún no especificada.
- [ ] Mallado C3D-02 aceptado — **no es prerrequisito para exponer los resultados C14 verificados**, pero no presentarlo como logrado.

## Fuentes primarias del repositorio

- [C14 / CASE_NOTES](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/CASE_NOTES.md)
- [C14 / system/controlDict](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/controlDict)
- [C14 / system/fvSolution raíz](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/fvSolution)
- [C14 / system/metal/fvSolution](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/system/metal/fvSolution)
- [C14 / 0/metal/T](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/0/metal/T)
- [C14 / 0/mold/T](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/0/mold/T)
- [C14 / 0/metal/U](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/0/metal/U)
- [C14 / 0/metal/p_rgh](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/0/metal/p_rgh)
- [C14 / constant/metal/fvModels](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant/metal/fvModels)
- [C14 / materiales metal](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant/metal/materials/castIron)
- [C14 / materiales arena](../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant/mold/materials/silica)
- [C16 / CASE_NOTES](../cases_controlled_buoyancy/C16_phaseRelax025_fromC14/CASE_NOTES.md)
- [C16 / phaseChangeSource.relax=0.25](../cases_controlled_buoyancy/C16_phaseRelax025_fromC14/constant/metal/fvModels)
- [3D / resultado de ablación](C3D_02_ABLACION_STL_V2_20261118_ES.md)
- [3D / referencia del doctor](C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md)
