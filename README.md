> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026:** el investigador ejecutó la ablación de STL v2 en OpenFOAM Foundation 14: **solo metal v2 → 1 celda metálica** (arena original 274,788, contacto residual de 3 caras); **solo arena v2 → 0 celdas de arena** (metal original 85,350, sin contacto). Por tanto, **las dos sustituciones producen colapso por separado**; las causas exactas en `snappyHexMesh` siguen sin demostrar. Se revisó además el caso original del doctor: `blockMesh` cuasi-2D con zonas de material desde los bloques, 6,400 celdas metal + 5,480 arena y 240 caras de contacto, **no** referencia CFD validada. Prioridad: diagnóstico de logs sin remallar y evaluación independiente de una posible malla multibloque conformante 3D, sin afirmar que esté implementada. **Sin solver 3D ni cambios a C14.** [Resultados de ablación](docs/C3D_02_ABLACION_STL_V2_20261118_ES.md) · [Caso doctor y alternativa](docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md) · [CSV de ensayos](docs/C3D_02_MESH_TRIAL_REGISTRY_20261118.csv).

> **18-11-2026 — Maestría / C3D02 diagnóstico objetivo de la nueva malla:** la malla global v2 tiene 589,821 celdas, pero se asignaron sólo 4 a metal y 4 a arena; 589,813 quedaron exteriores y no se generó contacto metal–arena. La causa inmediata es la clasificación `cellZones` en `snappyHexMesh`, no `splitMeshRegions`. Como ensayo verificable de geometría, se añadieron las variantes independientes `Allmesh --v2-metal-only`, `--v2-mold-only` y el orquestador `scripts/run_stl_v2_ablation.sh` con reporte y preservación de todas las pruebas anteriores. No se ejecutará CFD hasta recuperar los volúmenes y la interfaz reales. [Datos medidos y protocolo](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — C3D-02, hallazgo crítico de zona v2:** la corrida OpenFOAM con nuevos STL generó 4 celdas por material, 4 componentes inconexos y ningún parche hierro–arena. `checkMesh` falló en ambas regiones y **no se simuló**. Se mantiene congelada la malla fallida y se agregó `scripts/diagnose_stl_v2_zones.sh` para localizar el paso de pérdida desde los logs originales sin volver a mallar. [Evidencia medida](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — C3D-02 STL v2: diagnósticos en carpeta existente.** Los dos STL nuevos pasaron SHA y `surfaceCheck`, pero la nueva malla se detuvo al validar `metal_to_mold` como `mappedWall`. No se ha demostrado si es fallo físico de contacto, tipo de parche o parser. Corrección de etapa y modo nativo read-only `Allmesh --audit-stl-v2` incorporados para rescatar los parches reales y medir las dos mallas SIN recrear ni borrar `c3d-better-stl-v2` y SIN CFD. [Evidencia](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — C3D-02, nuevos STL definitivos de SolidWorks:** recibido `metalmm(2).STL` (hierro) y `QuickCupmm.STL` (arena), auditados en mm, con cierre y volúmenes correctos. Se registraron los SHA-256 de las versiones `metal_v2.stl` y `mold_v2.stl`, junto con `check_stl_v2.sh` y la prueba de mallado nativa `Allmesh --stl-v2` en carpeta nueva `c3d-better-stl-v2`. **Los dos STL binarios ya fueron subidos y verificados en `main`**, commit [`e8be4afe`](https://github.com/michels-lab/MasterProject/commit/e8be4afeae847411cd35b815f90748d71d1c5d90), dentro de `constant/geometry/`, preservando los originales. Se conservarán originales y C14; no CFD sin mallas aprobadas. [Inventario de fuentes](cases_3d/C3D_02_metal_sand_clean/constant/geometry/STL_V2_APPROVED_SOURCES.md).

> **17-11-2026 — C3D-02 `c3d - better`, resultado real:** repetición nativa reproducible pero sin mejora; hierro 4,834 cóncavas, 3 determinantes bajos; arena 14,951 cóncavas, 1 determinante bajo y 1 face-tet defectuoso. Fallaron 2 y 3 checks respectivamente: **no CFD**. Se corrigió un defecto del ensamblaje: los materiales C14 ahora se copian de manera verificable antes de la aceptación de malla, y se permite completar el caso existente con `Allmesh --stage-c14-better` sin remallado ni modificación física. [Detalle](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — Próximo C3D-02: `c3d - better`.** Se preparó la opción `Allmesh --better` para repetir en **carpeta nueva** `~/OpenFOAM/c3d-better` el mallado nativo L2 con `nSmoothPatch=3`, materiales y CAD idénticos, tabla comparativa `C3D_BETTER_COMPARISON.tsv` y revisión completa de ambas regiones. La denominación no equivale a malla mejorada ni CFD: sigue bloqueado `foamMultiRun` hasta validar calidad y condiciones de frontera 3D. [Bitácora](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — C3D-02, sensibilidad nativa ejecutada:** el ensayo `nSmoothPatch=6` **empeoró** la concavidad metal 4,834→5,004 y arena 14,951→15,079, sin eliminar checks fallidos; **rechazado, sin CFD**. Detectado y corregido un error de AWK que confundía el volumen mínimo de celda con el volumen total de la región y afectaba el control CAD. El reporte `Allmesh --compare` recalcula `CANDIDATE_COMPARISON_CORRECTED.tsv` **desde logs existentes, sin remallar**; ambas mallas históricas y las propiedades C14 permanecen intactas. [Bitácora detallada](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — C3D-02, primer ensayo controlado de mejora de malla:** tras confirmar con OpenFOAM los 6 VTK de defectos (hierro 2, arena 4), se añadió `Allmesh --candidate-smooth` para comparar **solo `nSmoothPatch: 3 → 6`**, mediante `foamDictionary`, en `~/OpenFOAM/C3D02_NATIVE_SMOOTH_01`. Produce `CANDIDATE_COMPARISON.tsv` para ambas regiones; conserva sin cambios la malla de referencia, geometría y materiales de C14. **Aún no ejecutado localmente y no se permite CFD con mallas rechazadas.** [Bitácora](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — Resultados reales `Allmesh --diagnose` C3D-02:** la malla metálica tiene **4,834 celdas cóncavas y 3 con determinante bajo** (85,350 celdas; 2 checks fallidos); la arena **14,951 cóncavas, 1 determinante bajo y 1 face-tet defectuoso** (274,788 celdas; 3 checks fallidos). Ambas regiones están conectadas y los volúmenes son cercanos al CAD. **Ninguna malla está aprobada; no CFD.** Se reforzó el diagnóstico nativo para generar VTK del hierro y la arena en **copias independientes** con `checkMesh`, sin Python ni remallado. [Bitácora detallada](docs/C3D_02_NATIVE_CHECKMESH_20261117_ES.md).

> **17-11-2026 — MasterProject C3D-02: prioridad a utilidades NATIVAS de OpenFOAM Foundation 14.** El flujo recomendado para la **etapa de malla** es `bash cases_3d/C3D_02_metal_sand_clean/Allmesh` (después de `git pull --ff-only`). Esta ruta ejecuta `foamDictionary`, `blockMesh`, `snappyHexMesh`, `splitMeshRegions` y `checkMesh` directamente, sin Python ni sustitución de las propiedades C14. `system/snappyHexMeshDict` ahora declara ambas zonas `metal` y `mold`. El constructor Python anterior queda como legado de experimentación, no como comando principal. **La nueva etapa nativa se ha programado, pero no se ha ejecutado ni validado en Ubuntu del investigador; NO hay CFD/CHT confirmado.** [Manual nativo y limitaciones](cases_3d/C3D_02_metal_sand_clean/README.md).

> **17-11-2026 — Localización automática permanente:** el comando integral de C3D-02 **siempre** crea `ERROR_ZONES.json` y `ERROR_ZONES.md` en su carpeta de entrega. Desde `PREFLIGHT`, registra el fallo; cuando existen mallas, ejecuta `checkMesh` con exportación de VTK **en copias**, identifica rangos XYZ y distribución axial de los defectos por material, sin scripts adicionales ni alterar los datos. No equivale a garantía de malla aprobada o CFD exitoso. [Regla para futuros casos](docs/AUTOMATIC_MESH_ERROR_LOCALIZATION_POLICY_ES.md). La coordinación inter-repos se registra en `michels-lab/OpenFOAM---PROJECTS` (no en Life Experience).

> **C3D-02 — Operación Granada 17-11-2026:** a petición del investigador, **no más scripts de prueba separados**. Un único comando intenta crear el CHT metal/arena: `cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py`. Genera un mallado común, regiones conformantes por `splitMeshRegions`, mappedWall recíprocos, verifica G1 y, solo si pasa, prepara C14 e inicia foamMultiRun. Guarda logs y `BUILD_STATUS.json` bajo `~/OpenFOAM/C3D02_DELIVERY_01`, sin sobreescribir resultados. **Ejecución/éxito CFD todavía no comprobados**. [Guía C3D02](cases_3d/C3D_02_metal_sand_clean/README.md).

> **15-11-2026 C3D-02:** `moldVolume` medido realmente por `foamPostProcess` en **103.409 cm³** (CAD 102.843 cm³; +0.550 %). A diferencia del volumen global 242.208 cm³, esta cifra corresponde únicamente a la zona de arena. [Extracción segura de moldVolume en copia](cases_3d/C3D_02_metal_sand_clean/scripts/extract_mold_zone_copy.sh) preparada y no ejecutada; `subsetMesh` no preserva automáticamente tipos de frontera. Todavía falta checkMesh de la zona extraída e interfaz metal-arena. [Bitácora](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **13-11-2026 — C3D-02:** se obtuvieron zonas geométricas de molde **`moldVolume` 274,788 celdas / `moldInterface` 97,492 caras** en L2 sin `snap`; el volumen global sigue siendo la caja de **242.208 cm³**, con 49,034 celdas cóncavas y un fallo de `checkMesh`. Preparada la [medición del volumen EXCLUSIVO de la zona](cases_3d/C3D_02_metal_sand_clean/scripts/measure_mold_zone_volume.sh) sin remallar ni CFD. [Registro técnico](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **C3D-02, 12-11-2026:** el cambio de `insidePoint` del molde a una posición fuera de cara **no corrigió el exterior retenido**: 568,134 celdas, 242.142 cm³ frente a 102.8431 cm³ CAD, `outerBox=15164`, 2 fallos de calidad. La malla del hierro conserva volumen correcto pero 2,422 celdas cóncavas. [Diagnóstico de fuga sin remallado](cases_3d/C3D_02_metal_sand_clean/scripts/inspect_mold_leak.sh) · [Bitácora](docs/C3D_02_DOS_MALLAS_20261112_ES.md). Sin CFD 3D ni CHT.

> **C3D-02, 12-11-2026:** el mallado independiente real de metal alcanzó **47.9621 cm³** frente a 47.9875 cm³ CAD y no retuvo exterior, pero falló por 2,422 celdas cóncavas. Mold retuvo exterior (**242.142 cm³**, `outerBox=15164`), 13,367 cóncavas y 10 face-tets. Se detectó que `insidePoint` de mold x=3 mm coincidía con una cara de la malla de fondo de 2 mm; [prueba única de arena con punto alejado de la cara](cases_3d/C3D_02_metal_sand_clean/scripts/try_mold_offface.sh), por ejecutar en Ubuntu. Ninguna malla aprobada ni CFD/CHT. [Bitácora detallada](docs/C3D_02_DOS_MALLAS_20261112_ES.md).

> **C3D-02 actualización 12-11-2026 — alternativa de dos mallas independientes preparada, NO ejecutada.** El primer mallado mezclado conservó 242.130 cm³ y exterior; ambos `insidePoints` sí pertenecían a sus STL correctos. Nuevo paso fuente: [mallas individuales metal + mold](docs/C3D_02_DOS_MALLAS_20261112_ES.md), con `run_material_meshes.sh`. No CHT ni solver 3D verificados.

> **12-11-2026: primera ejecución C3D-02 RECHAZADA:** `snappyHexMesh` generó 589,701 celdas con volumen 242.130 cm³ (vs. 150.831 cm³ para hierro+arena), `checkMesh` exhaustivo falló 2 verificaciones (14,586 cóncavas, 10 face-tets). No hubo exclusión del exterior ni acoplamiento CHT. **No relanzar sin diagnóstico**; comando de lectura `bash cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_mesh_readonly.sh`. [Registro](docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

> **12-11-2026, C3D-02 etapa de malla preparada:** nuevo diccionario Foundation 14 `insidePoints` hierro+arena y script de mallado aislado [run_mesh_only.sh](cases_3d/C3D_02_metal_sand_clean/scripts/run_mesh_only.sh). **Sin ejecución local confirmada; no CHT validado.** [Protocolo y criterios](docs/C3D_02_MALLADO_INICIAL_20261112_ES.md).

> **ACTUALIZACIÓN 2026-11-12 — Reinicio C3D:** la línea 3D de trabajo pasa a [C3D_02_metal_sand_clean](cases_3d/C3D_02_metal_sand_clean/README.md) (caso fuente limpio, **no simulado**). C3D-01 y sus carpetas temporales son **historial no validado, no borrar hasta respaldar**. Se reutiliza **sin cambiar valores** la física C14 (`castIron`, `silica`, `fvModels`, `g`, `pRef`); 3D requiere **dos sólidos, cero región de aire, malla y parches térmicos verificados**. [Decisión y evidencia](docs/C3D_REINICIO_20261112_ES.md) · [Lecciones OpenFOAM14](docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md). Sin CFD 3D ni validación física.

# MasterProject

> **Estado científico actualizado, 10-11-2026 — C3D-01:** recorte local metal + arena: **1,209,777 celdas; 151.230 cm³; 15 celdas cóncavas, 8 face-tets deficientes, 17 celdas de determinante pequeño; 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` separó `region1` (probable arena, **825,994 celdas; 103.256 cm³; 3 fallos**) y `region2` (probable metal, **383,783 celdas; 47.9735 cm³; 2 fallos**); **`No interfaces to add`**. **Sin interfaz CHT, sin CFD 3D ni malla aprobada.** El ensayo `-cellZones 'metal'` aún **NO** se ejecutó. [Evidencia](docs/C3D_01_ESTADO_REAL_20261110_ES.md) · [Manual](OPENFOAM_COMMAND_MANUAL_ES.md).


**MasterProject (formerly QuickCup-Solidification): Master's thesis simulation project.** multi-region casting/Quick-Cup solidification, conjugate heat transfer, buoyancy and enthalpy–porosity using **OpenFOAM Foundation v14**.

## 2026-10-08 research roadmap

[**Research plan: C15 adaptive, C16 phase relaxation, C3D and B free-surface/shrinkage**](NEXT_RESEARCH_ROADMAP_ES.md). B15/B16 and C15/C16 are prepared input-only cases, not simulated in GitHub or validated.

**Stage gate:** complete paired B/C studies through V16 first; then fork into C → 3D and B → metal-air free surface plus shrinkage/feeding. No GitHub-based CFD execution.

## New independent 3D research line — C3D-01

The first three-dimensional QuickCup mesh experiment lives in [`cases_3d/C3D_01_metal_mold`](cases_3d/C3D_01_metal_mold/README.md). It includes a 2 mm Cartesian `blockMeshDict`, native OpenFOAM Foundation v14 `units [mm]` in the background mesh, byte-identical SolidWorks STL staging for future `snappyHexMesh`, mesh-only shell script, region seeds, and static regression tests. **Prepared, not run in OpenFOAM; no 3D CFD results yet.** User CAD/STL data remain local because this repository is public.

See also the [3D case index](cases_3d/README.md). The existing C14 and B/C numerical research runs remain unchanged.

## Scientific agents and postprocessing

**Execution ownership:** all CFD runs occur on the user's laptop. The repository runs no CFD and only audits results after git push.

- [Postprocessing field and function-object guide (Spanish)](POSTPROCESSING_FIELD_GUIDE_ES.md)
- [Initial scientific results from the 2026-10-15 laptop push](analysis_results/v15_v16_postpush_20261015/README.md) — five cases have data to 10 seconds, but are not yet physically/experimentally audited.
- [V15/V16 controlled-input preflight (read-only)](analysis_tools/preflight_sensitivity_cases.py) — verifies B15/B16/C15/C16 provenance and single-variable changes before laptop runs; [evidence report](analysis_results/v15_v16_preflight/README.md).
- [Post-push evidence auditor (read-only)](analysis_tools/audit_pushed_results.py) — checks files already pushed from the user's laptop
- [Static OpenFOAM14 function-object auditor](analysis_tools/audit_postprocessing_config.py)
- [GitHub post-push/manual/scheduled audit workflow](.github/workflows/quickcup-research-audit.yml) — checks committed evidence only, never launches CFD; verify actual Actions success.
- [Specialized scientific agent roles](.github/agents/quickcup-postprocess-forensics.agent.md)

## Start here — all future runs and audits

1. [**RUN_MASTER_PROTOCOL.md — required between-run update checklist**](RUN_MASTER_PROTOCOL.md)
2. [**RUN_CASE_REGISTRY.csv — 30-case status and audit coverage**](RUN_CASE_REGISTRY.csv)
3. [Project audit log (ES/EN)](PROJECT_AUDIT_LOG.md)
4. [Validation matrix (ES/EN)](VALIDATION_MATRIX.md)
5. [Case guide in Spanish](CASE_GUIDE_ES.md)
6. [JMatPro → OpenFOAM traceability](JMATPRO_OPENFOAM_TRACEABILITY_ES.md)

## Coverage at 2026-10-08

- 34 controlled-case directories: **29 verified** and **5 prepared/not run** (`B11_energy2_test`).
- [Historical full-campaign audit](analysis_results/full_campaign_audit/README.md) covers **26 cases only**, not all currently verified cases.
- Additional independently verified results: [V14 B/C comparison](analysis_results/v14_bc_comparison/summary.md) and [C11 two-energy-corrector controlled test](analysis_results/c11_energy2_test/summary.md).
- Current baseline for future fixed-volume experimental validation: `C14_topFixedFlux_explicitRef`; historical frozen reference: C11; JMatPro provenance gate **J0 open**.

**Do not treat a successful run, old copied output, or `git push` alone as a completed scientific audit.** Follow the protocol and preserve the distinction between numerical verification and experimental validation.

Repository guidance lives here, not in a separate Michel's Lab main repository.

## GRANADA — Regla permanente de continuación del propietario

Cuando el propietario diga **GRANADA**, se aparca con trazabilidad cualquier pendiente inacabado/bloqueado/en QA/propiedad de otra rama, y se aborda **el siguiente bloque grande independiente**. Consultar primero `.michelslab/GRANADA.md` y la norma maestra `standards/GRANADA_CONTINUOUS_BLOCK_PROTOCOL.md`; respetar claims, PRs y colisiones de archivos. Registrar SHA, tests y punto de retorno; no cerrar pendientes falsamente ni publicar releases sin autorización.

## Documentation map and independent OpenFOAM ecosystem

- [Manuals, scientific protocols, results and audit logs](docs/DOCUMENTATION_INDEX.md).
- [Canonical MasterProject identity and preserved historical case names](docs/MASTERPROJECT_IDENTITY_ES.md).
- [Optional FoamLens interoperability and independent-project boundaries](docs/OPENFOAM_ECOSYSTEM.md).

All scientific evidence, original manuals and OpenFOAM runs remain owned by this repository. FoamLens and any coordination hub are **optional**, not runtime dependencies.
