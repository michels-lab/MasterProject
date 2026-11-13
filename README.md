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
