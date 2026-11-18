# C3D-03 — Piloto 3D conformante inspirado en el caso del doctor

**Estado 18-11-2026:** `blockMeshDict` y ejecutor **CREADOS en GitHub, NO ejecutados en Ubuntu**. (estado histórico previo a la ejecución; ver actualización arriba) El piloto **no reemplaza** al caso principal `C3D_02_metal_sand_clean`, ni los dos STL de SolidWorks, ni el caso `doctor_original/cht`. Es un ensayo **solo de topología y calidad**, sin `snappyHexMesh`, sin Python generador, sin termofísica, sin `foamMultiRun` ni CFD.

## Hallazgo geométrico: fuente real, no suposición de sección circular

Se inspeccionaron directamente los datos binarios de los STL oficiales `metal_v2.stl` y `mold_v2.stl` que GitHub conserva por SHA. Cortes del metal (Y constante, X/Z en mm):

| Y (mm) | Área CAD de corte del metal (mm²) | Ancho X/Z aproximado (mm) |
|---:|---:|---:|
| -39.999 | 799.64 | 28.278 |
| -38 | 1091.567 | 33.116 |
| -35 | 1113.120 | 33.444 |
| -20 | 1202.446 | 34.754 |
| -5 | 1295.204 | 36.064 |
| -0.01 | 1326.822 | 36.50 |

Las secciones son cuadrados ligeramente redondeados con conicidad y un redondeo pronunciado cerca de la base del metal. **No son cilindros**. El molde exterior se ensancha aproximadamente desde 46.08 mm a Y=-65.5 hasta 51.8 mm en Y=0. El molde incluye una abertura inferior **rectangular, NO cuadrada**, de 22.5 mm en X y 27.5 mm en Z, con X=14.65–37.15 y Z=10.86–38.36, que abre desde Y=-65.5 hasta Y=-56 mm. El espacio abierto no se modela como tercera región CFD.

El STL metálico tiene una superficie total de 7,679.519 mm², de los cuales ~1,326.886 mm² corresponden a la tapa superior y ~6,352.634 mm² a laterales + fondo (contacto físico CAD estimado, suponiendo toda esa superficie en contacto con el molde). Es una referencia geométrica a contrastar con el área que produzca la malla.

**Fuente CAD autorizada**: `../C3D_02_metal_sand_clean/constant/geometry/STL_V2_APPROVED_SOURCES.md`. Metal 47,987.697 mm³ y molde 102,843.333 mm³.

## Idea tomada literalmente del doctor

`doctor_original/cht/system/blockMeshDict` demuestra que el doctor construyó **metal y molde con vértices/caras compartidos desde `blockMesh`**, y cada bloque nombró su `cellZone`. El caso antiguo era cuasi-2D con `empty`; este piloto **sí** posee celdas en las tres direcciones y ningún parche `empty`. Las `cellZones metal/mold` se asignan directamente al declarar los bloques, no a partir de intersecciones de STL. `splitMeshRegions` separa el único `polyMesh` después.

## Diseño del piloto (volúmenes analíticos, todavía no datos `checkMesh`)

El diccionario es **una aproximación 3D escalonada en Y y de secciones rectangulares**. Usa 6 estaciones Y: -65.5, -56, -40, -38, -20, 0 mm. Las caras compartidas entre bloques usan los mismos índices globales. La apertura inferior se conserva y la base del metal descansa sobre arena a Y=-40 mm. Se incluyen paredes exteriores, tapa metal, tapa molde, paredes del hueco inferior y su techo; no hay aire volumétrico.

| Magnitud | Piloto geométrico estático | Referencia STL v2 | Diferencia |
|---|---:|---:|---:|
| Volumen metal | **48,011.916 mm³** | 47,987.697 mm³ | **+0.0505 %** |
| Volumen arena | **103,169.142 mm³** | 102,843.333 mm³ | **+0.3168 %** |
| Geometría | 24 bloques / 48 vértices | triangulación CAD | Aproximación, no copia exacta |
| Celdas previstas | **2,368 metal + 7,680 arena = 10,048** | no aplicable | Predicción discretizada |
| Contacto previsto | **1,248 caras por región**, incluidas 64 de la base | superficie CAD metal-laterales-fondo ~6,352.634 mm² | Conteo esperado, área aún sin medir en OpenFOAM |

**Los números del piloto son cálculos previos sobre el `blockMeshDict`, NO estadísticas de malla ejecutada.** La aproximación en secciones cuadradas no reproduce perfectamente los redondeos/esquinas del SolidWorks y no debe reemplazar el STL final hasta demostrar fidelidad geométrica (incluida área de contacto) y calidad de malla. El primer ensayo es de baja resolución para comprobar conectividad y zonas, **no** independencia de malla.

## Comando único de prueba en Ubuntu WSL / Foundation 14 (NO CFD)

Desde la carpeta raíz del repositorio, luego de sincronizar con Git:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_03_doctor_multiblock_pilot/Allmesh
```

El ejecutor:
- Verifica SHA de ambos STL v2 **sin modificarlos**.
- Rechaza carpetas de salida existentes. Por defecto entrega en `~/OpenFOAM/C3D03_DOCTOR_MULTIBLOCK_PILOT_01`; permite elegir **una ruta absoluta nueva** mediante `C3D03_OUT=/ruta/nueva`.
- Ejecuta solamente `blockMesh`, `checkMesh` del padre, `splitMeshRegions -cellZones 'metal mold' -noFields` y `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` en las dos regiones.
- Comprueba `mappedWall` recíprocos, el conteo esperado de 1,248 caras por región, volumen CAD ±2 %, número de celdas, conectividad, `Mesh OK` y ausencia de checks fallidos. Mantiene logs aunque rechace la malla.
- **No ejecuta** `foamMultiRun`, no prepara campos físicos 3D ni altera `C14` o las carpetas históricas.

Archivos útiles del resultado local: `log.blockMesh`, `log.checkMesh.parent`, `log.splitMeshRegions`, `log.checkMesh.metal`, `log.checkMesh.mold`, `PILOT_MESH_REPORT.tsv`, `PILOT_INTERFACE_REPORT.txt` y `NATIVE_BUILD_STATUS.txt`.

Si Foundation 14 devuelve un error, **no borrar el directorio, no modificar las condiciones para esconder el error**. Compartir los logs de la carpeta rechazada antes de ajustar una sola variable. El piloto solo se considerará preliminarmente aceptado si los diagnósticos nativos lo demuestran. La etapa siguiente es verificar el área de contacto real y fidelidad superficial CAD; posteriormente preparar BC 3D y pruebas térmicas.

## Fuentes y límites

- [Caso original del doctor](../../doctor_original/cht/system/blockMeshDict) y [resultado nativo de separación](../../doctor_original/cht/log.splitMeshRegions).
- [Diagnóstico de STL v2](../../docs/C3D_02_ABLACION_STL_V2_20261118_ES.md).
- [Estrategia A/B/C](../../docs/C3D_02_ESTRATEGIA_MALLADO_CONFORMANTE_20261118_ES.md).
- [Guía oficial Foundation 14, blockMesh](https://doc.cfd.direct/openfoam/user-guide-v14/blockmesh).
- [Versión Foundation 14 y separación regional](https://openfoam.org/release/14/).
