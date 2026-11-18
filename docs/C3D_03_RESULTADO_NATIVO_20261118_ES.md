# C3D-03 — Primera malla 3D conformante aceptada por OpenFOAM 14 (18-11-2026)

**Fuente de evidencia:** salida completa de terminal de Ubuntu WSL aportada por el investigador, tras `git pull --ff-only` y ejecución de `tests/test_native_multiblock_static.sh && Allmesh`. Se registran **resultados realmente calculados** por OpenFOAM Foundation 14, no números teóricos ni un solver CFD.

**Ubicación local preservada:** `/home/michel/OpenFOAM/C3D03_DOCTOR_MULTIBLOCK_PILOT_01`. Archivos relevantes: `log.blockMesh`, `log.checkMesh.parent`, `log.splitMeshRegions`, `log.checkMesh.metal`, `log.checkMesh.mold`, `PILOT_MESH_REPORT.tsv`, `PILOT_INTERFACE_REPORT.txt`, `NATIVE_BUILD_STATUS.txt`. No se han descargado ni versionado logs completos: los datos aquí provienen de la salida compartida, no de una inspección independiente de los archivos locales.

## Comprobaciones realmente superadas

La terminal imprimió:

```text
OK: C3D03 3D pilot static integrity, block zones, recess topology and native-only executable
region  cells   volume_m3         CAD_m3        mesh_ok
metal   2368    4.801191628e-05   4.7987697e-5   YES
mold    7680    0.0001031691429  1.02843333e-4  YES
mappedWall faces (each side): 1248
```

| Característica | Resultado nativo | Referencia CAD | Interpretación |
|---|---:|---:|---|
| Metal | **2,368 celdas**, 48.01191628 cm³ | 47.987697 cm³ | Desviación +0.0505 % |
| Arena | **7,680 celdas**, 103.1691429 cm³ | 102.843333 cm³ | Desviación +0.3168 % |
| Total | **10,048 celdas** | — | Primera malla multibloque del QuickCup |
| `metal_to_mold` | **1,248 caras, `mappedWall`** | — | Acopla topológicamente con `mold_to_metal` |
| `mold_to_metal` | **1,248 caras, `mappedWall`** | — | `neighbourRegion=metal` y `neighbourPatch=metal_to_mold` |
| `metalTop` | **64 caras, wall** | — | Superficie superior separada |
| `moldTop` | **128 caras, wall** | — | Superficie superior del molde |
| `moldExterior` | **1,760 caras, wall** | — | Exterior del molde |
| `moldBottom` | **128 caras, wall** | — | Base inferior |
| `moldRecessWall` | **256 caras, wall** | — | Paredes de la abertura inferior |
| `moldRecessRoof` | **64 caras, wall** | — | Techo de la abertura inferior |

**Estado**: `MESH_TOPOLOGY_PRELIMINARILY_ACCEPTED / NO_CFD` según el programa de puertas de calidad. El script nativo verifica `checkMesh` de malla padre y regiones, su conectividad, volumen, caras de interfaz y tipo de parches. Esta es **la primera topología 3D metal–arena que supera el protocolo de malla**, pero **no hay todavía** auditoría numérica nativa del área de contacto ni prueba de coincidencia superficial CAD, por lo que no debe llamarse geometría final o validación CFD.

## Limitación geométrica descubierta

C3D-03 representó las secciones metálicas como cuadrados sin radios explícitos. El resultado global es bueno por volumen, pero un corte horizontal a `Y=-39.8 mm` da **827.3 mm²** en el piloto y **909.9 mm²** en CAD (−9.07 %); a `Y=-39 mm`, **942.4 mm²** frente a **1,034.6 mm²** (−8.92 %). En cambio, en `Y=-35, -20 y -5 mm` el error estimado es de menos de 0.5 %. Además, la superficie geométrica interfacial prevista por C3D-03 es ~6,483.795 mm², un **+2.065 %** frente a los 6,352.634 mm² que representa el STL metálico, quitando su tapa. Esta cifra es un **cálculo geométrico del bloque, NO área medida desde sus caras de `polyMesh`**.

Por tanto, se decidió conservar este piloto exitoso inmutable y construir `C3D_04_rounded_multiblock_pilot` como variante **independiente**, con estaciones adicionales cerca del redondeo y arcos de esquina. La alternativa debe volver a superar todas las puertas de `blockMesh`/`checkMesh` y demostrar superficie de contacto adecuada. **No adaptar aún C14 ni ejecutar CFD.**

## Registro, estado y presentación al director

- Distinguir `mesh_ok YES` de validación geométrica frente al CAD y resolución CFD.
- Distinguir malla 3D de modelo 3D termofísico ejecutado; no se ejecutó `foamMultiRun`.
- La idea del doctor que funcionó fue **construir cellZones `metal/mold` en `blockMesh` usando caras compartidas**, luego dividir con `splitMeshRegions`; el doctor original era cuasi-2D, este piloto sí es 3D.
- C3D-02 conserva las pruebas STL fallidas; C14 2D conserva la física verificada.

Referencias: [código de C3D-03](../cases_3d/C3D_03_doctor_multiblock_pilot/README.md), [alternativa C3D-04](../cases_3d/C3D_04_rounded_multiblock_pilot/README.md), [método del doctor](C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md).
