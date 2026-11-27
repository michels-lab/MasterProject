# Historia científica de MasterProject — julio a noviembre de 2026

**Corte: 27-11-2026.** Registro de decisiones y evidencia, no una nueva simulación. La [bitácora original ES](../PROJECT_AUDIT_LOG_ES.md) conserva los identificadores AUD y los detalles de experimentos; la [versión EN](../PROJECT_AUDIT_LOG_EN.md) es su complemento. Los antecedentes de julio a septiembre incluyen entradas CHAT-RECOVERED ya documentadas, no logs recién verificados. La cronología Git comienza el 22-09-2026 UTC, no en julio. Los índices de commits y ramas fijan la procedencia sin afirmar que todo commit equivale a trabajo científico aceptado.

## 1. Julio–principios de septiembre: planteamiento

- 27-07: metodología composición → propiedades JMatPro → OpenFOAM → coladas QuickCup → comparación de curvas. 28-07: CHT metal/molde, entalpía-porosidad, fuente de solidificación, dominio cuasi-2D. 29-07: casos del doctor bcFourier y CHT como referencias. Datos históricos aproximados Tsol 1423 K, Tliq 1473 K, L 228600 J/kg, Cu 1e5, alpha1e .8, capa interfacial .2 mm/k=.1 W/(m K). No atribuir estas cifras a una nueva exportación JMatPro.
- 03-09: extensión cinética futura; 07-09: rebote térmico no prueba recalescencia; relax numérico no constante cinética. 11-09: formulación futura S_L=-rho L df_l/dt (W/m³). 18-09: tres niveles (equilibrio base, JMatPro/Scheil, cinética) y métricas de transformación distintas de RMSE.
- Fuente: PROJECT_AUDIT_LOG_ES.md, secciones 0–2. El identificador AUD-030 permanece sin entrada recuperada.

## 2. Septiembre: modelo base, errores y separación B/C

15-09, AUD-001–023: Foundation14, copia independiente cleanproy; se corrigió la confusión 0.05/0.5 mm. Malla 11880 HEX (6400 metal + 5480 molde), 240 caras interfaz, 1 celda z, empty, no ortogonalidad 0°, 24198 puntos y 47738 caras. createZones no alteró hash histórico; cajas se superponían, flujo actual conserva zonas blockMesh. splitMeshRegions -cellZones all sustituye sintaxis anterior. Correcciones de metalTop/h y Ta, emissivity. Corrida base 0–300 s reportada con End. Se detectaron dos contribuciones de flotación y se separaron: B icoTabulated rho(T), beta=0; C rhoConst y fuente explícita beta. Densidad inicial C histórica 6930, normalizada luego a 6820 kg/m³ en comparación controlada.

21-09, AUD-024–032: A/B/C históricos mostraban caída artificial inicial 1500→1473 K cerca de .009 s. Inicializar alpha1=1 eliminó corrección latente artificial de ~7.7 K; no equiparar refusión con recalescencia. Caso D corregido: cruce liquidus ~3.2506 s, alpha=.99 ~3.5624 s, cruce solidus ~104.9 s, alpha=.5 ~207.56 s, alpha=.01 ~227.59 s, alpha=0 y T~1329.77 K a 300 s (historia recuperada, no nueva validación). Rebote ~1455→1461.18 K entre 4.9–11.6 s acompañado por alpha .9283→.9527. Se distinguió PIMPLE global de correctores regionales.

22–24-09: B3/C3 (10 s, dt .001, outer2), B4/C4 (energía2), B5/C5 (outer3). Auditoría SHA reveló diferencia térmica adicional en familia B y riesgo de comparaciones no controladas. Se creó serie controlada con condiciones térmicas homologadas. Probes (20,20,5) mm y perfiles lineales a y=10/20/30 mm y x=20 mm. Regla: mantener originales, logs, identidad de commit y comparación de control. Véase AUD-033 en adelante y [VERSION_LOG](../cases_controlled_buoyancy/VERSION_LOG.md).

## 3. Septiembre–octubre: genealogía de experimentos controlados

| Generación | Pregunta | Cambio |
|---|---|---|
| V3 | Referencia | outer2, totalPressure, air gap OF13 heredado |
| V4 | Corrector energético | nEnergyCorrectors=2 |
| V5 | Sensibilidad outer | outer3 |
| V6 | Sensibilidad temporal | adaptive, Co=.25 |
| V7 | Sensibilidad outer | outer4, fijo |
| V8 | Interacción | adaptive + outer4 |
| V9 | Fuga superior | fixedFluxPressure; diagnóstico phi |
| V10 | Resistencia térmica | air gap Foundation14 con totalPressure |
| V11 | Tapa y resistencia | fixedFluxPressure + air gap OF14 |
| V12 | Alternativa director | fixedValue p_rgh consistente inicialmente |
| V13 | Atmósfera | prghPressure gauge |
| V14 | Referencia explícita | fixedFluxPressure+slip, pRefPoint (.02,.04,.005), pRefValue 1e5, U/phi por cara |
| V15 | Sensibilidad temporal C14/B14 | Preparado, ejecución no demostrada en registro |
| V16 | Sensibilidad phase relax | Preparado, ejecución no demostrada en registro |

Transiciones B5/C5_airGapOF14 y B9/C9_airGapOF14, V12/V13 provisionales y energy2 aislados se conservan; no cuentan doble. V3–V9 antiguos conservan sintaxis de gap OF13; V10+ emplea wallLayersHeatTransferCoefficient. B9 también extendió tabla rho(T) hasta 2273.15 K y añadió referencia de presión; no es experimento de un solo cambio.

[Auditoría histórica 26/26](../analysis_results/full_campaign_audit/summary.md), con 0 productos de perfiles faltantes; criterio runner COMPLETED y sonda >=9.999 s sin fatal detectado, no exige End en todos los logs. [Registro](../RUN_CASE_REGISTRY.csv): V14 B/C y C11_energy2 adicionales, fuera de los 26; B11_energy2 preparado. No confundir conteo de corridas históricas con validación.

03-10, [V14](../analysis_results/v14_bc_comparison/summary.md): B/C a 10 s, máximos Co .0673434/.0650864, continuidad -0.031019/4.44346e-13, sum(abs(phi)) máximo 8.47033e-22/0 kg/s y Uy de tapa 0 en muestras. T central 1470.07/1464.19 K, alphaL media volumétrica .9606902/.9620593, potencia total frontera 316.1799/313.9750 W. B14 conserva sensibilidad rho(T) y requiere mecanismo de cambio volumétrico; C14 referencia rígida impermeable. No atribuir continuidad B a fuga superior. V15/V16 no promovidos por análisis de configuración/logs ajenos.

20–21-10: se documentaron diagnósticos de frontera/energía, interfaz bilateral, viabilidad free-surface Foundation14, banco agua-aire y plan geométrico 3D; [índice documental](DOCUMENTATION_INDEX.md), [gobernanza](granada/GRANADA_GRANDE_GOVERNANCE_20261020.md). Se conservaron decisiones, informes y ramas anteriores.

## 4. Octubre–noviembre: transición 3D y descarte de rutas

C3D01: STL y unidades mm, blockMesh nativo, snappyHexMesh, recorte metal/arena. 10-11: 1209777 celdas, 151.230 cm³, 15 cóncavas, 8 face-tets deficientes, 17 determinantes pequeños; split desconectado dio dos regiones 825994/383783, sin interfaz; no CFD aceptado. [Registro](C3D_01_ESTADO_REAL_20261110_ES.md).

12–18-11, C3D02: reinicio sin borrar, dos mallas independientes, corrección sintaxis F14, insidePoint y clasificación por zonas; las selecciones retenían exterior. Se midió y extrajo moldVolume en copia; 15-11 VTK de defectos (2422 celdas cóncavas metal, 22737 arena, 1 determinante bajo); no aceptación. Ablaciones STL v2: metal solo 1 celda, arena sola 0; rechazadas. El ejemplo del director blockMesh con cellZones motivó conformidad, no reemplazo de CAD ni propiedades. [Reinicio](C3D_REINICIO_20261112_ES.md), [ablación](C3D_02_ABLACION_STL_V2_20261118_ES.md), [piloto C3D03](C3D_03_RESULTADO_NATIVO_20261118_ES.md).

18–19-11: rutas A y B en paralelo. A multibloque curvilíneo V4/T02, B STEP/Gmsh y HEX8. Los documentos de determinantes, no ortogonalidad y procedencia registran intentos fallidos y mallas aceptadas con advertencias; no remallar los originales. [A superficie](C3D_04_VALIDACION_SUPERFICIE_T02_20261119_ES.md), [B HEX8](C3D_05_HEX8_VALIDACION_INDEPENDIENTE_FINAL_20261119_ES.md). A 8960+12352 celdas, 2496 caras/side; B 92200+178588, 12636 caras/side. A/B no son idénticas resoluciones.

## 5. Noviembre: CFD nativo y análisis A/B

20–24-11: A reproduce C14 fluido/sólido a 10 s, 10000 pasos, 101 estados. Auditorías detectaron falsos PASS de foamPostProcess con cellZone faltante; recuperación en copias aisladas, perfiles verticales usando cuerda interior válida. Réplica fiel 1717 perfiles y análisis multidireccional; estado 9/10, 8/10=80% hitos. [Estado](C3D04_CASE_A_STATUS.json), [paridad](C3D_04_C14_3D_POSTPROCESS_PARITY_MATRIX_20261123_ES.md), [réplica](C3D04_A_STAGE09_FAITHFUL_NATIVE_ANALYSIS_20261124_ES.md).

19–24-11: B primero conducción T0 dos sólidos, luego C14 original fluido/sólido 10 s. 101 estados, alpha1 volumen final .8917029861; q bilateral 12636 pares. A 10 s q interfaz metal/molde +1581.564663/-1581.538327 W. Comparación integrada por trapecio exterior 1341.507907 J y deltaEref -1352.944201 J, diferencia -11.436294 J NO balance discreto. Sondas/perfiles corregidos; 1717 métricas y 404 estaciones comparativas, 287 eventos de signo Uy no inversiones globales. No fabricar 10001 muestras a partir de 101. B 3/7, 2/7=29% hitos. [Estado B](PROJECT_STAGE_STATUS.json), [cruce energía](granada/C3D05_B_C14_CRUCE_101_ESTADOS_CONFIRMADO_Y_AUDITORIA_TERMINOS_20261124_ES.md), [comparativo](granada/C14_COMPARATIVO_2D_3DA_3DB_SONDAS_20261124_ES.md).

## 6. Contracción: línea independiente

B14 no es predicción validada de rechupe. FS-C01 analogía agua-aire; FS-C02 y sucesores exploran VOF, alimentación y conservación. FS-C07 alcanzó 1 s, 20 snapshots, problema de asignación de fase a bajo VOF; no aceptar cambio bruto de volumen. FS-C08 inventarios de masa líquido/sólido/gas, energía interna con latente una vez, presión/volumen, Darcy y reconstrucción; shadow/sintético separado de solver real. B14_reference aproximado, K Fe puro provisional, no propiedades de fases calibradas. [Rama FS-C08 y bitácora de 12 lotes](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md). Lote 12, 75/75 pasos, 4/4 variantes, 5 μs, todos los gates locales finales; dependencia temporal fuerte y energía global/contracción física pendientes. Acumulado 501/757 pasos, 36/48 variantes únicas, no porcentaje de tesis. PR #79 separado, no merge.

## 7. 24–27 noviembre: campaña larga

Véase [cronología y tabla detallada](granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md). Fija laboratorio dt=.001, adaptación laptop dt inicial .001, Co=.25, MPI8 con/sin cap .025, no B14 3D. 6/8 combinaciones llegaron 200 s; **5/8 publicaciones completas verificadas al corte de esta revisión** (dos 3DB, C14-2D serial y MPI con tope, B14-2D MPI con tope); B14-2D sin tope sigue pendiente de manifiesto; A ambos adaptativos fallan .68/.70 s. La reparación de duplicados de muestreo no cambia física. A fijo laptop llegó 200 s, laboratorio reportado auditado pero sin manifiesto completo. WSL movido a HDD; reconexión restauró comandos. Los resultados locales no montados no se afirman inspeccionados directamente.

## 8. Archivos y trazabilidad permanente

- [Inventario de documentación y ramas congeladas](HISTORICAL_INVENTORY_20261127.json): metadatos SHA de archivos, ramas, límites de inventario.
- [Historia Git parte 1](MAESTRIA_COMMIT_HISTORY_20261127.json) y [parte 2](MAESTRIA_COMMIT_HISTORY_20261127_PART2.json): 2311 commits alcanzables desde snapshot main 134ac9bf6f631320630212274fd26cb8c31b5c31, 22-09 a 27-11; no incluye commits exclusivos de ramas sin integrar. No reemplaza las fuentes ni los logs.
- [Estado vivo](MAESTRIA_STATUS.json), [índice](DOCUMENTATION_INDEX.md), [plan](../NEXT_RESEARCH_ROADMAP_ES.md), [matriz](../VALIDATION_MATRIX_ES.md), [protocolo](../RUN_MASTER_PROTOCOL.md).
- [Primer avance solicitado por director](PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md): ecuaciones, IC/BC, Courant real, sensibilidad relax del cambio de fase. No inventar fecha de entrega ni concluir sensibilidad no ejecutada.
- [JMatPro](../JMATPRO_OPENFOAM_TRACEABILITY_ES.md): J0 abierto, curvas auténticas/QuickCup no verificadas. La copia de C14 o de B14 no cierra trazabilidad. No confundir h de interfaz con coeficiente externo.
- Prioridad de análisis FoamLens, ParaView complementario; distinguir productos nativos, canónicos y reconstruidos. Conservar evidencia física, unidades, hashes y criterio de aceptación.

## 9. Pendientes científicos

A: estabilidad adaptativa y conservación/independencia. B: cierre discreto y propiedades trazables. B14-2D sin tope: publicación pendiente, no rerun. Laboratorio: verificar manifiestos finales. FS-C08: sensibilidad temporal, energía global y propiedades reales. QuickCup/JMatPro: contrastar curvas y transformación, no prometer recalescencia. No porcentaje global. Documentación: registrar toda decisión y fallo en bitácora propietaria y sincronizar estados vivos; no reescribir retrospectivamente archivos históricos ni modificar ramas de resultados.
