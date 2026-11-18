# C3D-02 — Estudio del caso original del doctor y alternativa multibloque (18-11-2026)

## Qué se inspeccionó

Fuente del **caso original aportado por el doctor**, conservada en `doctor_original/cht/` dentro de `michels-lab/MasterProject`. Se inspeccionaron los archivos `system/blockMeshDict`, `system/createZonesDict`, `system/controlDict`, `Allrun`, `log.blockMesh`, `log.createZones`, `log.splitMeshRegions`, `log.foamMultiRun`, `0/{metal,mold}/T`, `constant/metal/fvModels` y los materiales del metal y del molde. **No se efectuó una ejecución local nueva** durante este análisis.

## Procedimiento de malla documentado

El `Allrun` original de Foundation **13** contiene:

```sh
runApplication blockMesh
runApplication createZones
runApplication splitMeshRegions -cellZonesOnly -overwrite
runApplication foamMultiRun
```

`blockMeshDict` construye **seis bloques hexaédricos**: uno central con zona `metal` y cinco alrededor con zona `mold`. Malla fina activa: bloque metálico `(80 80 1)`; bloques de arena `(14 80 1)`, `(14 30 1)`, `(80 30 1)`, `(14 30 1)`, `(14 80 1)`. Las coordenadas originales fueron declaradas en mm y escaladas con `convertToMeters 0.001`. El metal rectangular cubre 40×40 mm en el plano y 10 mm en Z; la superficie `frontAndBack` usa `empty`, así que se trata de **un dominio cuasi-2D**, no de un QuickCup 3D real. Paso de celda en plano: 0.5 mm; una sola celda de espesor 10 mm.

El log original `log.blockMesh` (28-07-2026, OpenFOAM 13, host `Michel-DuarteHP`) demuestra que el propio `blockMesh` registró `Adding cell zones: metal, mold`, con **11,880 celdas** globales. `log.createZones` terminó con `End`, sin detalle suficiente para atribuirle la creación inicial de las etiquetas. **Atención:** el `createZonesDict` conserva dos cajas geométricas con rangos solapados; no copiar esa selección de zonas al 3D sin estudiar el resultado. Las zonas ya existían en el log de `blockMesh`.

`log.splitMeshRegions` demuestra:
- **2 regiones**.
- `metal`: **6,400 celdas**.
- `mold`: **5,480 celdas**.
- **240 caras** interregionales, parches `metal_to_mold` y `mold_to_metal` creados.

El archivo `log.foamMultiRun` versionado está **vacío**: el `Allrun` contiene la orden de ejecutar el solver, pero con ese archivo **no puede certificarse** ejecución terminada, estabilidad numérica ni validación térmica/experimental.

## Física y contacto documentados (referencia, NO nuevos parámetros para C3D-02)

En `system/controlDict`, `regionSolvers { metal fluid; mold solid; }`; tiempo configurado a 300 s. El metal comienza con `T=1500 K` y la arena con `T=300 K`. La interfaz tiene condición `coupledTemperature` y una capa de espesor `2e-4 m`, conductividad `0.1 W/(m K)`. En `fvModels`, la solidificación está representada por `solidificationMeltingSource`: `Tsol=1423 K`, `Tliq=1473 K`, `L=2.286e5 J/kg`. La documentación es **descriptiva del caso del doctor**; la física vigente del caso C14 no se altera.

## Comparación con nuestro C3D-02

| Aspecto | Caso doctor, Foundation 13 | C3D-02, Foundation 14 |
|---|---|---|
| Construcción | `blockMesh` multibloque | `blockMesh` de fondo + `snappyHexMesh` sobre STL |
| Geometría | Rectángulos cuasi-2D, caras compartidas | QuickCup real curvo, dos sólidos 3D |
| Zonas | Nombres `metal`/`mold` agregados por `blockMesh` | `cellZones` asignadas al interpretar superficies |
| Contacto | 240 caras generadas en separación | Baseline 27,501 caras pero `checkMesh` falla; v2 pierde contacto |
| CFD validado | No certificado por `log.foamMultiRun` vacío | No ejecutado |

**Hallazgo técnico transferible:** en el caso del doctor la topología metal/molde era compartida desde la generación de los bloques; la clasificación no dependía de las superficies STL. No se ha probado aún que un multibloque pueda representar el QuickCup real dentro de la tolerancia geométrica definida.

## Alternativa propuesta — estado SOLO DE ESTUDIO

Evaluar una variante **independiente** que preserve el CAD y la física C14:
1. Extraer secciones, límites y superficies reales de ambos STL; verificar volumen y localización de la interfaz, incluida geometría superior y base del QuickCup.
2. Diseñar bloques 3D compatibles y conformantes (si la curvatura puede representarse con suficiente fidelidad), asignando `metal` y `mold` directamente. No usar `empty` para las caras de una malla 3D.
3. Validar un solo `polyMesh` con dos zonas volumétricas que correspondan a los volúmenes CAD (~47.9877 y ~102.8433 cm³), sin contaminarse con exterior auxiliar.
4. Separar las regiones con sintaxis **verificada para Foundation 14**, comprobar parches recíprocos, área de contacto real, `checkMesh -allGeometry -allTopology`, conectividad, volumen y temperaturas/BC antes de cualquier CFD.
5. Registrar coste, fidelidad geométrica y calidad contra la vía STL, sin reemplazar archivos ni casos históricos.

La opción multibloque **no está implementada ni ejecutada**. Es una alternativa de investigación motivada por la técnica del doctor, **no** una solución ya demostrada al problema STL v2. Se conserva la línea `snappyHexMesh` y sus evidencias.

## Rutas de evidencia

- [`doctor_original/cht/system/blockMeshDict`](../doctor_original/cht/system/blockMeshDict)
- [`doctor_original/cht/Allrun`](../doctor_original/cht/Allrun)
- [`doctor_original/cht/log.blockMesh`](../doctor_original/cht/log.blockMesh)
- [`doctor_original/cht/log.splitMeshRegions`](../doctor_original/cht/log.splitMeshRegions)
- [`doctor_original/cht/log.foamMultiRun` (vacío)](../doctor_original/cht/log.foamMultiRun)
- [Ensayos STL v2 de C3D-02](C3D_02_ABLACION_STL_V2_20261118_ES.md)
