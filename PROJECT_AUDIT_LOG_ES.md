> **27-11-2026 — Auditoría incremental:** registro por ruta/blob y alcance, siete inspecciones iniciales (dos completas documentales y cinco parciales); seis publicaciones adaptativas contrastadas por pasos con el índice de manifiestos. Sin cambios de física ni validación nueva. [Protocolo](docs/review/README.md).

> **27-11-2026 — Cierre vigente de auditoría documental:** 6/8 combinaciones adaptativas laptop calculadas y publicadas con manifiesto completo; solo A adaptativo con/sin tope fallido. 0 recuperaciones 2D pendientes. A 8/10=80%, B 2/7=29% hitos técnicos; FS-C08 lote 12 75/75 pasos de arranque, no validación física. Laboratorio fijo independiente; A reportado auditado sin manifiesto completo verificado. [Historia científica](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Estado JSON](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json). Las notas anteriores conservan su valor histórico, no prevalecen como estado vigente.

> **27-11-2026 — ESTADO VIGENTE (sustituye estados temporales antiguos, no los hechos históricos):** 2D histórica 26/26, V14 separado. A 9/10, 8/10=80% de hitos; B 3/7, 2/7=29%. Adaptativa laptop: 6/8 calculadas, 5/8 publicadas con manifiesto completo (C14-2D serial sin tope, C14-2D MPI limitado, B14-2D MPI limitado y C14-3DB MPI ambas políticas), B14-2D sin tope pendiente de publicación, A ambas políticas fallidas a .68/.70 s. Fija laboratorio: A reportado auditado, manifiesto pendiente; A fijo laptop 200 s observado, no confundir. FS-C08 lote 12: 75/75 pasos, 4/4 variantes a 5 μs, sin independencia temporal, energía global ni contracción validada. No porcentaje global de tesis. [Historia científica](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Estado integrado](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md) · [Estado JSON](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json).

> **Corrección de alcance autorizada por el investigador, 24-11-2026:** B14 NO es candidato 3D. Campaña activa exclusivamente C14-3DA-200s, C14-2D-200s, B14-2D-200s, C14-3DB-200s (4 corridas, 800000 pasos); B14-2D referencia de contracción, C14 candidato 3D. Excluir B14-3DA-200s, B14-3DB-200s de ejecución y descarga. El paquete histórico de seis entradas ya publicado permanece intacto; no es autorización para correr seis. Transferidor actualizado 3deb781c0f1a87cb84244fdb3c748b39dbce3fa4; no modifica física, mallas, almacenamiento, rama FS ni resultados previos. Proyección para cuatro casos 103865500374 bytes; no consumo medido. 4/4 entradas autorizadas publicadas; 0/4 CFD completos confirmados. Foundation 14 laboratorio confirmado por consola (14-a4867fc914c1); importación y CFD pendientes. Interrupción local A fue manual según investigador, no prueba de estabilidad. A 8/10=80%, B 2/7=29% históricos.

> **24-11-2026 | Campaña compacta: preparación WSL 6/6 confirmada.** Consola del investigador: `ALL_SIX_COMPACT_PREPARED_NO_CFD`, seis casos `PREPARED_COMPACT_NOT_RUN`. Proyección total 195999917264 bytes frente a 677717076556 bytes (reducción 71.0793893%); espacio libre WSL 930909974528 bytes; `all_fit_WSL_estimate=true`. Por caso: 2D 5865541742 bytes, 3DA 6722248179 bytes, 3DB 85412168711 bytes, iguales estimaciones por familia. CI estática #45516133349 completada con success; no equivale a CFD. Capacidad física Windows todavía no verificada. 0/6 corridas, cadencias nativas pendientes de validar en el primer segundo real. Prioridad C14-3DA-200s, utilizar únicamente el ejecutor compacto; conservar casos densos y originales. A 9/10, 8/10=80%; B 3/7, 2/7=29% hitos históricos.

> **24-11-2026 | Campaña 200 s — prioridad nueva: almacenamiento compacto.** Autorizado por el investigador. Mantener dt=.001 s, 200 s, 200001 muestras de sonda, perfiles/reducciones/topFlow/nearTop online cada .1 s (2001 estados previstos), volúmenes completos y momentum nativo cada 1 s (201 estados previstos); ASCII original, sin compresión o cambio físico. Los seis casos densos preparados permanecen intactos; nuevo preparador independiente `tools/compact_campaign_200s.py`, verifica hashes, requiere casos densos no ejecutados, audita el primer segundo real de la corrida y reserva disco. 6/6 densos preparados, 0/6 compactos observados, 0/6 CFD de 200 s observados. CI estática en cola al revisar #45516133349; no se afirma PASS, ejecución WSL ni ahorro total medido. A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29%. [Plan compacto](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_CAMPANA_200S_ALMACENAMIENTO_COMPACTO_20261124_ES.md).

> **24-11-2026 | Campaña 200 s: preparación WSL 6/6 confirmada.** Consola del investigador, HEAD 3ffe0b56a: las seis variantes PREPARED_NOT_RUN, ALL_SIX_PREPARED_NO_CFD. Proyección con margen: 677717076556 bytes; espacio libre reportado por WSL: 931037851648 bytes; all_six_fit_estimate=true. Confirmar también espacio físico del volumen Windows que aloja el VHDX; la estimación no garantiza capacidad real. 3DB 270788 HEX8, 12636 caras de contacto por lado, 1826 caras no ortogonales severas (advertencia conservada). 0/6 CFD ejecutados; A 8/10=80%, B 2/7=29% hitos. Prioridad actual A C14-3DA-200s según registro A, usar ejecutor específico sobre caso ya preparado, sin repetir preparación. [Plan](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_CAMPANA_B14_C14_200S_PLAN_20261124_ES.md).

> **24-11-2026 | Caso A prioridad 200 s:** investigador pospone sensibilidad; C14-3DA-200s conserva V4/T02 y diagnósticos fieles, cambia solo endTime. Ejecutor específico publicado, WSL pendiente; etapa9/10, 8/10=80%. [Evidence](docs/C3D04_A_C14_200S_PRIORITY_20261124_ES.md).

> **24-11-2026 | Caso A A5.1:** ejecutor de sensibilidad temporal publicado; dt=.001/.0005/.00025 s, malla V4/T02 y frecuencia física .1s intactas. Dos nuevas corridas WSL pendientes; no independencia acreditada. Etapa09/10, 8/10=80%. [Protocolo](docs/C3D04_A_STAGE09_TEMPORAL_SENSITIVITY_20261124_ES.md).

> **24-11-2026 | Caso A auditoría real WSL:** 606 archivos primarios idénticos, RMSE=0; residual combinado nominal +0.030516 J (0.1–10s), −6.421037 J (0–10s). A3/A4 diagnóstico guardado completo; no CFD ni cierre discreto. Etapa09/10, 8/10=80%. [Evidence](docs/C3D04_A_STAGE09_FAITHFUL_NATIVE_ANALYSIS_20261124_ES.md).

> **24-11-2026 | Nueva prioridad definida por el investigador: campaña de 200 s.** C14 es la referencia principal de solidificación (2D, 3D-A y 3D-B); B14 pertenece a la línea de contracción, y el investigador acepta preparar sus variantes 2D/3D-A/3D-B en la misma campaña. B14 no constituye por sí solo un solver de contracción/rechupe validado; FS-C08 sigue independiente. Preservar todos los resultados de 10 s. Seis corridas previstas, ninguna de 200 s preparada ni ejecutada en esta entrega. Antes de correr, verificar almacenamiento y costo, transferir cada formulación completa y homologar diagnósticos. A 9/10, 8/10=80%; B 3/7, 2/7=29%; hitos históricos sin cambio. [Plan de campaña](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_CAMPANA_B14_C14_200S_PLAN_20261124_ES.md).

> **24-11-2026 | A3/A4 Caso A:** análisis real en Git; RMSE probe T 6.706 K; residual energético diagnóstico metal 0.1–10s +1.514 J por inventario y −2.929 J por potencia latente; 0–10s −164.091/−168.533 J. CSV versionado, auditoría local bilateral publicada pendiente. No conservación discreta. Etapa09/10, 8/10=80%. [Evidence](docs/C3D04_A_STAGE09_FAITHFUL_NATIVE_ANALYSIS_20261124_ES.md).

> **24-11-2026 | SINCRONIZACIÓN MAESTRÍA — ESTADO VIGENTE (las entradas anteriores son históricas).** 2D: campaña histórica 26/26 corridas completas, sin productos de perfil faltantes; C14 referencia verificada, 10,001 muestras nativas de sonda; C15/C16 no se declaran corridos. 3D-A: etapa 9/10, 8/10=80% operativo, réplica fiel archivada con 10,000 pasos, 101 estados y 1,717 perfiles; conservación discreta, independencia y QuickCup pendientes. 3D-B: etapa 3/7, 2/7=29% técnico; corrida C14 fluido/sólido 10 s en 270,788 HEX8 completa, 101 estados, sondas corregidas (25.9,-20,25.9) mm, 17 líneas. [Análisis real PASS](https://github.com/michels-lab/MasterProject/actions/runs/45504719498): 1,717 métricas perfil-tiempo, 404 comparaciones de estaciones comunes 2D/B, 287 eventos directos de signo opuesto de Uy entre muestras consecutivas fuera de ±0.1 mm/s; no son 287 inversiones globales. Artefacto [14971467688](https://github.com/michels-lab/MasterProject/actions/runs/45504719498/artifacts/14971467688), no importación FoamLens verificada. Contracción FS-C08: rama independiente [estado](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/STATUS.json), solver conservativo implementado en código, PR #79 borrador, sin evidencia de compilación nativa del solver físico/CFD real ni datos de aleación trazados; pruebas shadow cerradas, no repetir. Sin nuevos hitos físicos cerrados, no porcentaje común. [Consolidado](docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261124_ES.md).

> **Caso A publicación científica:** réplica fiel C14 3D incorporada con estándares 2D: entradas, postProcessing, logs y evidencia SHA; malla generada y campos calculados preservados localmente. No CFD. Etapa09/10, 8/10=80%.

> **24-11-2026 | Caso A réplica C14 fiel REAL WSL COMPLETA:** FAITHFUL_C14_RUNTIME_READY, 10000 pasos, 10001 muestras nativas por T/U/p_rgh/rho/alpha1, 101 estados/reducciones, 1717 perfiles canónicos, 15 derivados en 101 estados, foamLog rc0, sin faltantes auditados; hashes controlDict/researchDiagnostics idénticos y evidencia base intacta. Nueva referencia preferente; analizar valores reales sin repetir CFD. Etapa09/10, 8/10=80% hitos; conservación discreta, independencia y QuickCup pendientes. [Evidencia](docs/C3D04_A_STAGE09_FAITHFUL_C14_RUNTIME_20261124_ES.md).

> **24-11-2026 | Caso A réplica C14 fiel autorizada:** nuevo ejecutor `run_c14_a_faithful_runtime.py` sobre V4/T02 idéntica, controlDict y física originales, functionObjects nativos y probe a dt=.001, perfiles originales y 13 líneas 3D adicionales. Conserva corrida base. Código publicado, WSL pendiente; 10001 muestras objetivo, no paridad verificada. Etapa09/10, 8/10=80% hitos. [Protocolo](docs/C3D04_A_STAGE09_FAITHFUL_C14_RUNTIME_20261124_ES.md).

> **24-11-2026 | Caso A comparación C14 2D–3D REAL WSL completa:** 101 tiempos, RMSE central temporal 4.053/6.555/13.155 K a 10/20/30 mm; Tliq 3D anticipada 0.6/1.2/4.8 s aprox.; vertical 80/80 RMSE 3.750 K; q/A contacto 231.179 vs 240.337 kW/m², A/V 75 vs 132.379 m^-1. No CFD ni muestreo repetidos. Etapa09/10, 8/10=80% hitos; independencia malla/tiempo, conservación discreta y QuickCup pendientes. [Evidencia](docs/C3D04_A_STAGE09_ARCHIVED_C14_COMPARISON_20261124_ES.md).

> **24-11-2026 | PRIORIDAD: PRIMERO COMPLETAR POSTPROCESAMIENTO DEL CASO B ORIGINAL, SIN REEJECUTAR CFD.** El usuario ya abrió en ParaView el C14-B original (10 s, **101 tiempos guardados**). Nuevo ejecutor integrado: `git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/POSTPROCESAR_CASO_B_C14_EXISTENTE.sh`. Genera en **copia física independiente** `~/OpenFOAM/C3D05_B_C14_POSTPROCESAMIENTO_C14_101_TIEMPOS_01` los functionObjects del C14 recuperables: perfiles y sondas de 101 muestras, vorticidad, flowType, gradT/magGradT, densidad/Courant, metalTop, foamLog y objetos opcionales de energía/momentum; abre `.foam` nuevo para inspección manual y reporta etapas fallidas. **NUNCA llama foamMultiRun ni añade nuevas pruebas**; no puede reconstruir 10,001 sondas nativas del dt=.001s con 101 campos espaciados a .1s. El segundo solver de 10 s queda EN PAUSA. El nuevo posprocesamiento **aún no se ha ejecutado en WSL**, no declarar paridad completa. [Manual](docs/granada/C3D05_B_C14_POSTPROCESAMIENTO_EXISTENTE_101TIEMPOS_ENTREGA_MANUAL_20261124_ES.md). Investigación formal 2/7 hitos.

> **24-11-2026 | C3D05-B: NUEVA CORRIDA CON LOS FUNCTIONOBJECTS LITERALES DEL C14 ORIGINAL, 0.001 s POR SONDA.** El investigador confirmó que ya abrió el Caso B original en ParaView. Para registrar `temperatureProbe` **en cada paso CFD** (y ejecutar `researchDiagnostics`/`lineProfiles` tal como C14), se necesita **otra ejecución real de 10 s**; el CFD anterior solo conserva 101 estados cada 0.1s. Ya se publicó el ejecutor sin pruebas adicionales **`bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/EJECUTAR_CASO_B_C14_COMPLETO.sh`**, previa actualización `git pull --ff-only`. Copia físicamente solo `0/constant/system` a una carpeta completamente nueva, mantiene `controlDict` original byte a byte y funciones C14 exactas; ejecuta `foamMultiRun`, `foamPostProcess` momentum/topFlow y `foamLog`, **sin remodelar malla ni alterar CFD original**. Se conserva `--post-only` para reiniciar únicamente postproceso. Coordenadas 2D de sondas/perfiles no alteradas: pueden no caer dentro de la geometría del Caso B. **Aún no está ejecutado en WSL**; no afirmar nuevas sondas hasta ver la salida. [Manual y rutas](docs/granada/C3D05_B_REEJECUCION_C14_FUNCTION_OBJECTS_001S_20261124_ES.md). Seguimos 2/7 hitos científicos.

> **24-11-2026 | Caso A comparación real C14 2D:** referencia versionada 10001 probe y 101 reducciones; T media reconstruida 1465.159 K (2D) vs 1450.709 K (3D-A), sólido 3.794% vs 10.276%, A/V contacto 75 vs 132.379 m^-1. Comparador de archivos existentes publicado, unión WSL con barridos A pendiente; no solver ni repetición de muestreo. Etapa 09/10, 8/10=80% hitos. [Evidencia](docs/C3D04_A_STAGE09_ARCHIVED_C14_COMPARISON_20261124_ES.md).

> **24-11-2026 | Caso A barridos 3D ampliados publicados:** 12 diámetros XZ, 5 verticales, estadística radial de hasta 8 muestras, Ur/Uθ, cuadratura área aproximada 41×41 a tres alturas y HTML. 101 estados solicitados, WSL no observado. No CFD, no sobrescritura y sin pruebas manuales. Comparación C14 2D pendiente; etapa 09/10, 8/10=80% hitos. [Protocolo](docs/C3D04_A_STAGE09_MULTIDIRECTIONAL_20261124_ES.md).

> **24-11-2026 | Caso A: comparación C14 2D–3D-A prioritaria.** Publicado ejecutor nativo offline con centros de sección y alturas desde base homologados, 3 horizontales/vertical central, 3 curvas de enfriamiento, medias volumétricas, T/U/p_rgh/alpha/gradT, cobertura, RMSE y HTML autónomo. No CFD ni micropruebas manuales; salida WSL no observada, depende de snapshots reales C14 2D. **Etapa 09/10, 8/10=80% hitos.** [Protocolo y comando](docs/C3D04_A_STAGE09_C14_2D_3D_COMPARISON_20261124_ES.md).

> **24-11-2026 | C3D05 Caso B: ENTREGA PARA REVISIÓN MANUAL OPENFOAM/PARAVIEW, SIN PRUEBAS NUEVAS.** El CFD original C14 Foundation14 ya completó **0–10 s con 101 tiempos**, hierro fluido y molde sólido. Se publicaron `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/ABRIR_CASO_B.sh` y `open_case_b_review.py`. Desde `~/OpenFOAM/MasterProject`: **`git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/ABRIR_CASO_B.sh`**. Genera `~/OpenFOAM/C3D05_B_C14_PARAVIEW_REVIEW/OPEN_IN_PARAVIEW/CASE_B_C14_10S.foam`, con los **101 directorios temporales** de ambas regiones enlazados a campos originales y los CSV disponibles en `RESULTADOS_CSV`; abre ParaView si está instalado. **No ejecuta foamMultiRun, wmake, unit tests ni reescribe CFD**. La ventana ParaView en la WSL del usuario **aún no ha sido verificada**. Conservación, QuickCup/JMatPro, convergencia y contracción todavía pendientes; hitos científicos **2/7**. [Instrucciones de revisión](docs/granada/C3D05_B_C14_ENTREGA_PARA_REVISION_MANUAL_PARAVIEW_20261124_ES.md).

> **24-11-2026 | C3D05-B C14: 9/9 pruebas WSL de disponibilidad energética PASSED; siguiente análisis de masa real `rho/phi` implementado, NO ejecutado.** El original 101 tiempos conserva `metal/T,U,p,p_rgh,alpha1` 101/101, `metal/rho,phi` 100/101, **metal `h/he` y molde `e/he/rho` 0/101**. Integral exterior de q guardado cada 0.1/0.2/0.5/1.0s: **1341.507907 / 1335.070047 / 1315.842351 / 1284.197812 J** (sensibilidad del muestreo, **NO estimación de error contra Δt CFD 0.001s**). Comparación ΔEref+qext **−11.436294 J** no es fuga ni residual de conservación. NUEVO `analyze_existing_case_b_c14_metal_mass_phi.py` y **11 pruebas fuente**, solo lectura: masa del hierro con densidades nativas `rho_i`, `alpha1` ponderada por masa, lectura por parches y unidades kg/s de `phi` si es accesible, sin inventar `t0` ni flujo cero, sin repetir CFD; todavía falta ejecución WSL. **Caso B etapa 3/7, 2/7 hitos cerrados (29%)**. [Bitácora y comando](docs/granada/C3D05_B_C14_WSL_READINESS_CONFIRMADA_Y_MASA_RHO_PHI_20261124_ES.md).

> **24-11-2026 | Caso A: WSL VISUALIZATION_AND_SOLIDIFICATION_READY, 101 estados, 29 campos comunes del metal, 21 familias postProcessing. T media metal 1450.709 K, fracción sólida volumétrica 0.1027550 a 10s, pico latente nominal 1038.8813 W a 7.2–7.3s, velocidad máxima guardada 0.0253385 m/s a 2.8s. Original intacto. Etapa08 operativa cerrada; etapa09 en curso, 8/10=80% hitos. Caso local C3D04_A_C14_VISUALIZATION_01/C3D04_A_C14.foam disponible; apertura gráfica no observada. No repetir CFD base ni diagnósticos; no pedir pruebas unitarias manuales. Conservación discreta, sensibilidad malla/tiempo y QuickCup pendientes.** [Evidencia](docs/C3D04_A_STAGE08_SOLIDIFICATION_REAL_20261124_ES.md).

> **24-11-2026 | C3D05-B: CRUCE REAL 101-TIEMPOS DE q(t) E INVENTARIO COMPLETADO EN WSL (12/12 pruebas)**. SHA del CFD original coincide; `∫q_out` por trapecio de los estados guardados 0.1s: metal→interfaz **+20283.452365 J**, molde→interfaz **−20283.567649 J** (neto bilateral **−0.115283 J**), metalTop **+1212.095291 J**, exterior molde **+129.412616 J** (total exterior **+1341.507907 J**). ΔEref combinada **−1352.944201 J**; comparación exterior `ΔEref + ∫q_exterior ≈ −11.436294 J` (**0.8525 % del exterior**), **NO es fuga ni residual de conservación**. Separación parcial metal **−181.048491 J**, molde **+169.496914 J** (tampoco residuales). NUEVO script `audit_existing_case_b_c14_energy_closure_readiness.py` + **9 pruebas fuente** para disponibilidad real de `h/e/rho/phi` durante 101 estados, desglose por región y sensibilidad del trapecio a submuestreo 0.1–1.0s; **no ejecutado aún en WSL**, no usa solver/compilador. La verdadera conservación necesita términos fuente `fvModels`, entalpía/advección/presión, BC externas, integral a dt solver 0.001s y QuickCup/JMatPro. G3-G7 abiertos; Caso B **3/7, 2/7 hitos (29%)**. [Evidencia y siguiente orden WSL](docs/granada/C3D05_B_C14_CRUCE_101_ESTADOS_CONFIRMADO_Y_AUDITORIA_TERMINOS_20261124_ES.md).

> **24-11-2026 | Caso A etapa 08/10, 7/10=70% hitos:** WSL real bilateral nativo 101 tiempos, 808 registros, 2496 pares de caras. Residuo nominal combinado 0.13051585053227654 J (0.1–10 s), interfaz integrada 0.40969414092978695 J. Original intacto. Hito operativo 07 cerrado; conservación discreta, independencia y QuickCup no verificados. NO repetir CFD ni postproceso agrupado. Publicador de visualización y solidificación listo en código; ejecución WSL pendiente. El investigador solicita entrega funcional directa: NO imponer pruebas unitarias manuales ni micropruebas antes de abrir resultados. [Evidencia y comando](docs/C3D04_A_STAGE07_BILATERAL_Q_COMPLETE_20261124_ES.md).

> **24-11-2026 | C3D05-B: FLUJOS CONDUCTIVOS REALES C14 F14 101/101 YA EXTRAÍDOS, 14/14 pruebas WSL PASSED.** Caso sombra q-only armónico `interpolate(kappa)` sin modificar CFD. A 10s: `q_out(metal→mold)=+1581.564663 W`, `q_out(mold→metal)=−1581.538327 W`; desajuste global `+0.0263364314 W` (**8.326×10⁻⁶ relativo**) y desacuerdo absoluto **1.870336 W por suma de caras**, **12,636 pares de caras**, normales opuestas y áreas iguales; salida metalTop `+117.062925 W`, salida molde exterior `+34.386288 W`, total exterior `+151.449213 W`. Fuente: WSL original 101 tiempos y 4 parches, NO `foamMultiRun`. **NUEVO** código `compare_existing_case_b_c14_native_q_and_storage.py` + **12 pruebas fuente** (aún no WSL) para cruzar SHA de q 101 tiempos con inventarios de metal/arena y aproximar trapecios de `q(t)` de 0.1s; salida aislada, **NO cierre de energía**. Original dt solver 0.001s; `fvModels`/advección/trabajo/condiciones externas/QuickCup/JMatPro y contracción pendientes. G3–G7 siguen abiertos; Caso B **3/7, 2/7 hitos**. [Bitácora y nueva orden WSL](docs/granada/C3D05_B_C14_FLUJOS_NATIVOS_101_ESTADOS_Y_CRUCE_ENERGETICO_20261124_ES.md).

> **24-nov-2026 | Caso A WSL: 101×80 ambos perfiles verticales interiores; residuo nominal metal 2.023 J.** 5/5 nuevas regresiones PASS. x=20 mm, z=8.29925 mm; y=-14.750105 a -0.050399 mm, tramo de 14.699706 mm (NO altura 2D equivalente). 0.1–10 s: ΔH metal=-12991.100 J, Δinventario latente=-7677.0344 J, Δinventario arena=19318.5479 J; calor metal→arena=19462.8944 J, exterior superior=1207.2631 J, total=20670.15745 J, advección neta cero. Residuo nominal 2.02303355 J; diferencia contacto menos inventario arena=144.34652 J NO pérdida exterior medida. Hashes intactos. Nuevo extractor bilateral nativo 8 parches y 2496 caras por lado, 4 regresiones añadidas; compilación/ejecución NO observada. **Etapa 7/10; 6/10=60 % hitos**, conservación discreta y QuickCup pendientes. [Estado](docs/C3D04_CASE_A_STATUS.json).

> **24-nov-2026 | Caso A REAL WSL: recuperación agrupada 7/7 sin FATAL, cinco series 101/101.** QA Python 5/5 PASS; selección `cellZone all` sólo en copia aislada (8960 celdas), entalpía a 0/0.1/10 s idéntica a resultados independientes a precisión de tabla (324845.2/324518.7/311527.6 J). Potencias totales salientes a 10s: top 117.2792 W, contacto 1524.644 W, total 1641.923 W; discrepancia relativa máxima suma vs total 4.7503433312219475e-7. **No balance global.** 7/9 perfiles finales completos; los dos verticales siguen en 27/80. Original y controlDict intactos. Se publicó continuación integrada de inventario de energía metal/arena y muestreo nativo vertical de cuerda interior en coordenadas x/z fijas, con auditoría 101×80 y cinco regresiones nuevas (no ejecutadas todavía). NO confundir cuerda interior con perfil 2D completo; no repetir CFD ni siete grupos. **Etapa 7/10, 6/10=60 % hitos.** [Estado](docs/C3D04_CASE_A_STATUS.json) · [Continuación](cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/continue_c14_stage07_grouped_evidence.py).

> **24-nov-2026 | Caso A — recuperación multitemporal agrupada implementada.** Nueva copia aislada con `cellZone all` exclusivamente en su `fvModels`, tras verificar conjunto exacto de 8960 celdas, SHA del original y referencias reales WSL. Gate de entalpía nativa 0/0.1/10 s frente a los tres resultados independientes existentes; si pasa, siete grupos recorren todos los 101 tiempos, sin lanzar un proceso por tiempo ni repetir CFD. Auditoría de FATAL, ejes/filas, potencias, perfiles y hashes; cinco regresiones añadidas, ejecución WSL/resultado CI no observados. No se cambió el CFD original, no se recupera ddt de 0.001 s ni se garantiza el perfil vertical o conservación. **Etapa 7/10, 6/10=60 % hitos**. [Ejecutor](cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_grouped_native_recovery.py).

> **24-nov-2026 | Caso A: WSL real confirma fallo multitiempo**. `metalSensibleEnthalpy` individual en 0/0.1/10 s: 3/3 PASS, 0 FATAL y una fila nativa cada uno; combinado: dos FATAL `Cannot find cellZone metal`, solo fila t=0. No se repitió CFD y controlDict intacto. No se ha probado causa C++ específica. Priorizar recuperación agrupada en copia aislada; F14 admite `cellZone all` y la zona original cubre las 8960 celdas de metal, pero la equivalencia de salida aún requiere comprobación y NO autoriza modificar la corrida original. Procesamiento independiente queda como respaldo. **Etapa 7/10, 6/10=60 % hitos; balance/QuickCup pendientes.** Fuente: stdout WSL aportado por investigador; [estado canónico](docs/C3D04_CASE_A_STATUS.json).

> **24-nov-2026 | Caso A C3D04, diagnóstico multitiempo F14:** El CFD original de 10 s y la copia _03 tienen `cellZone metal` de 8960 celdas y SHA idéntico, sin polyMesh temporal alternativo. El postprocesamiento original de 101 estados sigue fallando con 100 FOAM FATAL IO por grupo (core, energy, flow, momentum), mientras las tres tablas de potencia tienen solo t=0 y el perfil vertical tiene 27/80 puntos. Se implementó en main `probe_c14_native_f14_single_vs_multi_time.py`, que compara tres tiempos reales 0/0.1/10 individualmente y juntos en miniclones físicos nuevos con hashes originales protegidos, **sin repetir CFD**. QA nativa F14 de 27+27 celdas, run 45350869304: 0,0.001,0.002 individual y conjunto **PASS todos**; esto NO reproduce fallo genérico del bucle en sintético ni prueba arreglo V4/T02. Primer intento CI inválido por cwd /system documentado y corregido. Balance energético/QuickCup pendientes. **Etapa 7/10; 6/10 hitos, 60 %.** [Protocolo](docs/C3D04_A_STAGE07_FOUNDATION14_3TIME_LOOP_ISOLATION_20261124_ES.md).

> **24-11-2026 | CASO B: NUEVO EXTRACTOR C14 F14 REAL FLUIDO–SÓLIDO — CÓDIGO IMPLEMENTADO, WSL/COMPILACIÓN AÚN PENDIENTE.** Después de inventario metal (−13,576.3979 J), arena (+20,323.6519 J) y contenido latente líquido (−8,100.1982 J), suma referencial (−1,352.9442 J **NO** pérdida/«fuga» de calor), se publicó `c14_physics/native_flux/c3d05C14FluidSolidFlux.C` + `Make`, runner independiente `run_existing_case_b_c14_native_flux.py`, auditor `analyze_existing_case_b_c14_native_flux.py`, **8 pruebas fuente** y workflow CI para compilación OpenFOAM Foundation14. Diferencia esencial: metal=`fluidThermoThermophysicalTransportModel::q()`, arena=`solidThermophysicalTransportModel::q()`; NO confundir con extractor T0 de dos sólidos. Objetivo **101 tiempos × 4 parches** (`metal_to_mold`, `mold_to_metal`, `metalTop`, `moldOuterUnclassified`) más flujos por cara a t=10 s. Compilación/ejecución WSL **NO observadas**; todavía no existe `q` verificado, ni fuente `fvModel` ni balance de energía. Sin CFD nuevo. Caso B etapa **3/7, 2/7 hitos cerrados**. [Informe y orden WSL](docs/granada/C3D05_B_C14_FLUJO_NATIVO_FLUIDO_SOLIDO_F14_20261124_ES.md).

> **24-11-2026 | CASO B C3D05 — INVENTARIO DE REFERENCIA DE AMBAS REGIONES 101/101 CONFIRMADO EN WSL, NO BALANCE.** **8/8 tests** del molde PASSED; `sum(V_molde)=0.00010284340553162189 m³` en 178,588 celdas HEX8, discrepancia relativa `2.449027×10^-7` contra `checkMesh`. A 10s: **ΔE_sensible_molde=+20,323.651945808975 J; ΔE_sensible_metal=−13,576.397936155232 J; ΔE_latente_contenido_líquido_metal=−8,100.198210984614 J**, suma referencial **−1,352.9442013308708 J**, **que NO significa fuga de energía, error de conservación ni calor emitido verificado**. Falta **`q` nativo de `metal_to_mold`/ `mold_to_metal`, `metalTop`, `moldOuterUnclassified`, términos de flujo/fuente del solver**, además de JMatPro/QuickCup, convergencia, contracción. **No reutilizar el extractor térmico T0 de dos sólidos** como flujo C14 del metal fluido: requiere transporte de fluido original. Caso B **3/7, 2/7=29% hitos**. [Auditoría integrada](docs/granada/C3D05_B_C14_INVENTARIO_CONJUNTO_101_ESTADOS_WSL_20261124_ES.md).

> **24-11-2026 | C3D05-B: INVENTARIO REAL 101 ESTADOS METAL C14 COMPLETADO (9/9 pruebas WSL), MODELO DE ARENA EN PREPARACIÓN.** `Delta E_{sensible,metal}=-13576.397936155232 J` y `Delta E_{equivalente,solidificación}=+8100.198210984614 J` sobre **92,200 HEX8 nativos**, `alpha1_V(t10)=0.8917029860767621`. **El cambio de energía latente CONTENIDA en líquido es −8100.1982 J**, no +8100 J: hay que conservar signos. Ninguno es fuente latente integrada `fvModel` ni balance. Publicado `c14_physics/quantify_existing_case_b_c14_mold_and_combined_inventory.py` más **8 pruebas fuente**, para calcular la energía sensible de **178,588 HEX8 de arena** y solo el cambio de almacenamiento de referencia combinado, **aún NO ejecutado en WSL**. Sin solver ni alteración de CFD. G3–G7 físicos abiertos, Caso B **3/7 y 2/7=29% hitos**. [Informe científico y comando](docs/granada/C3D05_B_C14_WSL_INVENTARIO_METAL_Y_ARENA_PREPARADO_20261124_ES.md).

> **24-11-2026 | C3D05-B: MODELO C14 10s, 101 estados: `alpha1` VOLUMÉTRICO REAL confirmado.** Investigador ejecutó **8/8 pruebas** y `volume_weighted_existing_case_b_c14.py` en WSL sin solver: metal **92,200 HEX8**, 283,389 caras (269,811 internas), 106,529 vértices; `sum(Vi)=4.797539547720032e-5 m³`, discrepancia relativa **1.6145×10^-7** frente a `checkMesh`. A **t=10s**, `alpha1_V=0.8917029861`, complemento sólido V **0.1082970139 (10.8297%)**, frente a media por celdas **15.7579%**. Primer `alpha1<0.999` en tiempo guardado 0.3s, primer `alpha1=0` en 5.1s. Este cálculo NO valida calor latente, energía, propiedades QuickCup ni `dt`/malla. Código **nuevo** de inventario sensible `rho Cp Vi [T(t)-T(0)]` y *latente equivalente* `rho L Vi[alpha(0)-alpha(t)]` publicado con 9 pruebas fuente; **aún no ejecutado en WSL** y NO es balance de energía. **Caso B etapa 3/7; 2/7 hitos técnicos (29%)**. [Evidencia y límites](docs/granada/C3D05_B_C14_ALFA_V_PONDERADA_CONFIRMADA_Y_ENERGIA_INVENTARIO_20261124_ES.md).

> **24-11-2026 | Caso A C3D04, inspección WSL _03 no solucionó cellZone metal:** reporte fuente/copia SHA validado, pero cuatro subprocesos core/energy/flow/momentum acumulan 100 FOAM FATAL IO cada uno (Cannot find cellZone metal; Available cellZones 0). Phase alpha1 t10=0.897245. Tres perfiles horizontales 80 puntos finitos; vertical x20 27 puntos INCOMPLETE. Las tres potencias de frontera solo tienen una fila t=0, por lo que no hay cierre energético. No crear _04 ni procesar 101 estados a ciegas. Implementada auditoría nueva 100% read-only de metal/polyMesh/cellZones y posibles instancias temporales y SHA de geometría original, sin simulación ni sobrescrituras. **Etapa 7/10, hitos 6/10=60%**. [Reporte](docs/C3D04_A_STAGE07_03_ACTIVE_MESH_FORENSICS_20261124_ES.md).

> **24-11-2026 | CASO B C3D-05 — CRONOLOGÍA ALPHA1 REAL CERRADA Y PONDERACIÓN ESPACIAL EN DESARROLLO:** usuario ejecutó **9/9 pruebas PASSED** y cronología sobre 101 estados C14 reales; primer `alpha1<0.999` entre **0.2–0.3 s**, primer `alpha1=0` entre **5.0–5.1 s**, complemento sólido medio final **15.7579 % solo por celdas**, `Courant_max=0.267133`. Nuevo código nativo en GitHub `c14_physics/volume_weighted_existing_case_b_c14.py` para obtener **volúmenes reales por cada una de las 92,200 celdas HEX8** a partir de `points/faces/owner/neighbour` originales, cotejar contra `checkMesh`, y ponderar `alpha1` de 101 estados; ocho pruebas de geometría/regresión añadidas. **No se ha ejecutado aún en la WSL; ninguna fracción volumétrica se afirma medida.** No reejecuta CFD ni modifica mallas. G3–G7 físicos pendientes, Caso B **3/7, 2/7=29%** hitos. [Bitácora científica](docs/granada/C3D05_B_VOL_PONDERADO_ALPHA1_HEX8_Y_RESULTADOS_CRONOLOGIA_20261124_ES.md).

> **23-11-2026 | C3D04-A F14 cellZone: cuatro FATAL IO ocultos por exit0.** En la salida real WSL de _02 aparecen core/energy/flow/momentum con FOAM FATAL IO ERROR: Cannot find cellZone metal / 0() available, pese al reporte previo de 6 PASS. Pipeline nuevo clasifica FATAL independientemente de rc, y materializa zona 8960 celdas exclusivamente en copia separada _03 después de SHA de malla original. CI F14 real reproduce el fatal con exit0 y recuperación exit0 sin fatal sobre 27 celdas sintéticas. Tiempo0 de energía no se fabrica; se estudian 100/101 intervalos reales y perfiles. NO CFD original rerun ni modificación de _01/_02/B/FS. Stage 7/10 6/10 hitos=60%. [Reporte](docs/C3D04_A_STAGE07_NATIVE_METAL_CELLZONE_RECOVERY_20261123_ES.md).

> **23-11-2026 | CASO B C3D-05 — CFD C14 REAL 10 S COMPLETADO; AUDITORÍA DE ALPHA1 PREPARADA (AÚN NO CORRIDA EN WSL):** el investigador compartió el mensaje nativo `C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED` con `native_C14_F14_solver_run=true`. El C14 metal `fluid`, arena `solid`, `solidificationMeltingSource` concluyó 10 s en la malla STEP/Gmsh HEX8 real (92,200 + 178,588 celdas); **NO** repetir `--run-full`. Publicados `c14_physics/analyze_existing_case_b_c14.py` y 9 pruebas fuente/negativas para leer en **solo lectura** el log original, SHA, `T`, `phaseChangeSource:alpha1`, `p_rgh`, cruces Tliq/Tsol y el primer cambio de fase guardado, sin solver/remallado. Hasta ejecutar este análisis **NO se sabe el resultado de alpha1(t)**; no se ha verificado calor latente, energía, JMatPro/QuickCup ni convergencia. **Caso B etapa 3/7, 2/7=29 % hitos técnicos.** [Informe](docs/granada/C3D05_B_C14_10S_CFD_REAL_COMPLETADO_Y_ANALISIS_SOLO_LECTURA_20261123_ES.md).

> **23-11-2026 | Caso A WSL: `_02` ya existe; inspección SIN sobrescritura:** la segunda invocación del pipeline nativo terminó en preflight `new isolated copy output occupied`. No hubo CFD, ni copia, ni `foamPostProcess` en esa ejecución. Se desconoce si la carpeta `_02` corresponde a intento terminado/parcial/activo; no borrarla ni ejecutar automáticamente `_03`. El ejecutor actualizado inspecciona solo lectura y verifica el informe final, seis códigos de salida y SHA de logs y fuentes; si es parcial, conserva y reporta sin asumir éxito. Etapa 7/10, 6/10=60% hitos. [Procedimiento](docs/C3D04_A_STAGE07_F14_SOLVER_BACKED_NATIVE_RECOVERY_20261123_ES.md).

> **23-11-2026 | GRANADA C3D04-A — FATAL rho NATIVO DIAGNOSTICADO, RECUPERACIÓN -solver fluid EN COPIA NUEVA:** forense real WSL: `c14_functions` (solo) falló `Field rho not found in database`. Además, tres campos energía advectiva/difusiva/total no estaban en registry y faltaban 14 familias C14, 20 campos derivados, 5 perfiles. No son fallos probados de la CFD original, ya preservada 101 estados. Con manual F14 se usa `foamPostProcess -solver fluid -region metal` para modelos termo sin avanzar solver; se separan grupos core/energy/phase/flow/profiles/momentum y se conserva vieja workcopy. Nuevo código `run_c14_stage07_solver_backed_recovery.py` atestigua SHA del CFD y de forense, copia física aislada nueva y reporte de 6 subprogramas, siempre sin conservación/QuickCup ficticios. CI Python + smoke nativo F14 sobre 27+27 sintético no es malla V4/T02. **No WSL del nuevo recovery todavía, etapa 7/10, 6/10=60 % hitos.** [Reporte](docs/C3D04_A_STAGE07_F14_SOLVER_BACKED_NATIVE_RECOVERY_20261123_ES.md).

> **23-11-2026 | GRANADA CASO A C3D04 / C14 — EVIDENCIA REAL 101 SNAPSHOTS Y CAUSA NATIVA ABIERTA:** WSL investigador ejecutó recuperador en worktree A, `NEW_101_STATE_DIAGNOSTIC_PUBLISHED_NO_CFD`; CSV+JSON volumétricos anteriores existentes y válidos. Fracción líquida modelo alpha1 primer descenso guardado t=0.3s (0.2–0.3s), potencia latente nominal discreta máximo 1038.8813W de t7.2–7.3s, metal `<T>_vol` al final 1450.7091627651344K e inventario sólido nominal 0.03358283580064463 kg. Reporte original native SHA del CFD verificó procedencia, **pero `native_commands_verified=false`**: no afirmar paridad nativa, conservación o validación. Implementado informe read-only conjunto de códigos reales de subprocesos, logs F14, familias/campos/perfiles y diagnóstico energético metal-only con SHA e idempotencia. Las dos funciones `ddt` C14 no recuperan historia 0.001s desde 0.1s; no fingir recalescencia. No correr solver, no modificar A original/B/FS. **Etapa 7/10, 6/10=60% hitos.** [Informe](docs/C3D04_A_C14_NATIVE_101_STATES_REAL_FORENSICS_20261123_ES.md).

> **23-11-2026 | GRANADA C3D04-A ETAPA 07: RECUPERACIÓN SIN REPETICIÓN NI BORRADO:** el investigador confirmó directorios existentes de análisis 101-state y native postProcessing workcopy de Caso A mediante terminal. El runner antiguo exigía destinos nuevos y habría bloqueado. Incorporado analizador read-only de origen SHA, 101 T/alpha1 ponderados por volumen, bracketing de primer estado bajo Tliq/Tsol y primer alpha1 decreciente, inventario sólido nominal rho V (1-alpha), derivadas discretas Δt_saved=0.1s, energía latente y tasas de almacenamiento estimadas, más diagnóstico sin escritura de copia nativa C14. Sin reconstruir 10,001 sondas, CFD 10s, remallado, ni validación de energía/QuickCup. Nuevo reporte JSON+CSV en carpeta aislada, no sobrescribible. **Código y QA sintética; ejecución WSL nueva aún pendiente. Etapa 7/10; 6/10=60% hitos.** [Informe](docs/C3D04_A_STAGE07_FORENSIC_KINETICS_20261123_ES.md).

> **23-11-2026 | SEGURIDAD DE TRES SIMULACIONES CONCURRENTES — AISLAMIENTO A/B/FS:** Contracción mantiene rama research/fs-c02-metal-air-vof-20261117 en FS_C02_WORKTREE; A y B dispondrán de worktrees sin upstream, sin checkout ni pull del MasterProject principal y sin tocar carpetas externas de ejecución. Instalador fail-closed y pruebas de Git real con centinelas de CFD y rechazos de rutas/ramas. **CI validada, instalación real WSL todavía pendiente de evidencia; no supone avance en A 6/10=60 %, B 2/7=29 % ni contracción.** Ver docs/WSL_CONCURRENT_CASE_WORKTREES_20261123_ES.md.

> **23-11-2026 | CASO B C3D-05 — FIX DEL ARRANQUE FOUNDATION14, NO CFD EJECUTADO:** primer intento WSL de `run_case_b_c14_native.sh --run-full` abortó en `/opt/openfoam14/etc/bashrc: line 46: ZSH_NAME: unbound variable` por `set -u` de nuestro wrapper antes de cargar la configuración oficial. **Ningún Python materializador, malla copiada ni foamMultiRun se ejecutaron.** Corregido: `set +u` exclusivamente durante `source bashrc`, luego `set -u`; añadido `bash -n` y regresión shell con `ZSH_NAME` sin definir (CI aún no verificado). Estado Caso B **3/7; 2/7=29% hitos técnicos**, G3–G5 físicos abiertos. [Bitácora de causa y reparación](docs/granada/C3D05_B_C14_SOLIDIFICACION_3D_FASE_FISICA_20261123_ES.md).

> **23-11-2026 | CASO B C3D-05 — ADAPTACIÓN REAL DE FÍSICA C14 FLUIDO/SÓLIDO A 270,788 HEX8 (SIN CFD B NUEVO):** implementado `c14_physics/stage_c14_3d_case_b.py` y `run_case_b_c14_native.sh` para materializar/ejecutar una copia **AISLADA** de la malla STEP/Gmsh B con el **C14 original 2D**: hierro `fluid/heRhoThermo/hConst/enthalpy` con `U,p,p_rgh,solidificationMeltingSource/alpha1/L`; molde `solid/heSolidThermo/eConst`; `controlDict` idéntico (`10 s, dt=0.001 s`). Adaptaciones geométricas documentadas y verificadas: **5 BC exteriores idénticas de C14 A→1 `moldOuterUnclassified` B**, `pRefPoint`→`pRefCell 0`, `cellZone metal`→92,200 celdas solo sobre COPIA. Incluye fuente de **8 pruebas** y workflow CI estático (no CFD); **no hay evidencia aún de CI verde, materialización WSL ni run de solidificación B**. Caso B **etapa 3/7, 2/7=29 % hitos técnicos**; G3/G4 físicos/JMatPro/QuickCup y G5 fase/latente sin validar, 1,826 caras noort severas. No tocar la corrida T0 C14 ya concluida, no remallar. [Informe](docs/granada/C3D05_B_C14_SOLIDIFICACION_3D_FASE_FISICA_20261123_ES.md).

> **23-11-2026 | CASO B C3D-05 — DATOS ESPACIALES Q REALES EN WSL (NO NUEVO CFD):** ya terminó `analyze_existing_t0_spatial.py` con `C3D05_B_SPATIAL_NATIVE_Q_PUBLISHED_NOT_PHYSICALLY_ACCEPTED`: **12,636 pares de caras, 6 tiempos, 12 bandas Y** y archivos nuevos con SHA. Potencia saliente del metal **31.964 kW a 0.02 s → 19.248 kW a 0.10 s**, con `q(t0)=0` en campo guardado; potencias reciprocas de molde. La integral trapezoidal de **solo 6 q** ≈**2262.98 J**, frente a ≈**2640.70 J** cedidos por metal a partir de las T medias redondeadas: desfase aproximado **14.3 %**, dominado por el primer intervalo 0–0.02 s. **NO interpretar como fuga energética del solver:** submuestreo temporal y condiciones iniciales deben analizarse. Malla HEX8 original, solver y parámetros inmutables. **G3/G4 físicos abiertos, etapa 3/7; 2/7=29 % hitos técnicos, NO tesis.** [Nuevo informe](docs/granada/C3D05_B_Q_ESPACIAL_REAL_6_TIEMPOS_Y_CONTRASTE_ENERGIA_20261123_ES.md).

> **23-11-2026 | CASO B C3D-05 — GRANADA Q ESPACIAL (SIN REEJECUTAR CFD):** el T0 numérico C14 de dos sólidos sobre **270,788 HEX8**, con 12,636 caras acopladas por lado, energía y expediente SHA ya estaba completo. Publicado `scripts/analyze_existing_t0_spatial.py` (Python solo lectura) y `tests/test_existing_t0_spatial.py`: audita de nuevo la cadena SHA original, empareja geométricamente las caras y sus tiempos, distribuye `q` en **12 bandas Y** y exporta nube de centros de cara en **metros para ParaView** con potencias e irregularidades de flujo, más manifiesto SHA transaccional en directorio nuevo. **CÓDIGO publicado, WSL y CI aún NO verificados en este turno; no son resultados espaciales medidos ni física de solidificación.** Caso B **etapa 3/7; 2/7=29 % hitos técnicos**, G3/G4 físicos abiertos por JMatPro/QuickCup, condiciones reales y sensibilidad a 1,826 caras no ortogonales. [Plan y guía](docs/granada/C3D05_FLUJO_ESPACIAL_Y_PUERTA_FISICA_20261123_ES.md).

> **20-11-2026 | CASO B C3D-05 — T0 C14 REAL COMPLETADO EN WSL:** el investigador ejecutó las seis fases de Granada **sin repetir solver, C++ de q ni reconstruir HEX8** sobre **270,788 celdas reales**. Reauditoría SHA `RUN_REPORT_EXISTS_IDENTICAL`, seis promedios regionales metal **1500→1490.2409 K**, molde **300→324.45414 K**; `max|ΔE|/Qref=4.320292500161304e-8`. Reutilizó CSV nativos, **12,636 pares geométricos de interfaz por lado** y obtuvo discrepancia relativa agregada máxima `1.8239733799046786e-16`; publicados `T0_NATIVE_FACE_FLUX`, `T0_GRANADA_EVIDENCE_SUMMARY.json` (SHA) y marcador `.foam` ParaView. **FINALIZADO SOLO DIAGNÓSTICO NUMÉRICO C14 de dos sólidos**; `G3/G4` FÍSICOS abiertos, sin JMatPro/QuickCup ni sensibilidad de no ortogonalidad. **Etapa 3/7 · 2/7=29 % hitos técnicos, NO tesis.** [Evidencia](docs/granada/C3D05_WSL_T0_NUMERICO_COMPLETO_270788_HEX8_20261120_ES.md).

> **20-11-2026 | CASO B C3D-05 / WSL REAL ENERGÍA Y Q:** recuperación SHA de corrida C14 `foamMultiRun` sobre **270,788 HEX8** PASÓ sin repetir solver; `foamPostProcess` nativo: metal **1500→1490.2409 K**, molde **300→324.45414 K** entre 0–0.1 s (6 tiempos), discrepancia relativa máxima de energía **4.320292500161304e-8** solo diagnóstica. `wmake` y extractor C++ `q()` **terminaron realmente en WSL** para 12,636 caras por región; comparador Python falló por igualdad exacta de tiempos `%.17g` (CSV) vs JSON. Integrado emparejamiento cronológico biyectivo con tolerancia de representación limitada, regresiones negativas y reutilización de carpeta CSV temporal completa sin repetir q ni solver. **Aún no aprobada comparación q cara-cara, SHA final, JMatPro/QuickCup ni independencia de malla: G3/G4 ABIERTOS, etapa 3/7 · 2/7=29% hitos técnicos, NO tesis.** [Informe](docs/granada/C3D05_WSL_T0_ENERGIA_REAL_Y_TIEMPOS_Q_20261120_ES.md).

> **20-11-2026 | CASO B C3D-05 — SEGUNDA REENTRADA WSL / FIRMA F14 OFICIAL:** la continuación reutilizó entradas, malla y log originales **sin repetir `foamMultiRun`**, pero la revisión SHA quedó bloqueada antes de T/energía/q. Se identificó un segundo error en el parser: el encabezado real Foundation14 es `sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).` (con prefijo y punto), no la variante abreviada del fixture. Corrección fuente + regresión del formato auténtico + `audit_failure_reasons` y líneas fatales específicas en caso de nuevo rechazo. **NO se ha repetido solver ni validado conservación, q/JMatPro/QuickCup. Etapa B 3/7, 2/7=29 % hitos técnicos; G3/G4 abiertos.** [Detalle](docs/granada/C3D05_WSL_T0_270788_AUDITOR_RECOVERY_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_WSL_REAL_HEX8_AUDITOR_RECOVERY — CASO B:** el investigador compartió consola de **foamMultiRun F14 sobre 270,788 HEX8 reales** (metal 92,200; molde 178,588; 12,636 contactos/lado): solucionó `e` en ambas regiones, llegó a `Time = 0.1s` y `End`. El **exit=6 provino del auditor**, que rechazaba el sufijo `s` y confundía el banner normal `Enabling floating point exception trapping (FOAM_SIGFPE)` con una excepción real. Corregidos ambos parsers, creados regresiones y **revisión SHA separada** `T0_NUMERICAL_RUN_STATUS_REVIEWED.json`, preservando log e informe originales y continuando postpro T/energía/q **sin repetir foamMultiRun**. Aún **NO observados T/energía/q de la malla real**, log íntegro SHA no verificado, ni JMatPro/QuickCup/independencia; **G3/G4 ABIERTOS, etapa B 3/7 y 2/7=29 % técnico, NO tesis**. [Registro](docs/granada/C3D05_WSL_T0_270788_AUDITOR_RECOVERY_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_SOLVER_MAPPEDWALL_20261120 — CASO B / VERIFICACIÓN DEL SOLVER NATIVO:** `foamMultiRun` real OpenFOAM Foundation14 **100 pasos** (`dt=0.001 s`, `endTime=0.1 s`) sobre **2 sólidos sintéticos de una sola celda HEX8 cada uno** con `mappedWall` y `coupledTemperature` recíprocos usando los 10 diccionarios **originales** del T0 y valores archivados C14. Observadas 6 muestras regionales por `foamPostProcess`: metal **1500→1499.2 K**, molde **300→304.29709 K**, transferencia en dirección correcta. El análisis de energía productivo reportó **`max|ΔE|/Qref=2.63001153e-7`**, sin declararlo tolerancia física. **CI Foundation14 PASS** [#44841034109](https://github.com/michels-lab/MasterProject/actions/runs/44841034109). **Ningún CFD en 270788 HEX8 de la WSL, sin q de 12636 pares reales ni JMatPro/QuickCup; G3/G4 abiertos. ETAPA B 3/7, 2/7=29% hitos técnicos, NO tesis/CFD validado.** [Informe](docs/granada/C3D05_F14_CHT_DOS_SOLIDOS_SMOKE_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_POSTPROCESS_REAL_20261120 — CASO B, GRANADA INTEGRADA:** verificación **NATIVA REAL Foundation14** `foamDictionary` **10/10** sobre los diccionarios T0 de producción; `blockMesh` de 2 cubos sintéticos de 1 celda y `foamPostProcess` por región con `volFieldValue`: metal **1 m³/400 K**, arena **1 m³/300 K** y lectura real de `volFieldValue.dat` [CI PASS #44830571389](https://github.com/michels-lab/MasterProject/actions/runs/44830571389). Detectado y corregido en origen **ERROR `region0`**: cada `functionObject` debe tener `region metal/mold;`, no basta `foamPostProcess -region`. El análisis real de energía ahora EXIGE `t=0` observado y temperaturas iniciales congruentes. Granada `--solve` añade fase **6/6** que genera `T0_GRANADA_EVIDENCE_SUMMARY.json`: trazabilidad SHA de log/entradas/campos/12,636 caras, máximo residual energético y desajuste local, sin promover aceptación física; test negativo añadido. **C++ de q ya compilado realmente en F14 en CI #44828749324**, pero **NO se ejecutó la malla real en WSL, ni se validó CFD/QuickCup/JMatPro**. Caso B **ETAPA 3/7, 2/7 hitos=29% técnico, NO tesis**; G3/G4 ABIERTOS. [Informe](docs/granada/C3D05_F14_POSTPROCESS_SMOKE_Y_EVIDENCIA_UNICA_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_F14_REAL_COMPILER_20261120 — GRANADA C3D-05/B / COMPILADOR REAL:** OpenFOAM Foundation14 Ubuntu24 instaló paquete oficial, ejecutó `wmake` sobre extractor C++ bilateral de 12,636 caras, comprobó `ldd` y prueba de arranque `-help`: **PASS** [#44828749324](https://github.com/michels-lab/MasterProject/actions/runs/44828749324). Se repararon por causa raíz los errores C++ de API detectados por ese compilador (`fvCFD.H`, `fvMesh::boundaryMesh`, `polyBoundaryMesh::findPatchID` -> `findIndex`). Publicación de evidencia ahora ATÓMICA con los 2 CSV, diagnóstico, log y SHA, con regresión sintética 12,636 pares **PASS** [#44828766415](https://github.com/michels-lab/MasterProject/actions/runs/44828766415). **NO compilado ni ejecutado en WSL del investigador; NO hay CFD, balance real ni flujo cara-cara validado. ETAPA 3/7; 2/7 hitos=29% técnico, NO tesis.** [Auditoría](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D05_F14_WMAKE_REAL_20261120_ES.md).

> **20-11-2026 — C3D04-A PR54 16TEST NATIVEVOLUME FALLBACK. ETAPA 6/10, AVANCE 5/10=50 % Hitos.** El preflight de conducción T0 sobre V4/T02 tenía una dependencia implícita de `PILOT_MESH_REPORT.tsv`, cuya presencia no está garantizada. [PR #54](https://github.com/michels-lab/MasterProject/pull/54) fusionada `fdae7d256002431f878a265fa637bc43183de750`: si falta el TSV, se calcula volumen de cada región por integral de caras orientadas **de `polyMesh/points`, `faces` y conteo `neighbour`**, sin usar CAD ni valores inventados. Si hay TSV se exige coherencia de fuente/celdas/`mesh_ok`; el checkMesh nativo previo continúa como puerta. **16/16 tests** integrados (run `44826436332`, cubos sintéticos, orientación inversa y ausencia de TSV), **10/10 archivos interpretados por OpenFOAM14 nativo** (run `44826436229`, artifact `14673438862`), contrato y auditoría científica OK. [Evidencia reproducible](reports/case-a-t0/CI_STAGE06_VOLUME_FALLBACK_20261120.json). **No corrida CFD ni preflight de malla real en WSL**; avance permanece 50 % hasta cerrar etapa 06 con evidencia local. V4/T02 y C14 preservados; una sola ejecución integral para el investigador, no micropruebas.

> **20-11-2026 — GRANADA C3D04-A OF14 REAL CI 10DE10 20NOV26: ETAPA 6/10, AVANCE 5/10 = 50 % Hitos.** Por primera vez el paquete C14→T0 de Caso A superó **OpenFOAM Foundation14 nativo**: `foamDictionary` interpretó **10/10** diccionarios generados en Ubuntu24.04 GitHub Actions, artifact ID `14674730228` (run `44825262805`), **15/15 pruebas** integradas de CI (run `44825262837`), contrato (run `44825262666`) y auditoría QuickCup (run `44825262677`) PASS. [Reporte científico auditable](reports/case-a-t0/CI_NATIVE_F14_20261120.json). [PR #53](https://github.com/michels-lab/MasterProject/pull/53) fusionada `718bb48167d58218b344cad6eb169fef198b8dbf`. Se añadió la protección Ubuntu 26.04 para que `/opt/openfoam14/etc/bashrc` se cargue con `HWLOC_COMPONENTS=-gl` y solo una vez (evita pvdataserver hang). **CI no tenía el `polyMesh` real V4/T02, y `foamDictionary` no instancia BC ni ejecuta energía**; por ello se cierra solo diseño (hito 05) y se abre hito 06 de preflight WSL en un único bloque integral. **NO CFD/solidificación**; originales V4/T02, C14 y Caso B intactos. Estado persistente + [tracker CSV](docs/C3D04_CASE_A_MILESTONE_TRACKER.csv).

> **20-11-2026 | GRANADA_C3D05_PATCH_Q_12636_20261120 — CASO B / GRANADA FLUJO DIRECTO:** se añadió un extractor C++ `c3d05PatchFlux` basado en `solidThermophysicalTransportModel::q()` Foundation14, cargando SIMULTÁNEAMENTE metal y molde para `mappedWall/coupledTemperature`. Lee `q_n=-k snGrad(T)` nativo por **12,636 caras de cada lado**, centros/áreas/normales, y empareja geométricamente sin asumir índice compartido; cuantifica balance neto y `Σ |q_m A_m + q_a A_a|` para revelar errores locales que se cancelan globalmente. Controles anti-NaN, tiempo, geometría, SHA y no-sobrescritura; ejecutor `run_c14_numerical_granada.sh --solve` integra compilación aislada `wmake`, extracción bilateral y postprocesamiento tras energía volumétrica. **CÓDIGO IMPLEMENTADO, C++ NO COMPILADO NI CORRIDO EN WSL; resultados CFD/flujo/validación NO EXISTEN.** Caso B **ETAPA 3/7, 2/7 hitos=29% TÉCNICO, NO TESIS**, G3/G4 abiertos. [Reporte](docs/granada/C3D05_T0_FLUJO_INTERFAZ_12636_CARAS_20261120_ES.md).

> **20-11-2026 | GRANADA_C3D05_NATIVE_ENERGY_20261120 — CASO B GRANADA T0:** `foamPostProcess` Foundation14 por región con `volFieldValue(cellZone all,volAverage(T))` incorporado al mismo `run_c14_numerical_granada.sh --solve`. Usa campos T realmente escritos, ρCv y volúmenes del checkMesh aceptado para cuantificar E metal/molde, desviación de energía total e intercambio efectivo temporal, con controles SHA del log, tiempos, NaN y volumen. Un solver ya finalizado puede reutilizarse SIN rerun. **CI Python/Bash aprobada; NO corrida WSL ni energía validada**; tasas de energía NO son flujo directo por caras de interfaz. **Etapa B 3/7, 2/7 hitos=29% técnico, NO tesis/CFD**; G3/G4 abiertos. [Informe científico](docs/granada/C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md).

> **20-11-2026 — GRANADA C3D-04 20NOV26 CI 14-TEST PASS PR52. CASO A ETAPA 5/10, AVANCE 4/10 = 40%.** Corrigido un defecto real del T0: el modo `--preflight` devolvía **0 con configuración inválida**; ahora retorna código **3** antes de leer `polyMesh` y sin producir caso. CI reveló otro fallo: el test de materialización sintética con malla ficticia llamaba por segunda vez a `patch_area`, lo que confundía datos de preflight con geometría falsa. Se eliminó la lectura duplicada **en la causa**: `thermal_network_budget` se calcula una vez en el preflight de geometría nativa y se transfiere al materializador como evidencia tipificada; sin evidencia, se aborta antes de crear carpetas. Tras correcciones, **14/14 pruebas T0 pasaron**, además de la auditoría científica QuickCup y contrato de entregas del proyecto; 3 workflows GitHub Actions **success**. [**PR #52 fusionado**](https://github.com/michels-lab/MasterProject/pull/52) squash `78406c5bf17193b7807a3dc73e1d8ab3a4240ea4`. [**Evidencia CI verificable por IDs de corrida**](reports/case-a-t0/CI_GRANADA_20261120.json). **No se ha corrido OpenFOAM 14 en WSL, ni CFD, ni independencia de malla, ni validación de QuickCup 3D.** Preservados C14 y V4/T02; progreso sin inflar. No solicitar una orden por cada pieza.

> **19-11-2026 | GRANADA_C3D05_C14_NUMERIC_SHK_20261119 — OP GRANADA CASO B, CÓDIGO OPERATIVO:** paquete integrado C14→T0 de referencia NUMÉRICA (fuentes C14 SHA-256, hierro ρ=6820, Cp=827 aproximado explícitamente como Cv, k=Cp·μ/Pr, sílice ρ=1500/Cv=700/k=2, T=1500/300 K); 100 pasos de 0.001 s, caso independiente y comando único opcional `--solve` en WSL. Incluye generación idempotente, revisión nativa de 10 diccionarios, objetivo teórico de energía calculado desde volúmenes reales `checkMesh` y auditoría del log de `foamMultiRun` que NO confunde ejecución con conservación. Corregido también el fallo histórico de registro científico: los `THREE_D_*` se resuelven como carpetas bajo `cases_3d`, sin ascender estados a CFD; regresión en CI. **ETAPA B 3/7, 2/7 hitos = 29 % técnico, NO tesis.** Código publicado y pruebas estáticas; SIN corrida WSL, SIN validación JMatPro/QuickCup, SIN cierre G3/G4. CAD/C14/malla HEX8 intactos. [Informe completo](docs/granada/C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md).

> **19-11-2026 — OPERACIÓN GRANADA C3D-04 CASO A, ETAPA 5/10, AVANCE 4/10=40%.** Revisión de T0 contra referencia oficial Foundation14: la BC histórica C14 `externalWallHeatFluxTemperature` se transpone a `externalTemperature` F14, preservando h=10 W/m²K, Ta=300 K, emisividad 0.3/0.5 en seis paredes activas 3D y contacto `coupledTemperature` con capa de 0.2 mm / k=0.1 W/mK (h=500 W/m²K). Guard de fuente ampliado: SHA-1 de los ocho Git blobs C14 originales y comparación de 27 valores/capas; tests de corrupción de fuente. Se integraron áreas nativas de cada pared y de ambas interfaces V4/T02, conductancias y potencias iniciales de contacto/convección/radiación calculadas como **estimaciones de superficie uniforme, NO flujos CFD**; tests positivos/negativos en la misma suite, sin ejecutar solver ni modificar malla. **CI y F14 WSL NO ejecutados/observados; avance no inflado.** [Manual](cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md) · [Estado](docs/C3D04_CASE_A_STATUS.json).

> **19-11-2026 — C3D04 C14 VALORES PORTADOS SIN INVENTAR · ETAPA 5/10, AVANCE 4/10 = 40 % DE HITOS.** Por indicación explícita del investigador se abrió el caso base de repositorio `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef` y se comprobaron los materiales originales: `metal/materials/castIron` `rho=6820 kg/m³`, `Cp=827 J/kgK`, `molWeight=56`, `mu=5.5e-3`, `Pr=.14`, `T0=1500 K`; `mold/materials/silica` `rho=1500`, `Cv=700`, `kappa=2 W/mK`, `molWeight=28`, `T0=300 K`. `0/metal/T` y `0/mold/T` aportan convección externa `h=10`, `Ta=300`, emisividad 0.3/0.5 y acoplamiento de interfaz de capa `0.0002m` /`kappa=0.1 W/mK` (`hcontact=500 W/m²K`). `controlDict`: `deltaT=.001`, `endTime=10`, `writeInterval=100`; `system/fvSolution` global `nOuterCorrectors=3`, `nNonOrthogonalCorrectors=1`; `system/metal/fvSolution` regional declara `nEnergyCorrectors=2`, **sin demostrar equivalencia efectiva de módulo fluid C14**. Se publicó `t0_conduction/C14_PARAMETER_BASELINE.json`, llenó `T0_INPUTS.json`, ajustó los diez archivos generados para condiciones térmicas C14 y añadió auditor integrado que reabre los originales y valida **27 parámetros/capas**, guardando SHA256 de cada fuente. **Diferencia crítica declarada:** el metal C14 original es `heRhoThermo,hConst,Cp=827,sensibleEnthalpy,fluid`; el T0 de 2 sólidos conserva `heSolidThermo,eConst` y trata `Cp` como `Cv efectivo` SOLO para ensayo numérico, y deriva `k=mu Cp/Pr≈32.4893`; no es un modelo idéntico de fundición/solidificación. El T0 con C14 h=10 ya no es adiabático; equilibrio aislado anterior se etiqueta contrafactual. Fuente V4/T02 y C14 inmutables, CFD no ejecutado; CI actual y validación WSL Foundation14 no confirmadas, hito 5 sigue abierto. [Manual](cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md) · [Estado](docs/C3D04_CASE_A_STATUS.json).

> **19-11-2026 — C3D05/B / GRANADA: fvSolution DE C14, NO PARÁMETROS INVENTADOS.** El T0 de dos sólidos ya usa parámetros fuente C14: PIMPLE global 3/2/1, relajación e/eFinal=1; PCG+DIC tol 1e-6 y relTol 0.05 de la región sólida C14 arena para los dos sólidos; nEnergyCorrectors=2 de C14 metal trasladado al control global, todavía sin comprobar su efecto nativo. La adaptación excluye p_rgh/U y deja los originales C14 intactos. Fuente versionada con SHA Git y test de correspondencia. **ETAPA CASO B 3/7 (T0); AVANCE 2/7 = 29% hitos técnicos, NO tesis/CFD.** T0 sigue sin valores físicos documentados ni materialización/solver WSL; 1,826 caras severas noortogonales siguen siendo advertencia. [Bitácora detallada](docs/granada/C3D05_FVSOLUTION_C14_20261119_ES.md).

> **19-11-2026 — CASO A C3D-04 T0 INTEGRAL: SOLUCIÓN PIMPLE RAÍZ Y MATERIALIZACIÓN ATÓMICA. ETAPA 5/10, AVANCE 4/10 = 40% DE HITOS.** Auditoría del paquete integrado antes de enviarlo a laptop: `foamMultiRun` Foundation14 requiere `system/fvSolution` **global** además de `system/metal/fvSolution` y `system/mold/fvSolution`, como demuestra el tutorial oficial `heatedDuct`. Arreglado generador: **10 diccionarios**, `nEnergyCorrectors` configurable y justificado, mismas fuentes `rho/Cv/k/T` vacías (ningún número inventado), parches C3D04 activos revisados integralmente. Detectada y corregida expresión regular de parches con escape doble; nueva regresión rechaza parches activos no modelados. Materialización independiente/atómica ahora: SHA256 fuente-copia de `polyMesh`, `foamDictionary` Foundation14 sobre carpeta temporal, publicación solo después de 10 parses correctos y sin solver. Preflight también lee TSV de volúmenes nativos T02 y prepara objetivo **analítico** de conservación del sistema adiabático (`T_eq` ponderado por `rho Cv V`), aún sin valor real mientras insumos sean nulos. Runner único y CI con pruebas sintéticas de éxito/fallo, progreso dinámico y estado científico. **Código COMMITTED, ejecución CI/WSL y CFD no demostradas, etapa 5 NO cerrada**. [T0](cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md) · [Estado](docs/C3D04_CASE_A_STATUS.json).

> **19-11-2026 | GRANADA_C3D05_T0_INTEGRAL_20261119 — GRANADA CASO B, ENTREGA DE CÓDIGO PRE-CFD:** publicado [orquestador integrado T0](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_granada.py): valida en una sola operación entradas/fuentes, estado CAD-HEX8/contacto ya documentado, copia segura del caso y 9 diccionarios Foundation14 con foamDictionary; bloquea sobrescritura, concurrentes y valores sintéticos explícitos, permite reentrada idempotente cuando SHA/resultado coinciden; **NO ejecuta foamMultiRun, Gmsh ni checkMesh**. Añadidas [regresiones sintéticas](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_granada.py), [workflow estático](.github/workflows/c3d05-t0-granada-static.yml) y [bitácora integrada](docs/granada/C3D05_T0_INTEGRATED_GRANADA_20261119_ES.md). **Estado canónico sigue ETAPA 3/7, 2/7 hitos (29% técnico, NO tesis):** faltan propiedades termofísicas auténticas y ejecución WSL, por tanto T0 no está materializado ni validado. No se repiten auditorías de malla ni se alteran los ensayos históricos.

> **19-11-2026 — CASO A C3D-04 - ENTREGA INTEGRADA ETAPA 5/10, AVANCE 4/10 = 40% OPERATIVO.** Se creó [`docs/C3D04_CASE_A_STATUS.json`](docs/C3D04_CASE_A_STATUS.json) como estado canónico de diez hitos y [`cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md`](cases_3d/C3D_04_rounded_multiblock_pilot/AGENTS.md) como contrato persistente de **etapa/porcentaje obligatorios en cada reporte y prohibición de micropruebas WSL**. Hitos 1–4 basados en resultados reales: V4/T02 21,312 celdas, padre/metal/molde `Mesh OK`, interfaz 2496 caras por lado y área 6343.771874 mm², coincidencia superficial STL **muestreada** max 0.104973015 mm, no ortogonalidad >70° 572/276/232 y 64/64 caras parent-only identificadas en contacto real. Hito 5 **EN PROGRESO**, no `DONE`: [T0 conducción numérica de dos sólidos](cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/README.md), `T0_INPUTS.json` con propiedades e IC `null`, generador y verificador integrados de 9 archivos, condiciones para parches reales, fuente inmutable y CI estática. `CODE_COMMITTED` no equivale a prueba WSL ni a CFD; **falta contrastar Foundation14 y los datos físicos**, no se ha materializado el caso ni ejecutado solver. No repetir auditorías geométricas cerradas, ni pedir ejecución por una prueba individual. **No validación física/independencia de malla**.

> **19-11-2026 — PROJECT_PROGRESS_CONTRACT_20261119 (aplica a TODOS los casos):** regla permanente de **entregas integrales, corrección de raíz, verificaciones internas y cero cadenas de micropruebas WSL**. Cada actualización DEBE mostrar **caso, ETAPA, AVANCE cuantificable, evidencia, bloqueo y siguiente hito integrado**. Caso B C3D-05 **etapa 3/7 T0, 2/7 = 29% de hitos técnicos (NO tesis/CFD)**: geometría STEP y 270,788 HEX8/contacto comprobados, 1,826 caras nonorth >70°; T0 preparado sin propiedades documentadas, no materializado ni ejecutado. [Política](docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [estado](docs/PROJECT_STAGE_STATUS.json). Historial y resultados anteriores preservados.

> **19-11-2026 — C3D-04-A CIERRE 64/64 CARAS: NO MÁS AUDITORES DE UNA SOLA PIEZA.** Resultado auténtico de la laptop WSL del investigador: `audit_v4_t02_face_identity.py --self-test` correcto; padre 572 caras >70°, metal 276, arena 232; **unión regional 508**, **64 adicionales padre**, **64/64 sobre la interfaz real `metal_to_mold`/`mold_to_metal` de 2,496 caras**, **0** fuera, **0** regional-only y **0** overlap, intervalo Y−40..−39.8 mm; `FACE_IDENTITY_INTERFACE_HYPOTHESIS_VERIFIED_READONLY`. Reporte inmutable `~/OpenFOAM/C3D04_V4_T02_FACE_IDENTITY_AUDIT_01/C3D04_V4_T02_SEVERE_FACE_IDENTITY.json`. No se reconstruyó malla ni corrió CFD; las 3 puertas originales parent/metal/mold, contacto y superficie STL muestreada están registradas. Se **cierra** esta investigación y se adopta el criterio operativo del investigador: **trabajo en bloques integrales, validaciones agrupadas, sin una ejecución WSL por cada pieza ni repetición de informes previamente resueltos**. Próxima entrega: preparación integral de parámetros de conducción transitoria/CHT/solución numérica de Caso A, con trazabilidad a datos físicos y con bloqueo explícito antes de usar valores no verificados. **No declarar validez física, estabilidad o independencia de malla.** [Bitácora](docs/C3D_04_NO_ORTHO_T02_20261119_ES.md).

> **19-11-2026 — C3D-05/B: CAMBIO A MODELO T0 REAL EN EL REPO (PREPARADO, NO EJECUTADO):** creada carpeta [`t0_conduction`](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/README.md) separada del caso geométrico: plantillas OpenFOAM Foundation14 de dos regiones `metal solid;` y `mold solid;`, `physicalProperties` `heSolidThermo/eConst/rhoConst/constIsoSolid`, temperaturas `coupledTemperature` en `metal_to_mold`/`mold_to_metal`, `zeroGradient` en `metalTop`/`moldOuterUnclassified`, tiempo y `fvSchemes/fvSolution`. Hipótesis T0: cuerpos sólidos, fronteras externas adiabáticas y contacto ideal para verificar conservación/continuidad; NO fenómenos de fundición. `T0_INPUTS.json` documenta rho/Cv/kappa/molWeight/T de ambos y sus fuentes como `null`; NO asignar valores inventados. Añadido [validador/materializador seguro](cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/prepare_t0.py), 5 tests sintéticos y runner `run_t0_preflight.sh` de una sola orden para test + SHA/HEX8/contacto + detección Foundation14. Preparado script separado de materialización con `foamDictionary`; solo copia mallas a `~/OpenFOAM/C3D05_T0_CONDUCTION_01` si todo se documentó. **NO corrida WSL del preflight ni térmica; NO CFD, no caso térmico materializado**. [Contrato académico](docs/C3D_05_T0_CONDUCCION_MULTIRREGION_F14_20261119_ES.md).

> **19-11-2026 — C3D-04 CASO A V4/T02, 572 VTK PADRE = 572 LOG Y 64 EXCEDENTES EN Y−40..−39.8.** Auditoría facial real WSL `audit_v4_t02_vtk_faces.py`: `SELF_TEST_OK`, VTK padre **572 polígonos**, hierro **276**, arena **232**, todos igual a los conteos nativos de >70° de `checkMesh`; centroides por bandas Y [−40,−39.8), [−39.8,−39.5), [−39.5,−39) mm: padre **240/300/32**, hierro **32/212/32**, arena **144/88/0**; diferencial por banda **64/0/0**. Total de caras regionales menos padre = **2,496** igual al número de caras de interfaz; aún **NO demostrado por identidad de caras** que las 64 caras severas ausentes al dividir regiones pertenecen al contacto metal–arena. Se publicó `audit_v4_t02_face_identity.py` para mapear uno a uno polígonos VTK→IDs `polyMesh` padre y regionales, contrastarlos con ambas mitades de la interfaz y producir evidencia nueva de solo lectura. **El auditor de identidad está preparado pero NO ejecutado**, nunca afirmar resolución definitiva ni estabilidad numérica. NO CFD. [Informe](docs/C3D_04_NO_ORTHO_T02_20261119_ES.md).

> **19-11-2026 — CASO A C3D-04: 572/276/232 CARAS >70° EN PADRE/METAL/ARENA, AUDITOR NATIVO READ-ONLY COMPLETADO.** Tras corregir `metalTop=wall` en auditor, el nuevo pase WSL registró **parent 572/66,208 caras, max82.92036178°; metal 276/28,256, max77.9303929°; mold 232/40,448, max82.058116°**. Pruebas sintéticas de gates positivos/negativos y parser VTK `SELF_TEST_OK`; corroborada aceptación previa de padre, metal, mold y contacto recíproco. Histograma de **ocurrencias de vértices** de nonOrthoFaces.vtk concentradas entre Y−40..−39 mm; no son conteos de caras por banda. Suma de caras totales regionales − padre = **2,496**, identidad consistente con interfaz; diferencia de **64 caras severas** aún no explicada. Reporte preservado `~/OpenFOAM/C3D04_V4_T02_NONORTH_AUDIT_01/C3D04_V4_T02_NONORTH_REPORT.json`. Se publicó lector nuevo `audit_v4_t02_vtk_faces.py` de geometría y centroides faciales de VTK ASCII/BINARY con verificación nativa; **todavía no ejecutado localmente**. [Informe](docs/C3D_04_NO_ORTHO_T02_20261119_ES.md). No alterar V4/T02, no CFD, no convergencia.

> **19-11-2026 — RESULTADO REAL C3D-05: HOP DISTANCE RESUELTA EN MALLA HEX8 CAD ACEPTADA.** El investigador ejecutó `run_nonorth_hop_distance.sh` con `git pull`: 2 pruebas de nombre CAD y 4 de grafo **OK**; verificación independiente `OVERALL_GEOMETRY_TOPOLOGY: PASSED` ratificada. **Caras severas metal 595:** al contacto saltos min/mediana/p90/max `1/5/15/23`, 226 a 1 salto y 30 a 2, pared exterior `1/34/56/62`, 260 a ≤2 saltos de cualquier pared. **Arena 1231:** al contacto `1/9/22/43`, 235 a 1 salto y 43 a 2; exterior `1/5/12/20`, 398 a 1 salto y 62 a 2; 732 a ≤2 de cualquier pared. TOTAL 992/1826 = 54.3 % a ≤2 saltos de pared. Primer JSON `NONORTH_CELL_HOP_DISTANCE_20261119.json` generado en WSL y preservado. No físicos calculados, no CFD, no remesh; estas son **distancias del grafo**, no milímetros. Cambio de etapa: [registro científico y diseño del caso térmico](docs/C3D_05_NOORTH_HOPS_REALES_Y_TRANSICION_FISICA_20261119_ES.md), priorizar T0 conducción acoplada Foundation14 en caso nuevo y después solidificación/gradientes.

> **19-11-2026 — CASO A C3D-04/V4-T02, FALSO BLOQUEO DEL AUDITOR DE NO ORTOGONALIDAD.** La prueba sintética original pasó, pero el análisis WSL real abortó antes de cuantificar no ortogonalidad con `ValueError: Real polyMesh reciprocal mappedWall/top-face gate rejected`. Auditor exigía equivocadamente `metalTop.type=patch` aun cuando el **`blockMeshDict` C3D-04 fuente declara `metalTop.type=wall`**. Corregida la expectativa a `wall`, sin alterar `polyMesh`, CAD, contactos ni criterio de aceptación; se añadieron diagnósticos observado/esperado y regresiones positivas/negativas del gate completo. **Reejecución nativa de auditor pendiente; no afirmar caras severas medidas aún, NO CFD.** [Auditor](cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_v4_t02_nonorth.py) · [Bitácora](docs/C3D_04_NO_ORTHO_T02_20261119_ES.md).

> **19-11-2026 — C3D-05/B: AUDITORÍA NATIVA REAL DE ALTA NO ORTOGONALIDAD COMPLETADA.** El usuario ejecutó `run_nonorth_face_audit.sh` después de `git pull`; prueba estática, 2 tests CAD + 3 tests de auditoría **OK**. `review_accepted_hex_mesh.py` ratificó `OVERALL_GEOMETRY_TOPOLOGY: PASSED`, `Mesh OK` x3, STEP SHA256 auténticos, HEX8 270,788 y contacto. Datos nat. `nonOrthoFaces`: **metal 595 caras severas: 595 internas, 0 de frontera, 0 incidentes celdas de contacto, 0 incidentes celdas exteriores**; **arena 1,231: 1,231 internas, 0 frontera, 0 incidente contacto, 0 incidente exterior**. Suma **1,826** coincide exactamente con padre; `NATIVE_FACESET_AUDIT: PASSED`. JSON nuevo preservado local `NONORTH_FACESET_TOPOLOGY_AUDIT_20261119.json`; no solver. **Importante**: 0 adyacencia directa no significa distancia geométrica grande ni malla libre de riesgo. Para dirigir estrategia numérica se añadió [orquestador CSR/BFS de distancia en saltos](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_hop_distance.sh) con tests, **aún NO ejecutado**; jamás reusar el original para remallar. [Informe detallado](docs/C3D_05_NOORTH_CARAS_INTERNAS_20261119_ES.md).

> **19-11-2026 — CASO A C3D-04: AUDITOR NO ORTOGONALIDAD T02 PREPARADO, NO EJECUTADO:** tras auditoría muestral STL↔malla real favorable (máximo observado 0.104973 mm, no Hausdorff riguroso), se publicó [`audit_v4_t02_nonorth.py`](cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_v4_t02_nonorth.py). Lee logs nativos padre/metal/molde con sus conteos y determinantes, exige continuidad del `Mesh OK` y área más reciprocidad `mappedWall` de 2496 caras desde los `polyMesh/boundary` existentes, extrae los **conteos reales de caras no ortogonales >70°** y mapea **solo ocurrencias de vértices** VTK de superficies por bandas axiales sin convertirlos en número de caras. Escritura únicamente de nuevo reporte independiente, **sin remallado/checkMesh/CFD y sin relajar parámetros**. Requiere corrida local WSL para resultados. [Manual](docs/C3D_04_NO_ORTHO_T02_20261119_ES.md).

> **19-11-2026 — C3D-05/B: AUDITORÍA INDEPENDIENTE COMPLETAMENTE APROBADA (EVIDENCIA NATIVA).** El usuario ejecutó el runner `run_hex_readiness_review.sh` con checks previos de SHA canónico correctos; regresiones 2+9 **OK**; los siete subpredicados STEP/HEX8 y los siete controles de geometría/topología/contacto fueron **PASS** y apareció `OVERALL_GEOMETRY_TOPOLOGY: PASSED`. Padre **270,788** celdas HEX8, metal **92,200**, arena **178,588**, `Mesh OK` nativo x3, `mappedWall` recíprocos, contacto **12,636 caras por lado** con área **6,349.07567760369 mm²** por lado. La constante SHA de molde antes truncada fue corregida; no era fallo de CAD. El JSON `HEX8_NATIVE_ACCEPTANCE_REVIEW_CANONICAL_SHA_20261119.json` **ya existía y no se sobrescribió** en esta ejecución; auditoría actual en lectura. **Ningún CFD**, ni validación térmica, ni independencia de malla. Riesgo: **1,826** caras con nonorth >70° (metal 595/arena 1231). [Informe final](docs/C3D_05_HEX8_VALIDACION_INDEPENDIENTE_FINAL_20261119_ES.md). Se creó [auditoría `nonOrthoFaces` read-only](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_nonorth_face_audit.sh) con tests, sin ejecutar todavía en WSL.

> **19-11-2026 — C3D-04 CASO A V4/T02, DISTANCIA SUPERFICIAL STL–MALLA MUESTREADA COMPLETADA:** resultados de la terminal WSL sobre malla nativa preservada: `SELF_TEST_OK`, STL auténticos por SHA y comparación de hierro/arena en ambas direcciones. **Hierro**: STL→malla 4,421 muestras, máximo 0.104768977 mm, RMS 0.045467291 mm; malla→STL 2,910, máximo 0.102346260 mm, RMS 0.022718477 mm. **Arena**: STL→malla 3,897, máximo 0.104973015 mm, RMS 0.041813787 mm; malla→STL 4,311, máximo 0.099903895 mm, RMS 0.018156947 mm. Ningún punto muestreado a >0.5 mm. Reporte preservado `~/OpenFOAM/C3D04_V4_T02_CAD_SURFACE_AUDIT_01/SAMPLED_CAD_SURFACE_REPORT.json`. **Distancias muestrales ≠ Hausdorff riguroso; no asignar aprobado geométrico absoluto ni inferir CFD.** Siguiente tarea: localizar y cuantificar no ortogonalidad severa en la malla padre, hierro y arena, sin cambiar T02. [Bitácora detallada](docs/C3D_04_VALIDACION_SUPERFICIE_T02_20261119_ES.md).

> **19-11-2026 — C3D-05 CASO B: CAUSA EXACTA DE FALSO RECHAZO HEX8 EN REVISOR.** Salida WSL de auditoría independiente detallada muestra 6/7 predicados de CAD/HEX8 `PASS`, solo `source.mold_sha256=FAIL`: `STEP_CAD_AUDIT.json` contiene el SHA completo canónico **64 caracteres** `fe126d23bb639196258551fd156591d7fe2b0b4ce1d7c9ece47016e8ad08a40c`; el `review_accepted_hex_mesh.py` utilizaba por error `fe126d23bb639196258551fd156591d7c9ece47016e8ad08a40c` **52 caracteres**. No se identificó una discrepancia real en los STEP ni elementos HEX8. **Se corrigió únicamente la referencia SHA esperada**, con pruebas de hash directo contra los dos STEP de disco y de rechazo del SHA truncado. [Postmortem y revalidación](docs/C3D_05_HEX8_PROVENANCE_REVIEW_20261119_ES.md). **AUDITORÍA REEJECUTADA: PENDIENTE**, mantener evidencia de aceptación nativa + contacto y anterior rechazo independiente; el revisor escribirá nueva `HEX8_NATIVE_ACCEPTANCE_REVIEW_CANONICAL_SHA_20261119.json`, sin borrar las anteriores. CFD/validación física e independencia de malla: NO ejecutados. Los avisos de 1,826 caras >70° siguen vigentes.

> **19-11-2026 — CASO B C3D-05, REVISIÓN INDEPENDIENTE HEX8 RECHAZADA POR PROCEDENCIA:** salida real de `run_hex_readiness_review.sh` en WSL confirma `checkMesh` nativo de padre/metal/molde aprobados (270,788 / 92,200 / 178,588 celdas), contacto recíproco y áreas PASS, estatus del runner PASS y consistencia de conteo de caras no ortogonales PASS. **Pero falla `source_STEP_authentic_and_expected_hex8_topology` y `OVERALL_GEOMETRY_TOPOLOGY=NOT_PASSED`; no declarar aceptación integral.** El resumen mostrado no identifica cuál de 7 subpredicados de fuente/campo HEX8 falló; la inspección siguiente tiene que mostrar `cad_provenance_checks` observado vs esperado desde los archivos guardados, sin alterar requisitos ni remallar. Altos ángulos de no ortogonalidad (1,826 caras >70°) y `NO_CFD`. Se actualizó el [informe de Caso B](docs/C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md), el CSV de seguimiento y el encabezado neutral del revisor para evitar aseveraciones prematuras. [Revisor](cases_3d/C3D_05_step_gmsh_conformal/scripts/review_accepted_hex_mesh.py).

> **19-11-2026 — C3D-05 HEX8 / NUEVA AUDITORÍA CON FALLO DE PROCEDENCIA (RESULTADO REAL):** comando `run_hex_readiness_review.sh` sobre `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`: pruebas estáticas, 2 regresiones nombres y 4 revisor **OK**; revisor nativo reportó **PASS** `native_mesh_OK_all_three`, suma celdas 270,788, `reciprocal_mappedWall_contact_faces`, `contact_area_gate`, `native_runner_status_accepted`, recuento nonorth 1,826=595+1,231. **FAIL** `source_STEP_authentic_and_expected_hex8_topology`, por lo que **`OVERALL_GEOMETRY_TOPOLOGY: NOT_PASSED`** en la **segunda** puerta independiente. No hay evidencia de cuál de siete predicados fue responsable; **no inventar causa**. Primer JSON `HEX8_NATIVE_ACCEPTANCE_REVIEW_20261119.json` creado y preservado; código actualizado para diagnosticar campo por campo (observed/expected, sin relajar) y guardar `HEX8_NATIVE_ACCEPTANCE_REVIEW_PROVENANCE_DETAIL_20261119.json` nuevo. Script de una sola orden listo; **aún no ejecutado** en WSL. No Gmsh nuevo ni CFD. [Incidente y procedimiento](docs/C3D_05_HEX8_PROVENANCE_REVIEW_20261119_ES.md).

> **19-11-2026 — C3D-04 V4/T02, AUDITORÍA SUPERFICIAL PREPARADA, NO EJECUTADA:** una vez confirmados `Mesh OK` padre/metal/mold + área/volumen, se agregó [instrumento de distancias muestreadas bidireccionales `audit_accepted_surface_fit.py`](cases_3d/C3D_04_rounded_multiblock_pilot/scripts/audit_accepted_surface_fit.py): compara malla metal y arena contra `metal_v2.stl` / `mold_v2.stl`, hashes CAD, muestreo por intervalos axiales, nearest continuous triangle con BVH y reporte por cada dirección. Usa solo Python estándar y escribe en un directorio externo nuevo; **no modifica T02 ni ejecuta CFD**. La auditoría es **muestreada, no Hausdorff riguroso**, y todavía falta ejecutar y evaluar en WSL. [Protocolo](docs/C3D_04_VALIDACION_SUPERFICIE_T02_20261119_ES.md).

> **19-11-2026 — SEGUIMIENTO DE ACEPTACIÓN C3D-05 HEX8 (nuevo QA, sin nuevo CFD):** se publicó [`review_accepted_hex_mesh.py`](cases_3d/C3D_05_step_gmsh_conformal/scripts/review_accepted_hex_mesh.py) con pruebas sintéticas de volumen con puntuación de OpenFOAM, `Mesh OK` real y rechazo por determinante, y [`run_hex_readiness_review.sh`](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_readiness_review.sh) para una **única instrucción**. Auditoría **preparada, aún no ejecutada sobre WSL**, diseñada para confirmar por lectura de archivos ya preservados SHA256 de STEP, HEX8, 270,788 celdas, `Mesh OK` x3, `mappedWall` recíprocos y 1,826 caras de no ortogonalidad severa. No repite Gmsh, `checkMesh` ni solver, solo añade un JSON nuevo sin sobrescribir evidencia. [Informe principal del resultado HEX8 aceptado](docs/C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md). CFD todavía no corrido.

> **19-11-2026 — CASO A / C3D-04: PRIMERA MALLA CURVILÍNEA 3D CON 3/3 `Mesh OK` NATIVOS.** Corrida WSL de `C3D04_V4_TRANSITION_REPAIR/run_v4_sweep.sh` confirmada por salida primaria: preflight sintético OK, T01 (`inner_y=-0.12`) rechazado con 12 celdas de bajo determinante metálico; **T02 (`inner_y=+0.12 mm`) ACEPTADO PRELIMINARMENTE**, `runner_rc=0`, `Mesh OK` de padre/metal/mold, 0 celdas metal bajo determinante, 0 caras altamente sesgadas en arena, mínimos determinantes 0.002165381027 / 0.001566024926 / 0.002165381027, non-orth max 82.92036178° / 77.9303929° / 82.058116°, skewness max arena 2.841609695. Se conserva `/home/michel/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02` como caso de referencia, 2,496 caras `mappedWall` de interfaz por lado, área 6,343.771874 mm²; runner paró antes de T03–T07. **No hubo CFD ni validación superficial CAD completa, independencia de malla o BC/CHT.** Preservar todas las variantes anteriores. [Registro técnico actual](docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md) · [caso V4](cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/README.md).

> **19-11-2026 — HITO EXPERIMENTAL C3D-05/HEX8:** salida REAL de Ubuntu WSL del usuario tras ejecutar `run_hex_subdivision_pilot.sh`: preflight 2-materiales 3092 HEX8 OK, regressions OK; QuickCup original STEP AP214 convertido en `C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02` a **270,788 HEX8 (92,200 metal, 178,588 arena)**. `checkMesh` `Mesh OK` padre, metal y arena, conectividad 1/1/1, determinante mínimo metal `0.0568401483702`, arena `0.0520952173462`. Interfaz metal/arena `mappedWall` recíproca **12,636 caras y 6,349.07567760369 mm² en ambos lados**, diferencia 0, contacto vs STL −0.056 %, `contact_gate=true`; `metalTop` 942 caras y 1,326.6753792194886 mm². **Riesgo**: non-ortogonalidad máxima 76.7989°, **1,826** caras >70° en padre (595 metal, 1,231 molde). Malla HEX8 gruesa de 3.6mm base **aprobada para topología**, NO convergencia, NO condiciones térmicas, NO CFD. Carpeta local _02 preservada y otros candidatos intactos. [Informe con mediciones](docs/C3D_05_HEX8_SEGUNDO_INTENTO_ACEPTADO_20261119_ES.md). Estado en CSV actualizado distinguiendo `_01` fallido por Python y `_02` aceptado.

> **18-11-2026 — CASO A / C3D-04 V3 NATIVA: ARENA YA PASA, HIERRO AÚN NO:** el investigador entregó la tabla completa `C3D04_V3_BASAL_SWEEP_01` y los `checkMesh` de T01–T06: **6/6 padre `Mesh OK`, 6/6 mold `Mesh OK`, 0/6 metal `Mesh OK`**, exactamente **4 celdas de metal** con determinante bajo en cada prueba. Todas las caras de arena skew desaparecieron; skewness máxima arena desciende de **3.711322729 (T01)** a **2.841609695 (T06)**, máximo nonortho metal T06 79.34727593°, arena T06 82.058116°. Contacto 2,496 caras por lado y área **6,343.771874 mm²** en los seis. V3 final `ALL_TRIALS_REJECTED_OR_BLOCKED / NO_CFD`; ninguna malla 3D-A final aceptada. Se preserva T06 como referencia empírica y se publica [**V4 controlada para reparar las cuatro celdas**](cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V4_TRANSITION_REPAIR/README.md): 3 ensayos Y internos y, si no pasan, 4 ensayos de ajuste de contorno metal en estación Y−39.8 mm. Generadores, prueba de diff independiente, test estático, runner `blockMesh/checkMesh/splitMeshRegions` y postmortem automáticos; nuevos directorios inmutables. **V4 NO ejecutada y sin solver.** [Informe científico V1–V3](docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md).

> **18–19/11/2026 — C3D-05 HEX8, RESULTADO PRIMER INTENTO REAL:** `git pull` a `8736a58c1`; 6 unit tests previos OK; Gmsh preflight **HEX_SUBDIVISION_PREFLIGHT_OK** con 3,092 HEX8, 2 volúmenes, interfaz QUAD4 y physical groups en **modelo pequeño**. Intento QuickCup `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_01` **falló ANTES de importar STEP**: `UnboundLocalError: cannot access local variable 'volume_tags'`. Causa exacta: la función global `volume_tags` quedó localmente sombreada por desempaquetado `volume_types, volume_tags, _` posterior en `main`. **Se corrigió a `hex_element_tags` sin tocar geometría o tolerancias**. Se añadió `tests/test_build_step_mesh_regressions.py` (tablas `symtable` de globales y casos función auxiliar), integrado como gate antes de Gmsh; runner prepara **`C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`** y comprueba evidencia `UnboundLocalError` en la carpeta histórica `_01`. **Reintento _02 aún NO ejecutado; no malla HEX8 QuickCup ni CFD**. [Detalle científico](docs/C3D_05_HEX8_PRIMER_INTENTO_PYTHON_20261119_ES.md).

> **18–19-11-2026 — C3D-05/HXT RESULTADO NATIVO REAL:** prueba HXT del investigador: preflight `HXT_PREFLIGHT_OK`, 508,924 tetraedros (178,290 metal; 330,634 arena), volúmenes idénticos al control; `checkMesh` **rechazó** padre/metal/arena por **306/96/401** celdas `determinant<0.001`, frente al control Delaunay **306/96/402**. Auditoría de topología: **100 %** celdas malas HXT con 2 caras frontera y 2 internas; 96 metal top/interfaz, arena 95 exterior/interfaz + 306 exterior/exterior. Auditoría área: **6,348.106691699321 mm²** por lado, 16,218 caras cada lado, desviación −0.07126 %, `contact_gate=true`. Malla preservada `~/OpenFOAM/C3D05_STEP_GMSH_HXT_01`; **NO CFD**. Se añadieron opciones opt-in `--subdivide-to-hex` y `--max-base-tets` a `build_step_mesh.py`, variables correspondientes a `Allmesh` sin alterar defaults, preflight in-memory de dos materiales HEX8/QUAD4 y [runner de un solo comando](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hex_subdivision_pilot.sh). Futuro piloto coarse 3.6mm, límite 150k tetra previos y 4 GiB disponibles, **NO EJECUTADO**. [Registro técnico de HXT y cambio a HEX8](docs/C3D_05_HXT_RESULTADO_Y_PILOTO_HEX_20261118_ES.md).

> **18-11-2026 — CASO A C3D-04, V2 REAL Y V3 PREPARADA:** salida WSL de `C3D04_V2_BASAL_QUALITY/Allmesh`: **malla padre `Mesh OK`**; regional metal **4 celdas determinante <0.001** (V1: 92), molde **8 caras muy sesgadas** (V1:16), ambos `mesh_ok NO`, **NO CFD**. Max no ortogonalidad parent 83.30878084°, metal 80.25771334°, arena 81.21165315°; max skewness arena 4.070513822. Las superficies VTK del metal bajo determinante están en Y−40..−39.8 mm; arena skew en Y−39.8..−39.5 mm. Área de contacto reproducida **6,343.771874 mm² por lado**, error −0.139498% vs STL, reciprocidad exacta; tapa metal 1,326.384174 mm². [Evidencia V1/V2](docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md). La V2 queda preservada e inequívocamente rechazada en calidad regional. Nuevo [**V3 barrido nativo de seis ensayos, un solo comando**](cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V3_BASAL_SWEEP/README.md) generará casos frescos con perturbación de cuatro nodos internos del hierro, `simpleGrading` radial de 108 bloques de arena, pruebas estáticas, `checkMesh` tripartito y área, diagnóstico automático al fallar, resumen TSV, sin tocar CAD/C14/Caso B. **V3 sigue PREPARED_NOT_RUN, NO SIMULACIÓN.**

> **18-11-2026 — CASO A / C3D-04: DIAGNÓSTICO NATIVO LOCALIZADO Y V2 CONTROLADA:** el investigador ejecutó el analizador sobre `C3D04_ROUNDED_MULTIBLOCK_PILOT_01`, malla `blockMesh` 3D ya rechazada (92 celdas metal con determinante bajo y 16 caras sesgadas mold). VTK metal `underdeterminedCells`: vértices entre Y=−40 y −39.8 mm; mold `skewFaces`: entre Y=−39.8 y −39.5 mm. Los polígonos reales de `polyMesh` entregan **área de interfaz 6,343.771874 mm² en ambos lados**, desviación frente al STL −0.139498 %, tapa metal 1,326.384174 mm² (−0.037782 %). **Área preliminar PASS; calidad FAIL; NO CFD.** [Informe](docs/C3D_04_RESULTADO_PRIMER_MALLADO_20261118_ES.md). Se creó [C3D-04 V2 basal](cases_3d/C3D_04_rounded_multiblock_pilot/candidates/C3D04_V2_BASAL_QUALITY/README.md) con 12 vértices internos metal redistribuidos y `simpleGrading` radial del molde en 108 bloques; la comparación de fuentes confirma solo esos 120 cambios de línea, sin cambiar contornos ni contacto. **V2 PREPARED_NOT_RUN**; `Allmesh` nativo ejecutará validación completa en carpeta WSL nueva, nunca sobreescribe el original. Caso B no modificado.

> **18-11-2026 — REGISTRO NATIVO C3D-05 FRONTAL:** salida WSL recibida tras ejecución de `run_frontal_pilot.sh`: `main` a `2fbe20aff`, pruebas estáticas + 4+2 tests OK, Gmsh preparó superficies STEP, **Frontal 3D abortó con `Frontal algorithm requires Netgen`**; NO hay elementos volumétricos, `gmshToFoam` ni `checkMesh` ni CFD Frontal. Clasificar `BLOCKED_DEPENDENCY`, no `REJECTED_NATIVE_QUALITY`. Se conserva `C3D05_STEP_GMSH_FRONTAL_01` y la malla control Delaunay intacta. Alternativa [HXT=10 con preflight en memoria](cases_3d/C3D_05_step_gmsh_conformal/scripts/preflight_hxt.py) y [runner de una sola invocación](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_hxt_pilot.sh) ya incluidos, **todavía no ejecutados**. HXT también tetraédrico, por lo que puede conservar la patología de dos caras frontera por tet: no prometer éxito. [Bitácora de raíz y experimento](docs/C3D_05_FRONTAL_NETGEN_BLOQUEO_HXT_20261118_ES.md).

> **18-11-2026 — ENSAYO B C3D-05: SEGUNDO DIAGNÓSTICO NATIVO Y ACCIÓN DE CÓDIGO:** salida real recibida de `run_full_diagnostics.sh`: 4 pruebas de logs y 2 de topología **OK**; de 96 celdas metal y 402 arena con determinante <0.001, **100%** tiene exactamente 2 caras internas y 2 caras frontera. Metal 96 `metalTop`+`metal_to_mold`; arena 96 `moldOuterUnclassified`+`mold_to_metal` y 306 exterior+exterior. Área de contacto real 6,348.106691699194 mm² en ambos lados; 16,218 caras c/u; diferencia relativa **0**, −0.071261815% vs referencia, `contact_gate=true`. Área superior metal 1,326.5776804745685 mm² (−0.0232%). **NO Mesh OK:** único fallo check de determinante, no CFD. Se parametrizó `--algorithm-3d` en el generador Gmsh/`C3D05_ALGORITHM3D` en `Allmesh` (default 1 conservado), y se creó el orquestador [run_frontal_pilot.sh](cases_3d/C3D_05_step_gmsh_conformal/scripts/run_frontal_pilot.sh) para experimento **NUEVO**, una variable Gmsh `1→4`, sin sobrescribir malla original. **Aún NO ejecutado**. [Informe reproducible](docs/C3D_05_AREA_ARISTAS_Y_ENSAYO_FRONTAL_20261118_ES.md).

> **18-11-2026 — CORRECCIÓN DE FLUJO POR SOLICITUD EXPLÍCITA DEL INVESTIGADOR:** prohibido dar instrucciones de terminal separadas para una misma operación. Se instituyó [`docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md`](docs/REGLA_INSTRUCCIONES_UNIFICADAS_ES.md), enlazada desde README raíz y protocolo maestro: **un solo bloque de terminal con un comando compuesto por etapa; crear scripts orquestadores antes que múltiples bloques**. Se agregó `cases_3d/C3D_05_step_gmsh_conformal/scripts/run_full_diagnostics.sh` para encapsular pruebas de diagnóstico, lectura de celdas `underdeterminedCells` y medición de interfaz sobre el caso B preservado. No remalla, no ejecuta CFD, no borra evidencia.

> **18-11-2026 — POSTMORTEM C3D-05 YA CONCLUYENTE:** salida real del investigador `diagnose_existing_mesh.py` sobre la malla preservada confirma `checkMesh` **1 fallo exclusivo por `Cell determinant (wellposedness) < 0.001`**, con **306 celdas en padre**, **96 de 190,365 en metal** y **402 de 335,341 en arena**. Padre/ambos materiales 1 región conectada, volúmenes correctos, ortogonalidad/skewness/aspect ratio, face tets y concavidad **OK**. Parches recíprocos `mappedWall` **16,218 caras por región**, pero **sin auditoría de área**. La diferencia padre→regiones sugiere investigar cambio de estado interno/borde, **hipótesis NO causalidad demostrada**. Se añadió herramienta de inspección no destructiva de `underdeterminedCells` frente a `owner`/`neighbour`, con pruebas sintéticas. [Análisis técnico y próximos comandos](docs/C3D_05_DIAGNOSTICO_DETERMINANTE_20261118_ES.md). Malla rechazado, no CFD.

> **18-11-2026 — C3D-05 primera corrida Gmsh/OF14 hecha (NO CFD):** usuario sincronizó `main` a `79056bbce` y ejecutó `Allmesh` sobre los dos STEP reales versionados. Obtuvo **190,365 celdas metal, 335,341 molde**; volumen nativo metal `4.79675605036e-05 m³`, arena `0.000102843547305 m³`. **Ambas regiones `mesh_ok NO`; parada en `CHECK_REGION_QUALITY`; no se completó auditoría `mappedWall` ni área ni CFD.** El problema exacto de `checkMesh` sigue **PENDIENTE** porque no se han recibido `log.checkMesh.metal`/`mold`. Carpeta `/home/michel/OpenFOAM/C3D05_STEP_GMSH_PILOT_01` preservada, sin remallar. Se publicó herramienta Python de solo lectura [`diagnose_existing_mesh.py`](cases_3d/C3D_05_step_gmsh_conformal/scripts/diagnose_existing_mesh.py) y pruebas unitarias sintéticas para distinguir cada predicado. [Bitácora del primer mallado](docs/C3D_05_RESULTADO_PRIMER_MALLADO_20261118_ES.md). No bajar umbrales sin evidencia.

> **18-11-2026 — C3D-05, verificación local de dependencias:** el investigador ejecutó `git pull --ff-only` tras publicar los STEP; sincronizó `main` al commit `1408b9575`. Test estático `test_step_gmsh_static.sh`: **OK** (incluida integridad SHA-256 de ambos CAD). El siguiente comando `python3 -c 'import gmsh; print(...)'` falló con **`ModuleNotFoundError: No module named 'gmsh'`**. Esto identifica una **dependencia local faltante**, no defecto del CAD ni rechazo de la malla. **No se ejecutó `Allmesh`** ni `gmshToFoam`, `checkMesh` o CFD. Corrección indicada: `sudo apt update && sudo apt install -y python3-gmsh gmsh` (paquetes de Ubuntu 26.04/Universe); verificar importación y el Python activo, y conservar logs del primer ensayo nativo cuando pueda iniciarse. Estado C3D-05: `PREPARED_BLOCKED_LOCAL_GMSH_PYTHON`.

> **18-11-2026 — REPOSITORIO CAD C3D-05 ACTUALIZADO POR SOLICITUD:** originales AP214 `metalmm.STEP` y `QuickCupmm.STEP` versionados directamente en `main` bajo `cases_3d/C3D_05_step_gmsh_conformal/constant/geometry/`. Se reconstruyó el texto con finales CRLF intactos; comprobación `git hash-object` original vs SHA blob GitHub: **metal `604c63f136dc53443f73fe1259aedde9d798fc42`** y **arena `3fd753e268a3027e1dfb495a13a006b0d82101f5`**, coincidencia exacta. Se modificó `Allmesh` para seleccionar esos archivos automáticamente (sin `C3D05_METAL_STEP`/`C3D05_MOLD_STEP` obligatorios) y comprobar hashes SHA256; se reforzó la prueba estática. [Bitácora de fuentes y volumen](docs/C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md). **NO se corrió** Gmsh ni OpenFOAM Foundation14 ni CFD en esta acción.

> **18-11-2026 — VALIDACIÓN DIRECTA DE CAD C3D-05:** usuario adjuntó `metalmm.STEP` (38,011 bytes, SHA `ea5f65796c5156e4931eaec29ff656c279120925ebc083767a16b80892d0f475`) y `QuickCupmm.STEP` (71,973 bytes, SHA `fe126d23bb639196258551fd156591d7fe2b0b4ce1d7c9ece47016e8ad08a40c`). Cada archivo es AP214 SolidWorks 2026 y contiene 1 sólido B-Rep válido. OpenCASCADE devolvió volúmenes metal **47,988.524998 mm³**, arena **102,843.320825 mm³**, unión **150,831.845824 mm³**, 1 sólido al unir y área común de contacto **6,352.821119 mm²** (+0.00295 % vs STL). STEP usa **SI metros** internamente; OCC interpretó a mm correctamente. [Auditoría técnica detallada](docs/C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md). **Sólo CAD verificado; Gmsh, conversión a OpenFOAM y CFD aún NO ejecutados**. Ya no faltan archivos fuente, pero sí ubicarlos localmente en WSL.

> **18-11-2026 — DESARROLLO PARALELO C3D-04/C3D-05:** ante solicitud expresa, se aclaró que **C3D-04 es `blockMesh` curvilíneo 3D** y que una alternativa verdaderamente independiente requiere **Gmsh/OpenCASCADE sobre dos STEP sólidos compartiendo interfaz**. Se publicó C3D-05 con validador de volúmenes y contacto previo, fragmentación OCC, etiquetas físicas de metal/molde, salida MSH2 en metros, conversión `gmshToFoam`, checks regionales y medidor de área. **No corrido**: faltan dos STEP SolidWorks exportados con idéntico origen; también queda pendiente ejecutar C3D-04. Estado C3D-03: `checkMesh YES`, 2,368 metal y 7,680 mold, 1,248 caras por lado, confirmado por terminal. [Documentación comparativa](docs/C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md) · [CSV](docs/C3D_MESH_PROGRESS_20261118.csv). C14 no alterado, sin CFD 3D.

> **18-11-2026 — C3D-03 IMPLEMENTADO COMO FUENTE, NO CORRIDO:** se extrajeron secciones directamente de STL v2: metal cuadrado/taper (+redondeo basal), molde exterior cuadrado tapered y cavidad inferior rectangular 22.5×27.5 mm desde y=-65.5 a -56 mm. Nuevo [caso de piloto](cases_3d/C3D_03_doctor_multiblock_pilot/README.md) con `blockMeshDict` Foundation14, 24 bloques, 48 vértices, zonas `metal`/`mold` sin exterior, 10,048 celdas **teóricas**, 1,248 caras de contacto **teóricas**; metal 48,011.916 mm³ y arena 103,169.142 mm³ **analíticos**, aún sin `checkMesh` local. El script de malla solamente nativo preserva todos los casos anteriores, no corre `foamMultiRun`. **Ejecución y calidad en WSL pendientes.**

> **18-11-2026 — Encargo del director incorporado a MAESTRÍA:** el primer avance deberá contener **ecuaciones**, **condiciones de frontera e iniciales** (metal/molde, interfaz, ambiente, velocidad y presión), **valores numéricos relevantes incluido Courant máximo observado**, y **sensibilidad de `phaseChangeSource.relax`**. Base: C14 `relax=0.10` RUN/ANALYSIS-VERIFIED; C16 `relax=0.25` preparado/no corrido; `maxCo=0.25` configurado con `adjustTimeStep=no` no puede reportarse como Co observado. Documento central: [primer avance](docs/PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md). No mezclar con CFD 3D: C3D-02 solo mallados rechazados.

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — bitácora científica:** el usuario ejecutó `run_stl_v2_ablation.sh` tras observar cuatro mensajes `OK` de subpruebas estáticas; el estado final de la suite estática no consta en la terminal. `--v2-metal-only`: 1 celda metal, 274,788 molde, 314,913 exterior; 3 caras de contacto residual y malla rechazada. `--v2-mold-only`: 85,350 metal, **0** molde, 504,471 exterior y sin contacto; bloqueo `CHECK_INTERFACE`. El texto `UNKNOWN` del resumen local es bug de formato, no incertidumbre de conteo; `main` ya contiene el arreglo. El registro del doctor `doctor_original/cht` usa `blockMesh` cuasi-2D, 11,880 celdas globales → 6,400 metal + 5,480 molde y 240 caras de interfaz; `log.foamMultiRun` original está vacío, por tanto **no hay prueba de CFD completado**. Interpretación: los STL nuevos colapsan zonas por separado; causa exacta no determinada, no atribuir a autointersecciones ni contacto coplanar sin evidencia nativa. [Bitácora primaria](docs/C3D_02_ABLACION_STL_V2_20261118_ES.md) · [estudio del doctor](docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). No se cambian parámetros C14 ni se borra evidencia.

## 17-11-2026 — Operación Granada: detección espacial de fallos OBLIGATORIA en el comando único C3D-02

- El usuario exigió identificar **desde el inicio de la ejecución** las zonas de cualquier error, **siempre**, sin pedir una secuencia de scripts de diagnóstico, y mantener documentada la regla en los repositorios técnicos. Se corrigió la omisión: `build_c3d02.py` **no** generaba VTK de defectos, y el análisis de coordenadas solo existía en una utilidad independiente. Las verificaciones de CI anteriores no cubrían ese contrato.
- Ahora el comando integral importa `mesh_error_zones.run_error_localization` y crea **`ERROR_ZONES.json` y `ERROR_ZONES.md` al iniciar**; actualiza los informes en su salida normal y de fallo desde `status()`. El detector revisa automáticamente `global`, `metal`, `mold` cuando existan mallas; ejecuta `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` **sobre copias físicas** en `error_diagnostics/`, exporta los conjuntos VTK problemáticos, rangos XYZ en mm, tramos axiales Y, conteos `checkMesh` y logs. Los porcentajes por franja son **vértices VTK**, no frecuencia de celdas malas.
- Si no existe malla (falla en preflight, blockMesh o snappy), reporta la etapa y los logs sin inventar coordenadas. Ningún error del localizador debe esconder el error original. El código original del CFD mantiene bloqueo del solver si G1 falla.
- Se añadió autoprueba sintética obligatoria en `tests/test_template_static.sh` (compilación, importación, malla ausente, conjuntos e integración real con el punto de entrada). Nueva [política permanente](docs/AUTOMATIC_MESH_ERROR_LOCALIZATION_POLICY_ES.md) para los futuros builders; otros casos históricos **todavía no migrados**. `OpenFOAM---PROJECTS` es el hub técnico correcto, **no `Main-Repo---Life-Experience`**.
- **Pendiente evidencia en laptop:** CI estático no demuestra que el comando principal finalice ni que localice defectos reales en un mesh nuevo. Comando de usuario sigue siendo **uno**: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py`.

## 2026-11-17 — Operación Granada C3D-02 cambia a un SOLO comando integral de producción

El investigador pidió explícitamente **dejar de perder tiempo en arreglos y pruebas aisladas**, y recibir comandos que intenten crear el resultado completo desde el principio. **Se descontinúa como siguiente instrucción la prueba aislada `test_mold_zone_snap_l2.sh`** (su rama no se fusionó). El programa principal nuevo **`scripts/build_c3d02.py`** reemplaza la secuencia de scripts de prueba: preflight → malla combinada basada en los STL válidos → `cellZones` metal/mold → `splitMeshRegions` con **mappedWall recíprocos conformantes** → checkMesh exhaustivo + volúmenes por región y contacto → preparación C14/BC 3D y corrección explícita pRefPoint de referencia 2D → `foamMultiRun` solo después de calidad aprobada. Ninguna etapa de solver se disfraza de simulación si no concluye.

Fuente técnica Foundation 14: https://cpp.openfoam.org/v14/splitMeshRegions_8C_source.html , revisión de `addRegionPatches` demuestra creación nativa de `mappedWallPolyPatch` por región. NO se afirma que una malla generada o un solver numérico hayan pasado en la laptop; **entrega pendiente de ejecución nativa**. Todos los logs y `BUILD_STATUS.json` se concentran en nueva carpeta `~/OpenFOAM/C3D02_DELIVERY_01` sin sobrescribir las mallas originales de `C3D02_materials`.

**Único comando para el investigador (no más ensayos exploratorios secuenciales):**
```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py
```

## 2026-11-15 — C3D-02: defectos de metal y arena exportados en VTK, sin remallado [EVIDENCIA LOCAL]

- El investigador ejecutó `scripts/inspect_extracted_mesh_quality.sh`, `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` sobre **copias físicas** en `~/OpenFOAM/C3D02_materials/quality_evidence_01/{metal,mold}`; no se modificaron fuentes históricas ni STL ni materiales C14. `checkMesh` devolvió rc=0 para ambos, **pero anunció FAILED 1 (metal) y FAILED 2 (arena)**.
- **Metal:** 85,332 celdas, volumen **4.79621e-05 m³ = 47.9621 cm³**, una región, 30,028 caras en `material type=wall`; 2,422 celdas cóncavas, 1 fallo. Exportó **`metal/postProcessing/checkMesh/constant/concaveCells.vtk`**.
- **Arena extraída:** 274,788 celdas, volumen **0.000103409 m³ = 103.409 cm³**, una región; **22,737 celdas cóncavas, 1 celda con determinante menor de 0.001**, dos fallos. Además se exportó `twoInternalFacesCells` para **una** celda topológica; esto es una advertencia adicional, **no necesariamente un tercer fallo independiente**. Parches: `outerBox type=patch nFaces=0`, `oldInternalFaces type=internal nFaces=97492`. Archivos **`mold/postProcessing/checkMesh/constant/{concaveCells,underdeterminedCells,twoInternalFacesCells}.vtk`**.
- Los dos dominios están volumétricamente aislados, pero **NINGUNO pasa calidad exhaustiva** y no existe una interfaz metal-arena térmica validada.
- Nuevo análisis PREPARADO, NO EJECUTADO EN LAPTOP: `scripts/analyze_bad_mesh_vtk.py` lee `POINTS` de los cuatro VTK (legacy ASCII/binary sin dependencias), reporta cajas X/Y/Z y distribución axial Y **de vértices de superficies**, no de centros ni cantidad de celdas defectuosas, y calcula distancia mínima entre los puntos de las dos anomalías puntuales del molde. Un solapamiento espacial no prueba que sean la misma celda. Tiene prueba de regresión con VTK sintéticos. **No genera CFD, ni modifica malla ni archivos originales.**

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
cd cases_3d/C3D_02_metal_sand_clean
python3 scripts/analyze_bad_mesh_vtk.py
```

La salida indicará si las anomalías parecen agruparse cerca de extremos, centro o interfaz del STL; sin esa evidencia no conviene cambiar indiscriminadamente `snapControls` o relajar la calidad. `RUN_CASE_REGISTRY.csv` permanece `PREPARED_NOT_RUN`.

## 2026-11-15 — C3D-02: arena físicamente extraída en copia; calidad NO aprobada [EVIDENCIA LOCAL]

- Investigador ejecutó `scripts/extract_mold_zone_copy.sh`: `subsetMesh` concluyó y validó la copia `mold_extracted_l2_01`: **274,788 celdas**, volumen **0.000103409 m³ (103.409 cm³; +0.550% vs CAD)**, una componente, `outerBox=0`. La zona medida `moldVolume` y la extracción física concuerdan exactamente en celdas/volumen.
- `checkMesh -allGeometry -allTopology` en copia: `Face tets OK`, pero **22,737 celdas cóncavas** y **una celda con determinante <0.001**, **2 checks fallidos** (código de retorno 0 NO indica aprobación). Arena RECHAZADA para CFD.
- Fronteras de la copia: `outerBox type=patch nFaces=0`, `oldInternalFaces type=internal nFaces=97492`. El segundo no es interfaz térmica ni par recíproco compatible con metal; diseño de frontera pendiente.
- Hierro anterior: **85,332 celdas, 47.9621 cm³, 2,422 celdas cóncavas/1 check fallido**. Ambas mallas conservan problemas. **No ejecutar solver ni crear `mappedWall` sin validación geométrica.**
- Nuevo `scripts/inspect_extracted_mesh_quality.sh` preparado: se ejecutará `checkMesh` con exportación `-writeSurfaces -writeSets` VTK, **solo sobre COPIAS FÍSICAS** de hierro y arena en `quality_evidence_01`, con diagnóstico de celdas/zonas defectuosas, parches y calidad, sin cambiar geometrías ni materiales C14. **Aún NO ejecutado**. [Bitácora técnica](docs/C3D_02_DOS_MALLAS_20261112_ES.md).
- `RUN_CASE_REGISTRY.csv` conserva `PREPARED_NOT_RUN`; no hay CHT/CFD real 3D.

## 2026-11-15 — C3D-02: se midió el volumen REAL de moldVolume; extracción en copia preparada

- **Ejecución Ubuntu verificada por log:** `foamPostProcess` creó `volFieldValue moldZoneVolume`; identificó 274,788 celdas en `cellZone moldVolume` y reportó **0.000103409 m³ = 103.409 cm³**, frente a **0.00010284309608 m³ = 102.8431 cm³** para el STL reparado: diferencia **+0.550 %**. El filtro exploratorio ±5 % se cumplió. La malla global del ensayo tiene 568,135 celdas, volumen 242.208 cm³, `outerBox` 15164 caras y 49,034 celdas cóncavas, **NO aprobada**.
- La etiqueta geométrica es cuantitativamente plausible pero **no es una región física extraída ni prueba calidad de la interfaz**. Continúa sin definirse `mappedWall` recíproco metal-arena.
- Nuevo script `scripts/extract_mold_zone_copy.sh` preparado para crear una **única copia física nueva** `mold_extracted_l2_01`, usar la opción **`subsetMesh -cellZone moldVolume -noFields` de Foundation 14** solo allí y verificar con `checkMesh -allGeometry -allTopology` las 274,788 celdas, volumen, exterior, conectividad, calidad y parches. El código fuente oficial advierte que `subsetMesh` NO preserva los tipos de fronteras originales; esta malla es diagnóstica, no CHT.
- **Extracción NO ejecutada en Ubuntu todavía**; CI verifica únicamente sintaxis, integridad de C14 y restricciones de escritura. No cambiar STL, C14, otros casos ni registros de ejecución. `RUN_CASE_REGISTRY.csv` permanece `PREPARED_NOT_RUN`. [Bitácora completa](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 2026-11-13 — C3D-02: zona `moldVolume` encontrada, aún sin validar volumen zonal [EVIDENCIA LOCAL]

- `test_mold_geometric_zone.sh` completó `snappyHexMesh` en `mold_zoned_l2_01` usando `mode inside`, `cellZone moldVolume` y `faceZone moldInterface`, a nivel L2 y `snap false`. Se obtuvieron **568,135 celdas globales, 274,788 celdas etiquetadas en `moldVolume` y 97,492 caras `moldInterface`**. La asignación geométrica de zonas fue efectiva.
- `checkMesh`: volumen **global** 242.208 cm³ (= caja auxiliar completa), `outerBox=15164`, **49,034 celdas cóncavas y un test fallido** (`checkMesh` terminó con rc=0 a pesar de la condición fallida). No reportar malla aceptada ni asumir que los 274,788 elementos equivalen a 102.843 cm³. Sin conexión térmica ni CFD.
- Se preparó `scripts/measure_mold_zone_volume.sh` para medir con `volFieldValue` nativo de Foundation 14 el volumen **exclusivo** de `cellZone moldVolume`. Crea un caso sombra temporal con `constant/polyMesh` enlazado a la malla original; toda la salida de `foamPostProcess` se aísla en ese caso y se elimina al terminar. No genera malla, no cambia el STL, no ejecuta solver; tolerancia ±5 % solamente informativa, no aceptación. La ejecución de este script aún es PENDIENTE.
- La potencial extracción de `moldVolume` se evaluará ÚNICAMENTE después de conocer el volumen por zona, y en una copia con nuevo mapa de celdas, sin reusar sets de C3D-01 ni ejecutar CFD. Estado `RUN_CASE_REGISTRY`: **PREPARED_NOT_RUN**. [Guía detallada](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 2026-11-13 — C3D-02: L3 retuvo el volumen total de la caja; preparar clasificación de arena por cellZone

- **Ejecución real:** `mold_level3_cast_01`, `level (3 3)`, `snap false`. Después de crear baffles: 2,334,123 celdas; seleccionadas 2,334,117; **6 eliminadas**. `checkMesh`: 2,334,117 celdas, 1 región conectada, volumen **0.000242208 m³ = 242.208 cm³**, EXACTAMENTE toda la caja auxiliar de 58×72×58 mm; `outerBox=17543` caras, 225,732 celdas cóncavas, 1 chequeo exhaustivo fallido. `checkMesh rc=0` no certifica malla. El volumen CAD de arena es 102.8431 cm³.
- **Decisión:** la mayor densidad no produjo barrera de celdas. No intentar L4 o cambiar puntos a ciegas. El STL ya pasó `surfaceCheck -checkSelfIntersection` en Foundation 14.
- **Nueva hipótesis discriminante:** probar las etiquetas `cellZone moldVolume`, `faceZone moldInterface` y `mode inside` de Foundation 14 en el mismo STL a **nivel 2 con `snap false`**. Se agregó `scripts/test_mold_geometric_zone.sh` para un subcaso independiente `~/OpenFOAM/C3D02_materials/mold_zoned_l2_01`. Etiquetar células dentro de un STL cerrado no implica eliminar exterior ni validar interfaz. Se informarán tamaños de zona y calidad; no `subsetMesh`, `splitMeshRegions`, solver ni borrados.
- **Ejecutado en GitHub solo a nivel estático; aún NO ejecutado en Ubuntu.** C14, metal, todas las pruebas históricas y STL intactos. Mantener `RUN_CASE_REGISTRY.csv=PREPARED_NOT_RUN`. [Protocolo](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 13-11-2026 — C3D-02: surfaceCheck del molde correcto; preparar castellation L3 sin snap [EVIDENCIA LOCAL + NUEVO CÓDIGO NO EJECUTADO]

- El investigador ejecutó finalmente `surfaceCheck -checkSelfIntersection` de OpenFOAM Foundation 14, compilación `14-7b05503f98a8`, sobre `mold_repaired.stl`. Resultado **sin triángulos ilegales, sin puntos cercanos problemáticos, cerrada (todas las aristas con dos caras), una parte conectada, una zona de normales consistentes, sin autointersecciones**, `End` y código 0. Estadísticas: **3,084 triángulos, 1,544 vértices**. No manipular ni reparar la superficie sin nueva evidencia.
- En el subcaso de arena el recorte falló en la fase castellated: tras introducir baffles tenía 568,135 celdas, conservó 568,134; quedó `outerBox=15164` y 242.142 cm³. Un nuevo punto interior no alteró esos resultados. El problema de separación aparece ANTES de snapping y de CFD. **Causa exacta no determinada.**
- Con fundamento en el método de refinamiento de superficies, se prepara `scripts/test_mold_level3_castellation.sh` como experimento único de discriminación: `refinementSurfaces level (3 3)` (nominal 0.25 mm desde base de 2 mm), `snap false`, máximo 3,200,000 celdas, solo `mold_repaired.stl` y punto ya verificado. Trabajo exclusivo `~/OpenFOAM/C3D02_materials/mold_level3_cast_01`. Validar primero si `Selected for keeping`, volumen y `outerBox` mejoran; no calificar todavía calidad final ni contacto CHT.
- **Nuevo ensayo NO ejecutado en Ubuntu aún.** No se tocan otras geometrías, propiedades C14, subcasos anteriores ni CFD. Mantener `RUN_CASE_REGISTRY.csv=PREPARED_NOT_RUN`. [Protocolo científico](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 2026-11-12 — C3D-02: selección conservó 568134/568135 celdas; corregido diagnóstico surfaceCheck

- Logs locales `mold` y `mold_offface_01`: justo antes del recorte hay **568,135 celdas**; `Selected for keeping : 568134 cells`, tras el subset **568,134**. **Solo una celda fue eliminada**, permaneció un dominio de 242.142 cm³ con 15,164 caras `outerBox`. El cambio de `insidePoint` no cambió topología ni calidad. Hipótesis de fuga entre material y exterior sigue abierta; no afirmar autointersección sin correr `surfaceCheck` nativo.
- El script previo `inspect_mold_leak.sh` **no ejecutó `surfaceCheck`** porque buscaba `-outputThreshold`, opción no anunciada en la instalación local, además de `-checkSelfIntersection`. Esta restricción fue demasiado estricta. Se eliminó la dependencia de `-outputThreshold`: con opción `checkSelfIntersection` disponible, usarla; si no, revisión topológica básica. Se ejecuta en carpeta temporal aislada para evitar que las versiones que escriben auxiliares toquen el CAD o mallas. `mktemp -d` + limpieza exclusiva del directorio creado. No se ejecuta remallado ni CFD.
- Próxima evidencia requerida: **salida real nativa de `surfaceCheck`**, incluyendo cierre, aristas/manifold y autointersecciones si está soportada. `RUN_CASE_REGISTRY.csv` mantiene `PREPARED_NOT_RUN`.

## 2026-11-12 — C3D-02: mover el insidePoint del molde NO eliminó el exterior [EVIDENCIA LOCAL]

- Se ejecutó `scripts/try_mold_offface.sh` con punto `(0.0043 -0.0207 0.0259)` m para arena; las pruebas de integridad C14 y CAD fueron correctas y `snappyHexMesh` finalizó sin error de utilidad, pero **no** pasó `checkMesh` exhaustivo.
- Resultados `mold_offface_01`: 568,134 celdas, 2 parches, 1 componente conectado, volumen **0.000242142 m³** (242.142 cm³, frente a 102.8431 cm³ del STL), `outerBox` 15,164 caras, 13,367 cóncavas, 10 face-tets de mala calidad, **2 comprobaciones fallidas**. Son **idénticos** al anterior `mold/log.checkMesh.retry1`. `snappyHexMesh` informó `Selected for keeping : 568134 cells`.
- **Conclusión técnica:** el punto anterior x=3 mm estaba sobre una cara de `blockMesh`, pero moverlo a un punto interior alejado de la retícula **no solucionó la retención de aire**. No seguir cambiando semillas a ciegas ni declarar que esa coincidencia fuera la única causa.
- Revisión estática de `mold_repaired.stl` versionado: 3,084 facetas, 1,544 vértices, 4,626 aristas con valencia 2, orientación de aristas coherente, una componente de superficie, volumen firmado 102.843097 cm³. Cierre topológico != ausencia de autointersecciones != malla volumétrica conformante. La geometría incluye facetas muy delgadas, pero el STL del metal también posee algunas; **causa de la fuga por determinar**.
- Próximo único paso: leer los logs locales y usar `surfaceCheck -checkSelfIntersection -outputThreshold 0` si está soportado, mediante `scripts/inspect_mold_leak.sh`. **No se generan nuevas mallas, no se borran casos, no se toca C14 ni se activa CFD.** [Bitácora de la línea 3D](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 2026-11-12 — C3D-02: retry1 concluyó pero ambas mallas rechazadas; semilla de arena sobre cara [EVIDENCIA LOCAL]

- El investigador ejecutó `scripts/resume_material_meshes.sh` tras corregir `allowFreeStandingZoneFaces`, sobre las dos carpetas existentes de `C3D02_materials`; **ambos snappyHexMesh y checkMesh corrieron**. Logs disponibles localmente `metal/log.{snappyHexMesh,checkMesh}.retry1` y `mold/log.{snappyHexMesh,checkMesh}.retry1` (no importados a GitHub).
- **Metal:** 85,332 celdas, volumen 4.79621e−5 m³ (47.9621 cm³; desviación −0.053 % frente a STL), 1 componente, sin `outerBox`, `Face tets OK`, **2,422 celdas cóncavas y 1 fallo geométrico exhaustivo**. Selección física inicial prometedora; no aceptada por `checkMesh`.
- **Mold:** 568,134 celdas, volumen 0.000242142 m³ (242.142 cm³ frente a 102.8431 cm³ CAD, +135.4 %), 1 componente, **15,164 caras en outerBox**, 13,367 cóncavas, 10 face-tets deficientes, **2 fallos**. La malla **conserva el exterior**; no existe aún malla de arena ni interfaz térmica válida.
- **Causa candidata verificable:** en el `blockMeshDict` la discretización x = 58 mm/29 = **2 mm**, empezando en x = −3 mm. El `insidePoint` antiguo del molde x = 3 mm se encuentra **exactamente sobre una cara** de la malla de fondo, lo que incumple la regla del manual Foundation 14. Ese punto era geométricamente interior al STL, pero su coincidencia con la cara invalida la ubicación como semilla robusta; no afirmar que sea la única causa de fuga.
- Se comprobó geométricamente un nuevo punto interior para mold `(4.3,-20.7,25.9)` mm (`(0.0043 -0.0207 0.0259)` m) que no cae en los planos regulares de malla. Se corrigió `scripts/run_material_meshes.sh` para futuros casos nuevos y se preparó `scripts/try_mold_offface.sh` como **prueba aislada, una sola vez y solo de mold**. Preserva `metal/`, `mold/`, fuentes C14, geometrías y logs históricos. No se ha ejecutado esa prueba. [Protocolo](docs/C3D_02_DOS_MALLAS_20261112_ES.md).
- Estado CFD **PREPARED_NOT_RUN**, G1 geométrica/CHT/validación experimental abiertas. No ejecutar solver ni declarar malla aceptada.

## 2026-11-12 — C3D-02: fallo de diccionario Foundation 14 en ambos subcasos independientes [EVIDENCIA LOCAL]

- Tras `git pull --ff-only`, el investigador ejecutó `scripts/run_material_meshes.sh`: validaciones de materiales C14 y tres STL **OK**; `blockMesh` para `metal` y `mold` **OK**.
- En ambos subcasos, `snappyHexMesh` abortó antes de refinar: `keyword allowFreeStandingZoneFaces is undefined` en `castellatedMeshControls`. No hubo `checkMesh` ni malla material utilizable en ese intento. La ausencia de clave en nuestra plantilla original es un **error de configuración que introdujimos**, no un defecto demostrado del CAD ni de las propiedades.
- Corrección fuente: insertar `allowFreeStandingZoneFaces false;` en la plantilla de un material; nueva utilidad `scripts/resume_material_meshes.sh` verifica los errores anteriores y reutiliza `~/OpenFOAM/C3D02_materials/{metal,mold}`, preservando `log.snappyHexMesh` y generando logs `retry1`. **No repetir `blockMesh`, ni crear carpetas nuevas, ni ejecutar solver.**
- `RUN_CASE_REGISTRY.csv` mantiene `PREPARED_NOT_RUN`; resultados geométricos y CHT **pendientes de ejecución en laptop**. [Guía de reanudación](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 2026-11-12 — C3D-02: segunda ruta de mallado preparada; NO CORRIDA

- Se revisaron los STL versionados y se comprobó por intersecciones de rayo que `(25.9,-20,25.9) mm` cae dentro de `metal.stl` y fuera de `mold_repaired.stl`; `(3,-20,25.9) mm` cae dentro del molde y fuera del metal. No se justifica cambiar puntos a ciegas.
- Como `insidePoints` en la primera malla no aisló materiales de exterior (`outerBox 15929` caras, volumen 242.130 cm³), se preparó `system/materialSingle/snappyHexMeshDict.template` y `scripts/run_material_meshes.sh`: mallar **metal y arena como dos superficies cerradas independientes**, con un solo `insidePoint` por subcaso, control de volumen aproximado, ausencia de `outerBox`, calidad exhaustiva y logs aislados en `~/OpenFOAM/C3D02_materials/`.
- Estas dos mallas no están ejecutadas ni contienen interfaces térmicas `mappedWall`. Su validación es exclusivamente la próxima puerta **geométrica**; la ingeniería CHT queda después. C14 no cambia, no hubo CFD ni modificación de RUN_CASE_REGISTRY.
- [Protocolo completo](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

## 2026-11-12 — C3D-02: primera ejecución real de mallado falló calidad y exclusión de exterior [EVIDENCIA LOCAL]

- El investigador ejecutó `bash scripts/run_mesh_only.sh` tras sincronizar GitHub y verificar materiales/STL. Siete archivos idénticos a C14, tres geometrías SHA-256 correctas, ocho vértices únicos.
- `blockMesh` y `snappyHexMesh` concluyeron. `checkMesh -allGeometry -allTopology`: **589,701 celdas, 2 boundary patches, Number of regions: 1, volumen 0.00024213 m³ (242.130 cm³), 10 caras con tetraedros deficientes, 14,586 celdas cóncavas, Failed 2 mesh checks**.
- Volumen geométrico de referencia 150.8306 cm³ (metal+arena), por lo que quedan aproximadamente **91.2994 cm³ excedentes (~60.5%)**; no se logró excluir aire/exterior ni acreditar interfaz metal–molde. **NO** hay split de regiones, malla aceptada, solver ejecutado ni validación CFD/experimental; el registro queda `PREPARED_NOT_RUN`.
- La sintaxis `insidePoints` es válida en Foundation 14 para *regiones desconectadas*, pero el resultado es **1 componente**; su mera presencia no obliga a separar dos volúmenes. **Próxima acción sin remallado:** inspeccionar los logs actuales con `scripts/diagnose_mesh_readonly.sh`, no editar parámetros ni repetir ciegamente.
- Evidencia: transcripción de terminal del investigador, logs íntegros permanecen solamente en `~/OpenFOAM/C3D02_mesh/`; no se han subido a GitHub. [Guía actualizada](docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

## 2026-11-12 — C3D-02: diccionario de mallado nativo preparado; ejecución LOCAL pendiente

- Se agregó `cases_3d/C3D_02_metal_sand_clean/system/snappyHexMeshDict` para Foundation 14 con `insidePoints` interior al metal y arena, refinamiento en ambos STL y `cellZone metal`. Esto **no** significa que el exterior haya sido eliminado o creada una interfaz térmica.
- `scripts/run_mesh_only.sh` usa **una sola carpeta `~/OpenFOAM/C3D02_mesh`** y prohíbe reejecución destructiva; genera `blockMesh`, `snappyHexMesh`, chequeo exhaustivo, resúmenes de volumen y defectos. No realiza subset/split/solver.
- Se añadió condición preliminar de volumen basada en STL (150.8306 cm³) y pruebas estáticas de sintaxis. **No existe ejecución CFD ni mallado físico confirmado en la laptop**. No cambiar `RUN_CASE_REGISTRY.csv` de `PREPARED_NOT_RUN`.
- [Procedimiento y puertas científicas](docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

## 2026-11-12 — REINICIO C3D SIN BORRAR EVIDENCIA; NUEVO CASO SIN CORRIDA

- Por decisión expresa del investigador se abandona como base el conjunto de pruebas C3D-01 y se prepara [C3D_02_metal_sand_clean](cases_3d/C3D_02_metal_sand_clean/README.md) con hierro+arena, no aire. No se borran carpetas ni se alteran resultados 2D.
- La ejecución local posterior al registro del 10-11 confirmó `splitMeshRegions -cellZones 'metal'`: par `mappedWall` metal–surrounding de **5,334 caras**, 383,788 celdas metal y 1,122,059 surrounding. Esto **no** separó arena del volumen exterior; en ambas regiones hubo 3 fallos de chequeos exhaustivos, además de componentes aisladas e índices de `faceZones` advertidos.
- `topoSet surfaceToCell` identificó 825,994 celdas dentro del STL del molde y 383,783 dentro del metal, sin solapamiento, y 296,070 sin clasificar en la caja original. Este resultado es selección por geometría, no CHT ni malla aprobada.
- `C3D01_test_moldOnly`: quitar un `insidePoint` no cambió el total de 1,505,847 celdas ni la zona metal. `C3D01_metal_sand_v1`: `subsetMesh -cellSet keepMaterials` abortó con etiqueta obsoleta `1209778` fuera del rango, indicando incongruencia entre conjunto y malla presente; no repetir sobre ese mismo directorio.
- En el árbol fuente 3D original el investigador copió desde C14 `castIron`, `silica`, sus `physicalProperties`, `fvModels`, `g`, `pRef` (**7 archivos**), confirmado por terminal el 12-11. Los cambios locales no se consideran integrados a GitHub hasta commit.
- [Informe consolidado](docs/C3D_REINICIO_20261112_ES.md) | [Comandos y fallos Foundation 14](docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md). Sin CFD 3D ni G1/J0 cerradas.

## 2026-11-10 — C3D-01: recorte metal+molde y regiones separadas, SIN interfaz CHT [EVIDENCIA LOCAL]

- En OpenFOAM Foundation 14, `topoSet surfaceToCell` mostró 6,959/6,974 celdas cóncavas fuera de ambos STL en la malla con snapping, y 21,353/21,353 en la malla castellated; 15 y 0 cóncavas, respectivamente, dentro del molde seleccionado.
- `subsetMesh -cellSet materialVolume -noFields`, **ejecutado en una copia**, generó 1,209,777 celdas, 151.230 cm³, **15 cóncavas, 8 face-tets deficientes, 17 determinantes pequeños, 3 fallos de `checkMesh`**. La forma `subsetMesh materialVolume` falló por sintaxis en Foundation 14 y fue corregida.
- `splitMeshRegions -disconnected -noFields` sobre **otra copia** produjo `region1` (molde inferido: **825,994 celdas; 103.256 cm³; 6 face-tets deficientes, 14 determinantes pequeños, 15 cóncavas; 3 fallos**) y `region2` (metal inferido: **383,783 celdas; 47.9735 cm³; 2 face-tets deficientes, 3 determinantes pequeños; 2 fallos**).
- El programa informó **`No interfaces to add`**. Los parches `oldInternalFaces` **no prueban** acoplamiento térmico metal–arena; `splitMeshRegions -cellZones 'metal'` sobre una copia de la malla original conectada sigue **propuesto, NO ejecutado**. Sin malla aceptada, sin solver CFD 3D, sin validación experimental. J0/G1 abiertas.
- Procedencia: salidas de terminal proporcionadas por el investigador hoy; logs completos conservados **solo en laptop**. Fuente canónica: [registro técnico C3D](docs/C3D_01_ESTADO_REAL_20261110_ES.md) y [manual de comandos ES](OPENFOAM_COMMAND_MANUAL_ES.md). Las entradas de octubre se conservan como historia, no como último estado.

## 2026-10-21 — GRANADA: procedencia documental B11/C11 `energy2_test` [GIT-VERIFIED; NO CFD RUN]

- File Steward detectó dos parejas de `CASE_VARIANT.md` idénticas entre `B11_energy2_test/B11_topFixedFlux_airGapOF14` y `C11_energy2_test/C11_topFixedFlux_airGapOF14`. El examen de los `fvSolution` correspondientes confirmó que ambas carpetas `energy2_test` contienen `PIMPLE.nEnergyCorrectors 2` y las variantes canónicas no.
- La duplicación documental ocultaba una distinción de entrada. Se conservaron los documentos y se añadió una advertencia de procedencia a las dos copias `energy2_test`, separando las cifras verificadas del V11 canónico de afirmaciones no verificadas para `energy2_test`.
- Evidencia y control: [revisión documental](docs/granada/B11_C11_ENERGY2_DOCUMENTATION_AUDIT_20261021.md) y prueba `tools/test_energy2_case_provenance.py`. **Sin cambios de diccionarios, sin CFD local/GitHub y sin validación experimental**. Un test de archivos no demuestra efectos físicos. La CI de procedencia se verifica por separado, por ejecución/SHA.

## 2026-10-20 — GRANADA ambiciosa: macro-bloques multi-entregable (regla adoptada)

**Orden del propietario:** evitar correcciones mínimas encadenadas; elegir campañas de desarrollo con aproximadamente **3–6 paquetes sustanciales relacionados y no interferentes**, cuando el backlog lo permita. Cada paquete debe entregar código/experiencia tangible, recuperar estados y bordes, añadir pruebas de regresión y documentar las verificaciones reales. El tamaño no justifica pisar ramas/claims, mezclar cuentas, omitir QA ni dar por concluida una aceptación física pendiente. Si algún paquete está bloqueado por login, hardware, CI o release, aparcarlo con issue/PR/SHA y continuar con otro trabajo seguro. El objetivo es hacer más, **no aparentarlo**. [Estándar maestro](https://github.com/michels-lab/Michel-Software-Standards/blob/main/standards/OPERACION_GRANADA_STANDARD.md).

**Objetivo de producto para próximas Granadas:** Validated OpenFOAM thermal/solidification model, mesh refinement, recalescence/austenite evidence, solver conservation, WSL/MPI test traceability and experimental cooling-curve comparison. Never fabricate solver measurements.

**Estado de esta entrada:** adopción del protocolo únicamente; no afirma nueva funcionalidad, tests completados, integración de código ni publicación. Todo release/producción exige autorización expresa. Conservar los PRs y pendientes previamente registrados.

# QuickCup-Solidification — Bitácora de auditoría del proyecto

**Idioma:** 🇪🇸 Español | [🇬🇧 English](./PROJECT_AUDIT_LOG_EN.md) | [↩ Selector de idioma](./PROJECT_AUDIT_LOG.md)

> Registro técnico persistente del proyecto de tesis de OpenFOAM de Michel Duarte.
>
> **Regla del proyecto (2026-09-24):** cada vez que se actualice la bitácora de trabajo en ChatGPT, la misma entrada técnica debe añadirse también a esta bitácora en Git. Las entradas deben distinguir evidencia verificada de interpretación y nunca presentar supuestos como hechos.

## Etiquetas de evidencia

- **[CHAT-RECOVERED]** Recuperado de conversaciones previas o del historial de auditoría del proyecto.
- **[RUN-VERIFIED]** Respaldado por salida de terminal/log preservada en el historial del proyecto.
- **[GIT-VERIFIED]** Confirmado contra archivos actualmente rastreados en el repositorio.
- **[INTERPRETATION]** Interpretación técnica; no es por sí misma un resultado observado directamente.
- **[OPEN]** Pendiente de verificación o simulación adicional.

---

# 0. Contexto del proyecto previo a la auditoría

## 2026-07-27 — Secuencia metodológica
**[CHAT-RECOVERED]**

La metodología de trabajo quedó definida como:

1. Composición química.
2. Datos termofísicos/de solidificación de JMatPro.
3. Modelo OpenFOAM.
4. Coladas reales / curvas térmicas Quick-Cup.
5. Comparación numérico–experimental y ajuste del modelo.

JMatPro debía proporcionar propiedades como ρ(T), cp(T), k(T), liquidus TL, solidus TS, calor latente y datos de fracción líquida para alimentar el modelo de OpenFOAM.

## 2026-07-28 — Arquitectura numérica inicial
**[CHAT-RECOVERED]**

La arquitectura numérica inicial se identificó como transferencia de calor conjugada (metal + molde), basada en el caso del doctor, con cambio de fase mediante el enfoque entalpía–porosidad / `solidificationMeltingSource`.

Características base recuperadas:

- Sección metálica: aproximadamente 40 × 40 mm.
- Configuración cuasi-2D con fronteras frontal/posterior `empty` y una celda en profundidad.
- Malla fina posteriormente verificada como 6400 celdas de metal + 5480 celdas de molde.
- Δx ≈ 0.5 mm en el metal.
- Tsol ≈ 1423 K.
- Tliq ≈ 1473 K.
- L = 2.286×10^5 J/kg.
- Cu = 10^5.
- `alpha1e = 0.8`.
- Capas interfaciales: espesor 2×10^-4 m y conductividad 0.1 W/(m·K).

Se identificaron desde temprano dos riesgos:

1. Las geometrías de `createZonesDict` podían superponerse.
2. `emmisivity` estaba mal escrito en una condición de frontera temprana de temperatura.

## 2026-07-29 — Casos de referencia del doctor
**[CHAT-RECOVERED]**

El material del doctor contenía un caso `bcFourier` y un caso CHT metal/molde. El modelo de tesis debía conservar:

- transferencia de calor conjugada,
- evolución de fase líquido/sólido,
- calor latente,
- resistencia de zona pastosa,
- probes térmicos,
- comparación con curvas experimentales de enfriamiento.

## 2026-09-03 — Dirección futura del modelo de recalescencia
**[CHAT-RECOVERED]**

Se definió una posible extensión futura: reemplazar una fracción líquida puramente definida por temperatura, fl(T), por una evolución cinética df/dt, conservando CHT, energía, momento, resistencia por porosidad y calor latente.

Se trató como una extensión posterior de física, no como justificación para modificar prematuramente la línea base validada.

## 2026-09-07 — Regla de interpretación de recalescencia
**[CHAT-RECOVERED]**

La auditoría estableció que un rebote numérico de temperatura, por sí solo, no es evidencia suficiente de recalescencia física.

Regla recuperada:

- Una recalescencia física debe surgir de cinética de transformación / subenfriamiento / liberación de calor latente.
- La formulación estándar de fracción de fase en OpenFOAM puede refundir material cuando la temperatura aumenta.
- `relax` dentro de `solidificationMeltingSource` es un parámetro de relajación numérica, no una constante cinética física.
- La validación debe demostrarse primero en el modelo reducido antes de migrar a un caso 3D completo.

## 2026-09-11 — Verificación dimensional de la fuente de calor latente
**[CHAT-RECOVERED]**

Para una formulación cinética futura, la fuente de calor latente se escribió como:

`S_L = -ρ L ∂f_l/∂t`

con unidades requeridas de W/m³.

Se consideró explícitamente que una ley simple fs(T) no es suficiente por sí sola para reproducir física genuina de subenfriamiento/recalescencia.

---

# 1. Bitácora numerada de auditoría del proyecto

## 2026-09-15

### AUD-001 — Versión de OpenFOAM
**[CHAT-RECOVERED] [GIT-VERIFIED current case headers]**

El entorno de trabajo se identificó como **OpenFOAM Foundation v14**, parche **20260724**.

Los archivos actuales del repositorio todavía contienen una mezcla de encabezados heredados de v13 y archivos actualizados a v14; la configuración de ejecución auditada en septiembre corresponde a Foundation v14.

**Impacto:** los comandos y el comportamiento de diccionarios deben verificarse contra Foundation v14 y no asumirse desde documentación de v13 u OpenCFD.

**Estado:** ✅ confirmado.

---

### AUD-002 — Estructura independiente del proyecto de trabajo
**[CHAT-RECOVERED]**

Se estableció una estructura de trabajo independiente bajo `QuickCup_Solidification/cleanproy` en lugar de modificar directamente el caso fuente original del doctor.

**Estado:** ✅ línea base histórica establecida.

---

### AUD-003 — Discrepancia en la documentación del tamaño de malla
**[CHAT-RECOVERED]**

Un valor documentado de **0.05 mm** no coincidía con la malla ejecutada.

La discretización real del metal correspondía aproximadamente a:

`Δx = Δy = 0.0005 m = 0.5 mm`

**Impacto:** la documentación previa exageraba la resolución espacial por un factor de 10.

**Estado:** ✅ discrepancia identificada; la documentación debe usar la malla realmente ejecutada salvo que se cambie la malla.

---

### AUD-004 — Tamaño global de malla
**[CHAT-RECOVERED]**

La malla contenía **11,880 celdas**.

Dimensiones recuperadas aproximadas del dominio:

- 54 mm en x,
- 55 mm en y,
- 10 mm en z.

**Estado:** ✅ confirmado durante la auditoría de malla.

---

### AUD-005 — Carácter cuasi-2D
**[CHAT-RECOVERED] [GIT-VERIFIED]**

El caso tiene una sola celda en la dirección z y patches frontal/posterior de tipo `empty`.

Por tanto, el problema numérico es cuasi-2D aunque el bloque tenga una profundidad geométrica finita de 10 mm.

**Estado:** ✅ confirmado.

---

### AUD-006 — cellZones preexistentes
**[CHAT-RECOVERED]**

Antes de ejecutar `createZones`, la malla ya contenía los cellZones `metal` y `mold`.

Esto motivó comprobar específicamente si `createZones` realmente estaba modificándolos.

**Estado:** ✅ investigado en AUD-012–014.

---

### AUD-007 — blockMesh en OpenFOAM 14
**[CHAT-RECOVERED]**

`blockMesh` terminó limpiamente bajo el entorno auditado de OpenFOAM 14.

**Estado:** ✅.

---

### AUD-008 — checkMesh
**[CHAT-RECOVERED]**

`checkMesh` devolvió:

`Mesh OK.`

Totales recuperados:

- 24,198 puntos,
- 47,738 caras,
- 11,880 celdas hexaédricas.

**Estado:** ✅.

---

### AUD-009 — Direcciones geométricas de solución
**[CHAT-RECOVERED]**

`checkMesh` identificó direcciones geométricas activas equivalentes a:

`(1 1 0)`

consistentes con la solución 2D prevista en x-y.

**Estado:** ✅.

---

### AUD-010 — Calidad de malla
**[CHAT-RECOVERED]**

Métricas recuperadas:

- no ortogonalidad: **0°**,
- skewness máximo: aproximadamente **6.94×10^-14**.

**Impacto:** una mala calidad geométrica de malla quedó descartada como causa probable del comportamiento numérico investigado.

**Estado:** ✅.

---

### AUD-011 — Conectividad y zonas
**[CHAT-RECOVERED]**

La malla sin dividir era una sola región conectada que contenía dos cellZones: `metal` y `mold`.

**Estado:** ✅.

---

### AUD-012 — Conteo de celdas por zona antes de createZones
**[CHAT-RECOVERED]**

Antes de `createZones`:

- `metal` = **6400 celdas**,
- `mold` = **5480 celdas**,
- total = **11,880 celdas**.

Los conteos coincidían exactamente con el total global.

**Estado:** ✅.

---

### AUD-013 — createZones no modificó los cellZones
**[CHAT-RECOVERED]**

`createZones` terminó sin error de ejecución, pero el archivo `cellZones` presentó el mismo hash MD5 antes y después:

`6b858d42fedaa8f291432cd603c1c890`

**Conclusión:** en esa prueba, el paso ejecutado de `createZones` **no** modificó los cellZones existentes.

**Estado:** ✅ verificado en la corrida histórica.

---

### AUD-014 — Riesgo de superposición en createZonesDict
**[CHAT-RECOVERED] [GIT-VERIFIED]**

`createZonesDict` definía:

- caja de metal: `(-0.001 -0.001 -0.001)` a `(0.041 0.041 0.011)`,
- caja de molde: `(-0.008 -0.016 -0.001)` a `(0.048 0.041 0.011)`.

Estas cajas se superponen geométricamente.

En el `Allrun` actualmente rastreado, `runApplication createZones` está comentado y los cellZones ya son creados por `blockMesh`, por lo que la superposición está inactiva en el flujo actual.

**Estado:** ⚠️ el diccionario sigue siendo potencialmente inseguro si se reactiva; actualmente no forma parte de `Allrun`.

---

### AUD-015 — Cambió la sintaxis de splitMeshRegions en OF14
**[CHAT-RECOVERED]**

Comando histórico:

`splitMeshRegions -cellZones metal mold`

falló en OpenFOAM 14 con:

`Wrong number of arguments, expected 0 found 1`

Al fallar la separación, el `foamMultiRun` posterior no encontraba la malla regional esperada `metal/polyMesh`; ese error posterior no era por tanto una falla independiente del solver.

Comando corregido:

`splitMeshRegions -cellZones all`

**Estado:** ✅ corregido.

---

### AUD-016 — Separación de regiones verificada
**[CHAT-RECOVERED] [GIT-VERIFIED workflow]**

`splitMeshRegions -cellZones all` funcionó y produjo:

- metal: **6400 celdas**,
- molde: **5480 celdas**,
- interfaz metal/molde: **240 caras**.

Los scripts `Allrun` actuales usan esta sintaxis corregida.

**Estado:** ✅.

---

### AUD-017 — Falla inicial de foamMultiRun al leer frontera
**[CHAT-RECOVERED]**

`foamMultiRun` falló leyendo `0/metal/T`, específicamente la entrada `metalTop/h`, con un fallo de lectura de diccionario tipo `attempt to read beyond EOF`.

La causa se rastreó a sintaxis de condición de frontera, no a la física CHT o de cambio de fase.

**Estado:** ✅ causa raíz identificada.

---

### AUD-018 — Corrección de sintaxis de externalWallHeatFluxTemperature
**[CHAT-RECOVERED]**

Entradas escritas como escalares:

`h 50;`

`Ta 300;`

se corrigieron a sintaxis de campo/función compatible con la condición de frontera auditada:

`h uniform 50;`

`Ta constant 300;`

Después de la corrección, el caso pudo ejecutarse.

**Estado:** ✅.

---

### AUD-019 — Ortografía de emissivity
**[CHAT-RECOVERED] [GIT-VERIFIED historical cases]**

Los casos tempranos contenían:

`emmisivity`

en lugar de:

`emissivity`

Los archivos de temperatura posteriores B2–B5/C2–C5 usan la ortografía corregida.

**Estado:** ✅ corregido en los casos posteriores; los archivos históricos tipo B1/C1 conservan la ortografía anterior como parte del historial.

---

### AUD-020 — Corrida base 0–300 s
**[CHAT-RECOVERED]**

Después de corregir los diccionarios, el caso base de OpenFOAM 14 corrió de 0 a **300 s** y terminó con:

`End`

Los conteos regionales permanecieron:

- metal 6400,
- molde 5480,
- interfaz 240 caras.

**Estado:** ✅ línea base ejecutable.

---

### AUD-021 — Buoyancy dentro de solidificationMelting
**[CHAT-RECOVERED]**

La inspección del código fuente confirmó que `solidificationMelting` agrega una contribución explícita de flotación térmica de la forma:

`Sb = ρref g β ΔT`

(referencia recuperada: `solidificationMelting.C`, alrededor de la línea 379 en el código inspeccionado).

**Impacto:** `beta` dentro del modelo de cambio de fase es dinámicamente importante; no es simple metadata.

**Estado:** ✅ comportamiento del código fuente identificado.

---

### AUD-022 — Identificada una posible doble ruta de buoyancy
**[CHAT-RECOVERED]**

Se identificaron dos rutas independientes hacia la ecuación de momento en la formulación original:

1. `icoTabulated → rho(T) → -gh∇rho → netForce → U`
2. `solidificationMelting → rhoRef*g*beta*ΔT → fvModels().source(rho,U) → U`

**Conclusión de ese momento:** la configuración original representaba la flotación térmica por dos rutas.

**Decisión controlada:** separar ambas formulaciones en vez de mantener las dos activas simultáneamente.

**Estado:** ✅ diagnóstico histórico establecido; posteriormente refinado por la auditoría de código fuente AUD-051.

---

### AUD-023 — Formulación B: buoyancy impulsada por densidad
**[CHAT-RECOVERED] [GIT-VERIFIED descendants]**

Caso controlado histórico: `B_icoTabulated_only`.

Configuración:

- `icoTabulated` / ρ(T) tabulada activa,
- `beta = 0` en `solidificationMeltingSource`,
- resistencia pastosa y calor latente activos,
- fuente Boussinesq del modelo de cambio de fase deshabilitada.

La prueba histórica completó 0–300 s.

Los descendientes actuales de la familia B conservan esta separación física: densidad tabulada + `beta 0`.

**Estado:** ✅.

---

## 2026-09-21

### AUD-024 — Formulación C: solo fuente Boussinesq
**[CHAT-RECOVERED] [GIT-VERIFIED descendants]**

Caso controlado histórico: `C_Boussinesq_only`.

Configuración:

- `rhoConst`,
- ρ = 6930 kg/m³,
- `beta = 1.13e-4 1/K` en `solidificationMeltingSource`,
- ruta de flotación por densidad dependiente de temperatura deshabilitada,
- fuente Boussinesq del modelo de cambio de fase activa.

El caso histórico completó 0–300 s.

Los descendientes actuales de la familia C conservan esta separación física.

**Estado:** ✅.

---

### AUD-025 — Comparación térmica inicial A/B/C
**[CHAT-RECOVERED]**

Ubicación del probe:

`(0.02 0.02 0.005)`

Comparación recuperada:

| Métrica | A | B | C |
|---|---:|---:|---:|
| T = 1473 K | ~0.00918 s | ~0.00918 s | ~0.00923 s |
| T = 1423 K | ~4.901 s | ~4.901 s | ~5.000 s |
| intervalo pastoso nominal | ~4.892 s | ~4.892 s | ~4.991 s |
| T ≈ 1422 K | ~21.45 s | ~21.50 s | ~21.85 s |
| T(300 s) | ~1144.46 K | ~1144.50 K | ~1144.96 K |

Diferencias máximas recuperadas:

- max ΔT A-B ≈ **0.22 K**,
- max ΔT A-C ≈ **2.05 K**.

**Interpretación en esa etapa:** cambiar la formulación de buoyancy tenía relativamente poco efecto sobre la curva térmica central frente al error de inicialización mucho mayor identificado después.

**Estado:** ✅ comparación histórica recuperada.

---

### AUD-026 — Colapso térmico inicial no físico
**[CHAT-RECOVERED]**

Todas las formulaciones A/B/C mostraban un enfriamiento inicial extremadamente rápido de aproximadamente:

`1500 K → 1473 K`

en cerca de **0.009 s**.

Como aparecía independientemente de la formulación de buoyancy, esta se descartó como causa primaria.

**Estado:** ✅ anomalía aislada; investigada en AUD-027.

---

### AUD-027 — Inconsistencia del estado inicial de alpha1
**[CHAT-RECOVERED]**

El estado de cambio de fase era inconsistente al inicio:

- T0 = 1500 K,
- T0 > Tliq = 1473 K,
- pero la fracción líquida se inicializaba efectivamente como αl = 0 cuando el campo `phaseChangeSource:alpha1` estaba ausente/no inicializado de forma consistente.

Razonamiento recuperado del código fuente: `solidificationMelting::update` recalcula la fracción líquida desde temperatura e introduce la corrección energética latente correspondiente.

Con los parámetros auditados:

- L = 2.286×10^5 J/kg,
- Cp = 827 J/(kg·K),
- `alpha1e = 0.8`,
- `relax = 0.1`,

la primera corrección de fracción líquida se estimó en Δα ≈ 0.02786, correspondiente a un cambio artificial de temperatura por energía latente de aproximadamente **7.70–7.72 K**.

**Estado:** ✅ causa principal del colapso inicial identificada.

---

### AUD-028 — alpha1 inicializada como líquido
**[CHAT-RECOVERED] [GIT-VERIFIED current normal cases]**

Un caso corregido inicializó:

`phaseChangeSource:alpha1 = 1.0`

para el metal inicialmente por encima del liquidus.

Resultado: desapareció el colapso artificial inicial de ~7.7 K.

Los casos normales actuales B1–B5/C1–C5 rastreados en Git contienen un campo inicial `phaseChangeSource:alpha1` con `internalField uniform 1.0`.

**Estado:** ✅ corrección adoptada.

---

### AUD-029 — Fase inicial termodinámicamente consistente
**[CHAT-RECOVERED]**

Con αl(0)=1 y T0>Tliq, la simulación ya no comienza con fracción sólida artificial por encima del liquidus.

Esto se convirtió en la convención requerida de estado inicial para los casos normales de cambio de fase.

**Estado:** ✅.

---

### AUD-030 — Sin entrada recuperada
**[CHAT-RECOVERED]**

No se encontró contenido histórico para AUD-030. La numeración de la conversación original saltó de AUD-029 a AUD-031.

El identificador se deja intencionalmente sin uso en vez de inventar retroactivamente una entrada.

**Estado:** — hueco de numeración preservado.

---

### AUD-031 — El rebote de temperatura estuvo acompañado por refusión
**[CHAT-RECOVERED]**

En el caso corregido D:

- mínimo local T ≈ 1455 K cerca de **4.90 s**,
- la temperatura subió a aproximadamente **1461.18 K** alrededor de **11.6 s**,
- durante el rebote, la fracción líquida aumentó aproximadamente **0.9283 → 0.9527**.

**Conclusión:** el rebote involucró **refusión parcial** dentro de la formulación estándar de equilibrio/relajada de `solidificationMelting`.

No debe etiquetarse automáticamente como recalescencia física.

**Estado:** ✅ interpretación corregida.

---

### AUD-032 — Comportamiento de solidificación corregido en corrida larga
**[CHAT-RECOVERED]**

Para el caso D corregido con αl(0)=1:

- cruce de liquidus 1473 K: aproximadamente **3.2506 s**,
- αl = 0.99: aproximadamente **3.5624 s**,
- cruce de temperatura solidus 1423 K: aproximadamente **104.9 s**,
- αl = 0.50: aproximadamente **207.56 s**,
- αl = 0.01: aproximadamente **227.59 s**,
- a 300 s: αl = 0,
- T(300 s) ≈ **1329.77 K**.

**Impacto:** corregir la inicialización de fase transformó la escala aparente de solidificación, de un colapso inmediato no físico a un proceso largo de cambio de fase.

**Estado:** ✅.

---

# 2. Cronología adicional recuperada después de la auditoría numerada

## 2026-09-18 — Arquitectura de validación
**[CHAT-RECOVERED]**

Se separaron conceptualmente tres niveles de modelo:

1. **Nivel 1:** fs(T) base.
2. **Nivel 2:** fs(T) informado por JMatPro/Scheil.
3. **Nivel 3:** cinético fs(T,t,ΔT,nucleación/crecimiento).

La validación no debe depender solo de RMSE. Las cantidades objetivo incluyen:

- temperaturas de liquidus / transformación,
- temperatura mínima antes del rebote,
- temperatura recuperada/de rebote,
- ΔTrec,
- dT/dt,
- tiempo de inicio,
- duración,
- evolución de fracción de fase.

Los parámetros no deben ajustarse simplemente para forzar coincidencia.

---

## 2026-09-21 — Auditoría de convergencia y loops del solver B2/C2
**[CHAT-RECOVERED] [RUN-VERIFIED historical logs]**

Se estableció una distinción de control multi-región:

- `system/fvSolution` raíz controla el acoplamiento PIMPLE global de `foamMultiRun` (`nOuterCorrectors`, `nEnergyCorrectors`),
- `system/metal/fvSolution` y `system/mold/fvSolution` controlan los solvers lineales regionales y sus correctores locales.

La configuración C2 recuperada incluía `nOuterCorrectors 1` en raíz, mientras metal tenía sus propios correctores de presión/velocidad.

Valores representativos de C2 alrededor de t≈0.1 s:

- Courant medio ≈ 0.00054–0.00057,
- Courant máximo ≈ 0.00466–0.00488,
- residual de energía reducido a ~10^-10–10^-8 en los pasos muestreados,
- residuales finales de presión alrededor de ~10^-7 después de corrección.

Evidencia recuperada al final de B2:

- energía metal aproximadamente 4.68×10^-5 → 1.42×10^-11,
- energía molde aproximadamente 3.73×10^-5 → 3.69×10^-10,
- error acumulado de continuidad aproximadamente -1.7486×10^-7,
- corrida terminó con `End`.

Un diagnóstico de flujo de B2 también encontró media volumétrica |U| de aproximadamente:

- **0.0115–0.0116 m/s** cerca de 2 s,
- **0.0079 m/s** alrededor de 6.5 s.

Se observaron picos de velocidad antes de rebotes térmicos, pero no se consideró demostrada una relación causal convectiva.

---

## 2026-09-22 — B3_docFV / C3_docFV
**[CHAT-RECOVERED] [GIT-VERIFIED configuration]**

B3/C3 se crearon como descendientes de convergencia/documentación de B2/C2 con estructura revisada de `fvSolution`.

Corrida B3 recuperada:

- 0–10 s,
- Δt = 0.001 s,
- 10,000 pasos temporales,
- ~189.5 s CPU / ~197 s wall time,
- sin fallo,
- `nOuterCorrectors=2` en raíz,
- `nEnergyCorrectors` omitido → default 1,
- aproximadamente 2 soluciones de h, 2 de e y 4 de p_rgh por timestep,
- Courant máximo ≈ **0.175912**,
- Courant final ≈ **0.0607**,
- continuidad acumulada ≈ **1.66260×10^-4**.

Corrida C3 recuperada:

- 0–10 s,
- misma estructura Δt = 0.001 s,
- ~192.6 s CPU,
- sin fallo,
- mismas 2 h / 2 e / 4 p_rgh por timestep,
- Courant máximo ≈ **0.0701958**,
- Courant final ≈ **0.0245**,
- continuidad acumulada ≈ **1.78365×10^-4**.

**Estado:** ✅ B3/C3 completados y convertidos en referencia de convergencia para las siguientes pruebas controladas.

---

## 2026-09-22 — B4_energy2 / C4_energy2
**[CHAT-RECOVERED] [GIT-VERIFIED configuration]**

B4/C4 se crearon copiando B3/C3 y cambiando el acoplamiento multi-región raíz para incluir:

`nEnergyCorrectors 2;`

manteniendo el resto de configuraciones B3/C3.

**Propósito experimental:** aislar el efecto de repetir la corrección de energía en el acoplamiento multi-región global.

**Importante:** en ese punto histórico todavía no había evidencia recuperada que estableciera resultados cuantitativos B4/C4. No debía inventarse una conclusión antes de inspeccionar logs/resultados reales.

**Estado histórico:** 🟡 configuración verificada; el resultado cuantitativo se documentó posteriormente.

---

# 3. Auditoría del repositorio actual — 2026-09-24

## Estado del repositorio
**[GIT-VERIFIED]**

Repositorio:

`realmichelduarte/QuickCup-Solidification`

Último commit auditado en ese momento:

`614ee6e186a3dfbbbec159b27c4d89015703a95f`

Mensaje:

`Add convergence tests and update buoyancy cases`

El directorio `cases_buoyancy` contenía **12 casos** y **382 archivos de caso rastreados**.

Los casos normales B1–B5/C1–C5 contenían 32 archivos rastreados cada uno; los dos casos de control contenían 31.

### Linaje de casos en ese momento

- `B1_alphaini`
- `B2_test`
- `B3_docFV`
- `B4_energy2`
- `B5_outer3`
- `B_betazero`

y

- `C1_alphaini`
- `C2_test`
- `C3_docFV`
- `C4_energy2`
- `C5_outer3`
- `C_rhoconstant`

---

## 2026-09-24 — Auditoría SHA completa de todos los casos buoyancy
**[GIT-VERIFIED]**

Todos los archivos rastreados bajo `cases_buoyancy` se compararon por ruta relativa y blob SHA.

Solo estas rutas relativas variaban entre generaciones:

1. `0/metal/T`
2. `0/metal/phaseChangeSource:alpha1` (ausente en los dos casos de control)
3. `constant/metal/fvModels`
4. `constant/metal/materials/castIron`
5. `system/controlDict`
6. `system/functions`
7. `system/fvSolution`
8. `system/metal/fvSolution`
9. `system/mold/fvSolution`

Todos los demás archivos correspondientes eran idénticos dentro de sus grupos SHA.

---

## 2026-09-24 — Separación física B/C en ese momento
**[GIT-VERIFIED]**

### Familia B

La configuración B5 preservaba:

- `equationOfState icoTabulated`,
- ρ(T) tabulada,
- `beta 0` en `solidificationMeltingSource`,
- g=(0,-9.81,0),
- modelo de momento laminar,
- coeficiente externo de transferencia de calor en `metalTop`: h=10 W/(m²·K).

### Familia C

La configuración C5 preservaba:

- `equationOfState rhoConst`,
- ρ=6930 kg/m³,
- `beta 1.13e-04` en `solidificationMeltingSource`,
- misma aceleración gravitacional,
- coeficiente externo `metalTop`: h=50 W/(m²·K).

---

## 2026-09-24 — Secuencia de convergencia en ese momento
**[GIT-VERIFIED]**

### B3/C3 — referencia
`system/fvSolution` raíz:

- `nOuterCorrectors 2`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

### B4/C4 — experimento de corrector de energía
Misma estructura de referencia más:

- `nEnergyCorrectors 2`

### B5/C5 — experimento de outer correctors
`system/fvSolution` raíz:

- `nOuterCorrectors 3`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

Por tanto, B5/C5 **no** eran descendientes acumulativos del cambio B4/C4. Eran un experimento independiente respecto a B3/C3: el corrector de energía volvía al valor por defecto y el acoplamiento exterior global aumentaba de 2 a 3.

Configuración regional de metal en B5/C5:

- `momentumPredictor no`
- `nOuterCorrectors 1`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 0`

---

## 2026-09-24 — Asimetría startFrom en B5/C5
**[GIT-VERIFIED]**

- B5: `startFrom latestTime;`
- C5: `startFrom startTime;`

Si ambos casos se limpian antes de ejecutarse, esta diferencia no debería cambiar una corrida fresca desde el directorio `0`. Sin limpieza, B5 puede reanudar una solución previa mientras C5 inicia explícitamente desde el tiempo configurado.

**Impacto:** debe controlarse al comparar B5 y C5.

**Estado:** ⚠️ diferencia conocida de reproducibilidad.

---

## 2026-09-24 — Configuración de probes
**[GIT-VERIFIED]**

Los casos normales B1–B5/C1–C5 contienen un `temperatureProbe` en:

`(0.02 0.02 0.005)`

que registra:

- `T`
- `phaseChangeSource:alpha1`

en cada timestep.

Los dos casos de control solo registran `T`.

---

## 2026-09-24 — Solicitud del asesor de perfiles lineales
**[CHAT-RECOVERED] [GIT-VERIFIED absence in current cases]**

El asesor pidió perfiles de velocidad/temperatura directamente mediante OpenFOAM en vez de ParaView.

En ese momento los casos actuales **todavía no contenían un function object de muestreo lineal**.

OpenFOAM v14 dispone de mecanismos de muestreo line/graph apropiados para extraer campos sobre una línea. Entre las salidas candidatas para la tesis:

- T(x,t),
- U(x,t),
- |U|(x,t),
- αl(x,t),

y relaciones derivadas como |U|=f(T) en posiciones muestreadas coincidentes.

Líneas centrales potenciales de la sección metálica 40 × 40 mm:

- horizontal: (0,0.020,0.005) → (0.040,0.020,0.005)
- vertical: (0.020,0,0.005) → (0.020,0.040,0.005)

**Estado:** 🟡 solicitado; implementación todavía no añadida en ese momento.

---

# 4. Reglas permanentes de interpretación y reproducibilidad

1. **No llamar “recalescencia” a un rebote de temperatura únicamente porque dT/dt > 0.** Revisar evolución de fase y si el modelo está solidificando o refundiendo.
2. **No mezclar cambios del modelo físico con cambios de convergencia numérica en una misma comparación controlada.**
3. **Registrar siempre nombre exacto del caso, caso padre, archivos modificados, parámetro numérico cambiado, intervalo de corrida y diagnósticos relevantes.**
4. **Para comparaciones B/C, preservar la separación de buoyancy prevista:** B = ruta impulsada por densidad; C = ruta de fuente Boussinesq.
5. **Metal líquido inicial por encima de Tliq debe inicializarse consistentemente con αl=1.**
6. **Una salida exitosa del solver no basta como validación.** Seguir Courant, residuales, continuidad, evolución energética, fracción de fase y comparación con curvas experimentales.
7. **Cada vez que se actualice esta bitácora en el hilo de trabajo de ChatGPT, actualizar también el archivo Git correspondiente.**
8. **Si una entrada antigua no puede recuperarse exactamente, marcar explícitamente la incertidumbre en vez de rellenar el hueco por inferencia.**

---

# 5. Elementos abiertos en ese punto

- [ ] Inspeccionar/recuperar resultados cuantitativos B4/C4 si sus logs todavía existen fuera de Git.
- [ ] Ejecutar/analizar B5/C5 y compararlos contra B3/C3 y B4/C4 con las mismas métricas.
- [ ] Añadir muestreo lineal nativo de OpenFOAM para U, T y αl sin cambiar la física del solver.
- [ ] Definir una pipeline reproducible para graficar perfiles velocidad/temperatura.
- [ ] Continuar validación experimental/JMatPro y mantener separada la interpretación de recalescencia respecto a la refusión de equilibrio.

---

## 2026-09-24 — AUD-033 — La comparación B/C contenía una diferencia térmica adicional
**[GIT-VERIFIED]**

Una auditoría del repositorio encontró que los descendientes B2–B5 y C2–C5 diferían no solo en la formulación de buoyancy, sino también en el coeficiente externo de transferencia de calor de `metalTop`:

- B2–B5: `h = 10 W/(m²·K)`
- C2–C5: `h = 50 W/(m²·K)`

Esta diferencia ya estaba presente en el commit inicial del repositorio (`206f9594`) y seguía presente en los archivos.

**Impacto:** si B y C pretendían ser una comparación controlada de formulaciones de buoyancy, las curvas térmicas B/C no podían atribuirse únicamente a buoyancy mientras `h` también fuera distinto.

**Acción requerida antes de interpretar:** determinar si la diferencia B/C de coeficiente de transferencia era una representación intencional de dos condiciones físicas/experimentales distintas o una variable de confusión no intencional. Hasta resolverlo, reportar B/C como comparación multiparámetro.

**Estado:** ⚠️ asunto metodológico abierto; no modificar retroactivamente los casos históricos.

---

## 2026-09-24 — AUD-034 — El cambio térmico B2 no tenía justificación de diseño recuperada
**[CHAT-RECOVERED] [GIT-VERIFIED]**

El contexto histórico confirmó que:

- `B2_test` fue creado copiando `B1_alphaini`.
- `C2_test` fue creado copiando `C1_alphaini`.
- B2/C2 se diseñaron como pruebas numéricas/de convergencia cortas (~10 s).
- Los cambios documentados posteriores se referían al timestep, por ejemplo un intento `deltaT=0.1` que falló, seguido por retorno a `deltaT=0.001`, además de la cadencia de salida.

El historial Git mostraba:

- `B1_alphaini/0/metal/T`: `metalTop h = 50 W/(m²·K)`
- `B2_test/0/metal/T`: `metalTop h = 10 W/(m²·K)`
- `C1_alphaini/0/metal/T`: `metalTop h = 50 W/(m²·K)`
- `C2_test/0/metal/T`: `metalTop h = 50 W/(m²·K)`

No se recuperó ninguna entrada de bitácora o decisión conversacional que documentara una razón física deliberada para cambiar la rama B de 50 a 10 al crear B2.

**Regla de interpretación:** el cambio B1→B2 en `h` debe tratarse como un **cambio de modelo no documentado**, no como una decisión validada. Tampoco debe asumirse accidental sin evidencia adicional.

**Impacto:** B2–B5 vs C2–C5 están térmicamente confundidos salvo que se cree una comparación controlada con `h` común.

**Estado:** ⚠️ origen no resuelto; conservar casos históricos e investigar antes de interpretar físicamente.

---

## 2026-09-24 — AUD-035 — Coeficiente convectivo común recomendado para rerun B/C controlado
**[GIT-VERIFIED] [LITERATURE-SUPPORTED] [DECISION]**

Para la comparación B/C controlada planeada, el coeficiente de convección de la superficie superior debe ser idéntico en ambas ramas.

Línea base recomendada:

`metalTop h = 10 W/(m²·K)`

Razones:

- OpenFOAM trata `h` como coeficiente convectivo externo y `emissivity` como contribución radiativa separada.
- La geometría Quick-Cup representa una pequeña muestra abierta de metal fundido expuesta al aire ambiente.
- Correlaciones de convección natural para una placa horizontal caliente orientada hacia arriba sitúan el orden esperado alrededor de ~10 W/(m²·K) para esta longitud característica; `h = 50 W/(m²·K)` sería más consistente con flujo de aire forzado significativo o con un coeficiente efectivo que agrupe otros modos de transferencia.
- Como la radiación ya se representa explícitamente con `emissivity = 0.3`, el `h` convectivo no debería inflarse para representar radiación.

**Regla de implementación:** conservar B5/C5 históricos sin cambios. Crear una nueva comparación controlada derivada de B5/C5 donde la única diferencia física intencional sea la formulación de buoyancy y ambos usen `metalTop h = 10 W/(m²·K)`.

**Estado:** ✅ elección de línea base establecida; nuevos casos controlados todavía no creados/ejecutados en ese momento.

---

## 2026-09-24 — AUD-036 — La serie controlada B/C debe repetirse con frontera térmica común
**[METHODOLOGICAL DECISION] [GIT-VERIFIED BASIS]**

Debido a que los linajes B2–B5 y C2–C5 usaban coeficientes `metalTop` diferentes (`h=10` en B y `h=50` en C), esos casos históricos no eran válidos para una comparación controlada directa de las formulaciones de buoyancy.

### Consecuencia

- B2–B5/C2–C5 históricos siguen siendo útiles como historial de desarrollo y para observaciones numéricas dentro de cada familia.
- **No** son adecuados para atribuir diferencias B-vs-C únicamente a buoyancy.
- La secuencia de convergencia debe repetirse con `metalTop h` común si la tesis requiere comparación objetiva.

### Regla de nueva serie controlada

Usar la misma frontera térmica en ambas familias:

`metalTop h = 10 W/(m²·K)`

y reproducir simétricamente:

1. referencia,
2. referencia documentada con `nOuterCorrectors=2`,
3. prueba de energía con `nEnergyCorrectors=2`,
4. prueba de outer correctors con `nOuterCorrectors=3`.

Todas las demás configuraciones deben permanecer igualadas salvo la propia formulación de buoyancy.

### Regla de preservación

No sobrescribir ni borrar los B2–B5/C2–C5 históricos. Conservarlos como registro auditable y crear un nuevo linaje controlado limpio.

**Estado:** ✅ corrección metodológica establecida; reruns pendientes en ese momento.

---

## 2026-09-24 — AUD-037 — Auditoría B/C par a par identifica la serie limpia
**[GIT-VERIFIED] [METHODOLOGICAL CORRECTION]**

Se realizó una auditoría SHA completa para:

- `B2_test ↔ C2_test`
- `B3_docFV ↔ C3_docFV`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

### B2/C2

B2 y C2 diferían en **seis** archivos rastreados:

1. `0/metal/T`
2. `constant/metal/fvModels`
3. `constant/metal/materials/castIron`
4. `system/controlDict`
5. `system/fvSolution`
6. `system/metal/fvSolution`

Desajuste numérico importante:

- B2 raíz: `nOuterCorrectors 1`
- C2 raíz: `nOuterCorrectors 4`, `nEnergyCorrectors 1`

Por tanto, B2/C2 eran casos transicionales de desarrollo, no un par B-vs-C controlado.

### B3/C3

B3/C3 diferían solo en **cuatro** archivos:

1. `0/metal/T`
   - B3: `h = 10 W/(m²·K)`
   - C3: `h = 50 W/(m²·K)`
2. `constant/metal/fvModels`
   - B3: `beta = 0`
   - C3: `beta = 1.13e-04`
3. `constant/metal/materials/castIron`
   - B3: `icoTabulated` con densidad dependiente de temperatura
   - C3: `rhoConst = 6930 kg/m³`
4. `system/controlDict`
   - B3: `startFrom latestTime`
   - C3: `startFrom startTime`

Todos los demás archivos eran idénticos por SHA.

### B4/C4

B4/C4 diferían en exactamente los mismos cuatro archivos.

Ambos usaban:

- `nOuterCorrectors 2`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`
- `nEnergyCorrectors 2`

### B5/C5

B5/C5 diferían también en esos mismos cuatro archivos.

Ambos usaban:

- `nOuterCorrectors 3`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

### Clasificación de diferencias B3–B5/C3–C5

**Diferencias físicas intencionales a conservar:**

1. `fvModels/beta`
2. `castIron/equationOfState`

**Diferencias no físicas a normalizar:**

3. `metalTop/h`
4. `controlDict/startFrom`

Para el rerun controlado:

- `metalTop h = 10 W/(m²·K)` en ambas familias.
- `startFrom startTime` en ambas.
- correr desde estado limpio.

### Plan corregido

La serie de convergencia científicamente útil comienza en B3/C3. B2/C2 permanecen como casos históricos transicionales y **no** deben recrearse como si fueran un par controlado.

Se requieren seis casos:

- B3-controlled / C3-controlled — referencia
- B4-controlled / C4-controlled — `nEnergyCorrectors=2`
- B5-controlled / C5-controlled — `nOuterCorrectors=3`

Dentro de cada par, todos los inputs deben ser idénticos excepto las dos diferencias de modelo de buoyancy.

Esta entrada reemplaza la redacción más amplia de AUD-036 que sugería repetir B2–B5/C2–C5 como una sola secuencia controlada.

**Estado:** ✅ auditoría par a par completa; construcción de casos controlados pendiente en ese momento.

---

## 2026-09-24 — AUD-038 — La rama C controlada usará rhoConst = 6820 kg/m³
**[USER DECISION] [GIT-CONTEXT VERIFIED] [SOURCE-CHECKED]**

Para la nueva serie controlada de comparación de buoyancy, la familia C usará:

`rho = 6820 kg/m³`

en vez de 6930 kg/m³.

Razón desde la definición material B:

- B usa `icoTabulated` con `rho0 = 6820 kg/m³` a `T0 = 1473 K`.
- La tabla también da aproximadamente ρ = 6820 kg/m³ cerca del liquidus (~1473 K).

Esto convierte 6820 kg/m³ en la densidad de referencia seleccionada para los nuevos casos C.

### Parámetro acoplado importante

La fuente de buoyancy de `solidificationMelting` usa:

`Sb = rhoRef * g * beta * deltaT`

por lo que `rhoRef` escala directamente la fuente Boussinesq.

Si la rama C debe ser internamente consistente con una única densidad de referencia 6820 kg/m³, `constant/metal/fvModels` también debe usar:

`rhoRef 6820;`

en lugar del valor histórico 6930.

**Estado:** ✅ `rhoConst=6820` decidido; `rhoRef=6820` recomendado y posteriormente implementado.

---

## 2026-09-24 — AUD-039 — Serie controlada de comparación de buoyancy creada
**[GIT-VERIFIED] [IMPLEMENTED]**

Se creó una nueva familia fuera de `cases_buoyancy/`:

`cases_controlled_buoyancy/`

Los casos históricos permanecieron sin cambios.

### Casos controlados

- `B3_reference` — derivado de `B3_docFV`
- `C3_reference` — derivado de `C3_docFV`
- `B4_energy2` — derivado de `B4_energy2`
- `C4_energy2` — derivado de `C4_energy2`
- `B5_outer3` — derivado de `B5_outer3`
- `C5_outer3` — derivado de `C5_outer3`

### Normalizaciones aplicadas

1. `metalTop h = 10 W/(m²·K)`
2. `startFrom startTime`
3. Los ajustes numéricos históricos de los experimentos 3/4/5 se preservaron.

### Rama C

- `equationOfState rhoConst`
- `rho = 6820 kg/m³`
- `beta = 1.13e-04 1/K`
- `rhoRef = 6820 kg/m³`

### Rama B

- `equationOfState icoTabulated`
- densidad dependiente de temperatura
- `beta = 0` en `solidificationMeltingSource`

### Regla de reproducibilidad

Los pares 3/4/5 deben ser idénticos en todos los inputs rastreados excepto:

- `constant/metal/fvModels`
- `constant/metal/materials/castIron`

**Estado:** ✅ serie controlada creada; auditoría SHA posterior requerida.

---

## 2026-09-24 — AUD-040 — La serie controlada pasa la verificación SHA par a par
**[GIT-VERIFIED] [VALIDATED INPUT SET]**

Se auditó cada par:

- `B3_reference ↔ C3_reference`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

En los tres pares, los únicos archivos diferentes fueron:

1. `constant/metal/fvModels`
2. `constant/metal/materials/castIron`

### Ajustes comunes verificados

Ambas ramas usan:

- `metalTop h = 10 W/(m²·K)`
- `startFrom startTime`

### Rama C verificada

- `rhoConst`
- `rho = 6820 kg/m³`
- `beta = 1.13e-04 1/K`
- `rhoRef = 6820 kg/m³`

### Rama B verificada

- `icoTabulated`
- densidad dependiente de temperatura
- `beta = 0`

### Conclusión

La serie 3/4/5 quedó adecuada para una comparación B-vs-C objetiva porque cada par era idéntico salvo los archivos que implementan las dos formulaciones de buoyancy/densidad.

**Estado:** ✅ auditoría del set de inputs aprobada.

---

## 2026-09-24 — AUD-041 — Regla de sincronización README + Audit Log
**[PROCESS RULE] [IMPLEMENTED]**

La documentación de la serie controlada adoptó una regla de dos documentos:

1. La bitácora preserva la historia cronológica: qué cambió, por qué, evidencia, impacto y estado.
2. `cases_controlled_buoyancy/README.md` describe la configuración y flujo actualmente aceptados.

Cada cambio relevante en física, propiedades, fronteras, numerics, malla, timestep, probes, postproceso, nomenclatura o metodología de comparación debe reflejarse en ambos.

El README se amplió con:

- propósito de la serie B/C limpia,
- matriz de casos,
- configuraciones comunes,
- formulaciones B y C,
- `h = 10 W/(m²·K)`,
- `startFrom startTime`,
- `rho = rhoRef = 6820 kg/m³` en C,
- validación SHA,
- orden recomendado de ejecución,
- cantidades a comparar,
- trabajo planeado de perfiles,
- regla de mantenimiento.

**Estado:** ✅ regla activa.

---

## 2026-09-24 — AUD-042 — Los logs controlados pasan a versionarse
**[PROCESS RULE] [IMPLEMENTED]**

Se refinó la política de logs para simulaciones controladas.

Los logs generales seguían ignorados por defecto, pero esta ruta pasó a rastrearse explícitamente:

`cases_controlled_buoyancy/**/log.foamMultiRun`

### Razón

El log primario de `foamMultiRun` forma parte de la evidencia numérica porque contiene Courant, residuals, continuidad, progreso del solver y tiempos.

Los directorios temporales calculados, mallas generadas, logs generales y otros outputs grandes permanecían ignorados salvo selección deliberada.

**Estado:** ✅ `log.foamMultiRun` controlado incorporado al registro científico versionado.

---

## 2026-09-24 — AUD-043 — Logs de simulación rastreados por defecto
**[PROCESS RULE] [IMPLEMENTED]**

La política de retención se amplió.

Política anterior:

- logs generales ignorados,
- solo `cases_controlled_buoyancy/**/log.foamMultiRun` exento.

Política actual:

- logs de simulación y runtime **no se ignoran por defecto**,
- se eliminaron reglas amplias como `**/log.*`, `**/*.log` y `**/nohup.out`,
- los logs se consideran parte de la evidencia numérica/científica,
- logs temporales de editor como `.vscode/*.log` pueden seguir ignorados.

Directorios de tiempos calculados, mallas, postProcessing, media y builds siguen ignorados salvo selección deliberada.

**Impacto:** futuros logs OpenFOAM pueden añadirse a Git normalmente sin `git add -f`.

**Estado:** ✅ regla activa.

---

## 2026-09-24 — AUD-044 — Logs B3/C3 controlados guardados
**[GIT-VERIFIED] [RUN ARTIFACTS PRESERVED]**

Se ejecutaron localmente `B3_reference` y `C3_reference` y sus logs primarios se subieron a Git.

Archivos:

- `cases_controlled_buoyancy/B3_reference/log.foamMultiRun`
- `cases_controlled_buoyancy/C3_reference/log.foamMultiRun`

Commit:

`d6c307c8ac62755bf103fc15f4505874904c9bb9`

Tamaños aproximados:

- B3: 19.61 MB
- C3: 19.61 MB

Todavía no se registró interpretación cuantitativa en esa entrada. Debían extraerse Courant, residuals, continuidad, tiempo, temperatura y fracción de fase.

**Estado:** ✅ artefactos preservados; análisis cuantitativo pendiente en ese punto.

---

## 2026-09-24 — AUD-045 — Análisis de solver logs B3/C3
**[RUN-VERIFIED] [GIT-VERIFIED]**

Los `log.foamMultiRun` de `B3_reference` y `C3_reference` fueron analizados sobre los 0–10 s completos.

Ambos:

- ejecutaron 10,000 pasos con `deltaT = 0.001 s`,
- alcanzaron `Time = 10`,
- terminaron con `End`,
- sin `FOAM FATAL`,
- sin `WARNING`.

### Courant

B3:

- pico `Co_max = 0.175912` cerca de t = 0.283 s,
- Co medio en ese instante = 0.00742715,
- último `Co_max = 0.0606638`.

C3:

- pico `Co_max = 0.0700709` cerca de t = 2.510 s,
- Co medio = 0.0205809,
- último `Co_max = 0.0241928`.

Ambos picos están por debajo de `maxCo = 0.25`; como `adjustTimeStep no`, ese valor era umbral de comparación y no controlador activo.

### Continuidad

B3:

- máximo absoluto acumulado ≈ 1.70032e-4,
- final = 1.66260e-4.

C3:

- máximo absoluto acumulado ≈ 1.78360e-4,
- final = 1.78349e-4.

En la corrección final:

- B3: ~-1.14209e-11,
- C3: ~1.25471e-13.

### Residuales finales a 10 s

B3:

- h metal: 8.73216e-11,
- e molde: 3.73694e-10,
- p_rgh final: 3.88108e-8.

C3:

- h metal: 2.46231e-11,
- e molde: 3.76994e-10,
- p_rgh final: 2.68792e-8.

Después del transitorio inicial t≥0.1 s, los máximos residuales finales de las ecuaciones térmicas permanecieron por debajo de aproximadamente:

- B3: 4.27e-7 para h metal, 6.03e-8 para e molde,
- C3: 3.76e-7 para h metal, 6.01e-8 para e molde.

### Costo computacional

B3:

- ExecutionTime = 249.556 s,
- ClockTime = 258 s.

C3:

- ExecutionTime = 224.372 s,
- ClockTime = 225 s.

En estas corridas concretas, B3 consumió ~11.2% más CPU y ~14.7% más wall time. Es descriptivo de estas ejecuciones y no debe generalizarse sin repeticiones/control de carga.

### Límite interpretativo

Los logs demuestran que ambos casos completaron numéricamente sin fallo. Por sí solos no establecen la diferencia térmica/de fase.

Se requerían los probes de:

- T(t) central,
- `phaseChangeSource:alpha1(t)` central.

**Estado:** ✅ auditoría de solver logs completa; comparación térmica/de fase pendiente en ese punto.

---

## 2026-09-24 — AUD-045 — Corridas B3/C3 revisadas cuantitativamente
**[RUN-VERIFIED] [GIT-VERIFIED]**

Se revisaron los logs versionados del par controlado.

### B3_reference

- CPU: **249.556 s**
- Clock: **258 s**
- Courant máximo: **0.175912**
- Courant final: media **0.0154644**, máximo **0.0606638**
- continuidad acumulada final: **1.66260e-4**
- h metal final representativo: 4.54417e-05 → 9.91429e-09
- segundo solve h final: 8.43592e-08 → 8.73216e-11
- p_rgh final: **3.88108e-08**

### C3_reference

- CPU: **224.372 s**
- Clock: **225 s**
- Courant máximo: **0.0700709**
- Courant final: media **0.00934688**, máximo **0.0241928**
- continuidad acumulada final: **1.78349e-4**
- h metal final: 5.6893e-05 → 9.49871e-09
- segundo solve h final: 3.18791e-08 → 2.46231e-11
- p_rgh final: **2.68792e-08**

### Comparación

B3 usó ~11.2% más CPU que C3 y alcanzó un Courant máximo ~2.51× mayor.

Ambos permanecieron cómodamente por debajo de Courant 1 y terminaron sin divergencia.

Los errores acumulados de continuidad son del mismo orden (~1e-4), con C3 ligeramente mayor.

**Límite:** un Courant mayor en B3 es compatible con velocidades más altas en alguna zona, pero el log no establece la topología espacial ni su importancia térmica.

**Estado:** ✅ comparación a nivel solver completa.

---

## 2026-09-24 — AUD-046 — Análisis de probes centrales B3/C3
**[RUN-VERIFIED] [GIT-VERIFIED]**

Se compararon directamente:

- `postProcessing/metal/temperatureProbe/0/T`
- `postProcessing/metal/temperatureProbe/0/phaseChangeSource:alpha1`

Cada archivo contiene 10,001 muestras entre 0 y 10 s con Δt=0.001 s en `(0.02 0.02 0.005) m`.

### Métricas principales

B3:
- primer cruce descendente de liquidus 1473 K: **6.666 s**,
- primera desviación de `alpha1` respecto a 1: **6.668 s**,
- `alpha1 = 0.99`: ~**9.619 s**,
- T centro a 10 s: **1467.45 K**,
- `alpha1` final: **0.978184**.

C3:
- primer cruce descendente de 1473 K: **3.386 s**,
- primera desviación de `alpha1`: **3.388 s**,
- `alpha1 = 0.99`: ~**3.654 s**,
- T mínima central: **1456.25 K a 4.822 s**,
- `alpha1` mínimo: **0.932983 a 4.878 s**,
- T final: **1461.60 K**,
- `alpha1` final: **0.954394**.

Diferencias:

- C3 alcanza liquidus ~**3.280 s antes**.
- máxima diferencia absoluta de T central: ~**33.42 K a 4.644 s**.
- máxima diferencia absoluta de fracción líquida: ~**0.067017 a 4.878 s**.
- a 10 s, B3 está **5.85 K más caliente** y tiene ~**0.02379** más fracción líquida.

### Comportamiento no monótono

C3 presenta rebote:

- T: 1456.25 K a 4.822 s → 1461.60 K a 10 s (**+5.35 K**),
- alpha1: 0.932983 a 4.878 s → 0.954394 a 10 s (**+0.021411**).

El aumento simultáneo de T y fracción líquida es evidencia directa de **refusión local en el modelo numérico**.

B3 presenta una reversión menor:

- primer cruce descendente liquidus: 6.666 s,
- mínimo local inicial `alpha1 = 0.997042` a 7.045 s,
- retorno a `alpha1 = 1.0` a 7.460 s,
- cruce ascendente de 1473 K ~7.447 s,
- segundo cruce descendente ~9.069 s.

### Límite interpretativo

La comparación demuestra historias térmicas y de fase materialmente distintas aunque solver y fronteras estén controlados.

Los rebotes **no deben llamarse recalescencia física** a partir de estos datos. La formulación actual puede producir transporte convectivo y refusión local. Hace falta analizar perfiles/campo de velocidad y comparar con curvas experimentales.

**Estado:** ✅ comparación solver + térmica/fase completa; 🟡 validación experimental aún pendiente.

---

## 2026-09-24 — AUD-047 — Prueba B4/C4 de nEnergyCorrectors
**[RUN-VERIFIED] [GIT-VERIFIED]**

Los casos `B4_energy2` y `C4_energy2` y sus probes se compararon contra B3/C3. El único cambio intencional era aumentar `nEnergyCorrectors` raíz de 1 a 2.

Ambos:

- llegaron a 10 s,
- terminaron con `End`,
- sin `FOAM FATAL`,
- sin warnings.

B4:
- Co máximo = **0.176643** cerca de 0.290 s,
- Co final máximo = **0.0602696**,
- continuidad final = **1.67018e-4**,
- ExecutionTime = **240.667 s**,
- ClockTime = **248 s**.

C4:
- Co máximo = **0.0700709** cerca de 2.510 s,
- Co final máximo = **0.0241928**,
- continuidad final = **1.78349e-4**,
- ExecutionTime = **225.476 s**,
- ClockTime = **226 s**.

El aumento duplicó los solves de h metal y e molde de 20,000 a 40,000.

### Sensibilidad central

B3 vs B4:
- max |ΔT| = **0.19 K**,
- max |Δalpha_l| = **5.22e-4**,
- liquidus: 6.666 s → **6.678 s**,
- alpha_l=0.99: 9.619 s → **9.636 s**.

C3 vs C4:
- max |ΔT| = **0.01 K**,
- max |Δalpha_l| = **1.0e-6**,
- liquidus = **3.386 s** en ambos,
- alpha_l=0.99 = **3.654 s** en ambos,
- T mínima = **1456.25 K a 4.822 s** en ambos,
- alpha_l mínimo = **0.932983 a 4.878 s** en ambos.

B4 vs C4 conserva ~**33.42 K** de diferencia máxima central y ~**0.067017** en fracción líquida.

### Interpretación

Duplicar `nEnergyCorrectors` no cambia materialmente la solución térmica/de fase central en 0–10 s. La diferencia B-vs-C y la refusión/rebote de C persisten.

Los tiempos de una sola corrida no son benchmark estricto; B4 incluso fue ligeramente más rápido que B3 pese a más solves, mostrando variabilidad de máquina.

**Estado:** ✅ prueba completa; la solución B3/C3 es robusta frente a `nEnergyCorrectors=2`.

---

## 2026-09-24 — AUD-047 — Verificación redundante de convergencia B4/C4
**[RUN-VERIFIED] [GIT-VERIFIED]**

El conteo de logs confirmó:

- B3/C3: 20,000 solves de h metal y 20,000 de e molde,
- B4/C4: 40,000 solves de h y 40,000 de e,
- los cuatro: 40,000 solves de p_rgh.

Esto confirma que `nEnergyCorrectors=2` estuvo activo.

Métricas y conclusiones coincidieron con la entrada anterior: cambios centrales de temperatura ≤0.19 K en B y ~0.01 K en C, sin modificar la diferencia cualitativa B/C.

**Estado:** ✅ comprobación redundante preservada en el historial original.

---

## 2026-09-24 — AUD-047 — Comparación controlada B4/C4
**[RUN-VERIFIED] [GIT-VERIFIED]**

La comparación final B4/C4 preservó la misma conclusión:

- B4 peak Co **0.176643**, ExecutionTime **240.667 s**.
- C4 peak Co **0.0700709**, ExecutionTime **225.476 s**.
- B3→B4 max ΔT central ~**0.19 K**.
- C3→C4 max ΔT central ~**0.01 K**.
- B4 vs C4 max separación central ~**33.42 K**.
- C4 conserva Tmín=1456.25 K a 4.822 s y alpha1mín=0.932983 a 4.878 s, seguido por calentamiento/refusión.

**Conclusión:** el corrector extra de energía tiene impacto despreciable en la historia central; no explica la separación B/C.

**Estado:** ✅ comparación completa.

---

## 2026-09-24 — AUD-048 — Convergencia B5/C5 con nOuterCorrectors=3 y conclusión 3/4/5
**[RUN-VERIFIED] [GIT-VERIFIED]**

`B5_outer3` y `C5_outer3` se compararon contra B3/C3 y B4/C4.

Ambos:

- completaron 10,000 pasos hasta 10 s,
- terminaron con `End`,
- sin `FOAM FATAL`,
- sin warnings,
- ejecutaron 30,000 solves de h metal y 30,000 de e molde, confirmando el tercer outer correction.

### Solver

B5:
- peak Co = **0.175874 a 0.284 s**,
- Co final medio **0.0154835**, máximo **0.0602937**,
- máximo absoluto continuidad acumulada ~**1.70120e-4**,
- continuidad final **1.65205e-4**,
- h final **4.72045e-12**,
- e final **5.80792e-10**,
- p_rgh final **9.77911e-8**,
- ExecutionTime **291.137 s**,
- ClockTime **298 s**.

C5:
- peak Co = **0.0700712 a 2.510 s**,
- Co final medio **0.0093466**, máximo **0.0241931**,
- máximo absoluto continuidad acumulada ~**1.78180e-4**,
- continuidad final **1.78172e-4**,
- h final **1.19093e-10**,
- e final **5.78841e-10**,
- p_rgh final **5.2433e-8**,
- ExecutionTime **272.125 s**,
- ClockTime **273 s**.

### Sensibilidad térmica/fase

B3→B5:
- max |ΔT| **0.22 K** a 7.443 s,
- max |Δalpha_l| **6.48e-4**,
- liquidus 6.666 → **6.683 s**,
- alpha_l=0.99 9.619 → **9.633 s**,
- T final 1467.45 → **1467.52 K**,
- alpha1 final 0.978184 → **0.978433**.

C3→C5:
- max |ΔT| **0.01 K**,
- max |Δalpha_l| **4e-6**,
- liquidus **3.386 s**,
- alpha_l=0.99 ~**3.654 s**,
- Tmín **1456.25 K a 4.822 s**,
- alpha_lmín **0.932984 a 4.876 s**,
- T final **1461.60 K**,
- alpha1 final **0.954397**.

B5 vs C5:
- max diferencia T central **33.42 K**,
- max diferencia fracción líquida ~**0.067016**.

### Conclusión de convergencia 3/4/5

1. B4/C4 (`nEnergyCorrectors=2`) cambia de forma despreciable la solución central frente a B3/C3.
2. B5/C5 (`nOuterCorrectors=3`) también cambia de forma despreciable la solución central.
3. B5/C5 requiere más solves y en estas corridas ~**16.7%** más CPU en B y ~**21.3%** más en C frente a B3/C3.
4. La gran diferencia B-vs-C se reproduce en las tres configuraciones.

Para los cálculos controlados 0–10 s, B3/C3 queda aceptado como baseline numérica eficiente.

Esto es una conclusión de sensibilidad numérica, no una selección física de la formulación B o C.

**Estado:** ✅ serie 3/4/5 de sensibilidad numérica completa.

---

## 2026-09-24 — AUD-049 — Perfiles horizontales de OpenFOAM configurados
**[CONFIG-VERIFIED] [GIT-VERIFIED]**

Se añadió un function object de muestreo lineal común en `system/functions` de los seis casos controlados 3/4/5.

Se usa el objeto `sets` de OpenFOAM v14 con sets `lineUniform`, mecanismo subyacente de `graphUniform`.

### Geometría

Ambas líneas están en el plano medio del metal, z=0.005 m, y corren horizontalmente en x de 0.00025 a 0.03975 m.

1. `line_y20mm`
   - y=0.020 m,
   - altura geométrica central del metal.

2. `line_y30mm`
   - y=0.030 m,
   - 10 mm debajo de la superficie superior y=0.040 m.

Cada línea usa 80 puntos uniformes y `axis x`. Con la malla controlada de 80 celdas / 40 mm, el espaciamiento entre centros es 0.5 mm.

### Campos

- `U`: contiene Ux, Uy, Uz,
- `T`,
- `phaseChangeSource:alpha1`.

La magnitud se deriva en análisis como:

`|U| = sqrt(Ux² + Uy² + Uz²)`

para conservar la información direccional.

### Salida

- región: `metal`,
- interpolación: `cellPoint`,
- formato: `raw`,
- `writeControl writeTime`.

Es una adición de postproceso únicamente; no cambia malla, propiedades, fronteras, modelo, timestep ni correctores.

**Estado:** ✅ configuración común comprometida; extracción pendiente en ese punto.

---

## 2026-09-25 — AUD-050 — Ejecución de perfiles y análisis espacial B3/C3
**[RUN-VERIFIED] [GIT-VERIFIED]**

Se ejecutaron los perfiles horizontales para todos los tiempos guardados de 0 a 10 s en los seis casos.

Cada caso generó:

- 101 tiempos,
- 2 líneas por tiempo,
- 202 archivos por caso.

Total: **1,212 archivos de perfil**.

Columnas:

- x,
- Ux,
- Uy,
- Uz,
- T,
- `phaseChangeSource:alpha1`.

Uz observado es cero en los perfiles inspeccionados, consistente con la configuración cuasi-2D.

### Reversión de flujo central B3/C3

En x≈19.75 mm, B y C presentan direcciones verticales opuestas durante el intervalo temprano de cambio de fase.

A 3.4 s:
- 20 mm: B3 Uy = -0.01437 m/s; C3 Uy = +0.00962 m/s.
- 30 mm: B3 Uy = -0.02419 m/s; C3 Uy = +0.00357 m/s.

A 4.8 s:
- 20 mm: B3 Uy = -0.01104 m/s; C3 Uy = +0.01821 m/s.
- 30 mm: B3 Uy = -0.01492 m/s; C3 Uy = +0.00299 m/s.

B3 tiene flujo central descendente en ambas alturas; C3 flujo central ascendente.

### Estratificación térmica vertical

A 4.8 s y x≈19.75 mm:

- B3: T(20 mm)=1489.50 K; T(30 mm)=1485.99 K.
- C3: T(20 mm)=1456.46 K; T(30 mm)=1483.24 K.

C3 muestra ~26.78 K de separación vertical, frente a ~3.51 K en B3 y con signo opuesto.

A ese tiempo, la máxima diferencia B3/C3 en la línea 20 mm es ~33.05 K cerca de x≈20.25 mm.

### Diferencias de Uy

Valores representativos máximos |ΔUy|:

- 3.4 s, 20 mm: ~0.02399 m/s,
- 3.4 s, 30 mm: ~0.02776 m/s,
- 4.8 s, 20 mm: ~0.02925 m/s,
- 6.7 s, 30 mm: ~0.02949 m/s,
- 10 s, 30 mm: ~0.02916 m/s.

La formulación B puede mostrar velocidades locales/superiores mayores aunque C enfríe y solidifique el centro antes. Por tanto, Courant global o velocidad pico no bastan como proxy del transporte térmico central.

### Convergencia espacial

A perfiles representativos de 4.8 y 10 s:

- C3/C4/C5 son prácticamente coincidentes a la precisión muestreada, con diferencias T ≤ ~0.01 K y velocidad generalmente ~1e-6 m/s o menores.
- B3/B4/B5 tienen sensibilidad espacial pequeña pero medible: diferencias T hasta ~0.6–0.7 K y Uy hasta ~0.0015 m/s.
- Estas diferencias son mucho menores que B-vs-C y no cambian la estructura cualitativa de circulación.

### Interpretación

La diferencia térmica B-vs-C está asociada con una topología de flujo y redistribución vertical de calor materialmente diferente, no simplemente con mayor o menor magnitud escalar de velocidad.

C desarrolla flujo central ascendente persistente y fuerte estratificación vertical temprana, consistente con una ruta convectiva distinta que puede explicar por qué el centro alcanza liquidus y cambio de fase antes.

Es una interpretación mecanística numérica, no validación física.

**Estado:** ✅ perfiles y análisis espacial inicial completos; 🟡 figuras de tesis y validación experimental pendientes.

---

## 2026-09-25 — AUD-051 — Auditoría de implementación de buoyancy a nivel código fuente
**[SOURCE-VERIFIED] [INTERPRETATION-CORRECTION]**

Se auditó el código fuente después de observar grandes diferencias B-vs-C.

### Implementación B verificada

`B3_reference/constant/metal/materials/castIron` usa:

- `equationOfState icoTabulated`,
- tabla de densidad dependiente de T,
- de 6900 kg/m³ a 1423.15 K a 6820 kg/m³ a 1473.15 K.

`B3_reference/constant/metal/fvModels` usa:

- `beta 0`,
- `rhoRef 6930`.

La corrección de presión buoyant de Foundation v14 para p_rgh incluye explícitamente:

`ghGradRhof = -ghf*fvc::snGrad(rho)*mesh.magSf()`

y añade esa contribución de gradiente de densidad a la corrección presión/velocidad.

Por tanto, B **no es un caso sin buoyancy**. La flotación surge del campo de densidad dependiente de temperatura y la formulación nativa p_rgh. `beta=0` solo desactiva la fuente explícita adicional de `solidificationMelting`.

### Implementación C verificada

`C3_reference/constant/metal/materials/castIron` usa:

- `rhoConst`,
- ρ = 6820 kg/m³.

`C3_reference/constant/metal/fvModels` usa:

- `beta = 1.13e-4 1/K`,
- `rhoRef = 6820 kg/m³`.

Con densidad constante, el término nativo `-ghf*snGrad(rho)` se anula salvo roundoff.

`solidificationMelting` añade:

`Sb = rhoRef*g*beta*deltaT`

Por tanto, C **no es doble buoyancy**: su flotación térmica proviene de la fuente explícita mientras la ruta nativa está inactiva.

### Por qué B y C difieren tanto

No son formulaciones equivalentes.

La tabla B da una expansión térmica efectiva variable. Entre 1423.15–1473.15 K:

- ρ disminuye 80 kg/m³ en 50 K,
- beta efectivo ≈ 2.3e-4 1/K,

aproximadamente el doble de C.

Entre 1473.15–1573.15 K:

- ρ disminuye 80 kg/m³ en 100 K,
- beta efectivo ≈ 1.2e-4 1/K,

más cercano a C.

Además, la fuente C usa el `deltaT` interno del modelo de fase, definido respecto a la relación de equilibrio vigente y dependiente de fracción líquida; no es simplemente un término Boussinesq global lineal T-Tref.

### Impacto

Las diferencias B-vs-C siguen siendo numéricamente reales, pero deben interpretarse como consecuencias de **dos modelos distintos de buoyancy**, no como “sin buoyancy” en B o “doble buoyancy” en C.

La selección física requiere comparación con curvas experimentales y comportamiento termofísico esperado.

**Estado:** ✅ mecanismo verificado en código v14; 🟡 selección física pendiente.

---

## 2026-09-25 — AUD-052 — Auditoría de divergencia de configuración posterior a sesión con asesor
**[CONFIGURATION-AUDIT] [TRACEABILITY] [CONTROLLED-SERIES]**

Los seis casos controlados se reauditaron después de sincronizar cambios locales hechos durante/después de la sesión con el asesor.

### Matriz encontrada

| Caso | nOuterCorrectors | nEnergyCorrectors | adjustTimeStep | EOS metal | beta |
|---|---:|---:|---|---|---:|
| B3_reference | 2 | default (1) | **yes** | icoTabulated | 0 |
| C3_reference | 2 | default (1) | no | rhoConst | 1.13e-4 |
| B4_energy2 | 2 | 2 | no | icoTabulated | 0 |
| C4_energy2 | 2 | 2 | no | rhoConst | 1.13e-4 |
| B5_outer3 | 3 | default (1) | no | icoTabulated | 0 |
| C5_outer3 | 3 | default (1) | **yes** | rhoConst | **0** |

### B3 ya no correspondía a la referencia original fija

`B3_reference/system/controlDict` tenía `adjustTimeStep yes`.

Los nuevos logs B3 mostraban 2811 tiempos reportados, primero 0.0012 s y final 9.999798 s; `logs/deltaT_0` confirmaba timestep adaptativo.

Por tanto, esos outputs eran de un rerun adaptativo y no del dataset B3 fijo usado en la comparación anterior. Los datos originales seguían recuperables desde Git.

### C5 actual tampoco coincidía con el C5 analizado

El C5 analizado previamente había usado:

- `rhoConst = 6820`,
- `beta = 1.13e-4`,
- `adjustTimeStep no`,
- `nOuterCorrectors = 3`.

La configuración encontrada después tenía:

- `rhoConst = 6820`,
- `beta = 0`,
- `adjustTimeStep yes`,
- `nOuterCorrectors = 3`.

Con `rhoConst` y `beta=0`, la buoyancy térmica quedaba desactivada: era otro problema físico.

### Cambio fvSolution de molde en B3

Solo B3 tenía explícitamente:

```text
"(h|e)Final"
{
    solver          PCG;
    preconditioner  DIC;
    tolerance       1e-06;
    relTol          0;
}
```

mientras los otros cinco heredaban `$h; relTol 0;`.

Las plantillas CHT de Foundation v14 usan esta última forma. El bloque explícito B3 reproduce los mismos valores base con `relTol 0`; debe tratarse como reexpresión explícita, no como variable numérica significativa salvo demostración futura.

### Implicación

No crear el siguiente caso copiando ciegamente C5 actual.

Debe preservarse:

- B: `icoTabulated`, `beta=0`.
- C: `rhoConst=6820`, `beta=1.13e-4`.

y cambiar una variable numérica a la vez.

Un caso intencional sin buoyancy (`rhoConst + beta=0`) debe recibir nombre propio si se estudia.

**Estado:** ✅ divergencia identificada; definición siguiente pendiente.

---

## 2026-09-25 — AUD-053 — Definición V6/V7 y flujo foamLog
**[CONFIGURATION-RESTORE] [CONTROLLED-SERIES] [POST-PROCESSING]**

### Restauración histórica

Se eliminaron cambios temporales de la sesión del asesor:

- B3: `adjustTimeStep` restaurado a `no`; solver final del molde restaurado a `$h; relTol 0;`.
- C5: `adjustTimeStep` restaurado a `no`; `beta` restaurado a `1.13e-04 1/K`.

Los datos B3 adaptativos fueron sustituidos por outputs B3 fijos previos del historial. El set adaptativo `logs/` se eliminó.

Los logs `foamLog` históricos C5 se restauraron desde Git después de haberse eliminado accidentalmente durante sincronización.

### V6 controlado

Se crearon `B6_fvSolution` y `C6_fvSolution` desde V5 limpio.

Cambio controlado: solver final de energía del molde escrito explícitamente como el bloque PCG/DIC/tolerance/relTol mostrado arriba.

Todo lo demás permanecía V5.

### V7 controlado

Se crearon `B7_outer4` y `C7_outer4` desde V5 limpio.

Cambio:

`nOuterCorrectors 4;`

### foamLog estandarizado

Los casos controlados V3–V7 ejecutarían:

`foamLog log.foamMultiRun`

automáticamente desde `Allrun` tras terminar el solver.

Antes de parsear se eliminan `logs/` y `log.foamLog` anteriores para no mezclar diagnósticos.

`Allclean` elimina `logs/`.

**Estado:** ✅ restauración realizada; ✅ V6/V7 definidos inicialmente; ✅ foamLog estandarizado.

---

## 2026-09-25 — AUD-054 — Eliminación de outputs foamLog restaurados y obsoletos de C5
**[CORRECTION] [POST-PROCESSING] [TRACEABILITY]**

El directorio histórico `C5_outer3/logs/` restaurado en AUD-053 fue eliminado porque era inconsistente con el nuevo flujo, que requiere regenerar `logs/` desde el `log.foamMultiRun` rastreado.

El solver log fuente `C5_outer3/log.foamMultiRun` permaneció intacto.

Los nuevos `logs/` deben producirse con:

`foamLog log.foamMultiRun`

**Estado:** ✅ logs parseados obsoletos eliminados; solver log fuente conservado.

---

## 2026-09-25 — AUD-055 — Activación temporal de timestep adaptativo en V7
**[CONFIGURATION-CHANGE] [V7] [TIME-STEPPING]**

Por decisión del usuario, ambos V7 combinaron temporalmente:

- `nOuterCorrectors = 4`
- `adjustTimeStep = yes`

con:

- `deltaT = 0.001 s` inicial,
- `maxCo = 0.25`,
- `maxDeltaT = 0.1 s`.

Esto aplicaba a B7/C7 sin cambiar la física B/C.

Al modificar dos variables frente a V5, V7 dejaba de ser una prueba de una sola variable.

**Estado:** ✅ cambio transitorio documentado; posteriormente sustituido por AUD-056.

---

## 2026-09-25 — AUD-056 — Diseño final: V6 adaptive timestep y V7 outer correctors
**[CONFIGURATION-CHANGE] [CONTROLLED-SERIES] [SUPERSEDES-AUD-055]**

El diseño V6/V7 se revisó para conservar una variable numérica por comparación.

### V6 — timestep adaptativo

Los anteriores `B6_fvSolution` y `C6_fvSolution` se eliminaron antes de ejecución y se reemplazaron por:

- `B6_adaptiveDt`
- `C6_adaptiveDt`

copiados de V5 limpio y cambiando únicamente:

`adjustTimeStep yes;`

Conservan:

- `nOuterCorrectors = 3`
- `deltaT inicial = 0.001 s`
- `maxCo = 0.25`
- `maxDeltaT = 0.1 s`

La física B/C no cambia.

### V7 — sensibilidad a outer correctors

El ajuste temporal de AUD-055 se revirtió antes de ejecución.

Configuración final:

- `B7_outer4`
- `C7_outer4`
- `nOuterCorrectors = 4`
- `adjustTimeStep = no`
- `deltaT = 0.001 s` fijo

Así:

- V5 vs V6 aísla estrategia de timestep.
- V5 vs V7 aísla cantidad de outer correctors.

**Estado:** ✅ V6 adaptativo definido; ✅ V7 fijo con outerCorrectors=4; ✅ diseño de una variable a la vez restaurado.

---

## 2026-09-25 — Flujo documental paralelo: bitácora + manual práctico OpenFOAM

### Decisión

Desde esta fecha el proyecto mantiene dos capas paralelas:

1. **Bitácora de auditoría** — historia cronológica de cambios, pruebas, discrepancias, evidencia, resultados, impacto y estado.
2. **Manual práctico de comandos** — referencia tipo tutorial con bloques listos para copiar, explicación y recetas específicas.

### Razón

La bitácora responde **qué pasó y por qué**. El manual responde **cómo repetirlo rápidamente**.

Los comandos reutilizables deben incorporarse al manual cuando sean útiles más allá de una acción aislada.

### Incidente de rutas al encadenar casos 6/7

Se lanzó un bloque secuencial desde:

`~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy`

B6 completó su secuencia hasta `foamLog`, pero el siguiente subshell intentó:

`cd ../C6_adaptiveDt`

y falló:

`-bash: cd: ../C6_adaptiveDt: No such file or directory`

### Causa

Cada bloque entre paréntesis corre en un subshell. Al terminar:

`(cd B6_adaptiveDt && ./Allclean && ./Allrun)`

el shell padre sigue en `cases_controlled_buoyancy`.

Por tanto, el siguiente caso debe ser `C6_adaptiveDt`, no `../C6_adaptiveDt`.

### Patrón correcto

```bash
(cd B6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

Si B6 ya terminó:

```bash
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

### Impacto

La salida pegada no mostraba fallo de B6; su `Allrun` llegó a `foamLog`. La cadena se detuvo únicamente al intentar entrar a la ruta incorrecta de C6.

**Estado:** ✅ error explicado y documentado.

---

## 2026-09-25 — Manual bilingüe y recuperación histórica de comandos

### Cambio documental

El manual práctico se dividió en:

- `OPENFOAM_COMMAND_MANUAL.md` — selector.
- `OPENFOAM_COMMAND_MANUAL_ES.md` — español.
- `OPENFOAM_COMMAND_MANUAL_EN.md` — inglés.

Ambas versiones deben conservar el mismo conjunto de comandos y estructura.

### Recuperación histórica

Se incorporaron comandos usados antes del 2026-09-25, incluyendo:

- `paraFoam -builtin &` de B2/C2,
- `foamPostProcess -region metal -solver fluid -latestTime` relacionado con la solicitud del doctor de perfiles velocidad–temperatura (“plotline”),
- elementos `lineUniform`, `graphUniform`, `graphCell` y campos `U T phaseChangeSource:alpha1`,
- `find . -name "openfoam-solidification.agent.md"`,
- `git check-ignore -v cases_buoyancy/B2_test/10`,
- flujo Git pull/status/add/commit/push,
- `git add -f` para outputs seleccionados ignorados.

### Regla de atribución

Solo se etiqueta como “del doctor” o motivado por él aquello con evidencia histórica explícita. Los demás comandos se documentan como parte de la historia del proyecto sin inventar atribución.

**Estado:** ✅ selector bilingüe del manual activo; ✅ primera recuperación histórica completada.

---

## 2026-09-25 — Bitácora bilingüe

### Cambio documental

La bitácora se reorganizó con la misma lógica bilingüe del manual:

- `PROJECT_AUDIT_LOG.md` — selector de idioma.
- `PROJECT_AUDIT_LOG_ES.md` — versión completa en español.
- `PROJECT_AUDIT_LOG_EN.md` — versión completa en inglés.

Las dos versiones preservan:

- mismas fechas,
- mismos identificadores AUD,
- mismas etiquetas de evidencia,
- mismos comandos,
- mismos nombres de archivo,
- mismos valores numéricos,
- mismas decisiones y estados.

Solo cambia el idioma de la narrativa.

### Regla futura

Cada nueva entrada técnica deberá añadirse tanto a la versión española como a la inglesa para evitar que una se vuelva más actual que la otra.

**Estado:** ✅ estructura bilingüe establecida y traducción española creada.


---

## 2026-09-25 — Observación del asesor: sensibilidad del acoplamiento de `p_rgh` a `nOuterCorrectors`
**[ADVISOR-OBSERVATION] [USER-REPORTED] [OPEN]**

### Observación comunicada durante trabajo paralelo

El asesor está realizando sus propias corridas en paralelo a las simulaciones del usuario. Según lo reportado por el usuario, el asesor observó que al aumentar `nOuterCorrectors` disminuían de forma importante los residuals iniciales de `p_rgh`.

El usuario recuerda que el asesor pudo haber probado valores altos de `nOuterCorrectors`, posiblemente alrededor de **7**, pero el valor exacto no está confirmado y no debe tratarse como dato verificado hasta disponer del log, configuración o confirmación directa correspondiente.

### Evidencia propia relacionada

En los logs controlados ya preservados del proyecto, el primer timestep de varios casos muestra un `Initial residual` de `p_rgh` cercano a 1. Por ejemplo, en B5:

- `p_rgh_0 = 0.973321` a `t = 0.001 s`
- `p_rgh_1 = 0.00750951`
- `p_rgh_2 = 0.00516345`
- `p_rgh_3 = 2.51636e-05`
- `p_rgh_4 = 8.23277e-05`
- `p_rgh_5 = 7.45313e-07`

Por tanto, aunque la primera corrección de presión comienza con un residual de orden unidad, las correcciones PIMPLE reducen el residual varios órdenes de magnitud dentro del mismo timestep.

El mismo pico inicial ~0.973 aparece también en B3, B4, C3 y C4 en el primer timestep, por lo que no debe interpretarse automáticamente como una falla exclusiva de una formulación física.

### Hipótesis a reproducir

Probar de forma controlada la sensibilidad del acoplamiento presión–velocidad frente a:

`nOuterCorrectors = 2, 3, 4, 5, 6, 7`

manteniendo constantes las demás variables numéricas y físicas.

Las métricas deberán incluir:

- residual inicial máximo de `p_rgh`,
- residual de `p_rgh` después del último corrector,
- reducción total dentro del timestep,
- número de timesteps con spikes elevados,
- persistencia o desaparición de spikes después del arranque,
- continuidad,
- Courant,
- tiempo de CPU/reloj,
- efecto real sobre T y fracción líquida.

### Objetivo

Determinar el punto de **rendimientos decrecientes**: el menor número de outer correctors que logra un acoplamiento suficientemente robusto sin aumentar costo computacional de forma innecesaria.

### Implicación para OpenFOAM PostPlotter

Esta observación motiva un módulo de diagnóstico de acoplamiento que no solo grafique `p_rgh_0`, `p_rgh_1`, etc., sino que reconstruya automáticamente la reducción de residual dentro de cada timestep y entre outer correctors.

**Estado:** 🟡 observación del asesor documentada; valor máximo ensayado por el asesor no confirmado; prueba controlada propia pendiente.


---

## 2026-09-25 — Auditoría completa de Initial residuals: el comportamiento relevante está en `p_rgh`
**[RUN-VERIFIED] [GIT-VERIFIED] [COUPLING-DIAGNOSTIC]**

Se analizaron los archivos `foamLog` de Initial residual para los casos controlados disponibles B3/B4/B5 y C3/C4/C5. El análisis excluyó el primer transitorio de arranque al estudiar el comportamiento persistente (`t >= 0.1 s`).

### Familias de residual auditadas

Los `foamLog` disponibles contienen Initial residuals para:

- `p_rgh`
- `h`
- `e`
- `rho`

### `rho`

Todos los archivos `rho_*` de B3/B4/B5/C3/C4/C5 tienen el mismo blob SHA y contienen valores cero. No aportan una señal útil de convergencia en estos casos.

### `h` — entalpía del metal

El primer solve de `h` parte alrededor de 1.67–1.69e-3 a 0.1 s y disminuye de manera suave conforme avanza la simulación.

Los solves posteriores dentro del timestep reducen el residual a órdenes mucho menores. No se encontró una familia de spikes intermedios comparable con `p_rgh`.

Ejemplos:

- B3 `h_0`: máximo para t>=0.1 s = 1.67278e-3 a 0.1 s; mediana ≈ 1.029e-4.
- B5 `h_0`: 1.67354e-3 a 0.1 s; mediana ≈ 1.028e-4.
- C3/C5 `h_0`: 1.69063e-3 a 0.1 s; mediana ≈ 1.158e-4.

Los correctores adicionales llevan los `h` posteriores a aproximadamente 1e-7–1e-9 según configuración.

### `e` — energía del molde

`e_0` muestra una disminución suave desde aproximadamente 1.84e-3 a 0.1 s.

Los correctores posteriores están típicamente en órdenes 1e-8–1e-10. Tampoco se encontró una inestabilidad intermedia comparable con presión.

### `p_rgh` — residual no monótono y persistente

`p_rgh` es la familia que presenta el comportamiento de acoplamiento numéricamente interesante.

El pico de ~0.973 en t=0.001 s se considera un transitorio de inicialización y NO es la única evidencia relevante. Después de 0.1 s reaparecen residuals elevados durante la simulación.

#### Familia B

B3 (`nOuterCorrectors=2`), `p_rgh_0`:
- máximo post-arranque: **0.0343238 a 0.592 s**
- 2–4 s: máximo **0.0118509**
- 4–6 s: máximo **0.0153241 a 5.781 s**
- 6–8 s: máximo **0.012815 a 6.249 s**
- 8–10 s: máximo **0.00976308**

B5 (`nOuterCorrectors=3`), `p_rgh_0`:
- máximo post-arranque: **0.0317178 a 0.573 s**
- 2–4 s: máximo **0.0107382**
- 4–6 s: máximo **0.015842 a 5.791 s**
- 6–8 s: máximo **0.0128389 a 6.250 s**
- 8–10 s: máximo **0.0095283**

En B, por tanto, existen eventos importantes de residual alrededor de 5.3–6.25 s además del transitorio temprano.

#### Familia C

C3 `p_rgh_0`:
- 0.1–2 s: máximo **0.0112909**
- 2–4 s: máximo **0.0100891**
- 4–6 s: máximo **0.0121034**
- 6–8 s: máximo **0.0121384**
- 8–10 s: máximo **0.0173881 cerca de 9.985 s**

C5 `p_rgh_0`:
- 0.1–2 s: máximo **0.0105247**
- 2–4 s: máximo **0.0105513**
- 4–6 s: máximo **0.0120312**
- 6–8 s: máximo **0.0122043**
- 8–10 s: máximo **0.0178995 cerca de 9.981 s**

La rama C presenta un patrón diferente: el residual de presión vuelve a crecer hacia el final de la ventana 0–10 s.

### Persistencia de residuals altos

Para t>=0.1 s:

B3:
- `p_rgh_0 > 0.01` en 2100 de 9901 timesteps.
- `p_rgh_3 > 0.01` en 430 de 9901.

B5:
- `p_rgh_0 > 0.01` en 2036 de 9901.
- `p_rgh_5 > 0.01` en 428 de 9901.

C3:
- `p_rgh_0 > 0.01` en 1366 de 9901.
- `p_rgh_3 > 0.01` en 404 de 9901.

C5:
- `p_rgh_0 > 0.01` en 1427 de 9901.
- `p_rgh_5 > 0.01` en 245 de 9901.

### Efecto real de aumentar nOuterCorrectors 2 → 3

Se definió descriptivamente la razón:

`R = p_rgh_last / p_rgh_0`

dentro del mismo timestep, usando el último pressure solve disponible.

Para t>=0.1 s:

- B3 (2 outer): mediana R = **0.6054**
- B5 (3 outer): mediana R = **0.5975**
- C3 (2 outer): mediana R = **0.8127**
- C5 (3 outer): mediana R = **0.8010**

Por tanto, añadir un tercer outer corrector produce solo una mejora pequeña en la reducción típica del Initial residual de `p_rgh`.

Además, existen timesteps donde el residual del último pressure solve es mayor que el del primero:

- B3: ~2.62% de los timesteps auditados.
- B5: ~3.62%.
- C3: ~10.08%.
- C5: ~8.22%.

Ejemplos claros:

- B5 a 6.126 s: el residual aumenta de `p_rgh_0 = 0.00621936` a `p_rgh_5 = 0.00841035`, razón ≈ **1.35**.
- C5 alrededor de 8.0 s presenta eventos donde los outer correctors posteriores terminan con residuals aproximadamente **1.5–1.56×** el primer residual del timestep.

### Relación con pruebas numéricas previas

B4/C4 (`nEnergyCorrectors=2`) conserva esencialmente el mismo patrón de `p_rgh` que B3/C3. Aumentar correctores de energía no resuelve el comportamiento de acoplamiento de presión.

B5/C5 (`nOuterCorrectors=3`) ya había mostrado cambios térmicos/de fase despreciables frente a B3/C3 pero mayor costo computacional. Esta auditoría añade que el tercer outer corrector tampoco produce una mejora grande del residual típico de presión.

### Interpretación

El diagnóstico correcto no debe ser únicamente “el residual inicial es alto”. Debe distinguir:

1. transitorio de arranque,
2. spikes persistentes durante la corrida,
3. reducción entre outer correctors,
4. stagnation (`R≈1`),
5. deterioration (`R>1`),
6. comportamiento de cada formulación B/C.

El valor absoluto de un Initial residual aislado no debe etiquetarse automáticamente como error; se requiere observar su evolución dentro del timestep y en el tiempo.

### Siguiente prueba crítica

El caso V7 con `nOuterCorrectors=4` permitirá comprobar si aparece una reducción sustancial que no se observó al pasar de 2 a 3.

Si el asesor efectivamente observó mejoras claras con valores mayores, una serie posterior 4→5→6→7 deberá realizarse de forma controlada y con timestep fijo antes de concluir un valor óptimo.

### Implicación para OpenFOAM PostPlotter

La app debe evolucionar desde un visor de archivos `p_rgh_0`, `p_rgh_1`, etc. hacia un diagnóstico de acoplamiento que reconstruya automáticamente, por timestep:

- outer corrector,
- pressure corrector interno,
- `p_rgh_0 → ... → p_rgh_last`,
- razón `R = last/first`,
- reducción en órdenes de magnitud,
- eventos donde `R≈1`,
- eventos donde `R>1`,
- ranking de los peores timesteps,
- exclusión configurable del startup,
- comparación entre casos con diferente `nOuterCorrectors`.

**Estado:** ✅ Initial residuals B3–B5/C3–C5 auditados; ✅ `p_rgh` identificado como principal señal de acoplamiento; 🟡 B7/C7 pendientes para evaluar `nOuterCorrectors=4`.


---

## 2026-09-25 — Distinción entre convergencia del solver lineal y convergencia del acoplamiento PIMPLE
**[RUN-VERIFIED] [COUPLING-DIAGNOSTIC]**

Después de auditar los Initial residuals de `p_rgh`, se compararon también los `p_rghFinalRes_*` de B5 y C5 para distinguir dos fenómenos diferentes:

1. qué tan bien converge cada solve lineal de presión;
2. qué tan bien se cierra el acoplamiento entre outer iterations.

### B5

Para t>=0.1 s:

- `p_rghFinalRes_1`: mediana ≈ **6.68e-8**
- `p_rghFinalRes_3`: mediana ≈ **5.00e-8**
- `p_rghFinalRes_5`: mediana ≈ **3.91e-8**

Los segundos solves de presión de cada outer terminan consistentemente cerca del orden 1e-8–1e-7.

Sin embargo, los Initial residuals del siguiente outer pueden volver a valores de orden 1e-3–1e-2.

### C5

Para t>=0.1 s:

- `p_rghFinalRes_1`: mediana ≈ **6.76e-8**
- `p_rghFinalRes_3`: mediana ≈ **5.55e-8**
- `p_rghFinalRes_5`: mediana ≈ **5.09e-8**

De nuevo, cada solve lineal puede terminar con residual pequeño mientras el siguiente ciclo de acoplamiento comienza con un Initial residual mucho mayor.

### Interpretación

Esto indica que un residual inicial persistente de `p_rgh` no debe interpretarse automáticamente como incapacidad del solver lineal para resolver la ecuación de presión.

En los casos auditados, el solver lineal reduce correctamente su residual final, pero las actualizaciones acopladas de velocidad, presión, energía, densidad/fase y fuentes pueden hacer que la siguiente corrección de presión vuelva a comenzar con una discrepancia apreciable.

Por tanto, el diagnóstico debe separar explícitamente:

- **linear-solver convergence:** Initial residual → Final residual dentro de un único pressure solve;
- **PIMPLE/nonlinear coupling convergence:** Initial residual de un outer → Initial residual del siguiente outer.

### Implicación para la app

OpenFOAM PostPlotter debe mostrar estas dos métricas por separado. Un `Final residual` pequeño no debe ocultar un acoplamiento persistente, y un `Initial residual` alto no debe etiquetarse como fallo del solver lineal si ese solve converge correctamente.

**Estado:** ✅ solver lineal vs acoplamiento PIMPLE diferenciados con datos reales B5/C5.


---

## 2026-09-25 — Perfil vertical central añadido a la serie controlada
**[POST-PROCESSING] [CONFIG-VERIFIED] [GIT-VERIFIED]**

Se añadió un segundo function object de muestreo, `verticalProfiles`, a los diez casos controlados:

- B3_reference / C3_reference
- B4_energy2 / C4_energy2
- B5_outer3 / C5_outer3
- B6_adaptiveDt / C6_adaptiveDt
- B7_outer4 / C7_outer4

### Geometría

Nueva línea:

`line_x20mm`

con:

- x = **0.020 m**
- z = **0.005 m**
- y = **0.00025 → 0.03975 m**
- 80 puntos uniformes
- `axis y`

La línea atraviesa el centro geométrico del metal y la ubicación del probe central en x=20 mm, z=5 mm.

### Campos

Se conservan exactamente los mismos campos que en los perfiles horizontales:

- `U`
- `T`
- `phaseChangeSource:alpha1`

Por tanto, del vector `U` pueden analizarse Ux, Uy, Uz y |U|.

### Razón física

La gravedad del caso actúa en Y:

`g = (0, -9.81, 0)`

y el análisis espacial previo encontró que B y C presentan signos opuestos de `Uy` en el centro durante parte de la solidificación.

Las líneas horizontales existentes `line_y20mm` y `line_y30mm` cortan la circulación a alturas fijas. La nueva línea vertical permite observar la estructura completa de abajo hacia arriba y responder:

- dónde `Uy > 0`,
- dónde `Uy < 0`,
- dónde cambia de signo,
- cómo se relaciona con T(y),
- cómo se relaciona con alpha_l(y),
- si existe una celda de recirculación y cómo difiere entre B y C.

### Impacto

Es una modificación exclusivamente de postprocesamiento. No cambia:

- malla,
- propiedades,
- fronteras,
- modelo de cambio de fase,
- timestep,
- correctores,
- solución física.

### Nota de ejecución

Los casos B6/C6/B7/C7 ya habían comenzado a ejecutarse localmente antes de que esta configuración se añadiera al repositorio. Por tanto, esta modificación en Git no altera corridas locales que ya están en curso. Sus perfiles verticales pueden generarse posteriormente a partir de los tiempos guardados una vez sincronizada la configuración local.

**Estado:** ✅ configuración vertical añadida a B3–B7/C3–C7; 🟡 extracción/análisis de los nuevos perfiles pendiente.


---

## 2026-09-26 — Paquete completo de diagnósticos de solidificación añadido a V3–V7
**[POST-PROCESSING] [CONFIG-VERIFIED] [GIT-VERIFIED] [NOT-YET-RUN-VERIFIED]**

Se añadió a los diez casos controlados B3–B7/C3–C7 un paquete común de diagnósticos basado únicamente en function objects nativos de OpenFOAM Foundation v14.

Commit principal de implementación:

`bd77587a4bf8c813c40512cfdfc3a27ae4e0168f`

La modificación es exclusivamente de postprocesamiento. No cambia malla, propiedades, condiciones de frontera, modelo de solidificación, timestep, PIMPLE ni ecuaciones.

### Probe central ampliado

El probe en `(0.020 0.020 0.005) m` ahora registra en cada timestep:

- `U`
- `T`
- `p_rgh`
- `rho`
- `phaseChangeSource:alpha1`

Esto permite correlacionar directamente presión modificada, densidad, velocidad, temperatura y fracción líquida en el mismo punto.

### Gradiente térmico

Se añadieron:

- `gradT = grad(T)`
- `magGradT = |grad(T)|`

También se registra el máximo espacial de `magGradT` y su localización mediante `metalMaxThermalGradient`.

### Tasa térmica local

Se añadió el function object nativo `ddt`:

- `dTdt = dT/dt`
- `coolingRate = -dTdt`

Convención:

- `coolingRate > 0`: enfriamiento local
- `coolingRate < 0`: calentamiento local

Se añade además `metalMeanCoolingRate`.

### Gradiente de densidad

Se añadieron:

- `gradRho = grad(rho)`
- `magGradRho = |grad(rho)|`
- `metalMaxDensityGradient` con localización

Objetivo: comparar directamente las rutas de buoyancy B/C.

En B, la densidad depende de T y el gradiente de densidad participa en la buoyancy nativa de `p_rgh`.

En C, `rho` es constante, por lo que `gradRho` debería ser aproximadamente cero. Esto constituye además una comprobación interna útil de la formulación.

### Tasa de cambio de fase

Se añadieron:

- `dAlphaLdt = d(alpha_l)/dt`
- `solidificationRate = -dAlphaLdt`

Convención:

- `solidificationRate > 0`: solidificación local
- `solidificationRate < 0`: refusión local

Se verificó en el código fuente de OpenFOAM v14 que `solidificationMeltingSource` actualiza explícitamente `alpha1_.oldTime()`, por lo que el campo dispone del historial temporal requerido durante ejecución.

### Tasa de calor latente

Se verificó que los diez casos usan:

`L = 2.286e5 J/kg`

Se crea un campo uniforme nativo `latentHeat` con dimensiones físicas `J/kg`, y mediante `multiply` se calcula:

`latentHeatRateVol = rho * L * solidificationRate`

Dimensiones:

`W/m3`

Convención:

- valor positivo: liberación de calor latente por solidificación
- valor negativo: absorción de calor durante refusión

Se integra además sobre todo el metal:

`metalLatentHeatPower = integral(latentHeatRateVol dV)`

con resultado en W.

### Courant espacial

Se añadió el function object nativo:

`CoCell`

usando `phi` y `rho`. En v14, `CourantNo` detecta el flujo másico y divide por densidad internamente cuando corresponde.

También se registra:

`metalMaxCourant`

con valor y ubicación.

### Perfiles espaciales ampliados

Las dos líneas horizontales y la línea vertical central ahora muestrean:

- `U`
- `T`
- `p_rgh`
- `rho`
- `phaseChangeSource:alpha1`
- `vorticity`
- `flowType`
- `magSqrDevGradU`
- `gradT`
- `magGradT`
- `dTdt`
- `coolingRate`
- `gradRho`
- `magGradRho`
- `dAlphaLdt`
- `solidificationRate`
- `latentHeatRateVol`
- `CoCell`

Esto permite estudiar espacialmente, sobre exactamente las mismas líneas, flujo, presión, buoyancy, gradiente térmico, enfriamiento, avance/refusión de fase, liberación latente y carga numérica local.

### Diagnósticos energéticos ya presentes

Se conservan y quedan integrados con este paquete:

- `energyAdvectiveFlux`
- `heatFlux`
- `energyFlux`
- potencia en `metalTop`
- potencia en `metal_to_mold`
- potencia neta en ambas fronteras
- `metalSensibleEnthalpy`
- `metalMeanLiquidFraction`
- `vorticity`
- `flowType`

### Limitación importante de OpenFOAM v14

El propio código fuente de `functionObjects::ddt` indica que **`ddt` no está soportado por `foamPostProcess`**.

Por tanto, los campos:

- `dTdt`
- `coolingRate`
- `dAlphaLdt`
- `solidificationRate`
- `latentHeatRateVol`

deben generarse DURANTE una corrida del solver.

No pueden reconstruirse retrospectivamente con el `foamPostProcess` estándar de v14 a partir de una corrida ya terminada.

Para corridas antiguas, PostPlotter podrá estimar derivados temporales a partir de los datos almacenados; esas estimaciones deben distinguirse explícitamente de la evaluación nativa runtime `fvc::ddt`.

### Estado

- ✅ configuración añadida a B3–B7/C3–C7
- ✅ sintaxis y disponibilidad de `grad`, `mag`, `ddt`, `uniform`, `multiply` y `CourantNo` verificadas contra el código/caseDicts oficiales de OpenFOAM Foundation v14
- ✅ L verificado idéntico en los diez casos
- ✅ dependencias colocadas antes de `lineProfiles`
- 🟡 todavía no validado mediante una ejecución real del solver con este paquete completo
- 🟡 B6/C6/B7/C7 que ya estuvieran corriendo localmente antes de esta modificación no reciben estos nuevos function objects automáticamente



---

## 2026-09-26 — Validación real B3 del paquete de diagnósticos y corrección de nombre de `flowType`
**[RUN-VERIFIED] [BUG-FOUND] [FIXED]**

Se ejecutó `B3_reference` completo de 0 a 10 s con el paquete ampliado de diagnósticos.

La corrida terminó correctamente y `foamLog` se ejecutó al final.

### Campos verificados en `10/metal`

Se encontraron:

- `CoCell`
- `coolingRate`
- `dAlphaLdt`
- `dTdt`
- `gradRho`
- `gradT`
- `latentHeat`
- `latentHeatRateVol`
- `magGradRho`
- `magGradT`
- `magSqrDevGradU`
- `solidificationRate`
- `vorticity`

### Postprocesamiento verificado

Se generaron correctamente:

- `horizontalProfiles`
- `verticalProfiles`
- `metalBoundaryEnergyPower`
- `metalLatentHeatPower`
- `metalMaxCourant`
- `metalMaxDensityGradient`
- `metalMaxThermalGradient`
- `metalMeanCoolingRate`
- `metalMeanLiquidFraction`
- `metalMeanSolidificationRate`
- `metalMoldEnergyPower`
- `metalSensibleEnthalpy`
- `metalTopEnergyPower`
- `temperatureProbe`

### Hallazgo

No apareció un archivo llamado `flowType`.

La revisión del código fuente oficial de OpenFOAM Foundation v14 mostró que el function object `flowType` usa por defecto como nombre del campo de salida el **nombre del bloque function object**, salvo que se especifique explícitamente `result`.

La configuración usaba:

`flowTopology { type flowType; ... }`

por lo que el campo generado se denominaba `flowTopology`, mientras que los perfiles solicitaban `flowType`.

### Corrección

Se añadió a los diez casos:

`result flowType;`

dentro del bloque `flowTopology`.

Commit:

`c92c282ca7cb549b4efdd88b402191163c706066`

Con esto el nombre del campo queda canónico y consistente con `lineProfiles` y con el futuro parser de PostPlotter.

**Estado:** ✅ B3 validó el paquete de diagnósticos; ✅ inconsistencia de nombre identificada y corregida; 🟡 repetir B3 junto con la tanda final para producir un dataset completamente homogéneo.


---

## 2026-09-26 — Auditoría numérica final V3–V7 después del rerun completo
**[RUN-DATA-COMMITTED] [NUMERICAL-AUDIT] [COUPLING] [ADAPTIVE-DT]**

Los logs finales de los diez casos controlados fueron sincronizados al repositorio después de ejecutar la matriz V3–V7. Los commits de resultados incluyen `5d5ccb00f1b3` (logs finales) y `54182ef3cab9` (sincronización local restante).

El análisis siguiente usa los archivos `foamLog` versionados directamente en GitHub. Para las métricas de coupling de `p_rgh` se excluyó el startup y se usó `t >= 0.1 s`.

### Resumen

| Caso | Configuración | Pasos | Tiempo final parseado (s) | Exec. (s) | Co max | max `p_rgh_0` post-startup | Mediana R | P95 R | R>1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | outer=2, dt fijo | 10000 | 10.000000 | 202.005 | 0.175912 | 0.0343238 @ 0.592 s | 0.605438 | 0.945131 | 2.62% |
| C3_reference | outer=2, dt fijo | 10000 | 10.000000 | 196.543 | 0.0700709 | 0.0173881 @ 9.985 s | 0.812747 | 1.059338 | 10.08% |
| B4_energy2 | outer=2, energy=2 | 10000 | 10.000000 | 250.984 | 0.176643 | 0.0307308 @ 0.591 s | 0.604283 | 0.943883 | 2.92% |
| C4_energy2 | outer=2, energy=2 | 10000 | 10.000000 | 220.093 | 0.0700709 | 0.0179951 @ 9.999 s | 0.813191 | 1.063103 | 10.62% |
| B5_outer3 | outer=3, dt fijo | 10000 | 10.000000 | 282.222 | 0.175874 | 0.0317178 @ 0.573 s | 0.597503 | 0.950764 | 3.62% |
| C5_outer3 | outer=3, dt fijo | 10000 | 10.000000 | 273.060 | 0.0700712 | 0.0178995 @ 9.981 s | 0.800997 | 1.041475 | 8.22% |
| B6_adaptiveDt | outer=3, dt adaptativo | 2810 | 9.999657 | 80.778 | 0.287759 | 0.0186405 @ 0.784957 s | 0.374538 | 0.764803 | 1.59% |
| C6_adaptiveDt | outer=3, dt adaptativo | 1584 | 10.003410 | 47.336 | 0.287049 | 0.0223995 @ 9.983344 s | 0.794831 | 1.034915 | 7.58% |
| B7_outer4 | outer=4, dt fijo | 10000 | 10.000000 | 381.367 | 0.175849 | 0.0362977 @ 0.731 s | 0.603163 | 0.950615 | 2.96% |
| C7_outer4 | outer=4, dt fijo | 10000 | 10.000000 | 365.418 | 0.0700710 | 0.0174552 @ 9.996 s | 0.808822 | 1.082497 | 10.65% |

donde:

`R = p_rgh(last outer Initial residual) / p_rgh(first outer Initial residual)`.

### Solver lineal vs coupling

En los diez casos, el `Final residual` del último solve de `p_rgh` permanece extremadamente bajo:

- mediana aproximadamente `3.9e-8 → 5.7e-8`;
- P99 aproximadamente `< 1e-7`;
- máximo observado aproximadamente `< 1e-7`.

Esto refuerza la separación ya establecida: el solver lineal de presión converge fuertemente dentro de cada solve, mientras que la evolución del **Initial residual entre outer corrections** describe el comportamiento del coupling no lineal. Un `R>1` no significa por sí mismo fallo del solver lineal.

### Outer-corrector sensitivity: diminishing returns

En las ramas de timestep fijo:

- B: mediana R = 0.6054 (outer2), 0.5975 (outer3), 0.6032 (outer4).
- C: mediana R = 0.8127 (outer2), 0.8010 (outer3), 0.8088 (outer4).

El cambio 2→3 es pequeño y 3→4 **no produce una mejora monotónica**; outer4 regresa hacia valores cercanos a outer2.

El costo sí crece con claridad en este rerun:

- B5 outer3 cuesta ~39.7% más que B3.
- B7 outer4 cuesta ~88.8% más que B3.
- C5 outer3 cuesta ~38.9% más que C3.
- C7 outer4 cuesta ~85.9% más que C3.

Por tanto, para estos casos y este intervalo de 0–10 s, outer4 añade costo sustancial sin evidencia de una mejora proporcional del coupling de `p_rgh`. Esto es evidencia de **diminishing returns**, no una regla universal para otros casos OpenFOAM.

### Energy-corrector sensitivity

B4/C4 mantienen métricas de coupling prácticamente iguales a B3/C3, mientras que en este rerun el tiempo de ejecución aumenta ~24.2% para B y ~12.0% para C.

Esto es consistente con la conclusión térmica previa: `nEnergyCorrectors=2` no modifica materialmente la solución monitoreada y tampoco muestra una mejora clara de coupling que justifique el costo adicional en esta matriz.

### Adaptive timestep V6

Respecto a V5, que comparte `nOuterCorrectors=3`:

- B6 reduce los pasos 10000→2810 y el tiempo 282.222→80.778 s: ~3.49× más rápido.
- C6 reduce los pasos 10000→1584 y el tiempo 273.060→47.336 s: ~5.77× más rápido.
- Mediana de `deltaT`: B6 ≈ 0.003954 s; C6 ≈ 0.005902 s.
- Máximo `deltaT` observado: B6 ≈ 0.005321 s; C6 ≈ 0.026623 s.
- Co máximo: B6 = 0.287759; C6 = 0.287049, por encima del `maxCo=0.25` configurado.

La revisión del fuente oficial de OpenFOAM Foundation v14, `src/finiteVolume/cfdTools/general/include/setDeltaT.H`, confirma que `adjustTimeStep` calcula el **siguiente** `deltaT` usando el Co observado y limita el crecimiento a 1.2× por ajuste. Por ello `maxCo` funciona como objetivo/controlador para la actualización del timestep y no como garantía matemática de que ningún Co reportado pueda sobrepasarlo transitoriamente.

El acumulado final de continuidad reportado también es mayor en V6:

- B6: 2.44980e-4 vs B5: 1.65205e-4.
- C6: 2.71897e-4 vs C5: 1.78172e-4.

Esto merece seguimiento; no debe interpretarse por sí solo como invalidez física. Antes de seleccionar V6 como configuración productiva hay que comparar sus historias térmicas, fase, perfiles y diagnósticos físicos contra V5.

### Diferencia B/C en coupling

Las ramas B de timestep fijo muestran una reducción relativa de Initial residual más fuerte (mediana R ~0.60) y menos eventos `R>1` (~2.6–3.6%) que las C (~0.80 y ~8.2–10.6%).

Al mismo tiempo, B puede presentar máximos de `p_rgh_0` mayores que C. Por tanto deben mantenerse separadas dos preguntas:

1. magnitud del mismatch al inicio del solve;
2. reducción relativa conseguida durante el coupling.

La diferencia puede estar relacionada con las formulaciones físicas B/C, pero no se etiqueta aquí como “estabilidad superior/inferior” sin más evidencia.

**Estado:** ✅ logs finales V3–V7 versionados; ✅ outer2/3/4 auditado; ✅ V6 adaptive auditado numéricamente; ✅ convergencia lineal separada de coupling; 🟡 comparación física completa de V6/V7 con los nuevos outputs de `researchDiagnostics` todavía pendiente.


---

## 2026-09-26 — Auditoría numérica final V3–V7 desde resultados sincronizados
**[RUN-VERIFIED] [GIT-VERIFIED] [NUMERICAL-AUDIT]**

Los resultados finales de los diez casos controlados V3–V7 fueron sincronizados desde la estación de trabajo local al repositorio y auditados directamente desde los `log.foamMultiRun` y `logs/` versionados.

Commits de resultados:
- `5d5ccb00f1b3...` — actualización de logs finales V3–V7.
- `54182ef3cab9...` — sincronización restante de datos locales.

### Comparación de costo y coupling de `p_rgh` (startup excluido: t < 0.1 s)

| Caso | Pasos | Max p0 | Mediana p0 | Mediana R | p95 R | R>1 | Co max | Exec. s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | 10000 | 0.0343238 | 0.00835789 | 0.605438 | 0.945131 | 2.62% | 0.175912 | 202.005 |
| C3_reference | 10000 | 0.0173881 | 0.00748726 | 0.812747 | 1.05934 | 10.08% | 0.0700709 | 196.543 |
| B4_energy2 | 10000 | 0.0307308 | 0.00835290 | 0.604283 | 0.943883 | 2.92% | 0.176643 | 250.984 |
| C4_energy2 | 10000 | 0.0179951 | 0.00751839 | 0.813191 | 1.06310 | 10.62% | 0.0700709 | 220.093 |
| B5_outer3 | 10000 | 0.0317178 | 0.00825669 | 0.597503 | 0.950764 | 3.62% | 0.175874 | 282.222 |
| C5_outer3 | 10000 | 0.0178995 | 0.00775813 | 0.800997 | 1.04147 | 8.22% | 0.0700712 | 273.060 |
| B6_adaptiveDt | 2810 | 0.0186405 | 0.00236917 | 0.374538 | 0.764803 | 1.59% | 0.287759 | 80.778 |
| C6_adaptiveDt | 1584 | 0.0223995 | 0.00898528 | 0.794831 | 1.03491 | 7.58% | 0.287049 | 47.336 |
| B7_outer4 | 10000 | 0.0362977 | 0.00831734 | 0.603163 | 0.950615 | 2.96% | 0.175849 | 381.367 |
| C7_outer4 | 10000 | 0.0174552 | 0.00759476 | 0.808822 | 1.08250 | 10.65% | 0.0700710 | 365.418 |

Aquí `R = p_rgh,last(initial) / p_rgh,first(initial)` dentro del timestep. `R>1` significa que el Initial residual aumentó a través del coupling; no implica por sí solo fallo del solver lineal.

Los últimos solves lineales de presión siguen terminando con residual final típicamente de orden `10^-8` a `10^-7` en todos los casos, por lo que debe mantenerse separada la interpretación de convergencia lineal y convergencia del acoplamiento PIMPLE.

### Resultado de outer correctors

Comparando el baseline V3 con V5 y V7:

- B: mediana R = 0.6054 → 0.5975 → 0.6032 para outer 2 → 3 → 4.
- C: mediana R = 0.8127 → 0.8010 → 0.8088.
- El costo de B7 frente a B3 aumenta de 202.0 s a 381.4 s (~89%).
- El costo de C7 frente a C3 aumenta de 196.5 s a 365.4 s (~86%).

La cuarta outer correction no produce una mejora monotónica en la mediana de R respecto a outer3, mientras el costo aumenta fuertemente. Esto refuerza el resultado previo de diminishing returns para el rango probado. No se interpreta como una selección de modelo físico.

### Resultado de energy correctors

B4/C4 mantienen métricas de coupling muy próximas a B3/C3, mientras incrementan el costo. Esto es consistente con la sensibilidad térmica/central previamente observada como pequeña.

### Adaptive timestep V6

V6 reduce fuertemente el número de pasos y el tiempo de ejecución:

- B6: 2810 pasos, 80.78 s.
- C6: 1584 pasos, 47.34 s.

`deltaT` observado:
- B6: mediana 0.003954 s, máximo 0.005321 s.
- C6: mediana 0.005902 s, máximo 0.026623 s.

El Courant máximo registrado alcanza ~0.288 en ambos casos, por encima del `maxCo=0.25` configurado, mientras los valores finales quedan aproximadamente en 0.25. Esto se registra como un sobrepaso observado del target durante la adaptación y requiere interpretación en contexto del algoritmo de ajuste; no se etiqueta automáticamente como inestabilidad.

La continuidad acumulada final es mayor en V6:
- B6: 2.4498e-4.
- C6: 2.71897e-4.

Antes de aceptar V6 como sustituto del timestep fijo se requiere comparar los resultados físicos (T, fase, perfiles, gradientes y energía), no solo costo y residuals.

**Estado:** auditoría numérica final V3–V7 completada desde datos versionados. Siguiente etapa: comparación física de outputs de postProcessing.


---

## 2026-09-26 — Matriz de validación y auditoría de paridad con Quick-Cup experimental
**[VALIDATION-GATE] [SOURCE-AUDIT] [NO-PHYSICS-CHANGE]**

Se completó una auditoría de la configuración controlada V3–V7 contra el benchmark Quick-Cup hipereutéctico/hipoeutéctico descrito por Chiumenti et al.

Hallazgos principales:

- V3–V7 permanecen congelados como estudio de sensibilidad numérica y de formulación de buoyancy.
- El rebound térmico de C3/C4/C5 (+5.35 K) se reproduce con prácticamente la misma Tmin y recuperación de fracción líquida bajo los cambios numéricos probados, por lo que no es un artefacto de elegir B3/C3 frente a B4/C4/B5/C5. En el modelo actual coincide con remelting local y no se etiqueta como recalescencia por nucleación.
- El caso actual no es todavía un benchmark experimental alineado: 1500 K iniciales frente a 1573.15 K en el Quick-Cup del paper, HTC exterior 10 frente a 50 W/m2K y propiedades de molde distintas.
- La resistencia de la capa de interfaz actual, 0.2 mm con k=0.1 W/mK, equivale a aproximadamente 500 W/m2K y sí coincide con el HTC metal–molde del paper.
- La temperatura inicial actual (1226.85 °C) está ~33 °C por debajo del T_start_L=1260 °C utilizado por el modelo hipereutéctico/hipoeutéctico del paper.
- El `solidificationMelting` estándar usa una sola variable de fracción líquida ligada a una relación de equilibrio, mientras el modelo del paper usa transformaciones dendrítica y eutéctica con leyes cinéticas temporales y subenfriamiento.
- No se localizó en el repositorio ni en los archivos disponibles una serie temporal experimental raw/CSV; por tanto no se fabrican RMSE/MAE.

Se añadieron:
- `VALIDATION_MATRIX.md`
- `VALIDATION_MATRIX_ES.md`
- `VALIDATION_MATRIX_EN.md`

**Decisión:** antes de escribir un fvModel cinético, construir un caso de equilibrio alineado con las condiciones experimentales. La rama cinética se abre solo si ese caso demuestra una limitación estructural del modelo de equilibrio.


---

## 2026-09-26 — Diagnóstico directo de términos de momento de `solidificationMeltingSource`
**[POSTPROCESSING] [PHYSICS-DIAGNOSTICS] [NO-PHYSICS-CHANGE]**

Después de completar la auditoría numérica V3–V7, se añadió un diagnóstico específico para determinar si las diferencias observadas en velocidad y comportamiento de la zona pastosa provienen del acoplamiento presión–velocidad, de la flotación o del amortiguamiento Darcy del modelo `solidificationMeltingSource`.

El nuevo bloque `solidificationMeltingMomentumDiagnostics` fue añadido a:

- B3_reference
- B4_energy2
- B5_outer3
- B6_adaptiveDt
- B7_outer4
- C3_reference
- C4_energy2
- C5_outer3
- C6_adaptiveDt
- C7_outer4

El diagnóstico lee directamente de `constant/metal/fvModels` los parámetros `Cu`, `q`, `beta`, `rhoRef`, `Tsol`, `Tliq` y `alpha1e`; por lo tanto no duplica manualmente la parametrización entre casos.

Se reconstruye el coeficiente de amortiguamiento Darcy:

`D = Cu (1-alpha_l)^2 / (alpha_l^3 + q)`

y su contribución de aceleración:

`a_D = -D U`.

También se reconstruyen:

- `phaseChangeModelDeltaT`: diferencia térmica usada por el modelo de cambio de fase.
- `phaseChangeBuoyancyAcceleration`: escala de aceleración `g beta DeltaT`.
- `phaseChangeBuoyancySu`: fuente explícita de flotación `rhoRef g beta DeltaT`.
- `pRghAcceleration`: `-grad(p_rgh)/rho`.
- razones locales `phaseChangeDragToBuoyancy` y `phaseChangeDragToPressure`.

Campos escritos:

- `phaseChangeSolidFraction`
- `phaseChangeDarcyCoeff`
- `phaseChangeDarcySp`
- `phaseChangeDarcyAcceleration`
- `phaseChangeModelDeltaT`
- `phaseChangeBuoyancyAcceleration`
- `phaseChangeBuoyancySu`
- `pRghAcceleration`
- `magPhaseChangeDarcyAcceleration`
- `magPhaseChangeBuoyancyAcceleration`
- `magPRghAcceleration`
- `phaseChangeDragToBuoyancy`
- `phaseChangeDragToPressure`

### Relación con los resultados V6 y V7 ya documentados

Esta ampliación no modifica las conclusiones numéricas previas:

- V6 sigue siendo la rama de timestep adaptativo, con fuerte reducción de costo pero necesidad de comprobar equivalencia física.
- V7 sigue siendo la prueba de cuatro outer correctors, con costo mucho mayor y sin mejora monotónica clara del coupling respecto a V5.
- Los residuals lineales de presión siguen terminando típicamente en el orden de 10^-8–10^-7; el problema abierto no es un fallo simple del solver lineal.
- La siguiente comparación debe usar simultáneamente los resultados ya registrados de V3–V7 y los nuevos campos de fuerza/amortiguamiento.

### Estado de validación

El código de diagnóstico está versionado, pero sus nuevos campos todavía deben validarse mediante una corrida corta de B7 y C7 en OpenFOAM Foundation v14 antes de relanzar toda la matriz.

**Siguiente gate:** compilar/ejecutar B7 y C7, comprobar escritura de los campos nuevos y, si pasa, aplicar el diagnóstico a la comparación física V3–V7.


### Corrección de compatibilidad detectada en validación B7

La primera validación de B7 falló antes de ejecutar el solver por compilación del `coded` function object:

`fatal error: fvCFD.H: No such file or directory`

Se confirmó que el problema era exclusivamente de includes del código dinámico bajo OpenFOAM Foundation v14; no correspondía a un fallo físico ni numérico del caso.

Se sustituyó `fvCFD.H` por headers específicos compatibles (`fvMesh.H`, `volFields.H`, `uniformDimensionedFields.H`, `IOdictionary.H`, `zeroGradientFvPatchFields.H`, `fvcGrad.H`) en los diez casos V3–V7. La validación B7 debe repetirse antes de ejecutar C7 o la matriz completa.


### Segunda corrección de compatibilidad B7

La segunda validación de compilación del diagnóstico detectó dos diferencias adicionales de API en OpenFOAM Foundation v14:

- `Time::timeName()` requiere un argumento de tiempo en este contexto de código dinámico.
- `gMax(field)` devuelve directamente un `scalar`, por lo que no debe usarse `.value()`.

Correcciones aplicadas a los diez casos V3–V7:

- `m.time().timeName()` → `m.time().timeName(m.time().timeOutputValue())`
- `gMax(...).value()` → `gMax(...)`

El fallo sigue siendo exclusivamente de compilación del postproceso dinámico y no corresponde a inestabilidad del solver ni a un problema físico del modelo.


### Tercera corrección de compatibilidad B7

La tercera validación mostró que `Time::timeOutputValue()` no existe en la API de OpenFOAM Foundation v14 instalada. Se verificó contra la interfaz de `Time` de OpenFOAM 14 que `timeName` acepta un `scalar` explícito, por lo que el código se cambió a:

`m.time().timeName(m.time().value())`

Esta corrección fue aplicada a los diez casos controlados V3–V7. El fallo sigue siendo exclusivamente de compilación del postproceso dinámico.


### Validación runtime B7 del diagnóstico de momento

La corrida completa de `B7_outer4` compiló y ejecutó correctamente el bloque `solidificationMeltingMomentumDiagnostics` bajo OpenFOAM Foundation v14.

Valores observados al final de la corrida:

- `max(phaseChangeDarcyCoeff) = 1e8 1/s`.
- `max(|phaseChangeDarcyAcceleration|)` disminuyó aproximadamente de 546.7 a 332.0 m/s2 en las últimas escrituras mostradas.
- `max(|phaseChangeBuoyancyAcceleration|) = 0`, consistente con `beta = 0` en la familia B.
- `max(|pRghAcceleration|)` disminuyó aproximadamente de 1.897 a 1.723 m/s2.

El valor máximo de Darcy es consistente con la forma del modelo:
`D = Cu(1-alpha_l)^2/(alpha_l^3 + q)`.
Con `Cu=1e5 1/s`, `q=1e-3` y `alpha_l=0`, el límite sólido es `D=1e8 1/s`.

Advertencia de interpretación: los máximos globales de Darcy y presión pueden ocurrir en celdas distintas y no deben dividirse entre sí para inferir dominancia local. Para esa comparación deben usarse los campos celda-a-celda `phaseChangeDragToPressure` y `phaseChangeDragToBuoyancy`, junto con `alpha_l`, `U` y las magnitudes absolutas.

**Estado:** B7 diagnostic runtime validation PASSED. Siguiente caso de validación: C7.


### Validación runtime C7 del diagnóstico de momento

La corrida completa de `C7_outer4` compiló y ejecutó correctamente el bloque `solidificationMeltingMomentumDiagnostics` bajo OpenFOAM Foundation v14.

Valores observados al final de la corrida:

- `max(phaseChangeDarcyCoeff) = 1e8 1/s`.
- `max(|phaseChangeDarcyAcceleration|)` disminuyó aproximadamente de 422.25 a 418.58 m/s2 en las últimas escrituras mostradas.
- `max(|phaseChangeBuoyancyAcceleration|)` se mantuvo alrededor de 0.1070–0.1074 m/s2.
- `max(|pRghAcceleration|)` aumentó ligeramente de aproximadamente 0.08177 a 0.08247 m/s2.

A diferencia de la familia B, donde `beta=0` y la contribución de flotación del `solidificationMeltingSource` es nula, C7 presenta una contribución de flotación distinta de cero, consistente con `beta=1.13e-4 1/K`.

Advertencia: los máximos globales de Darcy, buoyancy y presión no necesariamente ocurren en la misma celda. Para evaluar dominancia local deben analizarse `phaseChangeDragToBuoyancy`, `phaseChangeDragToPressure`, `phaseChangeSource:alpha1` y `U` celda a celda.

**Estado:** C7 diagnostic runtime validation PASSED. El paquete de diagnóstico de momento queda validado para ambas formulaciones B y C.


### Exportación compacta de diagnósticos de momento a postProcessing

Se añadió `system/momentumPostProcessing` a B3–B7 y C3–C7 y se integró en `Allrun` después de una corrida que alcance `End`.

Objetivo: conservar en Git evidencia científica útil de los campos volumétricos de `solidificationMeltingMomentumDiagnostics` sin versionar todos los directorios temporales OpenFOAM.

El postproceso relee los campos volumétricos ya escritos y genera:

- `momentumMean`: promedios volumétricos de fracción sólida, coeficiente Darcy, deltaT del modelo y magnitudes de aceleración Darcy, buoyancy y gradiente de `p_rgh`.
- `momentumMax`: máximos y ubicación de los mismos campos.
- `momentumHorizontalProfiles`: perfiles en y=20 mm y y=30 mm.
- `momentumVerticalProfiles`: perfil en x=20 mm.
- Los perfiles incluyen vectores, magnitudes y ratios locales Darcy/buoyancy y Darcy/pressure.

Los ratios se conservan como diagnóstico local; no debe inferirse dominancia física dividiendo máximos globales o interpretando ratios grandes cuando el denominador es casi cero.

`Allrun` ejecuta esta reducción únicamente si `log.foamMultiRun` contiene `End`, evitando generar un paquete de resultados de una corrida fallida.

Los directorios temporales completos siguen ignorados por Git; `postProcessing/` permanece versionado.


### Corrección del helper de postprocesado por lote

La primera ejecución de `sh postprocess_momentum_all.sh` falló antes de llamar a `foamPostProcess` porque el script usaba `cd ${0%/*}`. Cuando el script se invoca como `sh postprocess_momentum_all.sh`, `$0` no contiene una barra y esa expansión produce el propio nombre del archivo, por lo que `cd` intenta entrar a un archivo.

Se sustituyó por una resolución robusta del directorio del script mediante `dirname "$0"`, de modo que el helper sea location-independent y funcione tanto con `sh postprocess_momentum_all.sh` como desde otras rutas.

No hubo fallo de solver ni pérdida de resultados; el error ocurrió antes de iniciar el postprocesado.


### Corrección de validación previa al postprocesado por lote

La primera versión corregida de `postprocess_momentum_all.sh` todavía usaba `grep "^End$"` sobre `log.foamMultiRun` como criterio de validez. Las corridas válidas de los casos controlados no contienen necesariamente una línea que coincida exactamente con ese patrón, por lo que todos los casos fueron omitidos con `SKIP`.

Se eliminó esa dependencia. El helper ahora exige:
1. existencia de `log.foamMultiRun`; y
2. existencia local de campos `phaseChangeDarcyCoeff` en los directorios de tiempo.

Para corridas futuras, `Allrun` captura inmediatamente el código de salida de `foamMultiRun` y solo ejecuta la reducción de momentum cuando el solver devuelve estado 0.

Este problema afectó únicamente la automatización del postprocesado; no invalida las simulaciones ya calculadas.


### Corrección de región en momentumPostProcessing

La primera ejecución real de `foamPostProcess` falló en todos los casos con:

`request for objectRegistry region0 from objectRegistry <case> failed; available objects: metal`.

Diagnóstico: los function objects de `system/momentumPostProcessing` (`momentumMean`, `momentumMax`, `momentumHorizontalProfiles`, `momentumVerticalProfiles`) no declaraban explícitamente `region metal;`. Aunque `foamPostProcess` se invocaba con `-region metal`, los `regionFunctionObject` seguían resolviendo la región por defecto como `region0`.

Corrección: se añadió `region metal;` a los cuatro function objects en B3–B7 y C3–C7.

El error ocurrió antes del cálculo de estadísticas/perfiles y no afecta las simulaciones CFD ni los campos volumétricos ya escritos.


### Validación de momentumPostProcessing en B3

La ejecución retrospectiva de `foamPostProcess` sobre `B3_reference` completó correctamente hasta `End`, confirmando que:

- los campos volumétricos nuevos se leen correctamente desde los directorios de tiempo;
- `momentumMean` y `momentumMax` funcionan sobre la región `metal`;
- la configuración multirregión corregida es válida en OpenFOAM Foundation v14.

Valores a `t=10 s`:

- fracción sólida media = 0.126972;
- coeficiente Darcy medio = 5.58325e6 1/s;
- `phaseChangeModelDeltaT` medio = -1.13266 K;
- aceleración Darcy media = 7.7232 m/s2;
- aceleración buoyancy media = 0 m/s2;
- aceleración media asociada a gradiente de `p_rgh` = 0.0967021 m/s2;
- máximo coeficiente Darcy = 1e8 1/s;
- máximo `|DarcyAccel|` = 334.288 m/s2;
- máximo `|pRghAccel|` = 1.72493 m/s2.

El valor de buoyancy igual a cero es consistente con la configuración B (`beta=0`). Los máximos globales no deben compararse entre sí como prueba directa de dominancia local.

**Estado:** retrospective momentum post-processing validation PASSED for B3.


## V5 fixed vs V6 adaptive — análisis espacial alineado por tiempo físico

Se compararon V5 y V6 usando los perfiles reales de `postProcessing`, evaluando V5 mediante interpolación temporal lineal en los tiempos físicos nativos de V6. No se compararon índices de timestep ni números de directorio.

Cortes principales:
- vertical: `x = 20 mm`, dirección Y;
- horizontal: `y = 20 mm`, dirección X.

La mushy zone se identificó con `0.05 < alphaL < 0.95`. Las métricas de campo se calcularon sobre la unión de puntos clasificados como mushy en cualquiera de los dos casos comparados.

### Familia B: B5 vs B6

Vertical, t = 2.035181 s:
- posición alphaL=0.5: B6 = 0.457 mm; B5 interpolado = 0.489 mm;
- posición alphaL=0.95: B6 = 6.728 mm; B5 = 6.601 mm;
- RMSE mushy: alphaL = 0.00874; T = 0.986 K; |U| = 7.45e-5 m/s;
- RMSE normalizado respecto al valor medio absoluto de B5: |U| = 3.28%, |DarcyAccel| = 19.0%, |pRghAccel| = 2.61%.

Vertical, t = 5.034212 s:
- alphaL=0.5: B6 = 0.984 mm; B5 = 1.031 mm;
- alphaL=0.95: B6 = 11.723 mm; B5 = 11.899 mm;
- RMSE mushy: alphaL = 0.01277; T = 1.63 K;
- |U| = 0.00201 m/s, equivalente a ~83.9% del valor medio absoluto de B5 en la zona evaluada;
- |DarcyAccel| NRMSE = 45.3%;
- |pRghAccel| NRMSE = 26.4%.

Vertical, t = 9.946515 s:
- alphaL=0.05: B6 = 0.940 mm; B5 = 1.007 mm;
- alphaL=0.5: B6 = 1.828 mm; B5 = 1.922 mm;
- alphaL=0.95: B6 = 19.433 mm; B5 = 17.923 mm;
- ancho 0.05→0.95: B6 = 18.493 mm; B5 = 16.916 mm, incremento ≈ 1.577 mm (+9.3%);
- RMSE mushy: alphaL = 0.01427; T = 1.77 K;
- |U| NRMSE ≈ 94.5%;
- |DarcyAccel| NRMSE ≈ 80.2%;
- |pRghAccel| NRMSE ≈ 50.4%.

Horizontal y=20 mm, t = 9.946515 s:
- alphaL=0.95 crossings B6: x = 13.236 y 26.764 mm;
- alphaL=0.95 crossings B5: x = 10.927 y 29.143 mm;
- ancho del núcleo con alphaL>0.95: B6 ≈ 13.529 mm; B5 ≈ 18.217 mm;
- el núcleo casi líquido es ≈4.69 mm más angosto en B6;
- alphaL NRMSE = 0.78%, T RMSE = 1.79 K;
- |U| NRMSE ≈ 58.4%, |DarcyAccel| ≈ 75.2%, |pRghAccel| ≈ 17.3%.

Interpretación B:
el adaptive timestep no desplaza simplemente un frente rígido. Produce una transición de fase espacialmente más ancha y altera fuertemente el campo de flujo/momentum en la mushy zone, aun cuando T y alphaL muestran diferencias globales pequeñas.

### Familia C: C5 vs C6

Vertical, t = 1.918353 s:
- C6 todavía no presenta cruce alphaL=0.5 sobre el perfil, mientras C5 lo presenta a y≈0.349 mm;
- alphaL=0.95: C6 = 3.895 mm; C5 = 3.630 mm;
- RMSE mushy: alphaL = 0.0292; T = 2.44 K;
- |U| NRMSE ≈ 8.14%;
- |DarcyAccel| ≈ 86.3%;
- |pRghAccel| ≈ 20.5%.

Vertical, t = 5.092511 s:
- alphaL=0.5: C6 = 0.921 mm; C5 = 0.989 mm;
- alphaL=0.95: C6 = 24.282 mm; C5 = 24.350 mm;
- RMSE mushy: alphaL = 0.0114; T = 1.42 K;
- |U| NRMSE ≈ 4.13%;
- |DarcyAccel| ≈ 14.9%;
- |pRghAccel| ≈ 8.49%.

Vertical, t = 9.182456 s:
- alphaL=0.05: C6 = 0.465 mm; C5 = 0.619 mm;
- alphaL=0.5: C6 = 1.370 mm; C5 = 1.489 mm;
- alphaL=0.95: C6 = 20.088 mm; C5 = 18.299 mm;
- ancho 0.05→0.95: C6 ≈ 19.623 mm; C5 ≈ 17.680 mm, incremento ≈ 1.943 mm (+11.0%);
- RMSE mushy: alphaL = 0.0184; T = 1.07 K;
- |U| NRMSE ≈ 8.26%;
- |DarcyAccel| ≈ 23.1%;
- |pRghAccel| ≈ 26.4%.

Horizontal y=20 mm, t = 9.182456 s:
- alphaL=0.95 crossings C6: x = 4.355 y 35.645 mm;
- C5: x = 4.324 y 35.676 mm;
- el ancho del núcleo alphaL>0.95 cambia solo ≈0.063 mm;
- alphaL NRMSE ≈ 0.027%;
- T RMSE ≈ 0.290 K;
- |U| NRMSE ≈ 4.34%;
- |DarcyAccel| ≈ 5.78%;
- |pRghAccel| ≈ 9.41%.

Interpretación C:
la sensibilidad adaptive es anisotrópica. El corte horizontal central permanece casi idéntico, pero el perfil vertical muestra ensanchamiento de la mushy zone. El efecto sobre velocidad y momentum es menor que en B al final, aunque no despreciable.

### Conclusión de V5 vs V6

V6 no puede considerarse todavía físicamente equivalente a V5 solo por reproducir promedios globales cercanos. La comparación a tiempo físico igual muestra que el adaptive timestep modifica principalmente:
1. el espesor/distribución espacial de la mushy zone;
2. la velocidad local;
3. las aceleraciones Darcy y asociadas a p_rgh.

La temperatura es comparativamente robusta (RMSE típicamente ~0.3–2.4 K en los cortes estudiados), mientras que las variables de momentum son bastante más sensibles.

La familia B muestra la sensibilidad más fuerte del flujo al adaptive timestep. La familia C mantiene mejor el perfil lateral, pero también presenta ensanchamiento vertical de la mushy zone.

Decisión provisional: mantener V5 fixed como referencia para validación física. V6 debe tratarse como una opción de aceleración que requiere un criterio de tolerancia explícito antes de adoptarse como configuración final.


## Análisis específico de perfiles de velocidad vertical Uy — B3–B7 / C3–C7

Se realizó una comparación explícita de la componente vertical `Uy` en los tres perfiles espaciales disponibles:
- horizontal `y = 20 mm`;
- horizontal `y = 30 mm`;
- vertical central `x = 20 mm`.

Los casos fixed se compararon a `t = 10 s`. Los casos adaptive V6 se compararon contra V5 interpolado al mismo tiempo físico disponible de V6.

### Sensibilidad entre versiones fixed — familia B

Referencia: B3.

A `t = 10 s`:

- B4 vs B3:
  - y=20 mm: NRMSE/RMS(Uy) = 4.44%, corr = 0.9990;
  - y=30 mm: NRMSE/RMS(Uy) = 9.45%, corr = 0.9955;
  - vertical x=20 mm: NRMSE/RMS(Uy) = 0.42%, corr = 0.999996.

- B5 vs B3:
  - y=20 mm: 4.00%, corr = 0.9992;
  - y=30 mm: 8.55%, corr = 0.9964;
  - vertical: 0.45%, corr = 0.999998.

- B7 vs B3:
  - y=20 mm: 5.47%, corr = 0.9985;
  - y=30 mm: 11.64%, corr = 0.9933;
  - vertical: 0.45%, corr = 0.999998.

Interpretación: en B, cambiar correctores produce diferencias modestas en Uy, especialmente cerca de la parte superior (`y=30 mm`), pero no cambia cualitativamente el patrón. El incremento a 4 outer correctors no produce convergencia monotónica hacia un perfil distinto; B7 presenta incluso la mayor diferencia lateral respecto a B3.

### Sensibilidad entre versiones fixed — familia C

Referencia: C3.

A `t = 10 s`, C4/C5/C7 son prácticamente indistinguibles de C3:

- y=20 mm: NRMSE/RMS < 0.007%;
- y=30 mm: NRMSE/RMS < 0.010%;
- vertical: NRMSE/RMS < 0.004%.

Correlaciones ≈ 1 en todos los perfiles.

Interpretación: la componente Uy de la familia C es esencialmente insensible a 2→3→4 outer correctors y al segundo energy corrector en esta serie.

### Efecto adaptive — B6 vs B5

Comparación a `t = 9.946515 s`, con B5 interpolado al mismo tiempo físico.

- y=20 mm:
  - NRMSE/RMS(Uy) = 50.18%;
  - corr = 0.865;
  - 4/80 puntos cambian de signo;
  - B5: Uy_min = -0.01762 m/s, Uy_max = +0.00512 m/s;
  - B6: Uy_min = -0.01531 m/s, Uy_max = +0.00645 m/s.

- y=30 mm:
  - NRMSE/RMS(Uy) = 80.60%;
  - corr = 0.716;
  - 2/80 puntos cambian de signo;
  - B5: Uy_min = -0.01933 m/s, Uy_max = +0.01354 m/s;
  - B6: Uy_min = -0.01027 m/s, Uy_max = +0.00306 m/s.

- vertical x=20 mm:
  - NRMSE/RMS(Uy) = 99.26%;
  - corr = 0.121;
  - 20/80 puntos cambian de signo;
  - B5: Uy_min = -0.01953 m/s, Uy_max = +0.00400 m/s;
  - B6: Uy_min = -0.00150 m/s, Uy_max = +0.00237 m/s.

Interpretación: B6 no conserva el campo vertical de velocidad de B5. La componente descendente sobre la línea vertical central se reduce aproximadamente en un orden de magnitud y la estructura espacial pierde correlación. El adaptive timestep altera fuertemente la convección vertical en la formulación B.

### Efecto adaptive — C6 vs C5

Comparación a `t = 9.182456 s`, con C5 interpolado al mismo tiempo físico.

- y=20 mm:
  - NRMSE/RMS(Uy) = 3.33%;
  - corr = 0.999964;
  - sin cambios de signo.

- y=30 mm:
  - NRMSE/RMS(Uy) = 1.69%;
  - corr = 0.999867;
  - sin cambios de signo.

- vertical x=20 mm:
  - NRMSE/RMS(Uy) = 3.42%;
  - corr = 0.999787;
  - sin cambios de signo;
  - C5 Uy_max ≈ 0.01282 m/s;
  - C6 Uy_max ≈ 0.01313 m/s.

Interpretación: C6 conserva razonablemente bien la estructura de Uy de C5 incluso con adaptive timestep.

### Diferencia de formulación B vs C

Comparación B3 vs C3 a `t = 10 s`:

- y=20 mm:
  - corr = 0.284;
  - 28/80 puntos cambian de signo.

- y=30 mm:
  - corr = -0.715;
  - 57/80 puntos cambian de signo.

- vertical x=20 mm:
  - corr = -0.689;
  - 46/80 puntos cambian de signo;
  - B3: Uy_min = -0.01945 m/s, Uy_max = +0.00401 m/s;
  - C3: Uy_min = -0.000239 m/s, Uy_max = +0.01209 m/s.

Interpretación: B y C no difieren solo en magnitud; muestran estructuras de circulación vertical cualitativamente distintas. En la línea vertical central, B está dominado por una componente descendente fuerte, mientras C está dominado por una componente ascendente.

### Conclusión sobre Uy

1. V4/V5/V7 fixed no cambian cualitativamente Uy respecto a V3.
2. La familia C es extraordinariamente estable frente a cambios de correctores.
3. La familia B muestra sensibilidad lateral moderada a correctores, especialmente cerca de y=30 mm.
4. B6 adaptive altera fuertemente Uy y no puede considerarse equivalente a B5 para estudios donde la convección sea relevante.
5. C6 adaptive conserva mucho mejor Uy y sí parece numéricamente cercano a C5 en la estructura de flujo vertical.
6. La diferencia B vs C es mayor que la diferencia entre versiones fixed dentro de una misma familia y corresponde a un cambio cualitativo del patrón de circulación.


## Barrido temporal exhaustivo de Uy — todas las corridas controladas

Se ejecutó `analysis_tools/uy_temporal_analysis.py` sobre todos los tiempos almacenados de los perfiles:
- `y=20 mm`;
- `y=30 mm`;
- `x=20 mm` vertical.

Los casos fixed se compararon en tiempos físicos exactamente comunes (101 muestras entre 0 y 10 s). Los casos adaptive se evaluaron en todos sus tiempos nativos y el caso fixed de referencia se interpoló linealmente al mismo tiempo físico.

Resultados completos:
- `analysis_results/uy_temporal/uy_temporal_metrics.csv`
- `analysis_results/uy_temporal/uy_temporal_summary.md`

### B fixed

B4/B5/B7 mantienen el patrón de Uy de B3 durante toda la simulación.

B4 vs B3:
- y20: mediana NRMSE/RMS = 4.21%, pico 12.95% a 8.2 s;
- y30: mediana 4.43%, pico 9.47% a 9.9 s;
- vertical: mediana 0.80%, pico 3.08%.

B5 vs B3:
- y20: mediana 3.57%, pico 11.53% a 8.2 s;
- y30: mediana 3.91%, pico 8.57% a 9.9 s;
- vertical: mediana 0.82%, pico 4.00%.

B7 vs B3:
- y20: mediana 5.20%, pico 16.02% a 8.2 s;
- y30: mediana 5.44%, pico 11.65% a 9.9 s;
- vertical: mediana 0.79%, pico 3.96%.

Conclusión: añadir correctores no genera una convergencia monotónica del perfil Uy; B7 puede diferir más de B3 que B5. Sin embargo, la correlación espacial permanece alta y no hay cambio cualitativo de circulación entre los casos fixed.

### C fixed

C4/C5/C7 permanecen prácticamente idénticos a C3 durante toda la corrida:
- medianas y picos de NRMSE/RMS por debajo de ~0.03%;
- correlación ≈ 1;
- sin cambios significativos de signo.

Conclusión: la solución Uy de la familia C es esencialmente insensible a los correctores adicionales probados.

### B6 adaptive vs B5 fixed

B6 diverge desde los primeros tiempos almacenados.

y20:
- primera diferencia >=5%: 0.223624 s;
- >=10%: 1.76685 s;
- >=25%: 2.31438 s;
- >=50%: 2.60859 s;
- mediana NRMSE/RMS = 33.10%;
- pico = 80.09% a 7.500923 s;
- correlación mínima = 0.6706 a 3.275592 s.

y30:
- >=10% ya a 0.223624 s;
- >=25% y >=50% a 1.254542 s;
- mediana = 59.12%;
- pico = 84.81% a 1.76685 s;
- correlación mínima = 0.5687.

vertical:
- >=25% desde 0.223624 s;
- >=50% a 0.763943 s;
- mediana = 75.23%;
- pico = 99.26% a 9.946515 s;
- correlación cae a 0.1211 al final;
- máximo desacuerdo de signo = 53/80 puntos a 9.422639 s.

La divergencia no aparece únicamente al final: comienza durante el transitorio inicial y después se acumula/reorganiza. En la línea vertical, B6 termina suprimiendo casi por completo la fuerte corriente descendente presente en B5.

### C6 adaptive vs C5 fixed

C6 presenta una discrepancia relativa inicial, pero posteriormente conserva bien el patrón Uy.

A 0.953122 s:
- y20: NRMSE/RMS = 13.81%, RMSE absoluto = 8.13e-4 m/s;
- y30: 13.70%, RMSE = 6.80e-4 m/s;
- vertical: 22.26%, RMSE = 5.08e-4 m/s.

Después:
- medianas: 3.03% (y20), 4.79% (y30), 3.42% (vertical);
- al último tiempo 9.182456 s: 3.33%, 1.69% y 3.42%, respectivamente;
- correlaciones finales > 0.9997;
- no se alcanzan 25% ni 50% en ningún perfil.

Conclusión: C6 tiene un transitorio temprano algo diferente, pero el campo Uy permanece estructuralmente muy cercano a C5 durante la mayor parte de la corrida.

### B3 vs C3

La diferencia de formulación aparece casi inmediatamente:
- los tres perfiles superan 25% NRMSE/RMS desde 0.1 s;
- y20 alcanza un pico de 189.3%;
- y30 145.7%;
- vertical 190.4%;
- correlaciones mínimas: -0.352 (y20), -0.731 (y30), -0.794 (vertical).

Conclusión general:
1. Los correctores adicionales no cambian cualitativamente Uy en los casos fixed.
2. La formulación C es extremadamente estable frente a los cambios numéricos probados.
3. B6 adaptive NO es equivalente a B5: altera la convección vertical desde etapas tempranas.
4. C6 adaptive sí conserva razonablemente la estructura de Uy de C5 después del primer transitorio.
5. La diferencia B-vs-C es física/estructural y mucho mayor que la sensibilidad entre versiones fixed.


## Análisis exhaustivo OF14: vorticidad, topología de flujo, transporte de energía y acoplamiento

Se ejecutaron analizadores reproducibles sobre las 10 corridas controladas:

- `analysis_tools/physics_diagnostics_analysis.py`
- `analysis_tools/coupling_analysis.py`

Resúmenes permanentes:

- `analysis_results/physics_diagnostics/physics_diagnostics_summary.md`
- `analysis_results/coupling/coupling_summary.md`

### Energía

Los casos fixed B3/B4/B5/B7 son energéticamente casi indistinguibles entre sí. Lo mismo ocurre con C3/C4/C5/C7.

En los casos fixed, aproximadamente 94.8% del transporte difusivo de energía por las fronteras evaluadas ocurre a través de `metal_to_mold`; ~5.2% corresponde a `metalTop`. Por tanto, la extracción energética difusiva está dominada por la interfaz metal-molde.

Familia C fixed:
- energía advectiva integrada de frontera ≈ +6.8 J;
- energía difusiva ≈ 7057.8 J;
- participación advectiva por magnitud ≈ 0.1%.

Familia B fixed:
- energía advectiva integrada ≈ -970 J;
- energía difusiva ≈ 7100 J;
- participación advectiva por magnitud ≈ 12%.

La contribución advectiva B proviene de `metalTop`; `metal_to_mold` tiene advección prácticamente nula. Debido a que `metalTop` combina `U: slip` y `p_rgh: totalPressure`, este flujo advectivo B debe tratarse como un asunto de consistencia de flujo de masa en la frontera antes de interpretarlo como pérdida física de calor por convección.

### Vorticidad y flowType

En OpenFOAM Foundation v14:
- +1 = flujo rotacional;
- 0 = shear paralelo;
- -1 = deformación/pure shear.

Los porcentajes calculados son fracciones de puntos muestreados en líneas, no fracciones volumétricas.

B fixed:
- y=20 mm: RMS típico de omega_z ≈ 7.34 1/s, pero solo ~10% de puntos clasificados como rotacionales;
- y=30 mm: RMS ≈ 5.82 1/s y ~45% de puntos rotacionales;
- línea vertical central: vorticidad mucho menor.

C fixed:
- y=20 mm: RMS ≈ 3.52 1/s, ~40% rotacional y ~37% de la intensidad muestreada asociada a clasificación rotacional;
- y=30 mm: ~12.5% rotacional;
- línea vertical central: vorticidad casi nula.

Esto confirma una topología de circulación distinta entre B y C.

B6 adaptive reorganiza fuertemente la circulación:
- y=30 mm: fracción rotacional ~45% -> ~20%;
- participación rotacional por intensidad ~12.9% -> ~2.5%;
- vorticidad en la línea vertical central prácticamente colapsa.

C6 conserva mucho mejor Uy que B6, pero no conserva exactamente las derivadas/topología:
- y=20 mm: fracción rotacional ~40% -> ~17.5%;
- participación rotacional por intensidad ~37.4% -> ~10.5%;
- RMS de vorticidad aumenta.

### Acoplamiento

Se definió:

`R_p_outer = residual inicial del primer solve de p_rgh en el último outer / residual inicial correspondiente en el primer outer`.

Menor valor implica mayor contracción típica a través del loop exterior; `R>1` no significa fallo del solver lineal.

Resultados principales fixed:

B:
- B3 median Rp=0.6104;
- B4=0.6084;
- B5=0.5976;
- B7=0.5989.

C:
- C3=0.8054;
- C4=0.8054;
- C5=0.7951;
- C7=0.8019.

B5/C5 solo mejoran modestamente la contracción mediana respecto a V3. V7 no aporta mejora adicional y en varios indicadores empeora.

El segundo energy corrector B4/C4 reduce drásticamente el residual de entalpía h:
- B3 Rh≈2.16e-3 -> B4≈1.92e-6;
- C3 Rh≈1.05e-3 -> C4≈3.10e-7.

Sin embargo, no mejora de forma relevante Re, los campos físicos, la vorticidad ni el balance energético. Por tanto, sobreconverge h sin beneficio físico observado en estas pruebas.

B6 presenta Rp mucho menor (~0.372), pero no puede considerarse mejor acoplado globalmente porque empeora continuidad, eleva Co y cambia radicalmente Uy/vorticidad.

Regla adoptada: un acoplamiento se considera preferible solo si reduce consistentemente residuales de coupling, mantiene residuales lineales y continuidad adecuados, respeta Co/timestep, preserva la solución física y evita costo innecesario.


## Auditoría de `metalTop`: inconsistencia entre pared impermeable y presión abierta

**[GIT-VERIFIED] [OPENFOAM-v14-SOURCE-VERIFIED] [INTERPRETATION]**

Se revisó la frontera `metalTop` después de detectar un `energyAdvectiveFlux` integrado de aproximadamente -970 J en los casos fixed de la familia B, mientras la familia C presenta ~+6.8 J.

### Geometría

En `system/blockMeshDict`, `metalTop` está declarado como:

```
metalTop
{
    type wall;
}
```

Por tanto, geométricamente es una pared.

### Velocidad

En todos los casos controlados revisados:

```
metalTop
{
    type slip;
}
```

En OpenFOAM Foundation v14, `slip` hereda la condición de simetría y proyecta fuera la componente normal del vector velocidad. Para una malla estática esto impone `U·n = 0`: deslizamiento tangencial permitido, penetración normal nula.

### Presión

Sin embargo, `p_rgh` usa:

```
metalTop
{
    type totalPressure;
    p0 uniform 1e5;
}
```

OpenFOAM v14 documenta `totalPressure` como una condición de presión de entrada/salida/entrainment. Está diseñada para fronteras donde el flujo puede entrar o salir, no para imponer el flujo nulo de una pared impermeable.

La condición `fixedFluxPressure`, en cambio, está diseñada precisamente para ajustar el gradiente de presión de modo que el flujo de la frontera coincida con el especificado por la condición de velocidad. Es la condición coherente con una pared/slip impermeable.

### Evidencia de flujo advectivo

OpenFOAM v14 calcula `energyAdvectiveFlux` mediante `calcPhihs`, usando:

`alphaRhoPhi` × entalpía sensible `hs`.

Por lo tanto, un `energyAdvectiveFlux` distinto de cero en `metalTop` implica que el flujo másico superficial utilizado por el solver (`alphaRhoPhi`) no es cero, aunque la condición `slip` sobre U imponga velocidad normal nula.

Esto demuestra una inconsistencia entre la condición cinemática de U y el flujo superficial resultante del acoplamiento de presión.

### Por qué B lo muestra mucho más que C

B utiliza:
- `heRhoThermo`
- EOS `icoTabulated`
- densidad dependiente de T
- `beta=0` en solidificationMeltingSource.

C utiliza:
- `heRhoThermo`
- EOS `rhoConst`
- `rho=6820 kg/m3`
- buoyancy explícita mediante `beta=1.13e-4`.

Ambos usan la misma `metalTop` y el mismo h=10 W/(m2 K), pero la formulación de flujo/densidad de B amplifica la inconsistencia de `alphaRhoPhi` en la frontera. Esto explica por qué B presenta ~-970 J de transporte advectivo de frontera mientras C queda cerca de cero, aunque todavía debe verificarse con un caso controlado.

### Implicación física

Si el modelo actual pretende representar la superficie superior del metal como una superficie libre fija, sin pérdida de masa y sin deformación de la interfaz, la combinación físicamente coherente es:

- U: `slip`
- p_rgh: `fixedFluxPressure`
- T: `externalWallHeatFluxTemperature`

Si se pretendiera una frontera realmente abierta con entrada/salida de metal, entonces `totalPressure` podría ser apropiada, pero `U: slip` no lo sería; debería usarse una condición de velocidad compatible con frontera de presión, p.ej. `pressureNormalInletOutletVelocity`/familia equivalente. Ese no es el modelo físico actualmente planteado.

### Consecuencia metodológica

La diferencia B-vs-C en Uy, vorticidad y transporte advectivo no debe atribuirse exclusivamente a la formulación de buoyancy hasta repetir una comparación controlada corrigiendo únicamente la presión en `metalTop`.

Prueba recomendada:
- clonar B5 y C5;
- cambiar solo `metalTop/p_rgh`: `totalPressure` -> `fixedFluxPressure`;
- mantener U=slip, T, malla, propiedades, PIMPLE y timestep idénticos;
- comparar top mass/energy advective flux, Uy, vorticity, phase fraction, continuity y energía.

No se modificaron los casos históricos durante esta auditoría.


## V8 adaptive + 4 outer correctors — resultado definitivo

Se ejecutó una comparación completa de B8/C8 contra V6 adaptive y V5 fixed, alineando todos los perfiles por tiempo físico mediante interpolación temporal. Se analizaron Uy, T, alphaL, vorticidad, flowType, aceleración Darcy, aceleración asociada a p_rgh, coupling, continuidad, Courant y costo.

Resumen permanente:
- `analysis_results/v8_comprehensive/summary.md`

### Familia B

B8 es prácticamente indistinguible de B6:
- Uy mediano NRMSE: 0.04% (y20), 0.13% (y30), 0.17% (vertical);
- T RMSE final ~0.004–0.005 K;
- alphaL prácticamente idéntico;
- vorticidad horizontal <0.2% de diferencia;
- flowType sin desacuerdo de clase;
- Darcy y p_rgh acceleration <~0.1%;
- posiciones del frente de fase indistinguibles.

Sin embargo B8 sigue muy lejos de B5:
- Uy final NRMSE: 50.2% (y20), 80.5% (y30), 99.2% (vertical);
- flowType disagreement: 40% en y20 y 85% en y30;
- Darcy acceleration: 42–71%;
- p_rgh acceleration: 20–50%;
- ancho mushy vertical: B5 16.916 mm vs B8 18.493 mm (+9.3%).

Acoplamiento/costo:
- B6 median Rp=0.3721, clock=119 s;
- B8 median Rp=0.3882, clock=220 s;
- continuidad prácticamente igual (~2.45e-4);
- Co prácticamente igual (~0.29).

Conclusión B: añadir el cuarto outer no recupera la solución fixed y casi duplica el costo. El problema de V6 no es falta de root-level outer PIMPLE coupling.

### Familia C

C8 también es prácticamente idéntico a C6:
- Uy mediano NRMSE ~0.01–0.03%;
- T RMSE ~0.003–0.004 K;
- alphaL ~idéntico;
- vorticidad horizontal <=0.08%;
- flowType sin desacuerdo;
- Darcy <=0.06%;
- p_rgh acceleration <=0.20%.

C8 sigue conservando las mismas diferencias adaptive-vs-fixed de C6:
- Uy aún cercano a C5 (~1.7–4.8%);
- Darcy ~10–16%;
- p_rgh acceleration vertical ~56%;
- ancho mushy vertical C5 17.679 mm vs C8 19.622 mm (+11.0%).

Acoplamiento/costo:
- C6 median Rp=0.7900, clock=65 s;
- C8 median Rp=0.7765, clock=121 s;
- Rp>1 mejora modestamente 6.25% -> 5.10%;
- continuidad y Co prácticamente iguales.

Conclusión C: el cuarto outer mejora modestamente la métrica de pressure coupling, pero no cambia la solución física y casi duplica el costo.

### Decisión

V8 es un caso de rendimientos decrecientes y no se recomienda como configuración de producción. La diferencia V5↔V6/V8 proviene de la trayectoria de timestep adaptativo/discretización temporal, no de un número insuficiente de outer correctors.

Se mantiene V5 fixed como referencia física. V6 queda, en todo caso, como estudio explícito de trade-off velocidad/precisión. V8 se conserva solo como evidencia de independencia respecto al número de outer correctors.


## Auditoría de jerarquía PIMPLE en foamMultiRun (OpenFOAM Foundation v14)

**[SOURCE-VERIFIED] [LOG-VERIFIED]**

Se auditó qué `fvSolution` controla realmente cada nivel del algoritmo en los casos multi-región ejecutados con `foamMultiRun`.

### Arquitectura real de OF14

`foamMultiRun` crea:

```
pimpleMultiRegionControl pimple(runTime, solvers);
```

y ejecuta el loop exterior mediante:

```
while (pimple.loop())
```

El objeto `pimpleMultiRegionControl` hereda de `multiRegionSolutionControl`, cuyo `dict()` lee el subdiccionario `PIMPLE` del `system/fvSolution` raíz. Su `pimpleLoop::read()` toma de allí `nOuterCorrectors`.

Por lo tanto:

- `system/fvSolution/PIMPLE/nOuterCorrectors` = número efectivo de **outer correctors multi-región**.
- `system/fvSolution/PIMPLE/nEnergyCorrectors` = número efectivo de **energy correctors globales**.

Cada solver regional dispone además de un `pimpleNoLoopControl` construido sobre el `fvSolution` de su propia malla/región. En el metal:

- `system/metal/fvSolution/PIMPLE/nCorrectors` = número efectivo de correctores PISO de presión por cada outer global.
- `system/metal/fvSolution/PIMPLE/nNonOrthogonalCorrectors` = correctores no ortogonales efectivos.
- `momentumPredictor`, `pRefPoint/pRefCell`, `pRefValue` y controles regionales similares también se leen del diccionario regional.
- Los bloques `solvers` y sus tolerancias son regionales.

El `nOuterCorrectors 1` presente en `system/metal/fvSolution` **no controla el outer loop de foamMultiRun**. `pimpleNoLoopControl` no posee un loop exterior propio; cuando está conectado al `pimpleMultiRegionControl`, la lectura del outer loop se delega al objeto multi-región.

Asimismo, las entradas duplicadas `nCorrectors` y `nNonOrthogonalCorrectors` del `system/fvSolution` raíz no son las que gobiernan los correctores internos del metal. Para el metal mandan los valores del archivo regional.

### Verificación con logs reales

Los logs confirman exactamente la estructura:

- B3: root outer=2, metal nCorrectors=2 -> **4** series `p_rgh_0...p_rgh_3`.
- B5: root outer=3, metal nCorrectors=2 -> **6** series `p_rgh_0...p_rgh_5`.
- B7: root outer=4, metal nCorrectors=2 -> **8** series `p_rgh_0...p_rgh_7`.
- B8: root outer=4, metal nCorrectors=2 -> **8** series.

La energía también confirma el control global:

- B3: outer=2 × energyCorrectors=1 -> **2** series de h/e.
- B4: outer=2 × energyCorrectors=2 -> **4** series de h/e.
- B5: outer=3 × energyCorrectors=1 -> **3** series de h/e.

### Corrección metodológica

La nomenclatura V3/V5/V7 usada hasta ahora para 2/3/4 outer correctors sigue siendo **correcta**, porque esos valores estaban modificándose en el archivo raíz, que es precisamente el que controla el loop multi-región.

Sin embargo, para describir la configuración completa debe distinguirse:

- **outer correctors multi-región**: root `system/fvSolution`;
- **pressure/PISO correctors del metal**: `system/metal/fvSolution`;
- **non-orthogonal correctors del metal**: regional;
- **energy correctors**: root.

En los casos actuales el metal usa efectivamente:
- `nCorrectors = 2`;
- `nNonOrthogonalCorrectors = 0`;
- `momentumPredictor = no`.

Por ello, la entrada root `nNonOrthogonalCorrectors = 1` NO debe reportarse como valor efectivo del metal.

### Recomendación de mantenimiento

No se modificaron casos históricos. En futuros casos conviene eliminar o comentar del `system/fvSolution` raíz las entradas `nCorrectors` y `nNonOrthogonalCorrectors` duplicadas para evitar ambigüedad, dejando en root solo los controles multi-región pertinentes y en `system/metal/fvSolution` los controles internos del solver regional.


## B9 topFixedFlux — incompatibilidad de masa en dominio cerrado

**[RUN-VERIFIED] [SOURCE-VERIFIED]**

B9 arrancó correctamente con `fixedFluxPressure` y la referencia interna de presión, pero abortó cerca de t=0.016 s cuando T alcanzó 1782.04 K, por encima del límite de la tabla `rho(T)` de `icoTabulated` (1773.15 K). C9 sí completó.

En OF14, `icoTabulated` usa `rho=rho(T)` y `psi=d(rho)/d(p)=0`. El solver `fluid` impone continuidad mediante `ddt(rho)+div(phi)=source(rho)`.

En un dominio rígido, cerrado e impermeable, sin fuente de masa, la masa total debe permanecer constante. Sin embargo, al enfriarse el metal, la tabla de B exige un aumento de densidad. Como la presión no puede modificar rho (`psi=0`) y la tapa ya no permite flujo de masa, el modelo no dispone de un mecanismo para acomodar la contracción térmica.

Esto explica el fuerte crecimiento temprano del error acumulado de continuidad y el posterior fallo por temperatura fuera de rango.

Los casos B históricos con `metalTop: totalPressure` permitían intercambio de masa a través del top. El término advectivo de energía ~-970 J observado allí debe interpretarse como evidencia de ese intercambio, no como una superficie superior impermeable.

Para la geometría actual de volumen fijo sin superficie libre móvil ni shrinkage, la formulación C (`rhoConst` + buoyancy mediante beta) es internamente consistente. La formulación B requeriría física adicional de cambio de volumen, superficie libre, alimentación o shrinkage. No se recomienda extender artificialmente la tabla de rho para forzar B9 a continuar.


## Corrección posterior: B9 completó 10 s con la tabla rho(T) extendida

**[RUN-VERIFIED BY USER OUTPUT] [INTERPRETATION UPDATE]**

La interpretación anterior de B9 como un caso incapaz de continuar en dominio cerrado fue demasiado fuerte. Tras extender diagnósticamente la tabla rho(T) más allá de 1773.15 K, B9 completó los 10 s.

Resultados finales reportados:
- metalTopPhiSum = 0;
- metalTop energyAdvectiveFlux = 0;
- metal_to_mold energyAdvectiveFlux ~ 7.3e-15 W;
- metalTop heatFlux = 36.603 W;
- metal_to_mold heatFlux = 342.301 W;
- total boundary heatFlux = 378.904 W;
- max Co ~ 0.0301;
- cumulative continuity = -0.0460268.

La conclusión correcta es ahora:
1. fixedFluxPressure + slip sí elimina el flujo de masa/energía advectiva por metalTop;
2. B9 puede evolucionar hasta 10 s si la tabla rho(T) cubre el overshoot térmico temprano;
3. la métrica cumulative continuity queda mucho peor que en B5, por lo que sigue existiendo una tensión importante entre la densidad termodinámica rho(T) y la continuidad;
4. el valor cumulative no debe interpretarse como una pérdida final de 4.6% de masa: en OF14 es la suma acumulada de la discrepancia normalizada entre rho y thermo.rho() durante las correcciones;
5. el fallo original a 1782.04 K debe reinterpretarse como salida del rango tabulado durante un overshoot temprano, no como prueba suficiente de runaway térmico irreversible.

Se requiere comparar el transitorio completo B9 vs B5 una vez subidos los resultados.


## V9 metalTop fixedFlux — resultado comparativo final

**[RUN-VERIFIED] [ANALYSIS-VERIFIED]**

Se compararon B9 vs B5 y C9 vs C5 con perfiles completos 0–10 s, energía de frontera, phi en metalTop, coupling, continuidad, Uy, T, alphaL, vorticidad, flowType, Darcy y p_rgh acceleration.

Resumen reproducible:
- `analysis_results/v9_top_fixedflux/summary.md`
- analizador: `analysis_tools/v9_top_fixedflux_analysis.py`

Resultado principal:
- `fixedFluxPressure + slip` hace `metalTop` impermeable: en B9 max |sum(phi)| = 2.54e-21 y la energía advectiva integrada de top ~0; en C9 ambos son exactamente 0 dentro de la precisión almacenada.
- C9 permanece físicamente muy cercano a C5: Uy mediano ~1.1–2.9% en horizontales y 1.76% vertical; T final RMSE <=0.15 K; mushy width cambia +1.4%.
- B9 cambia fuertemente respecto a B5: Uy mediano ~56% (y20), 95% (y30), 112% (vertical); mushy width +15%; center-T RMSE 14.6 K.
- B5 tenía -970.358 J de energía advectiva integrada por top; B9 ~0. C5 tenía solo +6.841 J; C9 0.
- B9 mejora enormemente la contracción residual de presión (median Rp~0.0021), pero la discrepancia transient rho-vs-thermo.rho acumulada crece a -0.046; esto no debe interpretarse como 4.6% de pérdida final de masa.
- C9 mejora coupling y continuidad sin cambiar materialmente la solución física.

Conclusión: el antiguo `totalPressure` tenía impacto físico despreciable en C pero fuerte en B. Las diferencias históricas B-vs-C no son una comparación limpia de formulaciones de buoyancy. Para el modelo Quick-Cup de volumen fijo actual, C9 es la referencia más limpia para continuar validación física.

Caveat: B9 necesitó una extensión lineal diagnóstica de rho(T) por encima de 1773.15 K; por ello B9-vs-B5 dejó de ser una prueba estrictamente de una sola modificación.


## V9 — causalidad de inversiones de Uy

**[ANALYSIS-VERIFIED]**

Se correlacionaron todas las inversiones resueltas de Uy de B9 y C9 con alphaL, grad(rho), vorticidad, flowType, aceleración Darcy y aceleración de p_rgh.

Corrección metodológica importante: B9 usa beta=0 en solidificationMeltingSource, por lo que su flotación no puede evaluarse con phaseChangeBuoyancyAcceleration. Para B9 se reconstruyó el término de densidad variable del solver como a_rho=-(gh/rho)grad(rho), con hRef=0 y gh=-9.81*y.

Resultado:
- B9 y30 conserva principalmente el par de inversiones simétricas clásico y predominantemente líquido. En 72% de todas sus inversiones resueltas, a_rho es la mayor de las tres escalas muestreadas (densidad, presión, Darcy); Darcy nunca es la mayor. Esto respalda un origen físico de convección por densidad variable.
- B9 y20 desarrolla estructura secundaria transitoria. A 5 s aparecen cuatro inversiones resueltas aun en líquido; a 10 s las cuatro están en alphaL~0.94. Las inversiones externas a 10 s tienen fuerte vorticidad y gran Darcy; las internas muestran casi cancelación a_rho,y ~ -0.073 y a_p,y ~ +0.0735 m/s2, con magnitudes Darcy comparables. La estructura es simétrica y sistemática, no consistente con simple ruido aleatorio.
- B9 vertical presenta inversiones de Uy, pero la vorticidad de la línea central es casi nula. No deben llamarse vórtices/celdas adicionales sin campos 2-D.
- C9 mantiene una estructura más simple de dos celdas. Sus fronteras de celda tardías también están fuertemente condicionadas por Darcy conforme avanza la zona de cambio de fase.
- Se corrigió la lectura previa de B9 y30: varias inversiones muy pequeñas detectadas sin umbral eran cruces cerca de Uy=0 y no deben contarse como celdas dinámicamente resueltas.

Limitación: los resultados versionados contienen perfiles lineales, no los campos volumétricos completos finales; por ello no puede demostrarse geométricamente el cierre de cada celda mediante streamlines desde el repositorio actual.

Resumen reproducible: analysis_results/v9_flow_causality/summary.md
Analizador: analysis_tools/v9_flow_causality_analysis.py


---

## 2026-09-28 — Regla permanente de auditoría de residuos de presión

### AUD-PRES — Evolución de p_rgh y p_rghFinalRes obligatoria en todos los casos B/C
**[GIT-VERIFIED]**

Se establece como regla permanente del proyecto que todo caso B/C con resultados de `foamLog` debe revisarse mediante la evolución completa de los residuos de presión, no únicamente mediante un residual final o una métrica agregada.

La auditoría obligatoria incluye:

- residual inicial `p_rgh` de cada solve;
- residual final `p_rghFinalRes` de cada solve;
- evolución contra tiempo físico;
- evolución contra índice de timestep;
- cociente `p_rghFinal/p_rghInitial` para evaluar la contracción del solver lineal;
- `R_p_outer` para evaluar la contracción del acoplamiento presión–velocidad entre outer correctors;
- frecuencia de `R_p_outer > 1`;
- continuidad, Courant, costo computacional y preservación de la solución física.

Motivación: evaluar explícitamente si el uso de pasos de tiempo muy pequeños produce mejora real del acoplamiento o únicamente aumenta el número de pasos mientras los residuos permanecen en una meseta.

Se añadió `analysis_tools/pressure_stagnation_analysis.py`, que descubre automáticamente todos los casos B/C que contienen `logs/` y genera tablas y, cuando matplotlib está disponible, gráficas semilogarítmicas de `p_rgh` y `p_rghFinalRes` contra tiempo físico e índice de timestep.

El indicador automático de meseta es deliberadamente conservador y se usa solo como cribado: un cambio menor de 0.25 décadas log10 en la mediana del residual durante el 25 % final de las muestras se marca como `plateau_candidate`. Esta bandera no sustituye la inspección de magnitudes, continuidad ni campos físicos.

**Estado:** ✅ regla incorporada al flujo de revisión.


---

## 2026-09-28 — Regla permanente de impermeabilidad / advección

### AUD-TOP-FLUX — La alerta que motivó V9 pasa a ser obligatoria
**[GIT-VERIFIED]**

La revisión de `metalTop` se formaliza como requisito permanente para todos los casos B/C.

La señal histórica que motivó V9 fue la presencia de transporte advectivo de energía a través de una tapa destinada a ser impermeable:

- B5: energía advectiva integrada por `metalTop` ≈ -970.358 J;
- C5: ≈ +6.841 J.

Después de cambiar `metalTop/p_rgh` a `fixedFluxPressure`:

- B9: energía advectiva integrada ≈ -5.0×10^-16 J y max |sum(phi)| ≈ 2.54×10^-21;
- C9: energía advectiva integrada = 0 J y sum(phi)=0 en los diagnósticos almacenados.

OpenFOAM Foundation v14 calcula el término advectivo mediante `fvc::flux(alphaRhoPhi, hs)`; por tanto, el diagnóstico representa transporte de entalpía sensible asociado al flujo másico del solver, no conducción/radiación.

Se establece que `U=slip` no basta para declarar una frontera impermeable. Todo caso futuro debe comprobar tanto `sum(phi)` como `energyAdvectiveFlux` en `metalTop`.

Se añadió `analysis_tools/boundary_flux_audit.py` y se incorporó `metalTopPhiSum` a B10/C10 para futuras ejecuciones. La corrida local que ya estaba en marcha antes de esta modificación no adquiere retrospectivamente ese function object; en ella la alerta advectiva sigue disponible mediante `metalTopEnergyPower`.

**Estado:** ✅ alerta V9 convertida en regla permanente.


---

## 2026-09-29 — Trazabilidad V10–V13 y auditoría de la condición de presión en `metalTop`

### AUD-V10-V11 — Linaje controlado con air gap OF14
**[GIT-VERIFIED] [CONFIG-VERIFIED]**

La bitácora global no había incorporado todavía los casos V10 y V11 aunque ya estaban versionados. Se corrige aquí ese hueco documental.

Casos canónicos:

- `B10_airGapOF14`: descendiente de B5/V5 con el air gap corregido para OpenFOAM Foundation v14 y tabla B de `rho(T)` extendida.
- `C10_airGapOF14`: descendiente de C5/V5 con el mismo air gap OF14.
- `B11_topFixedFlux_airGapOF14`: descendiente de B9/V9; combina `metalTop/p_rgh=fixedFluxPressure` con el air gap OF14 y la misma tabla B extendida.
- `C11_topFixedFlux_airGapOF14`: descendiente de C9/V9; combina `fixedFluxPressure` con el air gap OF14.

Air gap común:
- espesor: `2e-4 m`;
- conductividad: `1e-1 W/(m K)`;
- conductancia equivalente: `k/delta = 500 W/(m2 K)`.

Comparaciones primarias:
1. B10 vs B11: efecto de la BC superior con air gap y tabla `rho(T)` igualados;
2. C10 vs C11: mismo efecto en familia C;
3. B10 vs C10 y B11 vs C11: contraste B/C solo después de confirmar que las demás condiciones permanezcan emparejadas.

**Estado de evidencia:** la configuración está verificada en Git. No etiquetar V10/V11 como `RUN-VERIFIED` o `ANALYSIS-VERIFIED` hasta que los resultados correspondientes estén incorporados y auditados.

---

### AUD-V12-V13 — Canonicalización de las pruebas de presión
**[GIT-VERIFIED] [SOURCE-VERIFIED] [DECISION]**

V12 y V13 descienden directamente de V11. La regla de cambio controlado quedó verificada por SHA: frente a V11, los casos canónicos solo cambian físicamente `0/metal/p_rgh`; las diferencias adicionales son únicamente `CASE_NOTES.md` y `CASE_VARIANT.md`.

Casos canónicos:

- `B12_topFixedValue_airGapOF14`
- `C12_topFixedValue_airGapOF14`
- `B13_prghPressure_airGapOF14`
- `C13_prghPressure_airGapOF14`

Los primeros directorios duplicados/provisionales de V12/V13 fueron eliminados del árbol actual del repositorio para mantener una estructura inequívoca: una sola configuración de caso por versión y familia. La trazabilidad del intento inicial permanece en el historial Git, pero no como casos activos. El único runner V12/V13 vigente es `run_v12_v13_tests.sh`.

---

### AUD-PREF — Dos referencias de presión distintas que no deben confundirse
**[SOURCE-VERIFIED] [GIT-VERIFIED]**

OpenFOAM Foundation v14 define en la clase de buoyancy:

`p_rgh = p - rho*gh - pRef`

donde:
- `constant/metal/pRef` es un `uniformDimensionedScalarField` que forma parte de la definición de presión reducida;
- `hRef` es opcional y, si no existe el archivo, su valor por defecto es 0;
- `gh = (g·x) - ghRef`.

Esto es distinto de:
- `system/metal/fvSolution/PIMPLE/pRefPoint`
- `system/metal/fvSolution/PIMPLE/pRefValue`

que pertenecen al mecanismo `pressureReference` para fijar un nivel de presión en dominios que lo necesitan.

El código de `GeometricField::needReference()` establece que si alguna BC de presión `fixesValue()`, el campo no necesita una referencia interna adicional. Por tanto:

- V11, con `fixedFluxPressure` en `metalTop` y en la interfaz, necesita referencia interna y usa `pRefPoint/pRefValue`;
- V12 y V13 tienen en `metalTop` una BC derivada de `fixedValue`, por lo que `p_rgh.needReference()` pasa a falso y el anclaje `pRefPoint/pRefValue` deja de ser el mecanismo que fija el nivel del sistema;
- `constant/metal/pRef=1e5 Pa` sigue siendo físicamente activo en la reconstrucción `p = p_rgh + rho*gh + pRef`.

Esta distinción es obligatoria al explicar por qué `prghPressure` usa `p uniform 0` en V13.

Fuentes oficiales OF14:
- `src/finiteVolume/cfdTools/general/buoyancy/buoyancy.H`
- `src/finiteVolume/cfdTools/general/buoyancy/buoyancy.C`
- `src/finiteVolume/cfdTools/general/pressureReference/pressureReference.C`
- `src/finiteVolume/fields/GeometricFields/GeometricField/GeometricField.C`
- `applications/modules/isothermalFluid/correctBuoyantPressure.C`

---

### AUD-V12-CALC — Derivación exacta de los valores fixedValue de V12
**[SOURCE-VERIFIED] [GIT-VERIFIED] [CALC-VERIFIED]**

Datos del caso:
- `g=(0,-9.81,0) m/s2`;
- `hRef=0`;
- la superficie `metalTop` está en `y=0.040 m`;
- `constant/metal/pRef=1e5 Pa`;
- presión estática atmosférica objetivo: `p=1e5 Pa`.

Entonces:

`gh = -9.81*0.040 = -0.3924 m2/s2`

y, como `p-pRef=0` en la tapa:

`p_rgh = -rho*gh = rho*9.81*0.040`.

Familia B:
- `T0=1500 K`;
- interpolación lineal de la tabla `icoTabulated` entre 1473.15 K / 6820 kg/m3 y 1573.15 K / 6740 kg/m3:
- `rho_B(1500 K)=6798.52 kg/m3`;
- `p_rgh=6798.52*9.81*0.040=2667.739248 Pa`.

Familia C:
- `rho_C=6820 kg/m3`;
- `p_rgh=6820*9.81*0.040=2676.168 Pa`.

Por tanto los valores canónicos de V12 están respaldados directamente por la geometría, gravedad, EOS y definición de `p_rgh`; no son parámetros ajustados.

---

### AUD-V13-BC — Significado de `prghPressure p uniform 0`
**[SOURCE-VERIFIED] [DECISION]**

La implementación OF14 de `PrghPressureFvPatchScalarField` aplica:

`p_rgh = p_spec - rho*gh`

sobre el valor de presión estática suministrado por la BC. El solver reconstruye después:

`p = p_rgh + rho*gh + pRef`.

En este caso, con `constant/metal/pRef=1e5 Pa`, especificar:

`p uniform 0;`

produce una presión estática reconstruida de:

`p = 0 + pRef = 1e5 Pa`.

Por tanto, usar `p=1e5` dentro de `prghPressure` **duplicaría** el offset de referencia y conduciría a aproximadamente 2 bar reconstruidos en esta configuración.

El `value` de V13 (`2667.739248` Pa en B y `2676.168` Pa en C) es el valor inicial consistente; la BC lo recalcula durante la solución.

Fuente oficial OF14:
- `src/finiteVolume/fields/fvPatchFields/derived/PrghPressure/PrghPressureFvPatchScalarField.H/.C`
- `src/finiteVolume/fields/fvPatchFields/derived/pressure/pressureFvPatchScalarField.H/.C`.

---

### AUD-V12-V13-PHYS — Qué hipótesis física prueba realmente cada caso
**[SOURCE-VERIFIED] [METHODOLOGICAL DECISION]**

V11:
- `U=slip`;
- `p_rgh=fixedFluxPressure`.

La documentación oficial OF14 describe `fixedFluxPressure` como la BC que ajusta el gradiente de presión para que el flujo de frontera sea consistente con la BC de velocidad en presencia de fuerzas de cuerpo. Para una tapa rígida, fija e impermeable con `U=slip`, V11 es la combinación de referencia físicamente coherente. Esto ya fue confirmado empíricamente en V9 mediante `sum(phi)≈0` y advección de energía ≈0.

V12:
- mantiene `U=slip`;
- fija directamente `p_rgh` al valor atmosféricamente consistente del instante inicial.

En C, como `rho` es constante y la tapa es horizontal, ese valor permanece consistente con atmósfera. En B, al cambiar `rho(T)`, mantener `p_rgh` congelado implica que la presión estática reconstruida:

`p = pRef + p_rgh + rho*gh`

puede cambiar en el tiempo y espacialmente con `rho`. V12 es por tanto una prueba explícita de la propuesta de `fixedValue`, no una imposición de atmósfera estática constante durante todo el transitorio B.

V13:
- mantiene `U=slip`;
- prescribe presión estática atmosférica mediante `prghPressure`;
- permite que `p_rgh` se adapte a `rho` y a la altura.

En C12 vs C13, con `rhoConst` y una tapa horizontal fija, ambas BC deberían generar esencialmente el mismo valor de `p_rgh` en `metalTop` (salvo redondeo/implementación). Ese par funciona como control.

En B12 vs B13, la diferencia controlada es precisamente:
- V12: `p_rgh` permanece congelado;
- V13: la presión estática permanece atmosférica y `p_rgh` sigue a `rho(T)`.

**Advertencia metodológica:** ni `fixedValue` ni `prghPressure` deben declararse automáticamente equivalentes a una pared impermeable. Ambas fijan el valor de presión; la combinación con `U=slip` es una prueba deliberada y debe validarse con:
- `metalTopPhiSum`;
- `energyAdvectiveFlux`;
- continuidad;
- residuos de `p_rgh`;
- campos de U/T/alphaL.

La guía OF14 usa `fixedFluxPressure` en paredes y combina condiciones de presión atmosférica con condiciones de velocidad que permiten entrada/salida cuando se modela una frontera abierta. Por ello V12/V13 son diagnósticos controlados de BC y no sustituyen V11 como baseline impermeable sin evidencia de los resultados.

---

### AUD-V12-V13-STATUS — Corrida canónica completada
**[GIT-VERIFIED] [RUN-VERIFIED]**

El 29 de septiembre de 2026 se ejecutó localmente el runner canónico `cases_controlled_buoyancy/run_v12_v13_tests.sh` en OpenFOAM Foundation v14.

Resultado reportado por el runner:

- `B12_topFixedValue_airGapOF14`: PASS — `latest=10`, `End=YES`, `fatal=0`, `AllrunRC=0`.
- `C12_topFixedValue_airGapOF14`: PASS — `latest=10`, `End=YES`, `fatal=0`, `AllrunRC=0`.
- `B13_prghPressure_airGapOF14`: PASS — `latest=10`, `End=YES`, `fatal=0`, `AllrunRC=0`.
- `C13_prghPressure_airGapOF14`: PASS — `latest=10`, `End=YES`, `fatal=0`, `AllrunRC=0`.

Esto verifica que las cuatro configuraciones canónicas completan 10 s sin errores fatales de ejecución.

**Importante:** `RUN-VERIFIED` no equivale a `ANALYSIS-VERIFIED`. Antes de aceptar físicamente V12 o V13 deben auditarse, como mínimo:

- `metalTopPhiSum`;
- energía advectiva integrada en `metalTop`;
- residuos iniciales/finales de `p_rgh`;
- contracción del acoplamiento exterior;
- continuidad;
- Courant;
- U, T y fracción líquida.

El estado `ANALYSIS-VERIFIED` permanece pendiente.



---

## 2026-09-29 — Análisis V12/V13 de presión en `metalTop`

### AUD-V12-V13-RESULTS — Fixed reduced pressure vs atmospheric static pressure
**[RUN-VERIFIED] [ANALYSIS-VERIFIED]**

Resumen reproducible:
- `analysis_results/v12_v13_pressure_bc/summary.md`
- `analysis_results/v12_v13_pressure_bc/metrics.csv`

Hallazgos principales:

1. **C12 y C13 son indistinguibles dentro de la precisión almacenada.**
   Con `rhoConst` y tapa horizontal fija, `fixedValue p_rgh` y `prghPressure` producen esencialmente la misma solución. Su `sum(phi)` neto es ~0, pero la energía advectiva integrada (+6.29 J) no es cero: esto indica intercambio local de flujo que se cancela en masa neta pero no en entalpía. Por tanto tampoco deben llamarse estrictamente impermeables.

2. **B12 y B13 no son impermeables.**
   - B12: max `|sum(phi)|=9.739e-5 kg/s`; `∫phi dt=-5.642e-4 kg`.
   - B13: max `|sum(phi)|=9.771e-5 kg/s`; `∫phi dt=-5.799e-4 kg`.
   Eso equivale a aproximadamente 0.519% y 0.533% de la masa inicial B, respectivamente, en 10 s.

3. **La fuga lleva entalpía sensible por `metalTop`.**
   - B12: `∫P_adv,top dt=-660.77 J`; calor no advectivo top `+369.28 J`.
   - B13: `∫P_adv,top dt=-559.53 J`; calor no advectivo top `+374.77 J`.
   Durante el rebound, el flujo advectivo negativo supera al heatFlux positivo, por lo que el balance neto del top introduce energía al dominio.

4. **B13 presenta remelting local inducido por el transporte de frontera.**
   - T: 1471.28 K @ 5.167 s → 1475.28 K @ 7.237 s (`+4.00 K`).
   - alphaL: 0.993108 @ 5.231 s → 1.0 @ 6.222 s.
   El evento coincide con flujo/entalpía entrante por el top. No debe etiquetarse como recalescencia metalúrgica por nucleación.

5. **B12 también presenta rebound térmico**, 1478.93 K → 1483.27 K (`+4.34 K`), pero permanece por encima de Tliq y alphaL=1; no hay remelting.

6. **La extracción térmica no advectiva permanece casi igual** entre los casos (~4.06 kJ sobre todas las fronteras). La diferencia B12/B13 no proviene de h, emissivity o air gap; proviene del acoplamiento presión-flujo en `metalTop`.

7. **Los cuatro casos convergen numéricamente en presión.**
   `R_p_outer>1` ocurre en 0% de los 10 000 timesteps. Por tanto la fuga no es evidencia de divergencia; es una consecuencia de la condición de frontera resuelta.

8. **Interpretación de continuidad en B.**
   B12/B13 muestran cumulative continuity ~1e-6, mucho menor que el ~-0.046 histórico de B9 impermeable. La razón física es que B12/B13 permiten entrada de masa para acomodar el aumento de `rho(T)` en volumen geométrico fijo. Esa mejor continuidad no significa mayor fidelidad para una tapa impermeable.

### Decisión metodológica

Para el modelo actual de Quick-Cup con geometría fija y `metalTop` cinemáticamente impermeable:

- V12/V13 se conservan como pruebas diagnósticas;
- no se adoptan como baseline impermeable;
- `fixedFluxPressure + slip` sigue siendo la formulación coherente de tapa/pared impermeable;
- la familia C es internamente más compatible con el volumen fijo;
- conservar B con contracción térmica real requeriría modelar de forma coherente shrinkage, cambio de volumen, alimentación o superficie libre móvil.



---

## 2026-09-29 — Protocolo operativo MAZAPÁN

## MAZAPÁN — cierre completo de una corrida OpenFOAM

**MAZAPÁN** es el protocolo completo de cierre científico y documental de una o varias corridas del proyecto Quick-Cup. **No termina en el `git push`.**

Cuando Michel diga **“MAZAPÁN”** o **“haz MAZAPÁN”**, se debe ejecutar este flujo completo:

1. **Confirmar la corrida local**
   - comprobar `latestTime`;
   - comprobar `End`;
   - buscar `FOAM FATAL`, segmentation fault, floating point exception o procesos killed;
   - registrar el código de retorno cuando exista un runner.

2. **Sincronizar las carpetas completas de los casos**
   - añadir cada carpeta completa con `git add cases_controlled_buoyancy/<CASO>`;
   - dejar que `.gitignore` filtre automáticamente tiempos calculados, mallas generadas, archivos ParaView, imágenes, ZIP y demás outputs no versionables;
   - no enumerar manualmente `logs/`, `postProcessing/`, etc.;
   - no usar `git add -f` salvo una excepción explícita.

3. **Preservar primero los resultados locales**
   - commit local de resultados;
   - `git pull --rebase origin main`;
   - `git push origin main`;
   - nunca usar `force push` para resolver un remoto adelantado con resultados locales válidos.

4. **Verificar lo que realmente quedó en GitHub**
   - confirmar el commit;
   - confirmar que `logs/`, `postProcessing/` y demás evidencia científica necesaria sí quedaron versionados;
   - comprobar que outputs pesados/temporales no quedaron trackeados accidentalmente.

5. **Limpiar tracking accidental**
   - recordar que `.gitignore` no deja de rastrear archivos que ya estaban versionados;
   - si un tiempo calculado u otro output ignorado sigue trackeado, retirarlo del árbol/índice de Git **sin confundirlo con borrar el resultado local**;
   - verificar después que la ruta ya no esté trackeada.

6. **Auditar científicamente los resultados**
   Como mínimo, cuando existan:
   - flujo de masa en fronteras relevantes, incluido `metalTopPhiSum`;
   - energía advectiva y heat/energy flux;
   - residuos iniciales/finales de `p_rgh`;
   - contracción entre outer correctors;
   - continuidad;
   - Courant;
   - T, U, rho y fracción líquida;
   - balances y magnitudes integradas;
   - comparación contra el caso padre/baseline y contra la familia equivalente;
   - cualquier diagnóstico específico de la hipótesis probada.

7. **Separar estados de evidencia**
   - `RUN-VERIFIED`: terminó limpiamente;
   - `ANALYSIS-VERIFIED`: los resultados fueron auditados;
   - una corrida que da PASS **no** se declara físicamente válida solo por haber terminado.

8. **Crear o actualizar el registro de análisis**
   - guardar resumen reproducible en `analysis_results/` cuando el análisis lo amerite;
   - guardar métricas/tablas derivadas que permitan reconstruir la conclusión.

9. **Actualizar la bitácora global**
   - `PROJECT_AUDIT_LOG_ES.md`;
   - registrar qué se corrió, resultados, interpretación, decisión y nueva pregunta técnica.

10. **Actualizar las notas de CADA caso afectado**
    - `CASE_NOTES.md`: estado actual, resultados medidos, interpretación, advertencias y decisión;
    - `CASE_VARIANT.md`: propósito de la variante y conclusión posterior a la corrida;
    - no dejar una nota en modo “qué pretendemos probar” después de que el caso ya fue ejecutado y analizado.

11. **Actualizar documentación de comparación**
    Según lo que cambie:
    - README de la familia/prueba;
    - `VALIDATION_MATRIX_ES.md`;
    - documentación de baseline/casos canónicos.

12. **Actualizar las guías de aprendizaje**
    Si el resultado cambia o fortalece cómo entendemos el modelo:
    - `CASE_GUIDE_ES.md`;
    - `CASE_GUIDE_INTERACTIVE_ES.html`;
    - incorporar qué opción se probó, qué ocurrió realmente, qué opción queda como baseline y cómo defender la decisión oralmente.

13. **Actualizar el manual de comandos cuando aparezca un procedimiento reutilizable**
    - `OPENFOAM_COMMAND_MANUAL_ES.md`;
    - documentar comandos nuevos o corregidos que deban repetirse en futuras corridas.

14. **Reevaluar explícitamente la baseline**
    - decidir si la evidencia mantiene, reemplaza o limita la baseline vigente;
    - si la baseline cambia o queda reafirmada, reflejarlo en las notas de la baseline y de las variantes comparadas.

15. **Cerrar con verificación de consistencia documental**
    - ninguna guía debe llamar “pendiente” a una corrida ya analizada;
    - ninguna nota debe llamar “baseline” a una variante descartada;
    - los números de las notas deben coincidir con `analysis_results/`;
    - Git debe quedar sin outputs generados accidentalmente trackeados.

### Flujo Git de MAZAPÁN

```bash
cd ~/OpenFOAM/QuickCup_Solidification

git add \
cases_controlled_buoyancy/<CASO_1> \
cases_controlled_buoyancy/<CASO_2>

git commit -m "results: add simulation outputs"
git pull --rebase origin main
git push origin main
```

### Regla corta

> **MAZAPÁN = sincronizar + auditar + decidir + documentar + limpiar + verificar consistencia.**

El `git push` es solo la mitad del flujo.



---

## 2026-09-29 — Cierre científico V10–V13

### AUD-V10-V13-CLOSURE — V11 verificada directamente y campaña de BC de presión cerrada
**[RUN-VERIFIED] [ANALYSIS-VERIFIED] [DECISION]**

Los resultados locales de V10/V11 fueron incorporados al repositorio en el commit de resultados y se auditaron directamente junto con V12/V13.

Resumen reproducible:
- `analysis_results/v10_v13_closure/summary.md`
- `analysis_results/v10_v13_closure/case_metrics.csv`
- `analysis_results/v10_v13_closure/pair_metrics.csv`
- `analysis_results/v10_v13_closure/profile_metrics.csv`

#### Verificación directa de V11

B11:
- max `|sum(phi_top)| = 1.694066e-21 kg/s`;
- `∫phi_top dt = -1.27055e-22 kg`;
- `∫P_adv,top dt ≈ -1.22e-16 J`;
- T central final = 1470.07 K;
- alphaL central final = 0.988421;
- alphaL media final = 0.9606902;
- max Co = 0.0673434;
- mediana `R_p_outer = 0.001981`;
- `R_p_outer>1 = 0%`;
- cumulative continuity final = -0.0310209.

C11:
- `sum(phi_top)=0`;
- `∫P_adv,top dt=0 J`;
- T central final = 1464.19 K;
- alphaL central final = 0.964815;
- alphaL media final = 0.9620593;
- max Co = 0.0650864;
- mediana `R_p_outer = 0.0005954`;
- `R_p_outer>1 = 0%`;
- cumulative continuity final = 4.45e-13.

Con esto, la impermeabilidad de `fixedFluxPressure + slip` queda demostrada en los casos V11 mismos y ya no depende únicamente de la evidencia histórica V9.

#### B10 → B11

Cerrar la tapa elimina una contribución advectiva integrada de aproximadamente -629.63 J sin cambiar materialmente la extracción térmica metal→molde (3686.64 J vs 3687.23 J).

Efecto sobre la solución:
- T central RMSE = 8.53 K;
- max |ΔT| = 16.16 K;
- final ΔT = -2.46 K;
- Uy NRMSE final = 44.7% en y=20 mm, 217.5% en y=30 mm y 257.9% en x=20 mm;
- flowType class disagreement = 62.5%, 27.5% y 10%.

**Interpretación:** la antigua condición de presión superior participaba materialmente en la solución B. B10 no es una referencia limpia de buoyancy de densidad variable.

#### C10 → C11

Cerrar la tapa elimina solo +2.976 J de advección integrada.

Efecto sobre la solución:
- T central RMSE = 0.164 K;
- max |ΔT| = 0.43 K;
- final ΔT = -0.08 K;
- Uy NRMSE final = 0.52%, 1.70% y 0.44% en los tres perfiles canónicos.

**Interpretación:** C es robusta a la corrección porque el transporte superior previo ya era pequeño.

#### V11 frente a V12/V13

B12 se separa fuertemente de B11:
- max `|sum(phi)| = 9.739e-5 kg/s`;
- `Eadv,top=-660.77 J`;
- T RMSE vs B11 = 5.39 K;
- Uy NRMSE y=30 mm = 182%;
- flowType disagreement y=30 mm = 98.75%.

B13 puede parecer térmicamente cercano a B11:
- T RMSE = 0.234 K;
- Uy NRMSE = 8–12% según perfil;

pero mantiene:
- max `|sum(phi)| = 9.771e-5 kg/s`;
- `Eadv,top=-559.53 J`.

**Lección metodológica:** similitud de T(t) no demuestra equivalencia física si el balance de masa/frontera es incorrecto.

C12/C13 quedan cerca de C11 en T/U, pero conservan ~+6.29 J de advección integrada con flujo neto casi nulo, por lo que no sustituyen la condición estrictamente impermeable.

#### Decisión final de la campaña

1. V11 queda `RUN-VERIFIED + ANALYSIS-VERIFIED`.
2. `fixedFluxPressure + slip` queda confirmado como tratamiento de `metalTop` impermeable en el modelo actual.
3. **C11 queda como baseline físico preferido para la etapa G1 de validación experimental.**
4. B11 se conserva como diagnóstico de densidad variable; su cumulative continuity distinta de cero expone la incompatibilidad `rho(T)` + volumen fijo sin shrinkage/free-surface/feeding y no representa fuga por el top.
5. V12/V13 quedan como pruebas diagnósticas y no reemplazan V11.
6. No se justifica abrir nuevas variantes V14 de presión/PIMPLE por esta línea de investigación.
7. El siguiente paso científico es G1: alinear C11 a las condiciones experimentales Quick-Cup y comparar contra una serie numérica/digitalizada de termopar.


---

## 2026-09-29 — Auditoría JMatPro → OpenFOAM

### AUD-JMATPRO-001 — La simulación termodinámica queda como puerta J0 antes de G1
**[GIT-VERIFIED] [DOCUMENT-VERIFIED] [DECISION]**

Se auditó la relación entre la función metodológica de JMatPro en la propuesta de tesis y las propiedades realmente implementadas en la baseline C11.

La propuesta define JMatPro antes de OpenFOAM para:
- definir Mn controlado mediante estabilidad de fases e interacción Mn-S;
- estimar TL, TS, L, Cp(T), k(T), rho(T) y fL(T);
- alimentar el modelo numérico con propiedades calculadas por composición.

Estado real de C11:
- `rhoConst=6820 kg/m3`;
- `Cp=827 J/(kg K)` constante;
- `mu=5.5e-3 Pa s`;
- `Pr=0.14`;
- conductividad implícita `k≈32.4893 W/(m K)`;
- `beta=1.13e-4 1/K`;
- `Tsol=1423 K`;
- `Tliq=1473 K`;
- `L=2.286e5 J/kg`;
- `alpha1e=0.8`.

**Hallazgo:** C11 no usa actualmente curvas tabuladas Cp(T), k(T), rho(T) o fL(T). Los valores actuales del modelo no deben etiquetarse como derivados de JMatPro hasta conservar su exportación/fuente específica.

**Chequeo de consistencia de densidad:** la tabla rho(T) de B en el líquido 1473.15–1773.15 K tiene pendiente ~-0.8 kg/(m3 K), equivalente a `beta≈1.173e-4 1/K` con rhoRef=6820. Esto difiere solo ~3.81% del beta C11 y respalda conceptualmente la transformación `rho(T) → rhoRef + beta` para el modelo Boussinesq de volumen fijo. No demuestra por sí sola procedencia JMatPro.

**Hallazgo crítico de fase:** la propuesta muestra una fL(T) lineal entre TS y TL, pero el caso real usa `alpha1e=0.8`. La implementación de `solidificationMeltingSource` modifica la relación temperatura-fracción líquida; por ello la curva fL(T) de JMatPro debe compararse explícitamente contra la relación de OpenFOAM antes de G1.

### Decisión

1. C11 permanece congelado como baseline física.
2. Se crea la puerta **J0 — trazabilidad termodinámica** antes de G1.
3. JMatPro conserva dos papeles: metalurgia/estabilidad de fases y suministro/transformación de propiedades para CFD.
4. `rho(T)` no tiene que entrar directamente como EOS: puede transformarse en `rhoRef + beta`.
5. Antes de modificar C11 o crear G1 se deben archivar los exports JMatPro de las cuatro condiciones CE/S y cerrar la matriz de procedencia.
6. No se añade cinética de recalescencia antes de comparar primero fL_JMatPro(T), propiedades termofísicas reales y el modelo de equilibrio.

Documentación:
- `JMATPRO_OPENFOAM_TRACEABILITY_ES.md`;
- `analysis_results/jmatpro_openfoam_audit/current_model_matrix.csv`;
- `analysis_results/jmatpro_openfoam_audit/derived_checks.csv`;
- `thermodynamics/jmatpro/README_ES.md`.

## 2026-09-30 — AUD-POST-001 — Normalización canónica de postprocesamiento B/C + perfil y=10 mm

**Hallazgo.** La campaña `cases_controlled_buoyancy` mantenía la misma estructura general de ejecución, pero `system/researchDiagnostics` conservaba tres variantes históricas. Además, los perfiles horizontales disponibles estaban en y=20 mm y y=30 mm.

**Acción.**
- Se sincronizó `system/researchDiagnostics` en las 26 variantes B/C actuales usando la versión más completa, que incluye también `metalTopPhiSum`.
- Se mantuvieron idénticos en las 26 variantes: `Allrun`, `system/functions`, `system/researchDiagnostics`, `system/lineProfiles`, `system/lineProfilesDict` y `system/momentumPostProcessing`.
- Se añadió `line_y10mm` a `lineProfiles` con 80 puntos desde x=0.25 mm hasta x=39.75 mm, y=10 mm, z=5 mm.
- Se añadió el mismo `line_y10mm` al muestreo de `momentumPostProcessing`.
- El `Allrun` canónico ejecuta también el análisis espacial de `metalTop` después de una corrida exitosa.

**Verificación.** Auditoría por blob SHA en `main`: cada uno de los seis archivos canónicos anteriores presenta exactamente un único hash compartido por los 26 casos.

**Impacto.** A partir de esta normalización, las comparaciones entre generaciones B/C usan exactamente la misma instrumentación y muestreo de postprocesamiento. Los perfiles horizontales canónicos quedan en y=10, 20 y 30 mm, reduciendo sesgo por diferencias históricas de diagnóstico.

**Estado.** CONFIG-VERIFIED. Requiere nueva campaña limpia para que todos los resultados locales se regeneren bajo la instrumentación canónica.



## 2026-09-30 — AUD-RUN-001 — Falso negativo en auditoría de finalización de campaña completa

**Hallazgo.** La primera ejecución de `analysis_tools/full_campaign_audit.py` reportó 0/26 casos completos pese a que los 26 casos presentaron productos canónicos de postprocesamiento, sin faltantes en los perfiles y=10, 20, 30 mm y x=20 mm, y métricas finales coherentes.

**Causa identificada.** El criterio original exigía simultáneamente que el probe alcanzara 10 s, que `log.foamMultiRun` contuviera una línea exacta `End` y que no hubiera marcadores fatales. El runner de campaña ya registra explícitamente cada corrida exitosa en `analysis_results/full_campaign_run/status.tsv`, por lo que depender de la presencia textual exacta de `End` produce falsos negativos cuando la estructura del log difiere.

**Acción.** Se actualizó `full_campaign_audit.py` para considerar un caso completo cuando: (1) el probe alcanza al menos 9.999 s, (2) no se detecta error fatal y (3) `status.tsv` reporta `COMPLETED`; la línea `End` queda únicamente como respaldo cuando el status no está disponible.

**Hallazgo físico preliminar.** La campaña confirma una separación fuerte entre configuraciones de tapa: B12/B13 conservan flujo neto por `metalTop` del orden de 9.7e-5 kg/s y energía advectiva integrada de cientos de joules, mientras B11 y C11 presentan flujo superior prácticamente nulo. C12/C13 mantienen flujo superior cercano a 4.9e-10 kg/s. B9/B11 y C9/C11 comparten además `fixedFluxPressure` en `p_rgh` y `slip` en `U`, consistente con sus resultados prácticamente coincidentes.

**Estado.** AUDITOR-CORRECTED / RESULTS-PENDING-RECHECK. No se modificaron casos ni resultados; únicamente la lógica de auditoría.


## 2026-09-30 — AUD-RUN-002 — Campaña completa 26/26 confirmada; falso `fatal=True` resuelto

**Evidencia.** La auditoría detallada mostró para los 26 casos `status.tsv = COMPLETED`. Los probes de temperatura alcanzaron 10 s en los casos de paso fijo y entre 9.99966 s y 10.004 s en los casos con paso temporal adaptativo, consistente con el objetivo `endTime 10`.

**Causa del falso fallo.** `full_campaign_audit.py` interpretaba la ausencia de `log.foamMultiRun` como un error fatal mediante `if not txt: return True`. Como consecuencia, todos los casos aparecían con `fatal=True` y `complete=False` aunque el runner los hubiera marcado `COMPLETED` y los productos de postprocesamiento estuvieran completos.

**Acción.** Se separó explícitamente `log_available` de `log_has_fatal`. Un log ausente ya no se interpreta como fallo. Para campañas gestionadas por el runner, el criterio principal de finalización es: `status.tsv = COMPLETED`, probe >= 9.999 s y ausencia de marcador fatal cuando el log existe. `End` queda como respaldo únicamente si no hay estado del runner.

**Resultado.** La campaña controlada B/C queda confirmada como **26/26 corridas completadas hasta el objetivo temporal**, con los perfiles canónicos y=10, 20, 30 mm y x=20 mm disponibles en todos los casos.

**Estado.** RUN-COMPLETE / AUDITOR-FIXED. Pendiente: auditoría física de continuidad, transporte cara-a-cara en `metalTop` y selección de la configuración de referencia para tesis.


## 2026-09-30 — AUD-RUN-003 — Falso `fatal=True` causado por mensaje normal de OpenFOAM

**Hallazgo.** La auditoría detallada mostró `log file = True`, `status.tsv = COMPLETED` y probes en el objetivo temporal para los 26 casos, pero `fatal=True` en todos.

**Causa raíz.** El patrón de detección de fallos buscaba la cadena genérica `Floating point exception`. Los logs normales de OpenFOAM incluyen durante el arranque una línea que indica que el *floating point exception trapping* está habilitado. Esa línea es informativa y no representa una excepción ocurrida durante la solución.

**Acción.** Se eliminó la coincidencia genérica y el auditor ahora busca únicamente marcadores compatibles con fallo real: `FOAM FATAL ERROR`, `FOAM FATAL IO ERROR`, `Segmentation fault`, `Killed` o `Floating point exception (core dumped)`. También se corrigió el encabezado del reporte para no exigir una línea literal `End` cuando el runner ya registra `COMPLETED`.

**Impacto.** La clasificación anterior `fatal=True` para 26/26 casos era un falso positivo del analizador y no evidencia de inestabilidad del solver.

**Estado.** AUDITOR-FIXED / READY-FOR-FINAL-RUN-STATUS.


## 2026-10-03 — V14-CONFIG-001 — Referencia explícita de presión + topFlow directo solicitados por el director

**Objetivo.** Crear V14 como prueba controlada derivada de V11, conservando la tapa `fixedFluxPressure + slip` y aplicando la configuración solicitada para referencia de presión y registro directo de flujo en `metalTop`.

**Casos nuevos.**
- `B14_topFixedFlux_explicitRef`
- `C14_topFixedFlux_explicitRef`

**Cambios controlados respecto a V11.**
- `system/metal/fvSolution`: `pRefPoint (0.02 0.04 0.005)`;
- `system/metal/fvSolution`: `pRefValue 1e5`;
- `system/metal/fvSolution`: se añade `nEnergyCorrectors 2`;
- `system/functions`: se añade `topFlow`, `surfaceFieldValue` sobre `metalTop`, con `operation none`, `writeFields true`, campos `(U phi)` y `writeControl writeTime`.

**Condición de presión.** `0/metal/p_rgh` permanece sin cambio: `metalTop = fixedFluxPressure` con `value $internalField`.

**Hallazgo de compatibilidad OF14.** La región metálica usa el solver modular `fluid`. En OpenFOAM Foundation v14, `fluid::thermophysicalPredictor()` ensambla y resuelve una ecuación de energía por llamada y no consulta `nEnergyCorrectors`. Esa clave sí existe en `multiphaseEuler`. Por trazabilidad se conserva exactamente la configuración solicitada, pero V14 debe auditar el log para verificar su efecto operativo real y no asumir que cambia el número de solves de energía.

**Riesgo de arranque a verificar.** El punto `(0.02 0.04 0.005)` se encuentra sobre el plano superior geométrico. La rutina de referencia de presión requiere asociar el punto de forma unívoca con una celda; por ello la primera prueba V14 debe confirmar que OF14 acepta el punto sin error.

**Verificación de preparación.** Los dos casos contienen únicamente archivos de entrada/documentación: 138 blobs en total y cero `postProcessing/`, `logs/`, `log.*` o tiempos de solución heredados.

**Estado.** CONFIG-VERIFIED / NOT-RUN. Pendiente: corrida B14/C14 hasta 10 s y comparación directa contra B11/C11 de `phi` cara por cara, `sum(abs(phi))`, T, alphaL, Courant, continuidad y número efectivo de solves de energía.


---

## 2026-10-03 — V14-RUN-002 — Validación de impermeabilidad y referencia explícita de presión

**[RUN-VERIFIED] [GIT-VERIFIED] [ANALYSIS-VERIFIED]**

Se ejecutaron `B14_topFixedFlux_explicitRef` y `C14_topFixedFlux_explicitRef` hasta **10 s**. Ambos casos terminaron correctamente. El `pRefPoint (0.02 0.04 0.005)` fue aceptado por OpenFOAM 14 sin error de referencia.

### Auditoría cara por cara de metalTop

`topFlow` registró las **80 caras** de `metalTop`. En tiempos representativos 0.1, 5 y 10 s:

- B14: `max |Uy| = 0`; `max |phi| = 8.47033e-22` a 0.1 s y 0 a 5/10 s.
- C14: `max |Uy| = 0`; `max |phi| = 0` en los tres tiempos.
- Existe `Ux` tangencial no nulo, consistente con una condición `slip`.

La serie agregada de los **100 writeTimes entre 0.1 y 10 s** confirma:

- B14: máximo `sum(abs(phi)) = 8.47033e-22`;
- C14: `sum(abs(phi)) = 0` en todos los writeTimes.

Esto descarta la cancelación de flujos locales que podía ocultarse al observar solo `sum(phi)`. La combinación `fixedFluxPressure + slip` mantiene la tapa impermeable.

### Comparación V11 -> V14

Probe central, 10,001 pasos:

- B: `max |ΔT| = 0.01 K`; `max |ΔalphaL| = 7e-6`; T(10 s)=1470.07 K en ambos; alphaL(10 s)=0.988421 (B11) y 0.988414 (B14).
- C: T es idéntica a precisión almacenada durante toda la serie; `max |ΔalphaL| = 1e-6`; T(10 s)=1464.19 K y alphaL(10 s)=0.964815 en ambos.
- Las diferencias de velocidad son pequeñas y no cambian el régimen físico observado.

### nEnergyCorrectors regional

V11 y V14 producen la misma estructura de series de energía en `foamLog`: `h_0..2` y `e_0..2`, además de la misma cantidad de series de presión. Por tanto, el `nEnergyCorrectors 2` añadido en `system/metal/fvSolution` **no introdujo correcciones de energía adicionales** bajo la arquitectura actual de `foamMultiRun`. La clave efectiva de energía para el bucle multi-región sigue siendo la del control global/root, no la copia regional.

### Conclusión

V14 no representa una nueva física respecto a V11. Su función queda validada como **caso de referencia del director**: conserva la condición impermeable físicamente consistente de V11 y demuestra que la referencia explícita de presión solicitada no altera materialmente T, alphaL o el patrón de flujo.

**Estado:** ✅ RUN-VERIFIED / ANALYSIS-VERIFIED.


---

## 2026-10-03 — V14-BC-003 — Comparación B14/C14 con tapa impermeable común

**[RUN-VERIFIED] [GIT-VERIFIED] [ANALYSIS-VERIFIED]**

Se compararon B14 y C14 una vez eliminada la inconsistencia histórica de flujo en `metalTop`. Ambos casos alcanzaron 10 s y presentan tapa impermeable cara por cara.

Resultados principales:

- máximo `sum(abs(phi))` en `metalTop`: B14 = 8.47033e-22; C14 = 0;
- máximo Courant: B14 = 0.0673434; C14 = 0.0650864;
- continuidad acumulada final: B14 = **-3.10190e-02**; C14 = **4.44346e-13**;
- T central a 10 s: B14 = 1470.07 K; C14 = 1464.19 K;
- fracción líquida media: B14 = 0.9606902; C14 = 0.9620593;
- potencia térmica total de frontera: B14 = 316.1799 W; C14 = 313.9750 W;
- potencia advectiva de frontera: aproximadamente cero en ambos.

A 10 s los perfiles continúan mostrando diferencias sustanciales de velocidad y diferencias térmicas moderadas. Por ejemplo, en y=20 mm el RMSE B14/C14 es 3.7677e-3 m/s para Uy y 3.2461 K para T; en y=10 mm es 5.2355e-3 m/s y 7.8166 K.

**Interpretación:** como la extracción térmica de frontera es similar y la tapa ya no permite flujo de masa, la separación B/C se atribuye principalmente a la formulación densidad/flotación. En el dominio rígido, de volumen fijo e impermeable actual, la formulación B con rho(T) acumula una incompatibilidad de continuidad importante, mientras C con rho constante + flotación explícita conserva continuidad prácticamente a precisión de máquina.

**Decisión actual:** C14 queda recomendado como baseline físico/de producción para el modelo Quick-Cup rígido de la tesis. B14 se conserva como caso controlado de sensibilidad/formulación alternativa y podría recuperar relevancia física si posteriormente se incorporan contracción, alimentación, superficie libre móvil u otra física de cambio de volumen.

Resumen reproducible: `analysis_results/v14_bc_comparison/summary.md`.

**Estado:** ✅ ANALYSIS-VERIFIED. No se creó V15.


---

## 2026-10-03 — ENERGY-004 — C11 con 2 energy correctors efectivos

**[RUN-VERIFIED] [GIT-VERIFIED] [ANALYSIS-VERIFIED]**

Se ejecutó `C11_energy2_test`, derivado de `C11_topFixedFlux_airGapOF14`, cambiando únicamente `system/fvSolution/PIMPLE/nEnergyCorrectors = 2` en el diccionario raíz.

La corrida alcanzó 10 s y generó `h_0..5` y `e_0..5`, confirmando 6 solves de energía por timestep (3 outer correctors × 2 energy correctors). C11 normal genera `h_0..2` y `e_0..2`.

Comparación:
- T(t) central: RMSE 0 K; archivo byte-idéntico en 10,001 puntos.
- alphaL central: RMSE 4.80e-8; max |Δ| 1e-6.
- U central: RMSE 7.70e-9 m/s; max |Δ| 1e-7 m/s.
- fracción líquida media: RMSE 2.22e-8; max |Δ| 1e-7.
- perfil y=20 mm a 10 s: T y alphaL idénticos; Uy RMSE 4.04e-9 m/s.
- max Courant 0.0650864 en ambos.
- continuidad final: 4.44517e-13 (C11) vs 4.58617e-13 (energy2).
- executionTime: 289.433 s vs 387.542 s.
- clockTime: 302 s vs 398 s.

El segundo corrector reduce más el residual de entalpía, pero no cambia la solución física dentro de la resolución almacenada. Se clasifica como sobre-convergencia con costo adicional.

**Corrección sobre C14:** el `nEnergyCorrectors 2` de C14 está en `system/metal/fvSolution` y no controla el bucle global de energía. C14 solo produjo `h_0..2/e_0..2`; por tanto tuvo 1 energy corrector efectivo.

**Decisión:** mantener 1 energy corrector en la baseline actual.

Resultados: `cases_controlled_buoyancy/C11_energy2_test/`.  
Resumen: `analysis_results/c11_energy2_test/summary.md`.

**Estado:** ✅ RUN-VERIFIED / ANALYSIS-VERIFIED.

---

## 2026-10-08 — B11-E2-PREFLIGHT-005 — Limpieza de evidencia heredada y preparación de comparación controlada

**[GIT-VERIFIED] [OPEN / NOT RUN-VERIFIED]**

Al agregar `B11_energy2_test` el 5 de octubre también se versionaron inadvertidamente `logs/`, `postProcessing/` y `log.*` copiados de `B11_topFixedFlux_airGapOF14`. El blob SHA de la temperatura central era idéntico en padre y variante: `8e5b4c39dade992897df864f8d4f3dce135dcf24`. Esos datos no constituyen evidencia de ejecución de la variante.

Se compararon por SHA todos los archivos de entrada de `0/`, `constant/` y `system/`: **solo difiere `system/fvSolution`**, por el ajuste raíz `nEnergyCorrectors=2`. Se reconstruyó el árbol versionado de la variante sin los productos heredados, conservando `0/`, `constant/`, `system/`, `Allrun`, `Allclean` y sus notas. Los resultados del B11 original permanecen intactos.

**Próximo paso obligatorio:** correr localmente B11-energy2 con OF14 y auditar seis solves de energía por timestep, comparativa B11 de T, U, alphaL, impermeabilidad `metalTop`, continuidad, residuales, Courant y costo. No confundir esta prueba todavía abierta con `C11_energy2_test`, que sí está verificada.

La baseline de validación experimental permanece C14; J0 sigue ABIERTA.

---

## 2026-10-08 — RUN-PROTOCOL-006 — Inventario íntegro y protocolo autónomo de actualización entre corridas

**[GIT-VERIFIED] [OPEN / CONSOLIDATION PENDING]**

Se verificaron 30 carpetas en `cases_controlled_buoyancy/`. La auditoría `analysis_results/full_campaign_audit/` cubre únicamente los 26 casos históricos V3–V13: 26 filas `case_metrics.csv`, 13 parejas `bc_pair_metrics.csv`, 104 perfiles en `profile_inventory.csv`. **No** incluye B14/C14 ni C11-energy2, aunque están RUN-VERIFIED/ANALYSIS-VERIFIED y cuentan con resúmenes separados. B11-energy2 conserva estado PREPARED_NOT_RUN.

Se creó el protocolo autónomo `RUN_MASTER_PROTOCOL.md`, el registro de 30 casos `RUN_CASE_REGISTRY.csv`, el verificador de cobertura de solo lectura `analysis_tools/check_run_registry.py`, el README de alcance histórico y referencias en agente, guía y matrices. El verificador diferencia una campaña parcial de una global y no convierte outputs heredados en evidencia.

**Pendiente real:** extender/revalidar el generador de métricas antes de integrar los 3 casos posteriores a la campaña en todos los CSV globales. No se han recalculado ni modificado métricas físicas durante esta actualización documental. El registro no sustituye a la validación experimental J0/G1.

**Decisión:** toda corrida/MAZAPÁN futura consulta y actualiza el inventario y verifica cobertura sin depender de ningún repo maestro externo.


---

## 2026-10-08 — AGENTS-007 — Agentes científicos, auditoría de postProcessing y vigilancia local

**[GIT-VERIFIED] [CONFIG-VERIFIED / RUNNER PENDING]**

Se incorporaron cuatro perfiles especializados en .github/agents/ (observación durante corrida, forense de postprocesos, verificación numérico-física y actualización documental), el observador ejecutable analysis_tools/live_run_watch.py, el auditor analysis_tools/audit_postprocessing_config.py y el workflow programable quickcup-research-audit.yml. El observador local necesita ejecutarse junto al solver para ser realmente activo; el workflow de GitHub revisa solo archivos versionados. No se modificaron los casos físicos ni se ejecutó una nueva simulación.

Se creó POSTPROCESSING_FIELD_GUIDE_ES.md con las funciones reales de C14/V14, unidades, condiciones de interpretación y referencias a diccionarios e implementación; se actualizaron ambos manuales de comandos y la guía general.

**Advertencia:** el primer intento GitHub Actions puede fallar a nivel de runner; no considerar verificado hasta obtener run PASS. Los resultados originales quedan protegidos y los CSV históricos siguen incompletos para V14/C11-energy2.


### 2026-10-08 — AGENTS-008 — Lanzador local integrado y estado real de GitHub Actions

**[GIT-VERIFIED] [RUNNER NOT VERIFIED]**

Se añadió analysis_tools/run_with_agents.py: ejecuta Allrun de un caso preparado, inicia un observador de log en paralelo, se niega a sobreescribir casos con directorios temporales/logs/postProcessing existentes salvo opción explícita y entrega un informe de cribado. Permite --dry-run; la herramienta no sustituye MAZAPÁN.

Los intentos GitHub Actions del nuevo workflow registraron conclusion=failure sin pasos ejecutados en la respuesta de jobs. Por tanto la supervisión automática hospedada **NO** se declara funcional todavía; investigar disponibilidad/configuración de runner desde Actions UI. Esta limitación no impide vigilar una ejecución local usando el lanzador.


### 2026-10-08 — AGENTS-009 — Cobertura documental completa de functionObjects de V14

**[GIT-VERIFIED] [STATIC-CONFIG AUDIT]**

La revisión de las cuatro configuraciones principales de C14 identificó 37 nombres de functionObjects. La primera guía nombraba 20, por lo que se añadió un catálogo exhaustivo organizado por system/functions (2), researchDiagnostics (29), lineProfiles (2) y momentumPostProcessing (4), con tipo, significado y advertencias.

El auditor analysis_tools/audit_postprocessing_config.py ahora comprueba además la presencia documental del **nombre de cada objeto configurado**, y marca error si falta. Este chequeo no prueba por sí solo que la explicación sea correcta, que un campo se escriba durante la corrida ni que el modelo sea válido; eso exige la revisión física del agente especializado.

---

## 2026-10-08 — AGENTS-010 — Corrección de arquitectura por instrucción del investigador: CFD local, agentes después del push

**[GIT-VERIFIED] [WORKFLOW NOT YET RUN-VERIFIED]**

Se corrige la interpretación anterior: Michel ejecuta todas las simulaciones en su laptop y sube los resultados a GitHub. Se RETIRAN los lanzadores y vigilantes locales introducidos erróneamente en el repositorio (`run_with_agents.py` y `live_run_watch.py`). Los cuatro roles de agentes pasan a análisis de evidencia posterior al push. La automatización `analysis_tools/audit_pushed_results.py` inspecciona únicamente outputs presentes en Git (sin arrancar OpenFOAM) y genera un reporte de alertas y cobertura en artefactos de Actions, sujeto a que el workflow corra exitosamente.

Actualizados manuales ES/EN, guía de postprocesamiento, protocolo y README para eliminar instrucciones contradictorias. El flujo queda LAPTOP → simulación y postproceso local → git push → auditoría de evidencia + revisión científica/documental → actualización de bitácoras/manuales. No se modificó ningún caso ni resultado físico. Los archivos de agentes no se consideran procesos LLM autónomos.

---

## 2026-10-08 — RESEARCH-011 — Reunión con director; C15/C16 preparados y línea 3D/B-shrinkage

**[GIT-VERIFIED INPUTS] [PREPARED_NOT_RUN] [NO CFD EXECUTION]**

Decisión conversada con director: comenzar la transición de C14 a 3D; previamente estudiar tiempo adaptativo y coeficiente de relajación. Auditoría directa de C14 encontró `maxCo=0.25`, `relaxationFactors=1.0` en `system/fvSolution` y, crucialmente, `solidificationMeltingSource/relax=0.1` en `constant/metal/fvModels`.

Se prepararon nuevas variantes independientes de C14: **C15_adaptiveDt_fromC14** (solo `system/controlDict` cambia, adaptive y salida cada 0.1s físicos) y **C16_phaseRelax025_fromC14** (solo `constant/metal/fvModels` cambia, `relax:0.1→0.25`). Los archivos `0/`, `constant/`, `system/` más Allrun/Allclean se copiaron por SHA manteniendo input salvo el archivo correspondiente; se excluyeron tiempos solucionados, logs y postProcessing. Ambas permanecen PREPARED_NOT_RUN.

Se registró la necesidad de una geometría 3D físicamente representativa: C14 usa 80×80×1 celdas con caras `empty`. Se definió línea B paralela para modelar interfaz aire-metal y contracción, incluyendo auditoría de compatibilidad con módulos multiphase de OF14, sin asumir que un simple parche de presión corrige el balance de masa del B14 cerrado. El plan `NEXT_RESEARCH_ROADMAP_ES.md` distingue etapas y evidencias esperadas.

**Pendiente:** ejecutar C15/C16 en laptop, hacer push y validar numeria/físicamente contra C14; definir geometría 3D y arquitectura B-VOF/shrinkage. C14/B14 y resultados históricos intactos.

---

## 2026-10-08 — RESEARCH-012 — V15/V16 ahora paralelas B/C y bifurcación posterior

**[GIT-VERIFIED INPUTS] [PREPARED_NOT_RUN] [NO CFD EXECUTION]**

Corrección de secuencia del investigador: **V15 y V16 se realizan para ambas familias**, no solo C. Se preparan `B15_adaptiveDt_fromB14` y `B16_phaseRelax025_fromB14` como contrapartes de `C15_adaptiveDt_fromC14` y `C16_phaseRelax025_fromC14`. B15 cambia únicamente `system/controlDict` respecto a B14, con `adjustTimeStep=yes`, escrituras a 0.1 s físicos mediante `adjustableRunTime`; B16 cambia únicamente `constant/metal/fvModels` mediante `phaseChangeSource/relax: 0.1 → 0.25`. En ambos casos toda la física/materiales/tablas de la familia B se preserva, sin heredar `logs/` ni `postProcessing/`.

Se corrigieron comentarios no ejecutables de C15/C16 para reflejar valores actuales, sin cambiar sus parámetros activos. **Después de finalizar V16 para B y C** se abre una bifurcación: **C → 3D**, desde C14 como base física hasta evaluar los ensayos; **B → metal-aire con superficie libre, shrinkage y feeding**. Las variantes V15/V16 siguen siendo modelos cerrados 2D y no resuelven por sí mismas la continuidad del B14.

Total: **34 carpetas** con **29 RUN/ANALYSIS_VERIFIED históricos** y **5 PREPARED_NOT_RUN** (B11-energy2, B15, B16, C15, C16). Siguientes actividades: ejecutar en laptop, hacer push, auditar resultados pareados y recién después escoger la arquitectura de cada ruta. Actualizados roadmap, registry, matrices y agents. GitHub no ejecutó OpenFOAM.

---

## 2026-10-15 — V15/V16-PREFLIGHT-013 — Verificación de trazabilidad de entradas sin ejecutar CFD

**[GIT-VERIFIED INPUTS] [PREPARED_NOT_RUN] [NO CFD EXECUTION]**

Se inspeccionaron los árboles Git `0/`, `constant/` y `system/` para B15/B16/C15/C16 contra los padres congelados B14/C14. Todas las diferencias de blobs se reducen a `system/controlDict` en V15 o `constant/metal/fvModels` en V16; las lecturas de claves activas confirman las tres modificaciones temporales (`adjustTimeStep`, `writeControl`, `writeInterval`) y el único cambio de relajación de fase (`0.1 → 0.25`).

Se añadió una comprobación reproducible **de solo lectura** `analysis_tools/preflight_sensitivity_cases.py`, pruebas sintéticas `test_preflight_sensitivity.py` y un paso en `quickcup-research-audit.yml` para detectar cambios no controlados o evidencia copiada sin ejecutar OpenFOAM. Informe: `analysis_results/v15_v16_preflight/README.md`.

**Estado:** paridad de entradas verificada en la inspección; la ejecución de CI de la nueva rama y las cuatro corridas físicas se comprueban por separado. **J0 y G1 siguen ABIERTAS**. No se tocó B14/C14 ni se promovió ninguna variante a `RUN_VERIFIED`.

---

## 2026-10-15 — PUSH-014 — Evidencia nueva de cinco corridas y restitución accidental de workflows retirados

**[GIT-VERIFIED OUTPUTS] [PRELIMINARY-ANALYSIS] [SCIENTIFIC-CLOSURE-OPEN]**

Se comprobó que el commit `25e7cf8` subió `logs/`, `postProcessing/` y `log.foamMultiRun` para B11_energy2, B15, B16, C15 y C16. Las series `logs/Time_0` y los probes térmicos alcanzan 10 s. El registro de casos aún no está reconciliado con toda la evidencia y no deben declararse `ANALYSIS_VERIFIED` sin auditar log final, campos, masa, calor latente y fronteras. Comparaciones numéricas del punto central, Courant y continuidad: `analysis_results/v15_v16_postpush_20261015/README.md`.

Hallazgo adicional: un push local volvió a añadir al árbol Git tres workflows retirados que instalan OpenFOAM y/o generan variantes en Actions. El cambio correctivo los elimina de nuevo **sin tocar resultados**, y adapta el preflight para verificar entradas `constant/`, `system/` y scripts en casos ya ejecutados. El chequeo de entradas preparadas se conserva en modo estricto; la paridad de campos iniciales `0/` tras una corrida necesita revisión específica.

**Puertas científicas J0/G1 y bifurcación después de V16: sin cambios.** La documentación de esta sesión no convierte una evidencia temporal en validación física.


---

## 2026-10-19 — C3D-01: geometría CAD y barrera STL antes de mallar

**Estado: PRELIMINARY-GEOMETRY-PASS / OPENFOAM-NOT-RUN / SCIENTIFIC-GATES-OPEN.** Los STEP individuales de QuickCup y metal son sólidos válidos con contacto (distancia cero), sin intersección volumétrica según OCC. La triangulación local cerrada tiene 2668 triángulos en arena y 2252 en metal. La escala 51.8×65.5×51.8 mm sigue **pendiente de confirmar** por contradicción entre metadatos STEP y coordenadas.

Se añadió el preflight binario STL de solo lectura, verificación de región mediante 3 rayos por seed, comprobación de aristas/volumen y pruebas sintéticas sin OpenFOAM. La evidencia preliminar y los pasos locales quedan en [analysis_results/c3d_01_geometry/README.md](analysis_results/c3d_01_geometry/README.md). No se versionó CAD del investigador, no se ejecutó CFD en GitHub y no se tocaron B14/C14. El siguiente gate físico es multirregión+checkMesh+interfaces+BC en laptop.


---

## 2026-10-19 — [GIT-VERIFIED] Nuevo experimento C3D-01 en `cases_3d/`

A petición del investigador, el primer prototipo `blockMeshDict` fue llevado desde el ZIP local a la carpeta independiente [`cases_3d/C3D_01_metal_mold`](cases_3d/C3D_01_metal_mold/README.md), dejando intactos los casos C14/B14 y la línea de variaciones 2D. El material incluido consiste en `system/blockMeshDict` (58×72×58 mm, 29×36×29 = 30 276 celdas de fondo, paso 2 mm), `system/controlDict`, manifiesto con referencias geométricas exactas, preparador STL mm→m, script de ejecución **solo en laptop** y pruebas de configuración. Se corrigió el sentido de las normales de las seis caras externas y se añadieron pruebas para las orientaciones.

Las fuentes SolidWorks corregidas son `QuickCup(1).STL` (3 084 triángulos) y `metal(1).STL` (3 896 triángulos), con coordenadas compartidas. La prueba local de transformación binaria y preflight de geometría comprobó superficies cerradas, volúmenes y seeds; **no** acredita calidad de malla OpenFOAM. Por seguridad de propiedad intelectual, los STL originales no se versionan en el repositorio público; se reconocen por SHA-256 en `geometry_reference.json`.

**Estado:** `GEOMETRY_PREPARED; BACKGROUND_MESH_NOT_RUN; MULTIREGION_NOT_MESHED; CFD_NOT_RUN`. La tarea siguiente es `blockMesh`/`checkMesh` en Ubuntu, sin usar `Allclean` ni el `Allrun` de casos 2D. Ninguna prueba de GitHub instala OpenFOAM ni simula.


---

## 2026-10-19 — [GIT-VERIFIED] Corrección de rutas CAD y aclaración de snappyHexMesh

El investigador confirmó que las exportaciones vigentes de SolidWorks se llaman `QuickCup.STL` y `metal.STL` (sin `(1)`) y residen en una carpeta de su equipo Windows. Se actualizó el instructivo de C3D-01 para utilizar esos nombres con rutas entre comillas desde WSL, y un procedimiento alternativo para Ubuntu no-WSL. Los identificadores SHA-256 **siguen vinculados a las exportaciones con coordenadas originales verificadas**: cambiar un nombre no cambia el hash, pero una exportación distinta se rechaza para impedir volver inadvertidamente a las coordenadas positivas que producían interferencia.

Se aclaró que Python solo valida/prepara unidades de los STL; `blockMesh` genera la caja de fondo y el mallado 3D adaptado a la geometría metal/arena se hará con `snappyHexMesh` en un paso posterior con `snappyHexMeshDict` aún **no construido ni ejecutado**. Ninguna simulación CFD ni mallado fue ejecutado por GitHub.


---

## 2026-10-19 — [GIT-VERIFIED] Uso nativo de unidades `[mm]` en C3D-01 con OpenFOAM Foundation v14

Se confirmó con la guía oficial https://doc.cfd.direct/openfoam/user-guide-v14/blockmesh que `blockMeshDict` soporta `units [mm];`, convirtiendo la malla generada a SI. También se verificó en el código fuente de OpenFOAM-14 (`searchableSurfaces::triSurface::scale`) que las geometrías trianguladas aceptan `units [mm];` y que `scale` y `units` no deben declararse simultáneamente para la misma entrada. Por ello se actualizó el caso 3D: vertices de fondo escritos como [-3,55],[-69,3],[-3,55] mm; geometrías binarias SolidWorks se copian sin alterar coordenadas a `constant/geometry`; Python hace solo validaciones en memoria mediante `--stl-units mm`. Se añadieron pruebas estáticas y sintéticas para evitar regresiones de unidades y pérdida de integridad.

**Estado abierto:** No se ejecutó `blockMesh`, `snappyHexMesh`, `splitMeshRegions`, `checkMesh` en OpenFOAM. El fragmento `geometry` con unidades nativas está documentado, pero no existe aún un `snappyHexMeshDict` completo ni validado. La laptop será el único ejecutor CFD. No mezclar STL ya convertidos a m con la indicación `units [mm]` ni añadir `scale 0.001` duplicado.


---

## 2026-10-19 — [GIT-VERIFIED] C3D-01: mallado de fondo 100 % OpenFOAM; Python opcional

A petición expresa del investigador se retiró toda llamada obligatoria a Python del script `cases_3d/C3D_01_metal_mold/scripts/run_blockMesh_only.sh`. El script ahora solo verifica disponibilidad de OpenFOAM14 y la ausencia de `polyMesh`/logs existentes, luego ejecuta `blockMesh` y `checkMesh -allTopology -allGeometry`, preservando logs y sin sobrescribir pruebas. Ya **no requiere presencia de STL** porque `blockMesh` únicamente genera la caja auxiliar.

El flujo normal copia sin modificación `QuickCup.STL` y `metal.STL` desde `~/OpenFOAM/Piezas_STL/` a `constant/geometry/` mediante `cp -n`; los STL permanecen en milímetros y serán interpretados con `units [mm];` dentro del futuro `snappyHexMeshDict`. Se corrigieron README, pruebas estáticas y la carpeta de geometría. `prepare_geometry.py` y `preflight_c3d_stl.py` continúan como **herramientas de auditoría opcionales** y no ejecutan mallado. **No hay evidencia de `blockMesh`, `checkMesh` o `snappyHexMesh` ejecutados en laptop**; GitHub no los ejecutó. Las salidas C14 y anteriores permanecen intactas.
