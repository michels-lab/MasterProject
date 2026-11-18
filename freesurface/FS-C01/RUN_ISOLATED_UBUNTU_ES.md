# FS-C01 / B-FS-01 — ejecución AISLADA en Ubuntu (OpenFOAM Foundation 14)

Fecha: 2026-11-17. Estado: **RUNNER PREPARADO, NO EJECUTADO EN LA LAPTOP, CFD NO VALIDADO**.

**IDENTIFICADOR DE ESTE PROCEDIMIENTO: FS-C01.** Solo el análogo **agua–aire** de superficie libre. No es hierro fundido, ni contracción, ni solidificación, ni CHT, ni alimentación, ni porosidad. El proyecto 3D que puede estar ejecutándose en paralelo es **C3D-02** y **NUNCA** se toca aquí.

## Separación física y de rutas (obligatoria)

| Propósito | Identificador | Ruta |
| --- | --- | --- |
| Caso fuente congelado de superficie libre | **FS-C01** | freesurface/FS-C01/ dentro del worktree alternativo |
| Worktree Git exclusivo para FS-C01 | **FS-C01** | ~/OpenFOAM/FS_C01_WORKTREE/ |
| Salidas nuevas de FS-C01 | **FS-C01** | ~/OpenFOAM/FS_C01_RUNS/FS-C01_timestamp_id/ |
| Proyecto de mallas y CHT tridimensionales | **C3D-02** | ~/OpenFOAM/MasterProject/cases_3d/C3D_02_metal_sand_clean/ |

No ejecutar Allclean, Allrun, blockMesh, snappyHexMesh o foamRun a mano desde el árbol cases_3d/ para este procedimiento; **no cambiar de rama en el checkout que usa C3D-02**. Los recursos CPU/RAM de las dos líneas sí pueden competir si se ejecutan simultáneamente: monitorizar por separado.

## Primera ejecución: worktree aislado (sin cambiar el checkout 3D)

Abrir una terminal nueva en Ubuntu/WSL, separada de la terminal donde corre C3D-02:

    cd ~/OpenFOAM/MasterProject
    git fetch origin research/fs-c01-isolated-execution-20261117
    git worktree add --detach ~/OpenFOAM/FS_C01_WORKTREE FETCH_HEAD
    cd ~/OpenFOAM/FS_C01_WORKTREE

Activar el entorno **OpenFOAM Foundation 14** si la terminal no lo tiene cargado:

    source /opt/openfoam14/etc/bashrc
    echo "$WM_PROJECT_VERSION"

El valor debe ser 14. Si tu instalación tiene otra ruta para bashrc, usar la real. No utilizar OpenFOAM 13 ni una instalación de otra familia.

Preflight de integridad **FS-C01** (20 archivos SHA-256, sin mallas ni ejecución):

    python3 analysis_tools/run_fs_c01_local.py --preflight

Ejecución aislada FS-C01, en un directorio externo de nueva creación:

    python3 analysis_tools/run_fs_c01_local.py

El programa crea un ID FS-C01_YYYYMMDDTHHMMSSZ_sufijo y solo dentro de esa carpeta ejecuta, por orden:

1. blockMesh — construye la malla desde los archivos FS-C01 copiados.
2. checkMesh -allGeometry -allTopology — requiere retorno 0, marcador Mesh OK. y ausencia de Failed N mesh checks, incluso si checkMesh devolvió 0.
3. foamRun — requiere retorno 0 y marcador End; si falla, NO se realiza auditoría ni se afirma que corrió satisfactoriamente.
4. Auditor de volumen de agua original — verifica procedencia SHA-256, tiempo inicial/final y deriva de integral VOF. No mide todavía masa.

Si cualquier gate falla, el programa se detiene y conserva la copia/los logs. **No intenta reparar ni reiniciar C3D-02, ni sobreescribir salidas anteriores.**

## Archivos creados para cada ejecución FS-C01

    ~/OpenFOAM/FS_C01_RUNS/
      FS-C01_2026..._id/
        FS-C01/                    # copia de los 20 inputs + manifiesto
          0/
          constant/
          system/
          BFS01_MANIFEST.json
        FS-C01_RUN_STATUS.json     # estado real de cada etapa; nunca marca contracción
        logs/
          FS-C01_blockMesh.log
          FS-C01_checkMesh.log
          FS-C01_foamRun.log
          FS-C01_volumeAudit.log
        FS-C01_VOLUME_AUDIT/       # solo si pudo ejecutarse la auditoría

Si solo deseas preparar el caso, sin usar CPU para CFD:

    python3 analysis_tools/run_fs_c01_local.py --stage-only

**Nunca se ejecuta directamente sobre freesurface/FS-C01/ ni sobre una carpeta cases_3d/.**

## Evidencia y límites

Para revisar un error, compartir el FS-C01_RUN_STATUS.json y el archivo logs/FS-C01_etapa.log de esa misma ejecución, indicando siempre el identificador FS-C01. No usar logs de C3D-02 como evidencia de FS-C01.

Incluso con FS_C01_VOLUME_SCREEN_PASSED_MASS_NOT_VERIFIED solamente se ha superado un cribado de **volumen de agua VOF**; siguen **ABIERTOS** el balance de masa por fase, límites de alpha, coherencia hidrostática y energía. No constituye validación de contracción. El cambio a metal/aire y la ley rho(T, fracción sólida) requieren un caso posterior distinto y propiedades trazables; FS-C01 permanece congelado como benchmark.

**QA del repositorio**: los tests de Python y GitHub Actions son estáticos/sintéticos; no se ejecuta CFD desde GitHub.


## Reintento posterior al fallo real de `writeFields` (2026-11-17)

La primera ejecución local `FS-C01_20261118T001239Z_656d1a84` pasó `blockMesh` y `checkMesh` y falló al inicializar `foamRun`: faltaba `writeFields` en `system/functions!waterVolume`. La corrección se realiza **en el caso fuente y generador de FS-C01**, no editando el expediente fallido. Si el worktree `~/OpenFOAM/FS_C01_WORKTREE` YA existe, **NO** ejecutar `git worktree add` otra vez.

Desde una terminal nueva y sin cambiar la carpeta `~/OpenFOAM/MasterProject` que usa C3D-02:

    cd ~/OpenFOAM/FS_C01_WORKTREE
    git status --short
    git fetch origin research/fs-c01-isolated-execution-20261117
    git switch --detach FETCH_HEAD
    python3 analysis_tools/run_fs_c01_local.py --preflight
    python3 analysis_tools/run_fs_c01_local.py

Nota: antes de ejecutar, `echo "$WM_PROJECT_VERSION"` debe mostrar `14`; el ejecutor lo exige. `git switch` debe hacerse **solo** si `git status --short` no revela ediciones locales que el investigador necesite conservar. Se crea automáticamente un nuevo identificador de corrida FS-C01 y nunca se reusa ni limpia la anterior. Detenerse y compartir el nuevo `FS-C01_RUN_STATUS.json` ante cualquier error.
