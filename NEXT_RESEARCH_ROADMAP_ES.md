> **2026-11-20 | C3D-05/B REAL WSL T0 + AUDITOR RECOVERY (3/7, 2/7=29 % técnico):** investigador aportó consola Foundation14 real de 270,788 HEX8 con `Time = 0.1s`, DICPCG/e metal+molde y `End`; el antiguo auditor produjo un falso negativo `exit=6` por sufijo de segundos y banner informativo `FOAM_SIGFPE`. Parche y reauditoría SHA no destructiva integrados para recuperar log original, completar volAverage/energía/q bilateral y expediente **sin repetir solver**. Aún faltan log SHA íntegro, métricas WSL y validación JMatPro/QuickCup. [Informe técnico](docs/granada/C3D05_WSL_T0_270788_AUDITOR_RECOVERY_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_SOLVER_MAPPEDWALL_20261120 — ACTUALIZACIÓN C3D05/B:** F14 auténtico sí hizo una **corrida transitoria de 100 pasos** `foamMultiRun` (dt=0.001s, t=0.1s) y postprocesó **dos sólidos sintéticos** contiguos `mappedWall`/`coupledTemperature`, con **10 diccionarios de T0 sin modificar** y valores numéricos archivados C14. Metal `1500→1499.2 K`, molde `300→304.29709 K`, seis estados, discrepancia de energía `max|ΔE|/Qref = 2.63001153e-7` [CI PASS #44841034109](https://github.com/michels-lab/MasterProject/actions/runs/44841034109). Esto demuestra **software/condición de acoplamiento sobre 2 celdas**, no validación experimental ni simulación aceptada de **270788 HEX8/12636 caras** en WSL. Sin JMatPro/QuickCup ni sensibilidad; **G3/G4 ABIERTOS, Caso B etapa 3/7, 2/7=29% hitos técnicos, NO tesis**. [Informe](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D05_F14_CHT_DOS_SOLIDOS_SMOKE_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_POSTPROCESS_REAL_20261120 — MASTERPROJECT/CASO B:** Foundation14 real verificó **10/10 diccionarios** `fvSolution`/energía y postprocesamiento `volFieldValue` de metal/mold en 2 mallas de 1 celda (T=400/300 K) [CI nativa PASS #44830571389](https://github.com/michels-lab/MasterProject/actions/runs/44830571389). Se encontró/corrigió la falla de objeto `region0` (exigir `region metal;`/`region mold;`); ahora energía exige `t=0` y valores iniciales, y el ejecutor único `--solve` produce expediente `T0_GRANADA_EVIDENCE_SUMMARY.json` de entradas+log+energía+12,636 pares q, protegido por SHA. [53 pruebas integradas PASS](https://github.com/michels-lab/MasterProject/actions/runs/44830345144). **CI ≠ CFD en malla real; WSL solver NO ejecutado, datos/JMatPro/QuickCup pendientes. Etapa B 3/7, 2/7=29% hitos técnicos, NO tesis**. [Informe](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D05_F14_POSTPROCESS_SMOKE_Y_EVIDENCIA_UNICA_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_REAL_COMPILER_20261120 — CASO B:** compilación nativa C++ OpenFOAM14 F14 con `wmake`, bibliotecas `ldd` y arranque `-help` **PASS** [CI 44828749324](https://github.com/michels-lab/MasterProject/actions/runs/44828749324). CSV duales y análisis de 12,636 pares se publican atómicamente, pruebas sintéticas [PASS](https://github.com/michels-lab/MasterProject/actions/runs/44828766415). **NO solver en WSL ni validación CFD/QuickCup; etapa 3/7, 2/7 hitos=29% técnico, NO tesis.** [Informe](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D05_F14_WMAKE_REAL_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_PATCH_Q_12636_20261120 — CASO B / GRANADA FLUJO DIRECTO:** se añadió un extractor C++ `c3d05PatchFlux` basado en `solidThermophysicalTransportModel::q()` Foundation14, cargando SIMULTÁNEAMENTE metal y molde para `mappedWall/coupledTemperature`. Lee `q_n=-k snGrad(T)` nativo por **12,636 caras de cada lado**, centros/áreas/normales, y empareja geométricamente sin asumir índice compartido; cuantifica balance neto y `Σ |q_m A_m + q_a A_a|` para revelar errores locales que se cancelan globalmente. Controles anti-NaN, tiempo, geometría, SHA y no-sobrescritura; ejecutor `run_c14_numerical_granada.sh --solve` integra compilación aislada `wmake`, extracción bilateral y postprocesamiento tras energía volumétrica. **CÓDIGO IMPLEMENTADO, C++ NO COMPILADO NI CORRIDO EN WSL; resultados CFD/flujo/validación NO EXISTEN.** Caso B **ETAPA 3/7, 2/7 hitos=29% TÉCNICO, NO TESIS**, G3/G4 abiertos. [Reporte](docs/granada/C3D05_T0_FLUJO_INTERFAZ_12636_CARAS_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_NATIVE_ENERGY_20261120 — CASO B GRANADA T0:** `foamPostProcess` Foundation14 por región con `volFieldValue(cellZone all,volAverage(T))` incorporado al mismo `run_c14_numerical_granada.sh --solve`. Usa campos T realmente escritos, ρCv y volúmenes del checkMesh aceptado para cuantificar E metal/molde, desviación de energía total e intercambio efectivo temporal, con controles SHA del log, tiempos, NaN y volumen. Un solver ya finalizado puede reutilizarse SIN rerun. **CI Python/Bash aprobada; NO corrida WSL ni energía validada**; tasas de energía NO son flujo directo por caras de interfaz. **Etapa B 3/7, 2/7 hitos=29% técnico, NO tesis/CFD**; G3/G4 abiertos. [Informe científico](docs/granada/C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md).

> **19-11-2026 | GRANADA_C3D05_C14_NUMERIC_SHK_20261119 — OP GRANADA CASO B, CÓDIGO OPERATIVO:** paquete integrado C14→T0 de referencia NUMÉRICA (fuentes C14 SHA-256, hierro ρ=6820, Cp=827 aproximado explícitamente como Cv, k=Cp·μ/Pr, sílice ρ=1500/Cv=700/k=2, T=1500/300 K); 100 pasos de 0.001 s, caso independiente y comando único opcional `--solve` en WSL. Incluye generación idempotente, revisión nativa de 10 diccionarios, objetivo teórico de energía calculado desde volúmenes reales `checkMesh` y auditoría del log de `foamMultiRun` que NO confunde ejecución con conservación. Corregido también el fallo histórico de registro científico: los `THREE_D_*` se resuelven como carpetas bajo `cases_3d`, sin ascender estados a CFD; regresión en CI. **ETAPA B 3/7, 2/7 hitos = 29 % técnico, NO tesis.** Código publicado y pruebas estáticas; SIN corrida WSL, SIN validación JMatPro/QuickCup, SIN cierre G3/G4. CAD/C14/malla HEX8 intactos. [Informe completo](docs/granada/C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md).

> **19-11-2026 — C3D05/B / GRANADA: fvSolution DE C14, NO PARÁMETROS INVENTADOS.** El T0 de dos sólidos ya usa parámetros fuente C14: PIMPLE global 3/2/1, relajación e/eFinal=1; PCG+DIC tol 1e-6 y relTol 0.05 de la región sólida C14 arena para los dos sólidos; nEnergyCorrectors=2 de C14 metal trasladado al control global, todavía sin comprobar su efecto nativo. La adaptación excluye p_rgh/U y deja los originales C14 intactos. Fuente versionada con SHA Git y test de correspondencia. **ETAPA CASO B 3/7 (T0); AVANCE 2/7 = 29% hitos técnicos, NO tesis/CFD.** T0 sigue sin valores físicos documentados ni materialización/solver WSL; 1,826 caras severas noortogonales siguen siendo advertencia. [Bitácora detallada](docs/granada/C3D05_FVSOLUTION_C14_20261119_ES.md).

> **19-11-2026 | GRANADA_C3D05_T0_INTEGRAL_20261119 — GRANADA CASO B, ENTREGA DE CÓDIGO PRE-CFD:** publicado [orquestador integrado T0](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_granada.py): valida en una sola operación entradas/fuentes, estado CAD-HEX8/contacto ya documentado, copia segura del caso y 9 diccionarios Foundation14 con foamDictionary; bloquea sobrescritura, concurrentes y valores sintéticos explícitos, permite reentrada idempotente cuando SHA/resultado coinciden; **NO ejecuta foamMultiRun, Gmsh ni checkMesh**. Añadidas [regresiones sintéticas](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_granada.py), [workflow estático](.github/workflows/c3d05-t0-granada-static.yml) y [bitácora integrada](docs/granada/C3D05_T0_INTEGRATED_GRANADA_20261119_ES.md). **Estado canónico sigue ETAPA 3/7, 2/7 hitos (29% técnico, NO tesis):** faltan propiedades termofísicas auténticas y ejecución WSL, por tanto T0 no está materializado ni validado. No se repiten auditorías de malla ni se alteran los ensayos históricos.

> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119 — REGLA PERMANENTE PARA TODOS LOS CASOS:** entregar hitos integrales con QA interno y corrección de raíz, sin muchas pruebas WSL por pieza; comunicar SIEMPRE **ETAPA + AVANCE + evidencia + bloqueo + siguiente hito**. Caso B C3D-05: **etapa 3/7 T0; 2/7 hitos = 29% técnico** (NO tesis, CFD o validación). CAD/HEX8 y contacto aceptados; 1,826 caras >70°; T0 preparado, faltan propiedades físicas y no se ha ejecutado. [Política](docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [estado canónico](docs/PROJECT_STAGE_STATUS.json). La evidencia histórica permanece intacta.

> **18-11-2026 — Trabajo en paralelo, prioridad inmediata:** 1) Ejecutar C3D-04 (`blockMesh` curvilíneo con 144 arcos) en WSL y auditar `CONTACT_AREA_REPORT.json`; 2) conseguir dos STEP **sólidos** de SolidWorks (metal y molde separados, origen y mm iguales) para habilitar C3D-05 con Gmsh/OpenCASCADE, sin suponer que los STL sirven como STEP; 3) comparar ambos con CAD y malla nativa antes de BC/CFD. **Estado:** C3D-03 malla preliminarmente aceptada, C3D-04 preparada/no corrida, C3D-05 bloqueada por insumos CAD. [Comparativa](docs/C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md).

> **18-11-2026 — Compromiso explícito con el director / primer avance:** entregar ecuaciones de masa, momento y energía/solidificación, condiciones iniciales y de frontera reales, cifras de configuración y **Courant máximo obtenido de logs**, además de **sensibilidad de `phaseChangeSource.relax`** usando C14 `0.10` y C16 `0.25`. El 0.25 de `maxCo` en `controlDict` **no es dato medido**, y la corrida de C16 sigue pendiente. El estado de CFD C14 verificado es distinto al mallado 3D C3D-02 rechazado. [Plan detallado, fuentes y checklist](docs/PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md).

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — siguiente línea de trabajo C3D-02:** el ensayo aislado metal v2 colapsó a **1 celda** de metal; el ensayo aislado arena v2 colapsó a **0 celdas** de arena. Las dos variantes fracasaron; no repetir mallado idéntico. **Paso de diagnóstico**: comparar mensajes nativos `snappyHexMesh`/`cellZones` de ambos logs existentes y baseline, sin fabricar datos; **línea alternativa a evaluar**: malla multibloque 3D conformante que retome las caras compartidas del `blockMesh` cuasi-2D del doctor, verificando fidelidad al CAD QuickCup, volúmenes, contacto y `checkMesh`. Ningún diseño multibloque 3D está implementado ni validado. [Ensayos](docs/C3D_02_ABLACION_STL_V2_20261118_ES.md) · [estudio original](docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). C14 y J0/G1 sin cerrar.

> **Adenda 2026-11-12:** la línea C→3D pasa a [C3D_02_metal_sand_clean](cases_3d/C3D_02_metal_sand_clean/README.md), con dos sólidos (`metal`, `mold`) y física C14 preservada. Etapa de fuente preparada; siguen pendientes geometría/malla conformante, parches CHT, configuración regional y validación, **sin modificar** los estudios B/C 2D ni adelantar el estado de V15/V16. [Evidencia e incidentes](docs/C3D_REINICIO_20261112_ES.md).

# Plan de investigación QuickCup — acuerdos tras reunión con el director

> **Adenda actual (10-11-2026):** esta hoja de ruta de octubre conserva su función como plan, pero el trabajo 3D ha avanzado a dos ensayos de mallado, clasificación de STL, recorte metal+molde (**1,209,777 celdas**) y `splitMeshRegions -disconnected` en copia, con **dos regiones y sin interfaces conjugadas (`No interfaces to add`)**. `checkMesh` sigue fallando por región, **no hay CFD 3D ni validación**. Para cifras y próximos gates, ver [registro C3D](docs/C3D_01_ESTADO_REAL_20261110_ES.md) y [manual ES](OPENFOAM_COMMAND_MANUAL_ES.md).

Fecha: 2026-10-08 · Estado: hoja de ruta, no validación de resultados · OpenFOAM Foundation v14

## Prioridades y genealogía

```text
                           FASE COMÚN DE SENSIBILIDAD (2D)
B14 ──┬──> B15  adaptive timestep ─────┐
      └──> B16  relax fase = 0.25 ──────┤
                                       ├──> CIERRE V15/V16 ──> RUTA B
C14 ──┬──> C15  adaptive timestep ─────┤                       aire–metal,
      └──> C16  relax fase = 0.25 ──────┘                       shrinkage/feeding
                                                └─────────────> RUTA C
                                                                  modelo 3D
```

**Secuencia acordada:** V15 y V16 se ejecutan **en ambas familias B y C**, como pruebas de sensibilidad paralelas. **Después de cerrar V16** arrancan **dos rutas científicas diferentes**: C evoluciona a un modelo 3D desde la referencia C14 (o una configuración posterior justificada por evidencia), y B evoluciona a un modelo de superficie libre aire-metal y contracción/feeding. La transición de etapa es cronológica: **NO implica que C3D sea un clon de C16 ni que B-FS sea un clon de B16**. Se decide el padre físico según el análisis de V15/V16, manteniendo B14/C14 congelados. Ningún caso se ejecuta desde GitHub.

**Comparaciones pareadas**:
- V15: `B15 vs B14` y `C15 vs C14` (adaptativo), después diferencias de sensibilidad B/C.
- V16: `B16 vs B14` y `C16 vs C14` (relajación), después diferencias de sensibilidad B/C.
- El avance a 3D y superficie libre **solo se inicia tras disponer de los resultados V16 y revisar ambos grupos**; no se asume que las alteraciones numéricas resuelvan la discrepancia de continuidad B14.

### C15_adaptiveDt_fromC14 — PREPARED_NOT_RUN
- Diferencia numérica: `system/controlDict/adjustTimeStep yes`.
- Instrumentación de escritura para tiempos físicos comparables: `writeControl adjustableRunTime`; `writeInterval 0.1` segundos.
- Sin cambio respecto a C14: `deltaT inicial=0.001`, `maxCo=0.25`, `maxDeltaT=0.1`, `relax=0.1`.
- Precedente de cautela: las familias adaptativas C6/C8 y B6/B8 no reprodujeron exactamente el patrón de solidificación con dt fijo pese a la reducción de tiempo CPU.
- **Verificar después del push**: evolución real de dt; Courant; T(t)/U(t)/alphaL(t) y perfiles alineados por tiempo físico; balances e interface; tiempo de reloj y medidas de sensibilidad, no solo End.

### C16_phaseRelax025_fromC14 — PREPARED_NOT_RUN
- Diferencia única: `constant/metal/fvModels/phaseChangeSource/relax=0.25` (C14=0.1).
- El `maxCo=0.25` y `relaxationFactors=1.0` son conceptos DIFERENTES y quedan intactos.
- Código real: `solidificationMelting.C` en https://cpp.openfoam.org/v14/solidificationMelting_8C_source.html utiliza `relax` en actualización de `alpha1` por timestep: este cambio puede afectar respuesta transitoria de fracción de fase y fuente latente, no solo residuales.
- **Verificar después del push**: alphaL, dAlphaLdt, calor latente, T(t), fronts y velocidad, estabilidad/residuos, conservación y coste.

### B15_adaptiveDt_fromB14 — PREPARED_NOT_RUN
- Versión paralela directa de B14, con los **mismos tres ajustes** de `system/controlDict` que C15 frente a C14: `adjustTimeStep=yes`, `writeControl=adjustableRunTime`, `writeInterval=0.1` s.
- Permanecen `maxCo=0.25`, `maxDeltaT=0.1` s, `deltaT` inicial 0.001 s, `relax=0.1`, EOS `rho(T)` de B14, mismas condiciones de frontera y top `slip+fixedFluxPressure`.
- **Investigar** estabilidad, Courant, errores de continuidad, T/U/alphaL, energía, frente de fase y costo vs B14, con series alineadas por tiempo físico. Comprobar analogías/divergencias de sensibilidad con C15 vs C14.
- La prueba adaptativa **no arregla** por sí misma la incompatibilidad de densidad variable en volumen rígido cerrado.

### B16_phaseRelax025_fromB14 — PREPARED_NOT_RUN
- Versión paralela directa de B14. Solo cambia `constant/metal/fvModels/phaseChangeSource/relax` `0.1 -> 0.25`, manteniendo `adjustTimeStep=no` y `deltaT=0.001` s fijo.
- `maxCo=0.25` y `relaxationFactors=1.0` son diferentes al `relax` de solidificationMeltingSource; no tocarlos.
- **Investigar** respuesta de fracción líquida, latente, T/U, residual, continuidad y costo vs B14; contrastar `B16-B14` vs `C16-C14`.
- Separar resultado de relajación del diseño posterior de superficie libre/contracción. No declarar que `relax=0.25` valide la física de B.

## C3D-01 — expansión geométrica desde C14, fase siguiente

**Esta ruta 3D empieza después de concluir V16 para las dos familias.**

**C14 real NO es 3D**: `system/blockMeshDict` representa 40×40×10 mm en metal, con **80×80×1 celdas** y parches `frontAndBack` de tipo `empty`. Es un plano 2D extruido para mallado; hay que rediseñar geometría, mallado, parches y referencias.

**Pendiente del investigador/director**: determinar la geometría del QuickCup real (idealmente sección circular/anillo o dimensiones del molde medido), profundidad, volumen de metal, espesores y ubicación/posición 3D de termopar. Sin esos datos no proponer una malla realista arbitraria.

Plan gradual:
1. Congelar referencia 2D C14; replicar parámetros físicos y condiciones reales en un **caso nuevo** C3D-01.
2. Construir malla genuinamente 3D metal+molde; retirar `empty` solo cuando existan paredes/caras físicas correctas; corregir zonas/interfaces y controles térmicos, radiación/convección lateral y metalTop según geometría.
3. Verificar `checkMesh`, topología, normales de patches, volúmenes/áreas, conexión térmica metal–molde, balance de energía, punto de presión `pRefPoint`, malla/timestep; el probe 2D (0.02,0.02,0.005) no se reusa sin verificar.
4. Elegir comparación 2D↔3D en observables físicos medibles (T del termopar, masa y áreas de intercambio, frentes de solidificación, flujos), sin asumir que un cambio de geometría equivale a un cambio de discretización solamente.
5. Afinar malla y validar después con curvas de enfriamiento y datos JMatPro (puerta J0 sigue abierta).

## B-FS y B-SH — programa paralelo de superficie libre y shrinkage

**Esta ruta B empieza después de concluir V16 en las dos familias; B15 y B16 son ensayos numéricos previos y no contienen todavía aire, superficie libre ni shrinkage.**

**No descartar B14**: es un experimento útil de densidad variable, pero el dominio metálico impermeable y de volumen fijo exhibió continuidad acumulada ≈ -0.031. El resultado motiva explorar física de cambio de volumen, **no demuestra todavía** que incorporar aire o superficie libre resolverá exactamente ese residuo.

Distinción física: el metal fundido cambia densidad/volumen; la superficie metal-aire **desciende** si no hay alimentación, y el aire atmosférico ocupa el espacio expuesto. **No** representa que el aire se disuelva o entre a reemplazar masa dentro del metal. Si hay feeding, el balance de masa cambia; si hay contracción de solidificación, la porosidad o cavidades exigen física adicional.

Etapas **separadas**:
1. **B-FS-01 factibilidad numérica:** estudiar el módulo OpenFOAM Foundation v14 `twoPhaseVoFSolver` (captura VOF aire-metal) y/o otros módulos multiphase apropiados; confirmar integración real con energía metal-molde, `solidificationMelting`, propiedades de aire y metal, gravedad, tensión superficial y condición atmósfera. NO asumir que basta convertir la pared `metalTop` en `pressureInletOutletVelocity`.
2. **B-FS-02 interfaz sin solidificación:** un test simple y controlado de líquido/aire e hidráulica atmosférica, sin mezclar fuente latente ni shrinkage.
3. **B-SH-01 densidad dependiente de temperatura y fase:** representar `rho(T, alphaL)`, posible alimentación, desplazamiento de interfaz y cierre conservativo de masa; rastrear masa metálica, volumen y altura de superficie, densidad por fase, presiones y transporte de energía.
4. **B-SH-02 solidificación**: acoplar latente/Darcy y, si necesario, contracción de solidificación contra las leyes de mezcla; estudiar formación de porosidad únicamente si se incorpora un modelo que la represente, nunca inferirla solo del aire exterior.
5. Comparar B14 cerrado, B-FS, B-SH y familia C solo con geometría, propiedades, condiciones de frontera y magnitudes de interés equivalentes. Registrar costo numérico y conservación.

En Foundation v14 existen módulos `twoPhaseVoFSolver` y `multiphaseEuler`, pero su presencia **no garantiza** acoplamiento directo compatible con el fvModel del caso actual. Antes de codificar, revisar implementaciones y un tutorial representativo y decidir arquitectura/multirregión.

## Gates de prueba e integridad

- Los nuevos casos B15/B16/C15/C16 son solo **PREPARED_NOT_RUN** hasta ejecución real en laptop y push de evidencia. Nunca prometer funcionamiento o estabilidad sin logs.
- Tras cada push, usar informes GitHub si Actions funciona; los agentes declarativos no son trabajadores autónomos. Actualizar inventario y bitácoras ES/EN, CASE_NOTES y análisis.
- La puerta **J0 (JMatPro)** y experimental **G1** permanecen abiertas. Trabajar en 3D no sustituye verificar propiedades/condiciones experimentales.
- No copiar postProcessing heredado como evidencia del nuevo caso, ni editar C14/B14.

## 2026-10-15 — Preflight reproducible previo a ejecutar V15/V16

El árbol Git de las cuatro variantes se comparó directamente con su padre (B14/C14): únicamente difieren `system/controlDict` para V15 y `constant/metal/fvModels` para V16; los demás archivos de entrada conservan el mismo blob. Se añadió `analysis_tools/preflight_sensitivity_cases.py` con pruebas sintéticas `analysis_tools/test_preflight_sensitivity.py` para detectar diferencias no controladas, valores activos fuera de hipótesis, entradas faltantes y evidencia heredada. Uso: `python3 analysis_tools/preflight_sensitivity_cases.py --strict`.

**Esto verifica la preparación de entradas, NO el resultado numérico.** Los cuatro casos siguen `PREPARED_NOT_RUN`, a la espera de ejecución en laptop y auditoría MAZAPÁN. Evidencia: [analysis_results/v15_v16_preflight/README.md](analysis_results/v15_v16_preflight/README.md). La bifurcación C3D/B-FS continúa bloqueada hasta cerrar V16 de B y C.

## 2026-10-15 — Estado tras subir resultados B11E2 / V15 / V16

Las cinco variantes tienen archivos versionados de solver y sonda hasta 10 s. No repetir inmediatamente `Allclean`/`Allrun`: primero auditar evidencia y confrontarla con los padres. La comparación térmica preliminar y el diagnóstico de Courant/continuidad constan en `analysis_results/v15_v16_postpush_20261015/README.md`. La carpeta de B conserva un desbalance de continuidad ≈ -0.031. B15/C15 superaron marginalmente `maxCo=0.25`; estudiar la implementación del control adaptativo y sus consecuencias. **No se abre automáticamente C3D ni B-FS ni se cierran J0/G1** hasta completar la auditoría de V16.


## 2026-10-19 — Avance de C3D-01 independiente de FoamLENS (malla PRELIMINAR)

Se recibieron los STEP originales individuales del molde y metal; un chequeo CAD con OCC confirmó un sólido válido en cada archivo, intersección volumétrica nula y contacto entre ambos. Se prepararon STL separados, ambos cerrados y orientados, con referencia **condicionada** a un molde de 51.8×65.5×51.8 mm (el export STEP presenta inconsistencia de unidades). El metal ocupa ~47.99 cm³, la arena ~102.84 cm³.

Se creó una barrera geométrica **solo lectura** en `analysis_tools/preflight_c3d_stl.py` con cuatro pruebas sintéticas y manifiesto versionado en [analysis_results/c3d_01_geometry](analysis_results/c3d_01_geometry/README.md). El paquete de malla se entrega localmente y no se publican los archivos CAD del investigador en GitHub. **No se ejecutó OpenFOAM**: `surfaceCheck`, `blockMesh`, `snappyHexMesh`, `splitMeshRegions`, `checkMesh` y balances físicos aún necesitan la laptop. Se conserva C14 intacto y J0/G1 abiertos; la ruta B de superficie libre es independiente.


### 2026-10-19 — Primer caso 3D en carpeta separada (C3D-01)

Se incorporó la **preparación geométrica y de malla de fondo** como experimento independiente en [`cases_3d/C3D_01_metal_mold`](cases_3d/C3D_01_metal_mold/README.md). Utiliza el molde y el metal corregidos/exportados desde SolidWorks (`QuickCup(1).STL`, `metal(1).STL`), no los STEP antiguos con la escala equivocada. Las nuevas piezas tienen dimensiones 51.8×65.5×51.8 mm y 36.5×40×36.5 mm. Para el fondo se propuso una caja de 58×72×58 mm con 29×36×29=30 276 celdas uniformes de 2 mm. Las caras del `blockMeshDict` se corrigieron a orientación exterior y se introdujeron pruebas geométricas estáticas. Los originales STL permanecen locales; el conversor controlado mm→m evita desplazamiento y doble escalado.

**Separar preparación de simulación:** los comandos `blockMesh` y `checkMesh` aún no se han ejecutado en Ubuntu; `snappyHexMesh`, interfaz CHT, solver CFD, J0 y G1 siguen pendientes. Este avance no da por cerrada la auditoría V15/V16 ni valida físicamente la ruta 3D. GitHub Actions jamás ejecuta CFD ni meshing.


### 2026-10-19 — Actualización metodológica: unidades explícitas en OpenFOAM14

Tras revisar la guía oficial de `blockMesh` v14 y el código fuente `searchableSurfaces::triSurface::scale`, se aprobó sustituir el escalado numérico de STL mediante Python por la **declaración nativa `units [mm];`** en los diccionarios. `C3D_01_metal_mold/system/blockMeshDict` ahora expresa los 8 vértices directamente en milímetros; los STL binarios se copian byte a byte a `constant/geometry`, también en milímetros. La futura sección `geometry` de `snappyHexMeshDict` declarará `units [mm];` por superficie. El preflight Python audita volúmenes/coordenadas en SI en memoria, sin modificar archivos. No se realizó mallado OpenFOAM ni CFD. Prohibido doble escalado.
