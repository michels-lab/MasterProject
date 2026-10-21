# Plan D — Casos tridimensionales de QuickCup

**Identificador oficial de caso: [case3d-01](case3d-01/README.md).**

La ruta científica Plan D investiga solidificación y transferencia térmica metal–arena en 3D, independiente de la ruta B de superficie libre [FS-C01](../freesurface/FS-C01/).

- **[case3d-01](case3d-01/README.md)**: documentación canónica, gate de geometría y huellas STL, auditoría de logs OpenFOAM y script que prepara **una copia externa y nueva** del caso de malla de fondo con los STL originales sin cambiarlos. No es todavía un caso CFD completo ni contiene públicamente los STL privados.
- **[C3D_01_metal_mold](C3D_01_metal_mold/README.md)**: ubicación técnica heredada de los archivos CAD/inputs de malla mientras están abiertos los PR #18 y #19. Este nombre de carpeta no sustituye el identificador canónico `case3d-01`. No mover ni duplicar silenciosamente sus datos hasta reconciliar dichos PR.

Ambos directorios se refieren a la **misma línea de investigación Plan D**, no a dos simulaciones ni a resultados distintos. `blockMesh`, `checkMesh`, `snappyHexMesh` y los cálculos CFD requieren ejecución y validación en el Ubuntu del investigador; GitHub Actions únicamente verifica datos e integridad estática.

**Escala:** `units [mm];` en OpenFOAM Foundation 14; conservar STL SolidWorks en mm sin convertirlos por Python. La meta propuesta de 0.5 mm nominal en volúmenes completos continúa **en revisión científica**, no es una resolución comprobada.
