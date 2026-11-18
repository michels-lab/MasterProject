# FS-C03 — Piloto 3D metal + arena + aire exterior conectado (malla solamente)

**Estado al 18-11-2026:** nueva malla de bloques y auditoría topológica **creadas en rama de investigación**; **sin ejecución nativa** de OpenFOAM en Ubuntu, `checkMesh` aún pendiente; **sin CFD, CHT, VOF, solidificación ni contracción**. Nunca sustituir automáticamente C3D-02 ni la geometría real de los STL.

## Problema físico que corrige esta variante

El usuario exigió que el aire caliente pueda abandonar el modelo **sin un techo falso** y que el gas no sea únicamente una columna encima del metal: debe cubrir la boca del hierro, la cara superior de la arena **y los cuatro costados exteriores del molde de arena**. Las paredes arena–aire son superficies físicas con intercambio térmico futuro, no parches atmosféricos puestos sobre el sólido.

El piloto anterior `FS-C02_HIGH_AIR` de ancho 40 mm fue **bloqueado para CFD**: no contenía molde sólido ni aire en los laterales. Esta propuesta **no lo reactiva**.

## Procedencia y fidelidad

Se derivó del `blockMeshDict` **sin modificar** de [C3D-03 (rama main)](../../cases_3d/C3D_03_doctor_multiblock_pilot/README.md), y se incluye una copia congelada en `reference/C3D03_base_blockMeshDict`. Los 24 bloques originales de metal y arena, así como los primeros 48 vértices, son idénticos al piloto geométrico basado en el CAD; se añadieron otros 29 bloques de aire exterior y 36 vértices. **El propio C3D-03 es una aproximación escalonada del CAD, no una geometría fiel final**. Su forma de metal contiene secciones cuadradas redondeadas y conicidad que este piloto aproxima mediante bloques rectos; no afirmar concordancia de superficies ni área de contacto antes de compararla con los STL reales.

| Región | Celdas teóricas, NO medidas por checkMesh | Referencia |
| --- | ---: | --- |
| Metal (hierro) | **2,368** | volumen analítico del piloto: 48,011.916 mm³; CAD aprobado: 47,987.697 mm³ |
| Arena (sólido) | **7,680** | volumen analítico del piloto: 103,169.142 mm³; CAD aprobado: 102,843.333 mm³ |
| Aire exterior | **32,000** | dominio paramétrico piloto sin volumen CAD aprobado |
| **Total** | **42,048** | 53 bloques, 84 vértices |

Marco de referencia con eje vertical **Y** (mm): el metal termina en y=0, la arena exterior abarca aproximadamente de y=-65.5 a y=0, el aire lateral llega hasta y=-65.5 y el aire superior hasta **y=+80**. El aire se extiende lateralmente hasta x/z=-30 y +81.8 mm, es decir, aproximadamente **30 mm más allá de la arena superior**, cuya caja alcanza x/z 0–51.8 mm. Esas distancias exteriores son **hipótesis de mallado y sensibilidad**, no dimensiones de un recinto experimental. La salida superior y los límites lejanos laterales son `patch` abiertos, **no techos sólidos**. El dominio inferior de aire alrededor de la arena se corta en y=-65.5 mm con `atmosphereLowerSides` abierto; no se ha construido aún una envolvente real del apoyo/base.

### Interfaces topológicas previstas (bloques; caras de malla solo previstas)

| Materiales | Caras topológicas compartidas | Caras discretizadas esperadas a cada lado |
| --- | ---: | ---: |
| Metal–arena | 13 | 1,248 |
| Metal–aire, boca superior | 1 | 64 |
| Arena–aire, 4 costados + cara superior | 24 (20+4) | 1,888 |

Los parches externos al aire previstos son `atmosphereTop` (448 caras), `atmosphereSides` (3,040) y `atmosphereLowerSides` (256). Todo el aire exterior está construido como una sola región conectada de 29 bloques alrededor y encima de metal y arena. `moldBottom` y las caras del hueco inferior (`moldRecessWall`, `moldRecessRoof`) **permanecen provisionalmente de tipo wall** y no están aún acopladas con aire, porque falta el detalle de apoyo/exposición real. No llamar al conjunto una envolvente térmica completa de la base sin resolverlo.

## Cómo verificar sin CFD

La auditoría independiente comprueba propiedad de todas las caras entre bloques, asignación exhaustiva de límites exteriores, ausencia de triple solapamiento, conectividad del aire, dos regiones de material intactas y las superficies gas–arena/metal. No invoca OpenFOAM:

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
python3 analysis_tools/audit_fs_c03_exterior_mesh.py
python3 -m unittest discover -s analysis_tools -p test_audit_fs_c03_exterior_mesh.py -v
```

El ejecutor nuevo se inicia **por defecto solo para preparar la carpeta**; todas las rutas se crean fuera del repositorio y jamás se sobrescriben:

```bash
python3 analysis_tools/run_fs_c03_mesh.py
```

Para probar efectivamente la malla con las utilidades nativas **OpenFOAM Foundation 14**, cuando esté activo `WM_PROJECT_VERSION=14` y **sin arrancar CFD**:

```bash
python3 analysis_tools/run_fs_c03_mesh.py --native
```

El ejecutor `--native` crea un caso nuevo único en `~/OpenFOAM/FS_C03_AIR_TOPOLOGY_<UTC>_<id>`, corre `blockMesh`, `checkMesh -allGeometry -allTopology` del padre, `splitMeshRegions -cellZones 'metal mold air' -noFields` y `checkMesh` de las tres regiones. Verifica `mappedWall` recíprocos y el número de caras de contacto, el conteo de celdas, conectividad de aire, y los tres límites atmosféricos lejanos. Si falla, guarda logs, escribe `REJECTED_NATIVE_MESH` y no continúa a ningún solver. Produce `FS_C03_NATIVE_STATUS.json` únicamente sobre la carpeta **nueva**.

> **Importante para la física final:** la separación en **tres regiones** se usa **solo como auditoría geométrica**. Un solver VOF de hierro–aire requiere que las celdas inicialmente metálicas y gaseosas pertenezcan al **mismo dominio FLUIDO con fracción volumétrica `alpha.metal`**, separado de la región SÓLIDA `mold` para el acoplamiento térmico. Este piloto no ha implementado ni certificado ese solver multirregión, ni propiedades de gas/arena a temperatura, ni radiación, ni fracción sólida, ni contracción.

## Puertas pendientes

1. **Mallado nativo:** el resultado `checkMesh` del padre y de las tres regiones debe realmente pasar; no inventar tasas de error, áreas o calidad.
2. **Contacto real CAD:** comprobar diferencias de volúmenes/superficies (especialmente redondeos, conicidad, abertura inferior), áreas de intercambio y normals. El modelo de bloques es una aproximación.
3. **Soporte/base:** decidir mediante datos del montaje qué superficies inferiores están en contacto con una base y cuáles exponen arena/aire; no considerar toda la base expuesta por defecto.
4. **Partición de solver:** crear correctamente fluido metal+aire y sólido arena; acoplamiento térmico/masa y las BC finales; luego validar flujo, energía, límites atmosféricos, superficie libre y pérdidas térmicas.
5. **Validación metalúrgica:** solo tras lo anterior incorporar entalpía de fusión, microestructura/expansión por grafitización, contracción y cotejo con curvas QuickCup.

**Ningún caso de C3D-02, B14, FS-C01, FS-C02 RAS o el experimento laminar archivado se modifica o elimina.** Esta es una tercera línea piloto independiente de mallado.
