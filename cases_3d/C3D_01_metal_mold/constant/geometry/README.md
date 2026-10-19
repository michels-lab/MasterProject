# Superficies SolidWorks para snappyHexMesh en OpenFOAM Foundation v14

`prepare_geometry.py` almacena aquí `mold.stl` y `metal.stl` como **copias binarias idénticas** a los STL corregidos, sin alterar sus coordenadas en milímetros. Conservar el origen compartido es indispensable para el contacto metal–arena.

El futuro `snappyHexMeshDict` declarará `units [mm];` individualmente en las entradas `triSurfaceMesh`. OpenFOAM convierte en memoria estas superficies a la base SI [m]. No utilizar ninguna conversión adicional de 0.001 en estas mismas superficies.

Los STL son privados del investigador y se excluyen de GitHub; el manifiesto público sólo contiene hashes y dimensiones de referencia.
