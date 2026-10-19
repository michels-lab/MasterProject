# C3D-01 — QuickCup tridimensional: metal + molde de arena

**Estado científico:** PREPARADO / NO EJECUTADO EN OPENFOAM. **Etapa 1: únicamente malla de fondo.** Este caso es independiente de `cases_controlled_buoyancy/` (familias B/C en 2D). La rama 3D pertenece a la ruta C y toma como **referencia física futura C14**, sin copiar las ecuaciones todavía.

## Datos originales del investigador

Los archivos exactos de SolidWorks corregidos son `QuickCup(1).STL` (arena) y `metal(1).STL` (metal), binarios, exportados en **milímetros** y conservando su origen compartido. Ambos son superficies cerradas verificadas preliminarmente.

| Región | Tamaño exterior (X/Y/Z) | Triángulos | Volumen STL |
|---|---|---:|---:|
| Molde | 51.8 × 65.5 × 51.8 mm | 3084 | 102.843 cm³ |
| Metal | 36.5 × 40.0 × 36.5 mm | 3896 | 47.987 cm³ |

Por ser un repositorio **público**, los modelos STL originales no se publican aquí. El `geometry_reference.json` contiene los hashes SHA-256 y magnitudes esperadas, de manera que tu equipo pueda comprobar exactamente qué archivos utiliza. Los archivos STEP anteriores tenían un error de escala; **esta etapa se basa exclusivamente en la nueva exportación corregida**.

## Preparar en tu Ubuntu (sin CFD)

Desde tu clon del repositorio:

```bash
cd ~/OpenFOAM/QuickCup_Solidification
git pull --ff-only
```

Abre una terminal y accede a la carpeta del caso:

```bash
cd cases_3d/C3D_01_metal_mold
```

Copia los STL corregidos a tu carpeta local de descargas, por ejemplo `~/Downloads/QuickCup(1).STL` y `~/Downloads/metal(1).STL`. Ajusta esas rutas si usas `~/Descargas`.

```bash
python3 scripts/prepare_geometry.py \
  --mold "$HOME/Downloads/QuickCup(1).STL" \
  --metal "$HOME/Downloads/metal(1).STL"

source /opt/openfoam14/etc/bashrc
bash scripts/run_blockMesh_only.sh
```

El preparador compara **ambos hashes originales** y convierte las coordenadas de milímetros a metros **exactamente una vez**, sin desplazar ni reorientar las piezas ni sobrescribir tus STL originales. Valida las superficies y puntos interiores mediante `analysis_tools/preflight_c3d_stl.py`. Si los STL no coinciden con la referencia o ya existe una salida, se detiene.

El script de malla sólo ejecuta `blockMesh` y `checkMesh -allTopology -allGeometry`, crea `log.blockMesh` y `log.checkMesh.background`, y **se niega a sobrescribir una malla existente**. No llama a `Allrun`, `Allclean` ni al solver. Para un intento nuevo, usa una copia nueva del caso; no borres resultados existentes.

## Diseñamos juntos el diccionario

`system/blockMeshDict` define una caja cartesiana auxiliar:

| Eje | Mínimo [m] | Máximo [m] | Longitud [mm] | Celdas |
|---|---:|---:|---:|---:|
| X | -0.003 | 0.055 | 58 | 29 |
| Y | -0.069 | 0.003 | 72 | 36 |
| Z | -0.003 | 0.055 | 58 | 29 |

- **30,276 celdas hexaédricas de fondo**, nominalmente **2 mm** por lado, `simpleGrading (1 1 1)`.
- `convertToMeters 1;` porque todos los vértices del diccionario YA están en metros.
- `outerBox` es un parche temporal; **no** es una condición física de la pared de arena.
- Las seis caras tienen normales exteriores consistentes, cubiertas por una prueba estática automática.
- Los márgenes auxiliares de la caja no representan aire, arena adicional ni ningún otro material físico.

**Esta malla no resuelve el sólido ni distingue regiones.** No basta una comprobación favorable de `checkMesh` en la caja para afirmar que metal y arena estén mallados o térmicamente acoplados.

## Puertas de aceptación pendientes (no declararlas cerradas)

1. Ejecutar `blockMesh` + `checkMesh` en Ubuntu con OpenFOAM Foundation v14, conservar los logs y revisar `Mesh OK` y dimensiones efectivas.
2. Preparar juntos `snappyHexMeshDict`, captura de superficies y `cellZones`/regiones, **sin confiar en que dos STL bastan por sí solos para preservar la interfaz**.
3. Separar metal/arena, inspeccionar `checkMesh` de ambas regiones, áreas de interfaz, conectividad y orientaciones.
4. Configurar interfaces térmicas, BC 3D, gravedad, referencias de presión, propiedades y posición de termopares.
5. Implementar un caso físico C3D desde C14 sólo cuando lo anterior esté documentado; ejecutar CFD exclusivamente en la laptop del investigador.
6. Comparar conservación de masa/energía, malla, curvas de enfriamiento, fracción líquida, eventual recalescencia bajo interpretación física explícita.

Las pruebas GitHub son solamente estáticas/sintéticas, **nunca ejecutan OpenFOAM**. FoamLENS se desarrolla en paralelo y no es requisito para generar ni validar la malla en Ubuntu.

## Reproducibilidad

- `geometry_reference.json`: tamaño, checksums originales, volúmenes, coordenadas y semillas de regiones.
- `scripts/prepare_geometry.py`: transformación controlada de vértices STL mm → m y preflight.
- `scripts/run_blockMesh_only.sh`: malla y verificación locales sin borrar archivos.
- `scripts/test_c3d_background_case.py`: comprobaciones sintéticas de resolución, orientación y conversión.
- [Historial y decisiones](../../PROJECT_AUDIT_LOG_ES.md).
