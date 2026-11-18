# FS-C02: dominio de aire exterior sobre la arena del QuickCup

**Decisión del investigador, 18 de noviembre de 2026.** El aire caliente no debe encontrarse con un techo ficticio ni quedar atrapado en una columna vertical estrecha. **El dominio gaseoso debe cubrir en planta tanto el hierro expuesto como la cara superior de la arena** y continuar a una frontera atmosférica a suficiente distancia. **No ejecutar** como modelo físico la variante previa de 120 mm que solo aumentaba la altura de una columna de ancho 40 mm sin arena.

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
3. **Aire exterior conectado**: toda la región de aire por **encima del plano y=0** de metal y arena, extendida en X y Z **más allá del contorno exterior de arena** (x/z 0–51.8 mm) y hacia Y positivo. La región aérea no es solo el área x/z del metal (7.65–44.15 mm). No debe haber paredes artificiales en el espacio que físicamente es aire libre.
4. **Fronteras**: arriba, frontera abierta de presión con salida e ingreso de aire ambiente (300 K solo como condición de reentrada provisional); en las caras laterales exteriores del volumen atmosférico también estudiar fronteras abiertas o suficientemente distantes según la configuración experimental. Las paredes reales de arena permanecen superficies de intercambio térmico, no parches atmosféricos.
5. **Malla/interfaz**: distinguir dominio fluido metal–aire (VOF) del dominio sólido arena (CHT) con acoplamiento térmico consistente y partición de celdas. Esto requiere una estrategia multirregión real; los dos modelos existentes, FS-C02 2D y C3D-02 arena–metal 3D, **no conforman todavía un modelo combinado VOF+CHT de tres materiales**. No afirmar que `foamMultiRun` ya haya resuelto o validado este problema.
6. **Comprobaciones mínimas** antes de nuevo CFD: sin solapes/huecos espurios entre metal, arena y aire; área de cara metal–aire igual a CAD dentro de tolerancia definida; conectividad de la atmósfera superior con aire situado sobre toda la arena; normals/patch types correctos; resolución consistente cerca de metal y arena; `checkMesh` y conservación de volumen; sensibilidad de distancia al contorno superior y lateral.
7. **Diagnósticos físicos**: medir flujo firmado por fronteras, balance de energía metal–aire–arena, temperaturas del gas que abandona el dominio, temperaturas de arena, distribución térmica del metal y evolución espacial de `alpha.metal`. Un `sum(phi)` neto de mezcla no permite por sí solo afirmar flujo másico/entalpía del aire evacuado.

## Limitación específica de la propuesta previa (FS-C02_HIGH_AIR)

`analysis_tools/run_fs_c02_high_headspace.py` sigue disponible **solo en modo `--stage-only`** como geometría histórica para estudiar la posición del límite superior. Conserva x=0–40 mm, con paredes laterales hasta y=120 mm, sin la arena; por lo tanto no representa la abertura de aire sobre el molde real y **queda bloqueada como CFD**. La elección de y=120 mm nunca fue una dimensión medida de QuickCup: era un ensayo de sensibilidad numérica.

**Próxima tarea de implementación**: crear un nuevo caso piloto aparte con los tres volúmenes coherentes con el CAD (metal, arena, aire exterior) y una malla comprobable, primero **malla/contornos sin CFD**. No cambiar las corridas FS-C02 RAS ni las pruebas laminares archivadas. Tampoco tocar el checkout principal ni el caso C3D-02 que se trabaja en paralelo. La forma/volumen exterior definitivo del aire se elegirá mediante sensibilidad a las distancias de las fronteras, no inventando un tamaño definitivo de cámara atmosférica.

**Estado**: diseño físico acordado; todavía no hay nueva malla 3D aire+arena+metal ni simulación ejecutada.
