# Operación Uva — Auditoría incremental de MasterProject

Fecha de inicio: 2026-11-27. Corte inicial de revisión: `5ed9f38245647f1270d7fdffbf00f06a79db95cd`.

El inventario histórico anterior se conserva. La consulta recursiva de GitHub devolvió 30,416 blobs y `truncated=true`: es un mínimo, no el total. El inventario completo reproducible se obtiene de un clon Git con `git ls-tree -r -z` sobre un commit explícito, sin checkout ni lectura de las corridas locales. No se obliga al investigador a ejecutar una revisión manual ni se modifica ningún caso.

## Registro

[FILE_REVIEW_LEDGER.jsonl](FILE_REVIEW_LEDGER.jsonl) es append-only: una línea por evento, con fecha, ref inmutable, ruta, blob, nivel, estado, alcance y evidencia. Niveles: content (lectura/revisión de contenido), metadata (inventario), validation (verificación específica). Estados: reviewed, updated, partial, blocked, reopen. Solo reviewed/updated de nivel content y alcance completo aplicable cierran una revisión de contenido; para una corrección registrar el blob resultante tras confirmar la versión, no el blob anterior como corregido. En este corte se registran versiones anteriores realmente inspeccionadas; los nuevos blobs permanecen pendientes hasta verificación. La revisión de una dependencia exige evento reopen para la ruta afectada aun si su blob no cambia. No registrar una afirmación sin evidencia. No confundir validación científica con lectura documental.

La cola incluye todos los blobs versionados, incluidos históricos y binarios. Archivos idénticos bajo rutas distintas se revisan en contexto; nunca duplicar una revisión del mismo par ruta/blob salvo reapertura justificada. El propio ledger es un registro append-only, excluido de la cola para evitar autorreferencia; su sintaxis se valida en cada lectura. Los archivos históricos no se reescriben para actualizar el presente. Los datos CFD nativos se verifican por formato, integridad y manifiesto cuando estén disponibles, sin alterar datos.

## Uso por agentes

Leer este archivo y el ledger antes de abrir archivos. El siguiente comando solo lee objetos Git y emite JSONL a stdout; elegir el ref explícito ya disponible (no pull ni checkout en worktrees activos):

```bash
python3 tools/file_review_queue.py --ref origin/main --limit 100
```

`--prefix docs/` filtra una carpeta; `--limit 0` emite toda la cola. El resumen va a stderr. Para registrar un evento, editar el ledger en un commit de documentación tras la revisión, incluyendo evidencia específica. El script no certifica que una revisión haya ocurrido.

Prioridad: (1) estados y documentación vigente; (2) scripts, diccionarios, configuraciones y pruebas; (3) evidencia y resultados por caso; (4) ramas de investigación y publicación, con refs explícitos; (5) documentación histórica. No cambiar física, mallas, resultados ni ramas históricas sin evidencia y alcance autorizado.

## Corte inicial

Se registran siete inspecciones reales, dos de alcance completo documental y cinco parciales. Se cruzaron seis manifiestos adaptativos con el estado (pasos 11028, 11029, 14275, 14276, 15012, 15013). Se corrigió la rotulación de encabezados antiguos, no las cifras históricas. No se ejecutó OpenFOAM, no se descargaron binarios ni se validó experimentalmente. El total de archivos aún no está determinado por el conector. El siguiente bloque prioriza las versiones nuevas de documentación y los estados propietarios, luego manuales y herramientas. No hay porcentaje global de tesis ni de revisión exhaustiva en este corte.

## Verificación poscommit y ramas históricas

Las versiones actualizadas de AGENTS.md y MAESTRIA_STATUS.json se verificaron contra el padre y tienen recibos nuevos. Para una rama histórica que no contiene el ledger, usar `--ref <rama-o-commit> --ledger-ref origin/main`; no hace checkout. Para otro alcance usar `--include-closed` y registrar reapertura justificada si corresponde. La prueba de regresión de la cola es sintética, no CFD; su ejecución queda pendiente de verificación.

## Nombre operativo: Uva

Cuando el investigador diga «Operación Uva» o «Uva», continuar la cola incremental en bloques independientes, consultar primero el ledger y registrar cada revisión por ruta/blob. Priorizar archivos vigentes cambiados, corregir incoherencias demostrables y conservar evidencia histórica. No reiniciar la auditoría ni repetir archivos cerrados sin reapertura justificada. Publicar el balance real de cada bloque y sus bloqueos; Uva no ejecuta CFD ni sustituye Granada.

## Modalidad combinada Uva + Granada

En el contexto de MasterProject, «Op Granada» durante Uva significa ampliar cada bloque de auditoría y corregir incoherencias demostrables, sin ejecutar CFD por defecto. Consultar primero los recibos vigentes; conservar datos y ramas históricas; usar refs inmutables en los nuevos recibos. Los recibos históricos con refs simbólicos se conservan, se identifican como no fijados y no se inventa un commit retrospectivo. Los cambios en una rama de investigación se registran en el ledger central con su rama y commit.

El resumen de `tools/file_review_queue.py` incluye `ledger_summary`: eventos, rutas únicas registradas, pares ruta/blob de contenido, estados más recientes y número de eventos sin ref fijado. No confundir estos valores con cobertura del árbol de un commit ni porcentaje de tesis. El total de árboles inspeccionados sigue dependiendo del ref elegido; el mínimo inicial de 30,416 blobs no es un denominador de cobertura global. Los contadores de MAESTRIA_STATUS.json pertenecen al corte inicial salvo indicación explícita; para cifras vigentes consultar el ledger.
