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
