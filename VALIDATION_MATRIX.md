> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119 — REGLA PERMANENTE PARA TODOS LOS CASOS:** entregar hitos integrales con QA interno y corrección de raíz, sin muchas pruebas WSL por pieza; comunicar SIEMPRE **ETAPA + AVANCE + evidencia + bloqueo + siguiente hito**. Caso B C3D-05: **etapa 3/7 T0; 2/7 hitos = 29% técnico** (NO tesis, CFD o validación). CAD/HEX8 y contacto aceptados; 1,826 caras >70°; T0 preparado, faltan propiedades físicas y no se ha ejecutado. [Política](docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [estado canónico](docs/PROJECT_STAGE_STATUS.json). La evidencia histórica permanece intacta.

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026:** 3D C3D-02 Native Foundation14 **meshing experiments ran but failed** (metal-v2-only: 1 metal cell / 274,788 mold; mold-v2-only: 85,350 metal / **0** mold). `foamMultiRun` was **not** run, coupled CHT contact and 3D validation remain **OPEN**. Master's CSV `PREPARED_NOT_RUN` labels the **CFD** status, whereas [3D mesh-trial CSV](docs/C3D_02_MESH_TRIAL_REGISTRY_20261118.csv) labels actual mesh runs. [Scientific evidence](docs/C3D_02_ABLACION_STL_V2_20261118_ES.md) · [doctor's quasi-2D conformal blockMesh](docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md).

> **2026-11-12:** New clean C3D-02 case [source](cases_3d/C3D_02_metal_sand_clean/README.md) inherits C14 input physics without simulation. Historical 3D meshing still fails validation. [Updated evidence](docs/C3D_REINICIO_20261112_ES.md) and [OpenFOAM 14 command lessons](docs/OPENFOAM14_LECCIONES_C3D_20261112_ES.md).

# Validation Matrix — MasterProject

> **Estado C3D-01 actualizado al 10-11-2026:** la malla recortada metal+arena produjo **1,209,777 celdas y 151.230 cm³** (15 cóncavas, 8 face-tets deficientes, 17 determinantes pequeños; **3 fallos checkMesh**). `splitMeshRegions -disconnected` separó `region1` (**825,994 celdas, 103.256 cm³, 3 fallos**) y `region2` (**383,783 celdas, 47.9735 cm³, 2 fallos**) pero reportó **`No interfaces to add`**. No existe una interfaz CHT verificada, malla aceptada, solver CFD 3D ni validación experimental. `-cellZones 'metal'` **no se ha ejecutado**. [Scientific record](docs/C3D_01_ESTADO_REAL_20261110_ES.md). This is a language selector, not a validated result.


**Current evidence (10 Nov 2026):** [C3D-01 geometry and local meshing report](docs/C3D_01_ESTADO_REAL_20261110_ES.md) (mesh failed quality checks; no CFD validation). Historical V14 and B/C statuses remain independent.

- [Español](VALIDATION_MATRIX_ES.md)
- [English](VALIDATION_MATRIX_EN.md)
