# Carpeta heredada — no usar en OpenFOAM Foundation v14

El flujo C3D-01 vigente utiliza `constant/geometry/` con STL originales en milímetros y `units [mm]` dentro del futuro `snappyHexMeshDict`.

La antigua ruta `constant/triSurface/` queda obsoleta. No colocar STL en esta carpeta. Se mantiene temporalmente este aviso para evitar confusión en clones anteriores.
