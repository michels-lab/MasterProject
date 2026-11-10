# Carpeta heredada — no usar en OpenFOAM Foundation v14

> **Estado nativo verificado 10-11-2026:** el par `units [mm];` de `geometry` **ya se probó en `snappyHexMesh` Foundation 14** en el segundo ensayo local. Ambos STL fuente permanecen sin reescalar; el molde reparado tiene superficie cerrada. La malla castellated no aprobó `checkMesh`. Posteriormente, la copia recortada y separada en dos regiones sigue sin interfaz térmica conjugada ni CFD 3D. [Registro del ensayo](../../../../docs/C3D_01_ESTADO_REAL_20261110_ES.md).


El flujo C3D-01 vigente utiliza `constant/geometry/` con STL originales en milímetros y `units [mm]` dentro del diccionario experimental `snappyHexMeshDict`.

La antigua ruta `constant/triSurface/` queda obsoleta. No colocar STL en esta carpeta. Se mantiene temporalmente este aviso para evitar confusión en clones anteriores.
