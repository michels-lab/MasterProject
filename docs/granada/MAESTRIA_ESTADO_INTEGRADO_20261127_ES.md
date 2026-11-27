> **27-11-2026 — Uva, conciliación de publicación V2:** los cuatro manifiestos fijos y los cuatro informes de `analysis_preview` se leyeron en commits inmutables: 800000 pasos, 200 s por caso, 66 fragmentos declarados, 2159821556 bytes; A serial y restantes MPI8. Se recuperó el SHA de commit faltante de A en el índice (ba0d4d29), que impedía seleccionarlo en el recuperador, y se sincronizaron los indicadores de manifiesto A/B. No se descargaron binarios, no se ejecutó CFD y no se cerraron hitos físicos. [Auditoría](https://github.com/michels-lab/MasterProject/blob/main/docs/review/UVA_LAB_MANIFEST_RECONCILIATION_20261127_ES.md).

> **27-11-2026 — Uva + Granada Caso B (10 s histórico):** dos ejecutores reforzados, diez regresiones sintéticas incorporadas; CI pendiente, sin CFD nuevo ni cambios de hitos. Caso B etapa 3/7, 2/7=29%. [Informe](../review/UVA_CASE_B_OFFLINE_INTEGRITY_20261127_ES.md).

> **27-11-2026 — tiempos nativos laboratorio fijo:** última línea `ExecutionTime / ClockTime` de `log.foamMultiRun`, en s: A serial 7453.94 / 7464; B 3D MPI8 58371.9 / 58390; B14-2D MPI8 2918.26 / 2936; C14-2D MPI8 35466.2 / 35482. Suma de ClockTime 104272 s. El dato nativo completa A sin estimar el wall externo. C14-2D sigue siendo anómalo; no inferir utilización agregada MPI ni causa de la ralentización a partir de ExecutionTime. Comparaciones entre geometrías y modos no constituyen benchmark controlado. Fuente: consola WSL del investigador, última línea de cada log.

> **27-11-2026 — cierre de publicación laboratorio fijo:** 4/4 CFD, 4/4 auditorías y 4/4 manifiestos completos confirmados en GitHub. A reanudado tras fallo DNS; 66 partes, 2159821556 bytes de archivos compactos. Los cuatro hashes de archivo coinciden con la consola del investigador. No se descargaron las partes binarias ni se incluyeron campos volumétricos; conservar WSL. Campaña combinada: 10/12 resultados publicados; faltan dos variantes adaptativas A. No validación física. [Índice](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json). Los cortes previos son históricos.

> **27-11-2026 — publicación laboratorio fijo:** 4/4 CFD de 200 s, 4/4 auditorías; 3/4 manifiestos remotos confirmados (`C14-3DB`, `B14-2D`, `C14-2D`), rama de `C14-3DA` sin manifiesto por fallo de push. No repetir CFD; reintentar publicación preservando ramas parciales. Archivos compactos sin campos volumétricos; no validación física. [Índice](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json).

> **27-11-2026 — laboratorio fijo:** 4/4 CFD de 200 s, 800000 pasos y 4/4 auditorías de cobertura. A serial; B 3D y ambos 2D MPI8. Recuperados los dos perfiles verticales 2D: 2001 tablas y 2001 duplicados idénticos por caso, 80 puntos únicos por tabla; cero errores, sin interpolación ni CFD nuevo. Originales preservados. Publicación remota pendiente. Nuevo ejecutor `tools/publish_lab_fixed_recovered_20261127.py` separa los archivos publicados en ramas `results/campaign-200s-fixed-lab-v2/`. No validación física ni nuevos hitos A/B. Evidencia: consola WSL del investigador del 27-11. Los cortes anteriores son históricos.

> **27-11-2026 — A control fijo MPI8:** corrida diagnóstica real completada a 0.7 s, solver exit 0, Tmin metal 1456.73 K, Tmax 1499.98 K. Entradas preservadas salvo controlDict; contraste temporal fuerte, no causa exclusiva probada. A 8/10=80%, campaña original 6/8. No nueva campaña ni modificación exclusiva de A autorizada. [Evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D04_A_NATIVE_THERMAL_OBSERVED_20261127_ES.md).

> **27-11-2026 — A:** contraste nativo con referencia fija de 10 s, 7 tiempos y 3 sondas; enfriamiento progresivo fijo vs oscilación adaptativa en las mismas coordenadas. Sin causa raíz probada ni nueva CFD. A 8/10, campaña 6/8. [Evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D04_A_NATIVE_THERMAL_OBSERVED_20261127_ES.md).

> **27-11-2026 — A:** checkMesh nativo metal y molde `Mesh OK`, 276/232 caras >70°. No defecto local demostrado, no nueva CFD ni cambio de controles. A 8/10, campaña 6/8. [Evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D04_A_NATIVE_THERMAL_OBSERVED_20261127_ES.md).

> **27-11-2026 — Auditoría incremental:** registro por ruta/blob y alcance, siete inspecciones iniciales (dos completas documentales y cinco parciales); seis publicaciones adaptativas contrastadas por pasos con el índice de manifiestos. Sin cambios de física ni validación nueva. [Protocolo](../review/README.md).

> **27-11-2026 — A instrumentación nativa observada:** MPI8 reprodujo fallo térmico metal .68 s; 51 pasos completos, último .66 s. A 8/10=80%, B 2/7=29%, campaña 6/8 publicada. Sin validación física ni cambio de controles. [Evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/C3D04_A_NATIVE_THERMAL_OBSERVED_20261127_ES.md).

> **27-11-2026 — cierre de esta revisión documental:** 6/8 combinaciones adaptativas laptop calculadas y publicadas con manifiesto completo; B14-2D sin tope 14275 pasos/200 s, commit e066adf9. Las dos A fallaron (.68/.70 s); no hay caso 2D pendiente de recuperación. 97 ramas indexadas (95 del corte inicial + 2 altas), 3815 commits únicos con cadena de padres completa, 273 archivos documentales inventariados en el corte inicial. No validación física nueva. [Manifiestos](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json) · [Historia e índices](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md). Entradas anteriores históricas.

> **27-11-2026 — CORTE HISTÓRICO (segundo corte, superado por 6/8 publicadas):** campaña laptop 6/8 calculadas, 5/8 con manifiesto completo, 1/8 B14-2D sin tope pendiente, 2/8 A adaptativo fallidas. C14-2D MPI con tope (11029 pasos, 3dbcbee4) y B14-2D MPI con tope (14276 pasos, b02ef4a9) ya están publicados y auditados según sus manifiestos, sin nueva validación física. A 8/10=80% hitos, B 2/7=29%, FS-C08 lote 12 75/75 pasos. [Historia completa](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_HISTORIA_CIENTIFICA_ES.md) · [Manifiestos inspeccionados](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json). Las entradas anteriores quedan como historia.

# Historia integrada de investigación y estado vigente — 27-11-2026

Este registro consolida la historia disponible, sin sustituir los registros originales. Es una actualización documental, no una ejecución CFD. Fecha de corte: 27 de noviembre de 2026, hora local de México. Evidencia: archivos y manifiestos GitHub consultados en esta actualización, bitácoras anteriores, y salidas de consola aportadas por el investigador (no acceso directo a WSL ni al laboratorio). No se publican transcripciones personales ni credenciales.

## Estado por línea (denominadores independientes)

| Línea | Etapa y avance | Evidencia / pendiente |
|---|---|---|
| 2D histórica | 26/26 corridas históricas; C14 referencia solidificación, B14 referencia contracción | No implica validación experimental ni C15/C16 ejecutados. |
| 3D-A C3D04 V4/T02 | 9/10, 8/10 = 80% hitos operativos | C14 fiel de 10 s archivado; fijo 200 s observado en laptop y reportado auditado en laboratorio; adaptación fallida. Conservación discreta, independencia y QuickCup pendientes. |
| 3D-B C3D05 | 3/7, 2/7 = 29% hitos técnicos | C14 10 s /101 estados; dos corridas adaptativas MPI de 200 s publicadas. No equivalen a cierre físico. |
| FS-C08 | Lote 12: 4/4 variantes, 75/75 pasos de arranque | Cierre acoplado local aprobado; dependencia temporal, energía global y contracción física no validadas. |
| Campaña adaptativa laptop | 6/8 combinaciones calculadas y publicadas, 0 pendientes de auditoría/publicación, 2/8 fallidas | Una combinación sin tope usa serial; no es una matriz MPI homogénea. |
| Campaña fija laboratorio | C14-3DA reportado completo/auditado; otras tres sin final verificado en este corte | Rama A existe, MANIFEST.json no disponible al consultar; no afirmar publicación completa. |

No hay porcentaje único de tesis. Un hito no se cierra por un commit, una prueba fuente, una corrida finalizada o un manifiesto por sí solo.

## Índice histórico y trazabilidad

- 2D: [auditoría histórica 26/26](../../analysis_results/full_campaign_audit/summary.md), [C14](../../cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/CASE_NOTES.md), [B14](../../cases_controlled_buoyancy/B14_topFixedFlux_explicitRef/CASE_NOTES.md). Conservar curvas, condiciones, unidades y versiones.
- Antecedentes C3D01/02/03: iteraciones de CAD, STL, conformidad y clasificación de mallas; historia conservada en Git y documentos de geometría. No sustituir las mallas aceptadas.
- A: [registro canónico](../C3D04_CASE_A_STATUS.json), [README](../../cases_3d/C3D_04_rounded_multiblock_pilot/README.md), [réplica fiel](../../cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful/README.md). V4/T02: 8,960 celdas metal, 12,352 molde; 2,496 caras por lado. CFD de 10 s, 10,000 pasos y 101 estados; recuperación de cellZone y perfiles en copias aisladas; 1,717 perfiles en réplica fiel. No confundir la cobertura de perfiles de la cuerda interior con altura 2D completa. Cierre energético y convergencia pendientes.
- B: [registro canónico](../PROJECT_STAGE_STATUS.json), [README](../../cases_3d/C3D_05_step_gmsh_conformal/README.md). STEP/Gmsh HEX8: 92,200 metal + 178,588 molde, 12,636 caras por lado; 1,826 caras severamente no ortogonales. T0 dos sólidos de referencia no es modelo C14 fluido-sólido. C14 real 10 s/101 estados, alpha1 volumétrica final 0.8917029861; diferencia de energía referencial más integral exterior -11.436294 J NO es residual de conservación. [Análisis](C3D05_B_C14_COMPARATIVO_SONDAS_PERFILES_20261124_ES.md), [cruce energético](C3D05_B_C14_CRUCE_101_ESTADOS_CONFIRMADO_Y_AUDITORIA_TERMINOS_20261124_ES.md). Conservación completa, propiedades, convergencia y QuickCup pendientes.
- [Comparativo central C14 2D/A/B](C14_COMPARATIVO_2D_3DA_3DB_SONDAS_20261124_ES.md): máximos |U| 10.76/22.41/23.07 mm/s, T final 1464.19/1466.36/1467.76 K; B solo 101 estados, no 10,001 sondas nativas. No demuestra independencia.
- [Estado 24-11](MAESTRIA_ESTADO_INTEGRADO_20261124_ES.md), [estado 25-11](MAESTRIA_ESTADO_INTEGRADO_20261125_ES.md), [plan 200 s](MAESTRIA_CAMPANA_B14_C14_200S_PLAN_20261124_ES.md), [compactación](MAESTRIA_CAMPANA_200S_ALMACENAMIENTO_COMPACTO_20261124_ES.md), [historia adaptativa](MAESTRIA_CAMPANA_ADAPTATIVA_200S_20261124_ES.md).
- [FS-C08 bitácora de lotes](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/BITACORA_20261125_ES.md), [STATUS](https://github.com/michels-lab/MasterProject/blob/research/fs-c08-conservative-phase-mass-20261123/freesurface/FS-C08_conservative_phase_mass/STATUS.json), [PR #79](https://github.com/michels-lab/MasterProject/pull/79). Rama independiente, no merge físico.

## Cronología 24–27 noviembre: campaña 200 s

24-11: seis insumos densos y compactos preparados, luego alcance autorizado reducido a cuatro: C14-3DA, C14-2D, B14-2D, C14-3DB. B14 3D excluidos. Paquete original permanece en transfer/campaign-200s-compact-inputs-v1. Fijo: dt=.001 s, 200000 pasos; 201 tiempos volumétricos (1 s), perfiles/reducciones cada .1 s (2001), topFlow positivo 2000, sondas cada paso. No eliminar datos ni cambiar física para ahorrar espacio.

24–25-11: laptop adaptativa independiente, dt inicial .001 s, maxCo=.25, sin maxDeltaT; C14-2D serial terminó 11028 pasos/645.90 s de pared; C14-3DA falló .70 s con T0=-296.103 K; B14-2D interrumpido durante compilación; C14-3DB serial interrumpido a 2.411881 s/1444 s. Decisión posterior: comparar 8 MPI Scotch con maxDeltaT=.025 y sin tope explícito, manteniendo Co=.25 y cadencias. Variante sin maxCo revocada. Pilotos 3DB: con tope 2042 pasos/872.54 s, sin tope 2041 pasos/761 s, ambos a 3 s. Los pilotos no son corridas de 200 s.

25-11: C14-3DB con tope completó 200 s, 15013 pasos, 7698.286 s de pared; reconstrucción interrumpida cerca de 151 s por sistema de archivos solo lectura. Recuperación pos-solver incorporada en 5a64cb08 y cola continúa ante fallo individual 55dfb26e. WSL trasladado del SSD al HDD después de respaldo verificado; no eliminar procesadores ni backups. Recuperación completó reconstrucción hasta 200 y t=0, auditoría sin errores y publicación e763cdd. Sin tope completó 15012 pasos, 5626.916 s de pared, reconstrucción ~1501 s; faltó dTdt en t=0, recuperado de datos distribuidos, auditoría aprobada, publicado d416a79. Ambos dt máximos observados .02 s, mínimos ~.000934579 s; Co máximo observado .257422/.268245 (no garantía estricta de .25 ni de precisión térmica). No benchmark controlado de tiempos por diferencias de almacenamiento y ejecución.

25-11: pilotos 2D inicialmente rechazados por pRefPoint (.02,.04,.005) encontrado en dos dominios. Reintento de cola laptop con referencia (.01975,.03975,.005), registrada localmente; no modificar física de casos originales. Se omitió C14-2D sin tope MPI por existir resultado serial. Los tres nuevos 2D terminaron 200 s y reconstruyeron 201 estados; auditor rechazó perfil vertical por 81 filas. A fijo serial laptop llegó a 200 s con End y 201 volúmenes, no se verificó informe/publicación. Ambos A adaptativos volvieron a fallar a .68/.70 s por T0 negativa. No repetir idéntica configuración ni duplicar corridas del laboratorio.

26–27-11, corte histórico previo a la publicación final de las tres recuperaciones 2D: diagnóstico de perfiles: 2001 tablas line_x20mm.xy por corrida 2D MPI, 81 filas, 80 coordenadas únicas, 27 columnas; serial de referencia 80 filas. Ejemplos a .1 s contienen repetición idéntica en y=.01825 m. Pendiente verificar igualdad de todos los duplicados y cobertura exacta de 80 puntos (.00025 a .03975 m, separación .0005 m). Recuperación propuesta genera canónicos sin alterar nativos, sin promedio/interpolación, valida timeline, probes, reducciones, topFlow y volumen, luego publica. Es corrección local aún no verificada ni incorporada permanentemente al auditor. Desconexión HDD dejó WSL sin acceso; Windows no detectaba D:. Tras reconexión y reinicio, df/sed/Python/Git y rutas de OpenFOAM confirmados; 253 GiB físicos libres en D:, 113 GiB C:. Advertencia systemd de usuario; no prueba de corrupción ni garantía de integridad total. Último bloque de recuperación llegó a fetch main pero Python rechazó comilla sobrante (SyntaxError, salida 1) antes de ejecutar el cuerpo; corrección por historial entregada, resultado no recibido. En ese momento no había nuevo manifiesto 2D MPI confirmado. El corte posterior confirma los tres manifiestos de la matriz siguiente; la publicación no implica revalidación independiente de cada parte binaria.

## Matriz de resultados laptop

| Caso | Política | Pasos / tiempo | Estado |
|---|---|---|---|
| C14-3DB | MPI8 cap .025 | 15013 / 200 s | [MANIFEST](https://github.com/michels-lab/MasterProject/blob/results/campaign-200s-adaptive-mpi-r8-Co025-dt0p025-v1/C14-3DB-200s/MANIFEST.json), complete y cobertura true |
| C14-3DB | MPI8 sin tope | 15012 / 200 s | [MANIFEST](https://github.com/michels-lab/MasterProject/blob/results/campaign-200s-adaptive-mpi-r8-Co025-dtuncapped-v1/C14-3DB-200s/MANIFEST.json), complete y cobertura true |
| C14-2D | serial sin tope | 11028 / 200 s | [MANIFEST](https://github.com/michels-lab/MasterProject/blob/results/campaign-200s-adaptive-uncapped-v1/C14-2D-200s/MANIFEST.json), complete y cobertura true |
| C14-2D | MPI8 cap .025 | 11029 / 200 s | [MANIFEST](https://github.com/michels-lab/MasterProject/blob/results/campaign-200s-adaptive-mpi-r8-Co025-dt0p025-v1/C14-2D-200s/MANIFEST.json), complete y cobertura true; intento lafue34t |
| B14-2D | MPI8 cap .025 | 14276 / 200 s | [MANIFEST](https://github.com/michels-lab/MasterProject/blob/results/campaign-200s-adaptive-mpi-r8-Co025-dt0p025-v1/B14-2D-200s/MANIFEST.json), complete y cobertura true; intento 0a_f23k4 |
| B14-2D | MPI8 sin tope | 14275 / 200 s | [MANIFEST](https://github.com/michels-lab/MasterProject/blob/results/campaign-200s-adaptive-mpi-r8-Co025-dtuncapped-v1/B14-2D-200s/MANIFEST.json), complete y cobertura true; intento 8fd7lt71 |
| C14-3DA | MPI8 cap .025 | .68 s | fallo térmico; intento ckuf84dm |
| C14-3DA | MPI8 sin tope | .70 s | fallo térmico; intento fp6has9o |

6/8 manifiestos leídos directamente, no se descargaron/revalidaron sus partes binarias. Volúmenes completos no incluidos. 2/8 fallidas. A fijo laptop separado. C14-3DA cap T0 aproximada -139.17 K; sin tope -602.49 K, no temperaturas físicas aceptadas. Co no controla por sí solo la estabilidad térmica. No inferir causa única del fallo sin analizar ecuaciones/estados.

## Laboratorio: política fija separada

C14-3DA 200000 pasos reportado completo/auditado; rama results/campaign-200s-compact-v1/C14-3DA-200s sin MANIFEST.json disponible en la consulta. Se reportaron errores de autenticación y de preflight MPI. Commits 440b914f (finalización), 05a7f593 (cola fija MPI8), e5bef692 y bfbaba0c (preflight y localhost), 96b78d76 (referencia de presión), 643da42a (cola serial), 04e123f6 (reinicio desde checkpoint), 5da3faad (intentos MPI desde cero). Código no demuestra ejecución. Últimos estados reales de los tres restantes pendientes de consola/manifiestos; no reiniciar desde laptop.

## FS-C08: historia hasta lote 12, sin mezclar B14/A/B

Lotes anteriores: movilidad 40/40, flujo 39/40, energía 40/40, soporte 40/40; temporal 35/75; atribución 7/15; compresibilidad auxiliar 7/15; EOS finita 24/32; refinamiento EOS 150/150; residual térmico 40/160; cierre térmico previo 4/75 (0/4 completas). Acumulado anterior de la bitácora 426/682 pasos y 32/44 variantes únicas, no porcentaje de tesis. Véanse bitácora y STATUS para el detalle de cada intento, fallos de compilación excluidos y réplicas.

Nuevo lote thermal_closure: candidato sincronizado geometría/energía, HEAD probado 7b3ed1ff4, biblioteca SHA256 2b47f54fec6e429b6e7484c4440de718eca8d7611c2b90d1f938838faab82887. Lote 20261126T032157Z_1a7731a8; réplica 20261126T042933Z_0c0d778e idéntica en las métricas entregadas, no sumar dos veces. wmake exit 0, ejecución exit 0; 4/4 y 75/75, 5 tiempos comunes, horizonte 5 μs, K provisional 83.761 GPa, tolerancia lineal 1e-12, pasos fijos.

| dt μs | pasos | Umax m/s a 5 μs | pmax kPa a 5 μs | L1 energía local | residual máximo volumen |
|---|---:|---:|---:|---:|---:|
| 1 | 5 | 75.278332 | 207.815914 | 5.7046e-9 | 6.6613e-16 |
| .5 | 10 | 65.608821 | 176.681719 | 2.3342e-8 | 7.7716e-16 |
| .25 | 20 | 36.642851 | 141.862471 | 2.6350e-8 | 5.1070e-15 |
| .125 | 40 | 12.822502 | 115.526940 | 1.0925e-7 | 7.1054e-15 |

Todas las auditorías finales del estado acoplado pasan en los pasos guardados; residual equivalente térmico final <=1e-6 K. Masa sólida a 5 μs 9.4394e-7/6.0464e-7/2.8644e-7/9.6324e-8 kg. Dependencia temporal fuerte; no convergencia demostrada. global_energy_verified=false, physical_shrinkage_validated=false; estado STARTUP_PROBE_CONSERVATION_GATES_PASS__NOT_FULL_TRANSIENT. Acumulado actualizado 501/757 pasos, 36/48 variantes únicas (a partir del acumulado previo registrado). No extrapolar a 200 s ni aceptar contracción física. Próximo: identificar mecanismo de aceleración y sensibilidad temporal del acoplamiento, sin relajar criterios ni cambiar B14 histórico.

## Próximos hitos y mantenimiento

1. Las tres recuperaciones 2D están publicadas según manifiestos. Cotejo Uva 02: los seis manifiestos adaptativos leídos en commits inmutables coinciden con sus SHA de blob y cifras del índice; cinco MPI y uno serial. El serial no declara physical_validation explícitamente; no se presume validación física. No se descargaron archivos binarios. No CFD nuevo para ellas; conservar evidencia y comparar datos cuando se descarguen.
2. A: resolver estabilidad adaptativa sin cambiar silenciosamente la definición del experimento; preservar fijo 200 s. A 8/10 y B 2/7 se mantienen.
3. Confirmar laboratorio mediante manifiestos y logs; no repetir casos activos ni completos.
4. Comparar curvas T, alpha1, U y energía con cadencias y coordenadas homologadas; FoamLens primero, ParaView complementario. Verificar importación real, no afirmarla por estructura de archivos.
5. FS-C08: siguiente hito integrado de sensibilidad/consistencia y propiedades trazables, no un largo transitorio aún. QuickCup/JMatPro y validación experimental siguen pendientes.
6. Cada entrega futura debe actualizar bitácora propietaria, estado JSON, índice maestro y README en la misma operación documental, con fecha, rama/commit, evidencia, fallo/decisión, alcance y siguiente hito. No copiar información desactualizada como vigente. No borrar registros históricos ni ocultar intentos fallidos. Si no hay evidencia, marcar pendiente.

### Addendum de cronología laboratorio
Consola histórica recuperada: C14-2D serial se preservó cerca de 26.232 s después de ValueError: incomplete solver (25-11); C14-3DB MPI8 observado a 5.316/200 s, log log.lab_mpi8_fresh_20261125_163125.txt. C14-3DA fijo reportado completo, git push falló. No evidencia suficiente de finalización posterior de los tres restantes ni manifiesto final de A. No confundir con publicaciones adaptativas laptop.
