# Validation Matrix — MasterProject

> **Estado C3D-01 actualizado al 10-11-2026:** la malla recortada metal+arena produjo **1,209,777 celdas y 151.230 cm³** (15 cóncavas, 8 face-tets deficientes, 17 determinantes pequeños; **3 fallos checkMesh**). `splitMeshRegions -disconnected` separó `region1` (**825,994 celdas, 103.256 cm³, 3 fallos**) y `region2` (**383,783 celdas, 47.9735 cm³, 2 fallos**) pero reportó **`No interfaces to add`**. No existe una interfaz CHT verificada, malla aceptada, solver CFD 3D ni validación experimental. `-cellZones 'metal'` **no se ha ejecutado**. [Scientific record](docs/C3D_01_ESTADO_REAL_20261110_ES.md). This is a language selector, not a validated result.


**Current evidence (10 Nov 2026):** [C3D-01 geometry and local meshing report](docs/C3D_01_ESTADO_REAL_20261110_ES.md) (mesh failed quality checks; no CFD validation). Historical V14 and B/C statuses remain independent.

- [Español](VALIDATION_MATRIX_ES.md)
- [English](VALIDATION_MATRIX_EN.md)
