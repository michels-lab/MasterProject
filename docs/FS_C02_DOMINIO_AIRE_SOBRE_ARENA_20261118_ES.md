# FS-C02: dominio de aire exterior sobre y alrededor de la arena del QuickCup

**Decisión del investigador, 18 de noviembre de 2026, ampliada:** el aire caliente no debe encontrar un techo falso ni quedar atrapado en una columna estrecha. El dominio gaseoso debe envolver **la parte superior del metal y de la arena, y las cuatro paredes laterales exteriores de la arena**, formando una sola región de aire ambiente conectada, con fronteras atmosféricas a suficiente distancia. **No ejecutar** como modelo físico la variante previa de 120 mm que solo aumentaba la altura de una columna de ancho 40 mm sin arena.

## Datos de geometría CAD, no dimensiones supuestas

Fuente del proyecto: `cases_3d/C3D_02_metal_sand_clean/constant/geometry/STL_V2_APPROVED_SOURCES.md` y `cases_3d/C3D_03_doctor_multiblock_pilot/README.md`.

| Región | Caja envolvente CAD aprobada | Volumen CAD |
|---|---|---|
| Metal | x/z 7.65–44.15 mm; y -40–0 mm | 47.987697 cm³ |
| Arena | x/z 0–51.8 mm; y -65.5–0 mm | 102.843333 cm³ |
| Aire ambiente | **Sin CAD volumétrico definido todavía** | No calculado |

La geometría no es cilíndrica ni un prisma rectangular exacto. No sustituir ambos STL por sus cajas envolventes: las superficies reales con conicidad y redondeos deben conservarse y la geometría ha de representar las interfaces reales metal–arena.

## Topología exigida del dominio futuro (3D)

1. **Hierro en la cavidad**: metal líquido ocupa el volumen CAD correspondiente, con superficie libre superior hacia el aire. No convertir `alpha.metal` del VOF en fracción sólida.
2. **Molde sólido**: la arena ocupa su volumen CAD alrededor y debajo del metal; se comunica térmicamente con el metal por paredes/contacto y con aire ambiente por su superficie exterior expuesta. Nunca poner aire dentro de celdas sólidas de arena, a menos que se introduzca explícitamente un modelo de porosidad/permeabilidad validado.
3. **Aire exterior conectado superior Y laterales**: aire encima del plano y=0 (hierro y arena), **y alrededor de los cuatro costados x-/x+/z-/z+ de la arena desde su parte superior hacia su base expuesta**, extendido en X y Z más allá de su caja CAD (x/z 0–51.8 mm) y en Y positivo por encima de la abertura. Debe existir una ruta gaseosa libre, conectada y mallada entre el aire de cada pared lateral y el aire superior. No basta con tener parches atmosféricos en la parte superior ni con definir una columna de 40 mm sobre la boca del metal. **La envolvente gaseosa y el molde sólido no deben ocupar las mismas celdas.**
4. **Fronteras**: la superficie de arena expuesta al gas (tapa y cuatro costados) es una **interfaz pared sólido–fluido sin penetración de aire a la arena**, pero con intercambio térmico conjugado (conducción en arena y convección en gas, radiación si se incorpora y justifica). **No confundir una pared material real arena–aire con una pared artificial que cierre el volumen atmosférico.** La cara superior externa del dominio gaseoso debe ser abierta a presión atmosférica, permitiendo salida y posible reentrada a temperatura ambiente provisional; los límites externos laterales también deben ser abiertos o lo suficientemente distantes, sujeto a sensibilidad. Evitar imponer `fixedValue T=300 K` sobre las caras reales de la arena: eso eliminaría la física de convección externa. La base del molde requiere decidirse según montaje real: zona de apoyo/contacto térmico, superficie expuesta a aire o hueco inferior abierto (CAD documenta una abertura inferior rectangular); **no declarar aire debajo de toda la base sin evidencia experimental.**
5. **Malla/interfaz**: crear un **dominio fluido conectado de hierro líquido + aire** para la superficie libre VOF, y un **dominio sólido arena** para CHT, con interfaces metal–arena y aire–arena bien identificadas y acopladas térmicamente. Verificar que la superficie libre del metal llega a la región superior de aire, mientras que la arena permanece una región sólida impermeable al gas; las paredes laterales del molde deben ser caras internas de acoplamiento entre regiones, no `atmosphere` ni `empty`. La selección concreta de solver/multirregión OpenFOAM Foundation14 está pendiente de probar. Esto requiere una estrategia multirregión real; los dos modelos existentes, FS-C02 2D y C3D-02 arena–metal 3D, **no conforman todavía un modelo combinado VOF+CHT de tres materiales**. No afirmar que `foamMultiRun` ya haya resuelto o validado este problema.
6. **Comprobaciones mínimas** antes de nuevo CFD: sin solapes/huecos espurios; concordancia de áreas y volúmenes metal/arena contra CAD; aire conectado por encima **y en los cuatro costados** de la arena; identificar con precisión la superficie arena–aire de cada costado y cara superior y comprobar su área, normal y acoplamiento conjugado; no imponer condiciones atmosféricas sobre el contacto arena–gas ni paredes en los extremos externos abiertos; malla 3D y `checkMesh` por regiones; fidelidad del contacto metal–arena; resolución y calidad de interfaz; sensibilidad de distancias al contorno superior y lateral; tratamiento explícito del apoyo, base y abertura inferior del molde. El pilotaje anterior de solo aire no constituye una prueba de estas condiciones.
7. **Diagnósticos físicos**: medir flujo firmado por fronteras, balance de energía metal–aire–arena, temperaturas del gas que abandona el dominio, temperaturas de arena, distribución térmica del metal y evolución espacial de `alpha.metal`. Un `sum(phi)` neto de mezcla no permite por sí solo afirmar flujo másico/entalpía del aire evacuado.

## Limitación específica de la propuesta previa (FS-C02_HIGH_AIR)

`analysis_tools/run_fs_c02_high_headspace.py` sigue disponible **solo en modo `--stage-only`** como geometría histórica para estudiar la posición del límite superior. Conserva x=0–40 mm, con paredes laterales hasta y=120 mm, sin la arena; por lo tanto no representa la abertura de aire sobre el molde real y **queda bloqueada como CFD**. La elección de y=120 mm nunca fue una dimensión medida de QuickCup: era un ensayo de sensibilidad numérica.

**Próxima tarea de implementación**: crear un nuevo caso piloto aparte con los tres volúmenes coherentes con el CAD (metal, arena, aire exterior) y una malla comprobable, primero **malla/contornos sin CFD**. No cambiar las corridas FS-C02 RAS ni las pruebas laminares archivadas. Tampoco tocar el checkout principal ni el caso C3D-02 que se trabaja en paralelo. La forma/volumen exterior definitivo del aire se elegirá mediante sensibilidad a las distancias de las fronteras, no inventando un tamaño definitivo de cámara atmosférica.

**Estado**: diseño físico acordado; todavía no hay nueva malla 3D aire+arena+metal ni simulación ejecutada.

## Actualización física — aire en las paredes exteriores de arena

**Confirmación del investigador:** las cuatro paredes laterales exteriores de la arena intercambian calor con aire ambiental, igual que la cara superior expuesta. El dominio de gas debe rodear el molde 3D (dejando sin invadir las paredes sólidas) y conectar lateralmente con el volumen sobre la abertura. Esto cambia el dominio de una columna vertical a una **envolvente de aire exterior alrededor del molde**. La ampliación deberá respetar los STL reales y no construirse con una caja de metal/arena ficticia. La elección de dimensiones exteriores se hará mediante sensibilidad de frontera.

La base no se clasificará automáticamente como toda expuesta: el CAD contiene un hueco inferior y el montaje podría tener apoyos; modelaremos aire donde haya una cavidad efectivamente abierta y contacto térmico donde haya apoyo. **Ni el nuevo dominio 3D ni su solver multirregión se han construido/validado todavía**. Por seguridad sigue prohibido ejecutar como caso físico el piloto vertical `run_fs_c02_high_headspace.py` (modo `--stage-only` exclusivamente).

## Actualización de implementación: piloto FS-C03 creado (malla NO CFD)

Ya se creó el piloto independiente `freesurface/FS-C03_exterior_air_pilot/` basado en los **24 bloques originales de C3D-03**, ampliados con **29 bloques de aire** sobre el metal, sobre la arena y en los **cuatro costados** de la arena. La nueva topología tiene **53 bloques, 84 vértices y 42,048 celdas previstas** (metal 2,368; arena 7,680; aire 32,000), pero sigue siendo una **aproximación geométrica**, no la reproducción CAD exacta ni un solver combinado VOF+CHT. La auditoría de conteo de caras en la construcción no detectó superficies exteriores sin parche; `checkMesh` y la separación nativa todavía deben ejecutarse para confirmarlo.

Las interfaces topológicas teóricas son metal–arena (13 caras de bloque), metal–aire (1 cara de bloque en la boca) y arena–aire (24 caras de bloque: 4 superiores + 20 laterales). **Esto mejora el criterio físico sobre la región exterior del aire**, sin resolver todavía la exposición del hueco inferior ni la conducción/convección real.

El volumen gaseoso experimental se extiende horizontalmente a x/z de `-30` a `81.8 mm`, verticalmente a y de `-65.5` a `+80 mm`, sin ocupar el sólido arena. `atmosphereTop`/`atmosphereSides`/`atmosphereLowerSides` son parches externos abiertos, mientras que la arena intercambiará calor con el gas en interfaces materiales **todavía sin BC térmicas implementadas**. Las distancias externas son provisionales para sensibilidad de malla.

Se incluyen:
- `system/blockMeshDict` y `system/controlDict` de malla-only.
- `reference/C3D03_base_blockMeshDict` como copia inmutable de la geometría base.
- `analysis_tools/audit_fs_c03_exterior_mesh.py` para verificar propiedad de caras, zonas e interconectividad (sin OpenFOAM).
- `analysis_tools/run_fs_c03_mesh.py` para copiar a un directorio externo nuevo; con `--native` prueba `blockMesh/checkMesh/splitMeshRegions` **sin ejecutar CFD**.
- Pruebas de regresión que prohíben el techo falso, solapes topológicos, aire faltante sobre arena o en los costados y sobrescritura de ensayos anteriores.

**Clave de solver:** la separación de `metal/mold/air` en **tres regiones nativas es diagnóstica**. El eventual caso metal–aire de superficie libre requiere un **fluido único** con `alpha.metal`, y arena como sólido separado con acoplamiento térmico. No confundir la topología separada de este piloto con un caso multirregión térmico operativo ni declarar `foamMultiRun` ejecutado.

Instrucciones: [FS-C03 README](../freesurface/FS-C03_exterior_air_pilot/README.md). Estado real: **sólo construcción y pruebas estáticas; sin mallado nativo ni CFD verificados**.

## Continuación del 18 de noviembre — FS-C03 confirmado en Ubuntu; FS-C04 de dos regiones preparado

**FS-C03 (prueba real Foundation 14):** el investigador aportó salida completa de la auditoría estática (84 vértices, 53 bloques, 42,048 celdas previstas, 29 bloques de aire conectados), los **15 tests OK** y el ejecutor nativo `NATIVE_3_REGION_TOPOLOGY_PASSED_NO_CFD` sobre `/home/michel/OpenFOAM/FS_C03_AIR_TOPOLOGY_20261118T202905Z_6ef0cd90`. Esto confirma que el ejecutor nativo pudo comprobar la malla de tres zonas, el `checkMesh` y las interfaces de acuerdo con sus criterios. No prueba fidelidad STL, balance de energía ni CFD.

**FS-C04 (nuevo piloto independiente, TODAVÍA SIN resultado nativo):** `freesurface/FS-C04_fluid_mold_mesh_pilot/`. Mantiene idénticos los 53 hexaedros, vértices, subdivisiones y parches atmosféricos externos de FS-C03; **une las zonas inicialmente `metal` y `air` en una zona continua `fluid`** con **34,368 celdas previstas**, separada de `mold` con 7,680. El auditor Python comprueba dos regiones conectadas, las 37 caras de bloque fluido–arena (13 originales metal–arena + 24 aire–arena), y preserva las 9 caras de bloque de salida superior y las caras exteriores laterales abiertas. El frente metal–aire inicial deja de ser una pared y será representado más adelante por `alpha.metal` dentro del dominio fluido; **el campo `alpha.metal` no está implementado todavía**.

El ejecutor `analysis_tools/run_fs_c04_mesh.py --native` (solo mallado, no CFD) deberá comprobar de forma independiente en OpenFOAM Foundation 14 `blockMesh`, `checkMesh`, `splitMeshRegions -cellZones 'fluid mold' -noFields`, las dos regiones y las **3,136 caras `mappedWall` recíprocas** que se esperan en `fluid_to_mold` / `mold_to_fluid`. Sin ese resultado nativo queda **PENDIENTE**, aunque la geometría base FS-C03 haya pasado.

Se preservan todas las corridas ya aprobadas y el caso C3D-02 en paralelo. Todavía falta fidelidad CAD exacta, contacto/base inferior, separación térmica fluid–solid y propiedades/física metalúrgica antes de cualquier solver.
