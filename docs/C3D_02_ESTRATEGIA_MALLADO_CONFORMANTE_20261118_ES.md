> **18-11-2026 — AVANCE METODOLÓGICO:** la alternativa A del documento **ya es `C3D-04`**: `blockMesh` curvilíneo 3D con aristas `arc`, 180 bloques, fidelidad de secciones de la base mejorada (**fuente, no corrida**). La opción B **ya se implementó como fuente independiente `C3D-05`**: dos STEP auténticos + Gmsh/OpenCASCADE fragmentación de volúmenes, etiquetas físicas y conversión a OF14, aún bloqueada por falta de STEP y sin mallado verificado. Ver [comparación vigente](C3D_04_C3D_05_MALLADO_PARALELO_20261118_ES.md). Ambas conservan C3D-03 y no ejecutan CFD.

> **ACTUALIZACIÓN 18-11-2026 — La alternativa A ya tiene un PILOTO PREPARADO:** se implementó [C3D-03](../cases_3d/C3D_03_doctor_multiblock_pilot/README.md), ensayo separado con `blockMeshDict` real, 24 bloques/48 vértices, moldes + metal en un solo polyMesh y apertura inferior rectangular según el STL. Sus volúmenes **calculados** metal 48,011.916 mm³ (+0.0505 %) y arena 103,169.142 mm³ (+0.3168 %); se esperan 10,048 celdas y 1,248 caras interregionales por región. **Aún no se ejecutó `blockMesh` / `checkMesh` de este piloto en Ubuntu; no presentar esos números como salida nativa.** La aproximación cuadriculada es solo el primer ensayo de topología, no fidelidad superficial CAD certificada. Los textos originales de este plan describen la etapa previa; esta adenda prevalece.

# C3D-02 — Estrategia de continuación 3D con referencia al caso original del doctor

**Decisión técnica provisional — 18-11-2026.** Este documento distingue criterios físicos, hechos reales ejecutados en la laptop y experimentos **propuestos y NO ejecutados**. No cambia CAD, STL, C14, mallas ni `Allmesh`.

## La lección del caso del doctor que SÍ podemos trasladar

Fuente primaria: `doctor_original/cht/system/blockMeshDict`, `Allrun`, `log.blockMesh` y `log.splitMeshRegions`. El modelo original Foundation 13 era cuasi-2D: 6 bloques, uno de metal y 5 de molde, una celda de espesor con `frontAndBack empty`. `blockMesh` creó directamente `cellZones metal/mold` (11,880 celdas), `splitMeshRegions` separó 6,400 metal / 5,480 molde e interfaz de 240 caras. `createZones` figura en `Allrun`, pero las dos zonas ya aparecen en el log previo de `blockMesh`; la función exacta de las cajas solapadas de `createZonesDict` no debe extrapolarse a QuickCup. `log.foamMultiRun` conservado está vacío: NO prueba solver completado.

**Principio transferible:** definir desde el inicio volúmenes no solapados `metal` y `mold` que compartan **la misma malla de caras** antes de separar regiones. No copiar la geometría del doctor ni las condiciones de `empty` de 2D a 3D.

## Situación experimental de C3D-02

| Experimento ya ejecutado | metal celdas | mold celdas | contacto | conclusión |
|---|---:|---:|---|---|
| STL originales, malla nativa OF14 | 85,350 | 274,788 | 27,501 caras | Volumen e interfaz plausibles, **checkMesh rechazado en ambos** |
| Pareja STL v2 | 4 | 4 | ausente | zonas colapsadas |
| V2 solo metal | 1 | 274,788 | 3 caras residuales | no contacto físico confiable |
| V2 solo arena | 85,350 | 0 | ausente | zona de arena inexistente |

**No repetiremos automáticamente esas pruebas.** Los STL v2 pasaron verificaciones nativas de superficie de procedencia; la causa algorítmica exacta del colapso de `cellZones` todavía es desconocida y no debe atribuirse sin evidencia a STL defectuosos. No tocar `mappedWall` manualmente.

## Geometría real y límites de aproximación

- `metal_v2.stl`: bbox x/z 7.65–44.15 mm (36.5 mm de ancho), y -40–0 mm (40 mm de altura), volumen **47.987697 cm³**.
- `mold_v2.stl`: bbox x/z 0–51.8 mm, y -65.5–0 mm (65.5 mm de altura), volumen de arena **102.843333 cm³**.
- Una caja de hierro de `36.5×36.5×40 mm` tendría **53.29 cm³**, desviación de aprox. **+11.05 %** contra CAD. Por ello **es incorrecto** tomar solo la caja envolvente como geometría válida para la tesis. No suponer que la sección es un círculo ni que las paredes son rectas sin inspeccionar los STL/STEP.
- Se debe conocer en secciones reales el contorno interior/exterior, transiciones en altura, espesor de base, redondeos y superficie común metal–arena. Conservar los STL como referencia de comparación, aunque se decida mallar desde B-Rep STEP.
- No duplicar escala: usar `units [mm];` y comprobar m³ al exportar a OpenFOAM. Volúmenes de referencia: `4.7987697e-5 m³` hierro y `1.02843333e-4 m³` arena.

## Decisión entre tres rutas: criterio ANTES de ejecutar mallas costosas

**A — Multibloque 3D curvilíneo nativo (PREFERENCIA CONDICIONAL).** Si los contornos CAD tienen geometría parametrizable con número razonable de bloques y continuidad entre metal y arena, construir una malla única desde `blockMesh` Foundation 14: regiones `metal` y `mold` con `cellZones` propias, vértices, caras y aristas curvilíneas o `project` a geometría según corresponda; misma discretización en cada cara común, sin aire como tercer material físico, sin `empty` en el 3D. Requiere corroborar geometría del STL antes de declarar viable el esquema. `blockMesh` v14 admite `units [mm]`, `arc`, `spline` y proyección geométrica; v14 agregó `sweepFace` para caras curvas. No asumir que un tipo específico de curva resuelve cualquier geometría real.

**B — Un solo CAD multivolumen STEP con topología compartida y mallador de CAD (ALTERNATIVA PARA GEOMETRÍA IRREGULAR).** Si el esquema de bloques no reproduce paredes/redondeos/espesores sin distorsión, exportar desde SolidWorks volúmenes `metal` y `mold` a un modelo STEP con caras compartidas / fragmentación geométrica; mallar **los dos volúmenes en una operación** con etiquetado físico `metal`/`mold`. Evaluar conversión `.msh`→OpenFOAM mediante `gmshToFoam` **verificando** formato, unidades, zonas e interfaces con la instalación Foundation 14 antes de usar el resultado. Este enfoque sigue la idea del doctor (volúmenes con una frontera común) aunque no use `blockMesh` como mallador. **No afirmar compatibilidad de un formato particular sin un caso piloto.**

**C — Refinar baseline original `snappyHexMesh` (RESPALDO CON EVIDENCIA EXISTENTE).** Retiene 85,350/274,788 celdas e interfaz, pero `checkMesh` reportó 4,834/14,951 celdas cóncavas y determinantes bajos. Antes de tocar `nSmoothPatch`, contrastar VTK nativos de defectos con la geometría. La repetición literal y `nSmoothPatch=6` no mejoraron. Este camino puede ser más corto si los defectos son localizables y corregibles.

**Orden recomendado:** 0) caracterización geométrica de secciones/caras comunes mediante CAD ya disponible; 1) si la geometría admite bloques, piloto A; en caso contrario B; 2) diagnóstico C en paralelo por lectura de VTK/logs existentes, sin gastar otra corrida repetida. La elección final se basa en fidelidad + calidad + contacto + costo, NO en que un comando termine `End`.

## Diseño del primer ensayo nuevo (todavía NO corrido)

- Crear un **caso de prueba separado**, no reescribir `C3D_02_metal_sand_clean` ni `doctor_original/cht`. Malla 3D **gruesa solo para prueba de topología**, con resolución nominal a definir después de caracterizar contornos; no copiar sin evidencia las subdivisiones 2D `(80 80 1)`.
- Conservar **solo** zonas de volumen metal y arena, cobertura completa y exclusiva, con interfaz única compartida, sin volúmenes solapados ni huecos artificiales.
- Generar `polyMesh` con el método seleccionado y comprobar **antes de separar** número de celdas por zona, volumen por zona, conectividad, ausencia de `unassigned` y existencia/topología de frontera común.
- Separar con **sintaxis verificada en `splitMeshRegions -help` de Foundation 14** (v14 reescribió opciones), comprobar `metal_to_mold` y `mold_to_metal` recíprocos `mappedWall`, cuentas iguales de caras, **área total compatible con CAD**, normales y orientación. No usar contacto artificial de 3 caras.
- `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` para metal y arena; una región conectada, `Mesh OK`, cero tests fallidos, volúmenes próximos al CAD y superficie/área conforme al error geométrico que se documente. Criterio de volumen de proyecto ya empleado: **±2 %**, pero la exactitud de áreas y contornos se estudiará por separado. No relajar el veredicto nativo.
- Sólo tras puertas geométricas y de calidad, adaptar **BC 3D reales** desde C14: sustituir `frontAndBack empty`; definir superficie superior `metalTop`, paredes exteriores, contacto, `U`/`p_rgh`/`T`, revisar `pRefPoint` por posición 3D, material constante `castIron`/`silica` y `solidificationMeltingSource`. A continuación ejecutar prueba de lectura del solver y corrida muy corta, y solo entonces campaña 3D.
- Los indicadores de Courant real, PIMPLE, energía y sensibilidad `relax=0.10→0.25` forman parte de [requisitos del primer avance](PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md). No confundir sensibilidad 2D C14–C16 pendiente con simulación 3D.

## Incertidumbres y datos necesarios para tomar la decisión A/B

1. Secciones horizontales de `metal_v2.stl` y `mold_v2.stl` a distintas alturas, con puntos característicos de curvatura, chaflanes, conicidad y uniones; el bbox NO basta.
2. Área real y segmentación de la interfaz común, incluido el posible contacto en base y caras laterales.
3. Disponibilidad de **STEP multicuerpo** exportado desde SolidWorks; no indispensable si A es factible, muy útil para B.
4. Calidad y posición de los VTK nativos de `concaveCells`/`underdeterminedCells` del baseline original.
5. Compatibilidad exacta de opciones de conversión y separación comprobada en el OpenFOAM Foundation 14 de Ubuntu. No ejecutar solver ni cambiar fuentes científicas para resolver estas dudas.

## Referencias

- [Caso original doctor, `blockMeshDict`](../doctor_original/cht/system/blockMeshDict), [Allrun](../doctor_original/cht/Allrun), [log de regiones](../doctor_original/cht/log.splitMeshRegions).
- [Resultados reales C3D-02](C3D_02_ABLACION_STL_V2_20261118_ES.md).
- [Fuentes STL definitivas y dimensiones](../cases_3d/C3D_02_metal_sand_clean/constant/geometry/STL_V2_APPROVED_SOURCES.md).
- [Manual OF14 oficial: `blockMesh`](https://doc.cfd.direct/openfoam/user-guide-v14/blockmesh).
- [Manual OF14 oficial: zonas de malla](https://doc.cfd.direct/openfoam/user-guide-v14/mesh-zones).
- [Notas de versión oficial OpenFOAM 14](https://openfoam.org/release/14/).
