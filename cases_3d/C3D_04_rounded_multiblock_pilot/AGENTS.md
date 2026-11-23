## 23-11-2026 — No actualizar Caso A mientras B/FS están en ejecución

Caso A fuente futura: ~/OpenFOAM/C3D04_A_WORKTREE (work/c3d04-a-isolated, sin upstream). Su corrida 10s C14 ya existente permanece fuera de repo en ~/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01. **Nunca git pull en MasterProject, ni solver desde árbol vivo de otro caso, ni limpieza de B o FS.** La creación segura sin actualizar main se documenta en docs/WSL_CONCURRENT_CASE_WORKTREES_20261123_ES.md. Contracción FS_C02_WORKTREE ya existe y está fuera de este alcance; no intervenir. No incrementar hitos 6/10=60% por worktrees, seguir etapa 07/10.

---

## 23-11-2026 — C14 POSTPROCESSING PARITY: NO SOLO T Y ALPHA1

Mandato científico explícito: Caso 3D-A debe reproducir **todo** lo que se calcula en el caso 2D original C14 en postProcessing (los 29 researchDiagnostics, sondas U/T/p_rgh/rho/alpha1, horizontal/vertical profiles, tasas térmicas/solidificación, vorticidad/topología, gradientes, energy/heat/advectiveFlux, metalTop phi/U por cara, contacto metal-arena, energía sensible/latente, Darcy/buoyancy/pRgh, momentumMean/Max/Profiles y foamLog). Añadir cálculos volumétricos 3D que el 2D no ofrece. La fuente canónica es el inventario de **diccionarios auténticos** en docs/C3D_04_C14_3D_POSTPROCESS_PARITY_MATRIX_20261123_ES.md, no una selección simplificada.

El código del primer bloque volumétrico está en c14_physics/c14_3d_postprocess_parity.py, que calcula sobre **los mismos 101 estados existentes** pero aún **no ha sido ejecutado en WSL por el investigador**. Las cifras verdaderas previas de 3D se conservan. No recuperar ni fingir las 10,001 mediciones originales de probes 2D C14 desde snapshots de 0.1 s. No cambiar física, C14, malla ni 10s CFD, y NO ejecutar C14 Allrun; postproceso nativo faltante será en copia aislada. Sin energía de fronteras nativa no declarar balance. **Etapa 07/10, 6/10=60%, en progreso**; esto es un requisito pendiente y no un nuevo hito concluido.

---

## 23-11-2026 — Evidencia real de solidificación en C14 3D V4/T02

**NO CONFUNDIR** el avance de solidificación que observa OpenFOAM con validación de energía, independencia o QuickCup. El investigador corrió `analyze_existing_c14_3d_results.py` en WSL sobre sus **101 estados existentes** y encontró a los 10 s metal `T=1401.91..1471.07 K`, media por celda 1444.7185 K, **8960/8960 bajo liquidus 1473 K**, **1158/8960 bajo solidus 1423 K**, `phaseChangeSource:alpha1=0..0.992311`, media por celda 0.8367355; la fracción líquida ya no está uniformemente en 1. Del log completo: 10 000 pasos, Courant máximo real **0.0240415** (`maxCo=0.25`), máximo residuo final `p_rgh=0.00776125` en alguna iteración. Fuente: `docs/C3D_04_C14_V4_T02_REAL_10S_PHASE_NUMERICAL_RESULTS_20261123_ES.md`. Los números son del **resumen impreso por WSL**; no afirmar que GitHub posee el CSV/JSON o 28 MB del log local.

**Etapa 07/10 en progreso; 6/10 = 60 % operativo**. No cerrar el hito 07 sin balance energético/diagnóstico numérico, ni el hito 08 sin estudiar la secuencia temporal y término Darcy. Ningún parámetro C14 cambia. **Nunca reejecutar los 10 s para obtener estadísticas que ya están guardadas**: tras auditoría inicial usar `c14_physics/summarize_existing_c14_phase_timeline.py` para analizar el CSV/JSON existentes en otra carpeta nueva; este script solo lee estados y no ejecuta OpenFOAM. Evento `first_saved_time_s` es el primer fotograma escrito, nunca instante exacto del inicio físico. Los promedios son por celda y NO ponderados por masa/volumen.

---

## Evidencia más reciente — 23-11-2026, Caso A REAL YA CORRIDO

El usuario aportó salida de su laptop confirmando **`foamMultiRun` nativo en V4/T02 con C14 ORIGINAL 0–10 s: `native_solver_run=true`, `Time = 10s`, `End`, 101 tiempos guardados, `ClockTime=839 s`**. El intento siguiente se bloqueó correctamente por carpeta existente: **NO indicar repetir 10 s ni eliminar la carpeta; no tratarla como «aún no hay CFD»**. La evidencia está en `docs/C3D_04_C14_V4_T02_REAL_10S_20261123_ES.md`. La etapa 06 nativa está terminada; **etapa 07/10, avance 6/10=60 % de hitos**, sin validación de conservación, fracción de fase, independencia ni QuickCup. Para análisis: ejecutar **solo lectura** `c14_physics/analyze_existing_c14_3d_results.py` sobre la corrida previa; el analizador crea resultados en carpeta separada. En respuestas posteriores **siempre consultar estado JSON canónico**. Es imperativo preservar el C14 físico original, sin cambios numéricos/materiales.

---

## Contrato definitivo del investigador: C14 idéntico, únicamente de 2D a 3D (20-11-2026)

**Instrucción literal de intención:** conservar TODO del Caso 2D C14; **el único cambio del modelo de investigación es su dimensionalidad y la geometría de mallado 3D**. Ninguna propiedad, constante, modelo, ecuación, tratamiento físico, condición inicial/física ni control numérico puede cambiar por conveniencia. La copia física completa conserva el `system/controlDict` original de **10 s, Δt=0.001 s y writeInterval=100**, además de los originales `fvModels`, termofísica y fluid/solid.

**Lista blanca técnica, no nuevo modelo:** parches `frontAndBack/empty` 2D → paredes e interfaz metal/arena de la V4/T02 aceptada; punto geométrico de referencia de presión `pRefPoint` → **índice `pRefCell` de la región 3D**, sin alterar su valor de presión de referencia; `cellZone metal` → todos los índices reales de la región metálica sin cambiar parámetros de solidificación; sintaxis F14 equivalente cuando el ejecutable lo exija y sin modificar valores (ej. `externalTemperature`). Cada diferencia debe quedar justificada y comprobada contra C14 original; si no, bloquear.

El ensayo `--smoke` de 0.002 s es **solo diagnóstico en carpeta sintética/aislada**; NO sustituye ni redefine el caso de 10 s de investigación. **No introducir el T0 de dos sólidos, VOF, contracción, otros casos, propiedades dependientes de temperatura, nuevas condiciones de frontera ni correcciones numéricas no solicitadas.** El preparador `enforce_C14_3D_only_delta` rechaza cambios en cualquier archivo científico del C14 fuera de la lista blanca, y las pruebas negativas deben permanecer verdes. Malla V4/T02 original y C14 fuente, solo lectura.

## Regla científica prioritaria del investigador — C14 original (20-11-2026)

**La física del Caso 3D-A debe conservar el modelo realmente utilizado en el caso 2D C14**: hierro `fluid` (`heRhoThermo/hConst/sensibleEnthalpy`, `U`, `p`, `p_rgh`), arena `solid` (`heSolidThermo/eConst`), `solidificationMeltingSource` con `Tsol/Tliq/L/alpha1e/beta/rhoRef/relax/Cu/q`, gravedad, flujos de frontera y parámetros numéricos de C14. **Está prohibido sustituirlo silenciosamente por el T0 auxiliar de dos sólidos o convertir Cp de hierro en Cv.** Leer las fuentes originales de C14 y el [contrato de fidelidad del Caso A](c14_physics/README.md) antes de editar diccionarios.

El T0 anterior es únicamente una prueba de conducción y arranque de módulos, **no** el solver de tesis ni equivalente al C14. Cualquier transición 2D→3D debe limitarse a cambios acreditados por la geometría V4/T02 real (parches `empty`→paredes 3D, referencia de presión, `cellZone`) y sintaxis Foundation14, conservando valores físicos idénticos y documentando cada transformación. El ejemplo ya probado de sintaxis F14 `externalTemperature` usa `h uniform 10` y `Ta constant 300`, no modifica los valores. Si un mapeo no está verificado, bloquear materialización y solver; nunca introducir constantes inventadas ni copiar una rama de contracción/VOF/Caso B.

**El 50 % operativo histórico (5/10 hitos, etapa 6/10) no es el progreso de implementación de física C14 en 3D.** No subir el porcentaje por inventario, diccionario o CI de dos celdas. El preflight WSL y un futuro CFD del modelo C14 aún requieren evidencia nueva.

# Contrato operativo persistente — Caso A / C3D-04 (OpenFOAM 3D)

**Vigente desde 2026-11-19. Autoridad: instrucción expresa del investigador.**
Aplica al trabajo dentro de `cases_3d/C3D_04_rounded_multiblock_pilot/`, a sus informes en `docs/` y a las respuestas que anuncien trabajo sobre Caso A. No confundirlo con Caso B / C3D-05.

## 1. Reporte obligatorio de ETAPA + AVANCE en TODA respuesta de proyecto

Antes de trabajar consultar `docs/C3D04_CASE_A_STATUS.json`; no reemplazarlo por memoria de chat ni por un porcentaje improvisado. Al entregar una respuesta incluir, **siempre y en un lugar visible**:
- **Etapa actual:** `N/10`, título del hito activo y responsable/bloqueo actual.
- **Avance operativo:** `D/10 = P %`, donde D= número de hitos `DONE`; `P=100*D/10`. Etiquetarlo avance de hitos, **no validación física** ni estimación temporal. Si un hito es parcial, NO contarlo completo.
- **Evidencia nueva realmente obtenida y cambio realizado:** commit(s), casos nativos, pruebas propias ejecutadas o archivos, especificando si algo sigue preparado/no ejecutado.
- **Siguiente trabajo agrupado**, pendientes indispensables, CFD/solidificación, independencia y validación.
Al 20-11-2026, tras pruebas nativas Foundation14 en CI, el estado canónico es **ETAPA 6/10, AVANCE 5/10 = 50%**. Este número es una fotografía histórica: **el JSON siempre prevalece y debe recalcularse**, nunca congelar 50 % en futuras respuestas. Al completar un hito se actualiza **en la misma entrega** el estado JSON, README, bitácora de proyecto, tracker CSV, y el reporte al usuario. Nunca incrementar el progreso por publicar un script sin ejecución/capacidad verificada.

## Etapa 5 completada: alcance exacto de la evidencia

La [evidencia del 20-11-2026](../../reports/case-a-t0/CI_NATIVE_F14_20261120.json) registra **10/10 archivos T0 con parámetros C14 interpretados por `foamDictionary` REAL de Foundation14**, además de **15/15 pruebas estáticas** y dos workflows de gobierno y auditoría científica con éxito. Esta evidencia **CI_NATIVE_DICTIONARY_PASS** permite cerrar el hito de diseño T0 (05/10); **NO** equivale a `WSL_FULL_MESH_T0_PREPARED` o `T0_SOLVER_EXECUTED`. El hito activo ahora es 06/10: una sola verificación integrada **en el equipo donde existe el `polyMesh` V4/T02 original**. No volver a pedir al investigador que revise cada diccionario o cada propiedad C14 de forma independiente. En Ubuntu 26.04 la carga de F14 debe exportar `HWLOC_COMPONENTS=-gl` antes de cargar `/opt/openfoam14/etc/bashrc`; el runner integrado ya lo hace.

## 2. Prohibición de micropruebas y de pedir una orden por componente

**No volver a repetir el flujo una prueba/auditor de una pieza → pedir una ejecución WSL → siguiente script → pedir otra ejecución.** Por defecto:
1. Leer primero evidencia ya obtenida y scripts existentes; no volver a ejecutar las 64 caras, la topología/área, ni la comparación superficial de V4/T02 sin una justificación real de regresión.
2. Diseñar una **unidad completa de trabajo** (por ejemplo, T0 térmico: campos, propiedades, parches, discretización, conservación/diagnóstico y límites) y resolver todas las subpiezas posibles en repositorio antes de solicitar una ejecución del investigador.
3. Incluir autocontroles estáticos positivos y negativos, validaciones de entrada y rechazo seguro en **un único orquestador** de etapa. Auditar los mensajes y el caso de fallo antes de enviar instrucciones.
4. Proporcionar, como máximo, **una única instrucción de terminal por hito significativo**, no una por script; no obligar a revalidar lo que ya tiene evidencia y no cambió. Si una prueba pequeña es indispensable para depurar, realizarla desde el entorno disponible de la asistencia o integrarla en ese único orquestador.
5. Si faltan datos científicos auténticos, **no inventarlos ni pedir ejecuciones repetidas**: dejar `BLOCKED_PENDING_REAL_INPUTS`, fuentes requeridas y una ruta de resolución; terminar todo trabajo útil que sí pueda resolverse.
6. Cambios en V4/T02 original, datos, ensayos anteriores, solver o parámetros experimentales no autorizados: prohibidos. Conservar evidencias y usar carpetas nuevas para entregables.
7. Distinguir `CODE_COMMITTED`, `STATIC_TESTED`, `WSL_VERIFIED`, `NATIVE_CHECKMESH_ACCEPTED`, `T0_SOLVER_EXECUTED`, `EXPERIMENT_VALIDATED`; jamás sustituir uno por otro.

## 3. Evidencia y seguridad científica

Malla de referencia inmutable: `~/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02`.
- `Mesh OK`: padre 21,312, hierro 8,960, arena 12,352.
- Contacto: 2,496 caras `mappedWall` recíprocas por lado, área 6,343.771874 mm².
- Ajuste STL: máximo **muestreado** 0.104973015 mm, no Hausdorff riguroso.
- No ortogonalidad >70°: padre 572, metal 276, arena 232; diferencia 64/64 probada en interfaz, diagnóstico **cerrado**, no es prueba de estabilidad.
- CFD/CHT/solidificación, independencia de malla y curvas experimentales 3D: **NO realizados**.
- Fundición durante solidificación no debe confundirse con dos sólidos de conducción T0: una hipotética prueba T0 es solo verificación numérica, no la física de vaciado real.

## 4. Prevención de reincidencias auditable

Antes de cada entrega revisar:
- [ ] ¿Se indica **Etapa N/10** y **Avance D/10=P%** del JSON?
- [ ] ¿La entrega cubre un bloque integral y evita micropruebas nuevas?
- [ ] ¿Se respetaron caso A, la malla y los resultados ya cerrados?
- [ ] ¿Los resultados están atribuidos a commits o salidas reales y los bloqueos están explícitos?
- [ ] ¿Una sola orden como máximo, solo cuando procede, y comprobaciones internas agrupadas?
- [ ] ¿Se actualizaron JSON/bitácoras/README/tracker si cambió el progreso?
La falta de cualquiera de los primeros dos puntos es un **DEFECTO DE ENTREGA**, no una preferencia estilística.
