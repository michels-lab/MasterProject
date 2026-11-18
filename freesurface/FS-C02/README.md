# FS-C02 — hierro fundido–aire (continuación de la familia B)

Caso correcto: **FS-C02 / B-FS-02**. Independiente de **FS-C01** (agua–aire), **B14** (hierro–molde original) y **C3D-02** (malla 3D activa).

Estado: **STAGING IMPLEMENTADO; SIN CFD Y SIN VALIDACIÓN FÍSICA**. El script analysis_tools/run_fs_c02_local.py convierte una COPIA de las entradas congeladas de FS-C01 (probadas con Foundation v14) en un banco VOF metal–aire. Consulta de solo lectura el archivo de material del caso B14 original. Nunca cambia las entradas originales.

## Física y propiedades provisionales

| Aspecto | Valor de prueba | Procedencia/limitación |
| --- | --- | --- |
| Fases | metal y air | VOF, sin fracción sólida |
| Solver | compressibleVoF Foundation 14 | Base FS-C01 |
| Dominio | 40 × 60 × 10 mm; 80 × 120 × 1 | Geometría de FS-C01, NO B14 |
| Metal inicialmente ocupado | 40 mm de altura | V inicial = 1.6e-5 m3 |
| Densidad metal | rhoConst = 6820 kg/m3 | rho0 de B14, NO rho(T,f_s) |
| Calor específico de prueba | eConst Cv = 827 J/(kg K) | Aproxima Cp de B14, NO termodinámica validada |
| Viscosidad metal | 0.0055 Pa s | B14 |
| Pr metal | 0.14 | B14 |
| T inicial | metal 1500 K, aire 300 K | Campo T zonal, sin acoplamiento con arena |
| Tensión superficial | 1.0 N/m | PROVISIONAL SIN VALIDACIÓN |
| Aire | modelo original FS-C01 | Sin alimentación, cavidad, ni gas de molde |
| Modelo de turbulencia | RAS kEpsilon y damping de FS-C01 | No calibrado para hierro |
| Horizonte temporal | 0–0.1 s | Smoke test, no solidificación |

Masa metálica esperada de la configuración: 1.6e-5 m3 × 6820 kg/m3 = **0.10912 kg**. Todavía NO medida desde solución CFD.

**Ausentes intencionalmente:** cambio de fase, calor latente, molde 3D/CHT, contracción, alimentación, microporosidad, recalescencia. No asumir que compressibleVoF junto con B14 implica shrinkage. El modelo térmico eConst utiliza Cv estimado desde Cp a modo de prueba y requerirá termodinámica/JMatPro trazable; la expansión por grafitización del hierro tampoco está representada.

## Procedimiento aislado en Ubuntu/WSL

Abrir otra terminal, no cerrar ni cambiar la rama del checkout ~/OpenFOAM/MasterProject usado por C3D-02. Tampoco reutilizar ~/OpenFOAM/FS_C01_WORKTREE.

    cd ~/OpenFOAM/MasterProject
    git fetch origin research/fs-c02-metal-air-vof-20261117
    git worktree add --detach ~/OpenFOAM/FS_C02_WORKTREE FETCH_HEAD
    cd ~/OpenFOAM/FS_C02_WORKTREE

Asegurar que la variable WM_PROJECT_VERSION sea 14. Si no lo es, activar Foundation 14 desde /opt/openfoam14/etc/bashrc (o la ubicación local real).

Primero preparar únicamente inputs; esto NO ejecuta CFD:

    python3 analysis_tools/run_fs_c02_local.py --stage-only

Para ejecutar smoke test en carpeta NUEVA, sin reciclar ni sobrescribir salidas anteriores:

    python3 analysis_tools/run_fs_c02_local.py

El ejecutor crea ~/OpenFOAM/FS_C02_RUNS/FS-C02_<UTC>_<id>/FS-C02 y logs FS-C02_blockMesh.log, FS-C02_checkMesh.log, FS-C02_foamRun.log; también FS-C02_RUN_STATUS.json. No ejecuta Allclean, ni modifica B14, FS-C01 o C3D-02.

Si falla la lectura de termodinámica o una BC, leer el log FS-C02_foamRun.log de ESA ejecución e identificar la causa; NO parchear los resultados ni afirmar un solver validado.

## Siguientes verificaciones científicas (NO realizadas)

1. Arranque de compressibleVoF con fluidos metal/aire y ecuaciones térmicas.
2. alpha.metal en [0,1], volumen en el tiempo, cambios de interfaz, campos rho/T/U/p_rgh.
3. Balance real de masa de metal por dominio y contornos. La integral de alpha.metal NO es masa.
4. Balance térmico y transferencia con molde en un siguiente caso, verificando compatibilidad con foamMultiRun + solid.
5. Modelo VoFSolidificationMelting y ley fracción sólida vs T validada, sin suponer implementación automática de shrinkage.
6. Introducir densidades por fase o volumen específico dependiente de T y f_s, cerrar masa y seguir eventual expansión por grafitización.
7. Porosidad y feeding son física adicional y requieren validación independiente.

Los tests del repositorio son solo sintéticos; NO ejecutan OpenFOAM ni prueban estos criterios físicos.
