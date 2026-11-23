# Protección real de corridas concurrentes — OpenFOAM C3D04-A, C3D05-B, contracción FS

## VERIFICACIÓN REAL WSL: AISLAMIENTO A/B/CONTRACCIÓN COMPLETADO (23-11-2026)

**Estado operativo observado:** `APPLIED_AND_VERIFIED`. Evidencia: salida completa de terminal proporcionada por el investigador tras ejecutar `git fetch origin` y `git show origin/main:tools/isolate_active_openfoam_cases.py | python3 -B - --apply`. No es un resultado inferido exclusivamente de CI.

- `~/OpenFOAM/C3D04_A_WORKTREE` — `refs/heads/work/c3d04-a-isolated`, `EXISTING_PRESERVED`, `HEAD=4d11e7bb3339e10db8329cbcd0674b1db2bc49f7`.
- `~/OpenFOAM/C3D05_B_WORKTREE` — `refs/heads/work/c3d05-b-isolated`, `EXISTING_PRESERVED`, `HEAD=4d11e7bb3339e10db8329cbcd0674b1db2bc49f7`.
- `~/OpenFOAM/FS_C02_WORKTREE` — `detached=true`, `branch=null`, `EXISTING_PRESERVED`, `HEAD=437bf13c3265d6ac1507cee20436b32669ed740d`; ascendencia verificada contra `refs/remotes/origin/research/fs-c02-metal-air-vof-20261117`. Su HEAD no se cambió.
- Snapshot remoto de creación de A/B: `origin/main=4d11e7bb3339e10db8329cbcd0674b1db2bc49f7`.
- Las NUEVE carpetas protegidas figuran `exists=true`: `C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01`, `C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01`, `C3D04_A_C14_3D_VOLUMETRIC_POSTPROCESS_01`, `C3D05_T0_C14_SHK_01`, `C3D05_STEP_GMSH_PILOT_01`, `FS_C01_RUNS`, `FS_C05_VOF_CHT_RUNS`, `FS_C06_RUNS` y `FS_C07_RUNS`.

**Límite de evidencia:** `exists=true` demuestra presencia de directorios, no integridad de cada archivo, finalización de todos los postprocesos, corrección física ni estado actual del proceso CFD. El instalador únicamente verificó y creó worktrees; no ejecutó CFD ni inspeccionó campos termofísicos. Esta puerta de **aislamiento operativo** sí está cerrada, pero NO suma hitos de investigación. A continúa en etapa 7/10, 6/10 (60 %); B en etapa 3/7, 2/7 (29 %); el avance científico FS no se deduce de esta ejecución.

**Regla de continuidad:** NO volver a pedir instalar estos worktrees. Antes de cualquier modificación, usar el worktree preciso del caso y revisar su HEAD; no se hará `git pull` en `~/OpenFOAM/MasterProject` para actualizar solo un caso, ni `git switch` en FS_C02_WORKTREE. La copia de ejecución independiente seguirá siendo la fuente para postprocesar campos ya calculados.

---

**23 de noviembre de 2026 · Contrato operacional del investigador · No altera física CFD.**

## Problema de origen

Un git pull en MasterProject actualiza **todos** los archivos rastreados de la rama extraída, no solamente el caso cuyo nombre se menciona en el mensaje. Esto incluye los directorios cases_3d/C3D_04_..., cases_3d/C3D_05_..., freesurface y los postProcessing/logs que estén versionados. Si un solver, compilación o diagnóstico está LEYENDO configuraciones desde esa misma ruta, un pull podría alterar los archivos fuente durante su ejecución, incluso si los resultados finales están en otro directorio. Por otra parte, un pull no borra automáticamente carpetas no rastreadas externas a MasterProject.

**La separación de las carpetas de resultados y la separación de los árboles Git son DOS controles diferentes y obligatorios.** Git worktree por sí solo no congela una corrida si se le cambia el diccionario a mitad de ejecución; para cada CFD conservar una COPIA DE EJECUCIÓN INDEPENDIENTE de la versión de sus entradas.

## Estructura protegida y comprobable

- Desarrollo Caso A, nueva rama local sin upstream: ~/OpenFOAM/C3D04_A_WORKTREE, branch work/c3d04-a-isolated; fuente cases_3d/C3D_04_rounded_multiblock_pilot.
- Desarrollo Caso B, nueva rama local sin upstream: ~/OpenFOAM/C3D05_B_WORKTREE, branch work/c3d05-b-isolated; fuente cases_3d/C3D_05_step_gmsh_conformal.
- **Contracción:** ~/OpenFOAM/FS_C02_WORKTREE. Su código procede de research/fs-c02-metal-air-vof-20261117, pero en el equipo real se usó `git switch --detach FETCH_HEAD`; por tanto, el checkout puede estar legítimamente en **detached HEAD**, no sobre la rama local. El instalador comprueba que Git lo registre en la ruta prevista, que comparta repositorio, que su HEAD tenga el archivo FS-C06 versionado y que el commit detached sea antecesor de la rama remota de investigación. **No conecta, reescribe, cambia ni actualiza HEAD**. La referencia remota puede avanzar mientras la copia de ejecución queda fija.
- Checkout central compartido: ~/OpenFOAM/MasterProject, permanece SIN checkout, merge ni pull automático.
- Ejecución 3D-A preservada: ~/OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01.
- Ejecución 3D-B preservada: ~/OpenFOAM/C3D05_T0_C14_SHK_01.
- Corridas FS-C01/05/06/07: ~/OpenFOAM/FS_C01_RUNS, FS_C05_VOF_CHT_RUNS, FS_C06_RUNS, FS_C07_RUNS. No inferir que cada una está activa ahora: son ejemplos de expedientes existentes.
- Los archivos de resultados versionados dentro de MasterProject (postProcessing, logs) siguen bajo el comportamiento ordinario de Git. Debe evitarse editar o actualizar esa rama durante un solver que utilice esos archivos.

**Atención:** todos los worktrees comparten los objetos Git, refs remotas y metadatos de worktrees, PERO cada uno dispone de HEAD, índice y archivos extraídos propios. Por eso se aíslan las ACTUALIZACIONES DEL ÁRBOL DE TRABAJO; no son repositorios Git enteramente separados. Crear A/B desde origin/main es una fotografía del origen descargado, no una promesa de que las tres ramas sean idénticas en el futuro.

## Instalación sin git pull del checkout principal

**UNA invocación integrada**. Esta receta descarga referencias con fetch (NO actualiza archivos extraídos) y lee la herramienta directamente desde origin/main, sin pull sobre MasterProject. Ejecútese en bash/WSL:

    set -o pipefail
    git -C "$HOME/OpenFOAM/MasterProject" fetch origin &&
      git -C "$HOME/OpenFOAM/MasterProject" show origin/main:tools/isolate_active_openfoam_cases.py |
      python3 -B - --repo "$HOME/OpenFOAM/MasterProject" --apply

Con fetch se actualizan referencias Git, no la carpeta fuente que ejecuta un CFD. El script hace PREFLIGHT DE LOS TRES caminos antes del primer cambio. Solo llama git worktree add para los A/B ausentes, usando --no-track (sin upstream) para que un git pull simple desde estos worktrees no haga una fusión accidental. Si una carpeta existe pero no es el worktree reconocido, una rama está ocupada o la procedencia del HEAD experimental no se puede verificar, **SE DETIENE, sin borrar, mover, reasignar, force, reset, clean ni prune**. Un FS `detached HEAD` con código versionado y ascendencia de la rama remota **sí es válido**. El rechazo previo `contraction: unexpected existing worktree/branch` fue causado por asumir erróneamente que el worktree de investigación siempre debía mantener una rama local conectada. No repetir ese control.

**Para ver el plan, sin instalar worktrees**, cambiar el argumento final --apply por --plan.

**Para auditar luego**, cuando la herramienta esté presente en alguno de los worktrees:

    python3 -B ~/OpenFOAM/C3D04_A_WORKTREE/tools/isolate_active_openfoam_cases.py --repo ~/OpenFOAM/MasterProject --plan

Los resultados son JSON con rutas, ramas, hashes de la fuente de los A/B y presencia de carpetas CFD, sin subir resultados privados. Un segundo --apply es idempotente: solo verifica, no reescribe ni recrea worktrees.

## Política de actualización obligatoria desde ahora

1. **No más comandos genéricos "cd ~/OpenFOAM/MasterProject && git pull && foam..."** mientras los tres casos puedan estar corriendo. El agente debe producir una orden específica para la rama/caso correcto, y leer primero estado/bitácora de ese caso. Tampoco debe ejecutar worktree remove/prune, git reset --hard, git clean -fdx ni borrar archivos de otras corridas.
2. Solo se permite cambiar una rama de desarrollo cuando no haya solver o herramienta de procesamiento leyendo directamente sus archivos; los CFD ya materializados en carpeta fuera del worktree permanecen inmutables.
3. Para inspeccionar actualizaciones sin cambiar archivos: git fetch origin; git -C ~/OpenFOAM/C3D04_A_WORKTREE diff --name-status HEAD..origin/main; equivalente para B. Para contracción comparar exclusivamente con su propia rama research/fs-c02-metal-air-vof-20261117, **NO con main**.
4. **Nunca ejecutar un pull/rebase/reset sobre FS_C02_WORKTREE** mientras contracción pueda estar corriendo; sus avances siguen en su rama experimental. No integrar FS-C02 a A ni a B por defecto.
5. Para actualizar un caso una vez parado y verificado, revisar el diff y decidir una integración explícita a la rama de ese caso. El instalador no hace esta actualización. Las ramas A/B creadas no tienen upstream: un pull sin argumentos no tiene destino implícito.
6. Para las próximas corridas, el solver deberá recibir solo su propia carpeta materializada fuera de cualquier worktree, con copia completa de controlDict/fvModels, propiedades, malla y SHA de entrada; nunca enlaces simbólicos a archivos vivos del repo.
7. No modificar valores de C14, JMatPro, flujo, interfaz, contracción, malla aprobada ni resultados CFD como parte de este cambio. El aislamiento de Git NO suma hitos científicos.

## Puertas verificadas y pendientes

Código añadido: tools/isolate_active_openfoam_cases.py. Se prueba con repositorios Git LOCALES DESECHABLES reales: inicialización remota, 3 ramas, instalación A/B, branch FS preexistente, sin upstream, HEAD inalterado, centinelas simulados de resultados y untracked en checkout principal, segundo apply idempotente, negativa a sobrescribir destino y negativa a recrear una contracción ausente. Workflow: .github/workflows/wsl-concurrent-cfd-worktrees-safety.yml.

**La suite CI solo demuestra comportamiento del instalador con repositorios Git sintéticos. No certifica haber accedido a la laptop, que una corrida esté activa, que la fuente real de los solvers carezca de symlinks o que las carpetas A/B ya existan físicamente en WSL.** La salida real del instalador servirá de evidencia para cerrar SOLO el hito operativo de separación, sin alterar el estado científico de A/B/FS.
