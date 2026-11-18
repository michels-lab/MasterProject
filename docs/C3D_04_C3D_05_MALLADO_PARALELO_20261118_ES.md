> **ACTUALIZACIÓN 18-11-2026 — CAMBIO DE ESTADO DE CAD:** se recibieron en chat los dos STEP sólidos reales de SolidWorks, **ya validados como B-Rep auténticos**. Metal 47,988.524998 mm³; arena 102,843.320825 mm³; interfaz CAD estimada por unión booleana 6,352.821119 mm², correspondiente a la referencia STL en +0.00295 %. [Registro primario](C3D_05_STEP_SOURCE_AUDIT_20261118_ES.md). Donde el plan histórico dice «falta STEP» significa **falta disponibilidad de esos archivos en la WSL para ejecutar**, NO que todavía haya que exportarlos. C3D-04 y C3D-05 siguen sin ejecución nueva ni CFD; conservar y comparar ambas vías.

# Dos rutas de mallado 3D EN PARALELO — C3D-04 / C3D-05

**Registro de decisión:** 18-11-2026, proyecto de maestría QuickCup, OpenFOAM Foundation 14. Esta comparación separa **método de generación**, **fidelidad CAD** y **solver físico**.

## Qué es «3D curvilínea»

`C3D-04` **ya es una malla 3D curvilínea**, no una alternativa distinta de `blockMesh`: precisamente usa `blockMesh` para una malla hexaédrica estructurada de 180 bloques, 144 `arc`, 10 estaciones verticales y secciones redondeadas. Debe ejecutarse en WSL antes de declarar éxito nativo.

La **segunda alternativa independiente** es `C3D-05`: mallado multivolumen **no estructurado** mediante Gmsh/OpenCASCADE sobre los dos STEP de SolidWorks. Comparte con el doctor el principio de interfaz metal–arena construida de manera conformante, pero **no comparte `blockMesh` como algoritmo**.

| Comparación | A: C3D-04 blockMesh curvilíneo | B: C3D-05 Gmsh STEP conformante |
|---|---|---|
| Geometría | Secciones CAD aproximadas por 180 bloques con arcos | B-Rep STEP original (requiere dos sólidos auténticos) |
| Tipo típico de elemento | Hexaédrico | Tetraédrico/no estructurado |
| Interfaz material | Caras de bloques comunes | `OpenCASCADE.fragment` + mallado compartido |
| Capacidad de malla estructurada | Sí | No se exige |
| Estado actual | Archivo y ejecutor publicados, **NO ejecutado** | Scripts y controles publicados, **BLOQUEADO: STEP auténticos aún no suministrados** |
| Predecesor verificado | C3D-03 pasó checkMesh y mappedWall | Sin prueba numérica todavía |
| Condiciones físicas | Sin BC 3D finales ni CFD | Sin BC 3D finales ni CFD |

## Puertas de aceptación A/B (aplicables por separado)

1. `blockMesh`/Gmsh y conversión completados con logs nativos **sin errores**.
2. Un solo dominio con exactamente dos `cellZones`, metal y arena, **sin exterior asignado como material** ni huecos o volúmenes solapados.
3. `checkMesh -allGeometry -allTopology` de malla completa y de cada región, sin checks fallidos, conectividad de una sola región por material.
4. Volúmenes metal y arena dentro de **±2 %** del CAD.
5. Dos parches de contacto recíprocos `mappedWall`, mismo número de caras y área compatible con CAD dentro de **±3 %**; coherencia entre lados dentro de **0.1 %**.
6. Áreas y contornos de superficies externas correctas, abertura inferior real, radios de la base y paredes. Área global **no sustituye** una futura medición de distancia superficie–CAD.
7. Pruebas de refinamiento y convergencia de malla antes del solver físico; la misma física C14 no se importa sin revisar BC 3D (prohibido copiar `empty` de 2D).
8. Comparación posterior usando Courant **medido en logs**, residuos, `T(t)`, `alpha1(t)`, energía y costo CPU, sin confundir `maxCo` configurado con `Co_{max}` medido.

## Acciones siguientes

**Ruta A (YA tiene STL y diccionario):**
```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_04_rounded_multiblock_pilot/tests/test_rounded_multiblock_static.sh &&
bash cases_3d/C3D_04_rounded_multiblock_pilot/Allmesh
```

**Ruta B (preparada, depende del STEP):** exportar desde SolidWorks dos cuerpos sólidos, `metal.step` y `mold.step`, con unidades milimétricas, mismo origen y sin duplicación de volumen. Gmsh valida contacto y geometría antes de mallar. El usuario ejecutará después `C3D-05/Allmesh`, según [manual de C3D-05](../cases_3d/C3D_05_step_gmsh_conformal/README.md).

**Política de preservación:** no sobrescribir `C3D-03` validado, ni C3D-02 rechazado, ni STEP/STL originales, ni la física C14. Cada ensayo en carpeta WSL distinta; no ejecutar CFD automáticamente.

## Evidencias

- [El doctor original: blockMesh cuasi-2D](../doctor_original/cht/system/blockMeshDict).
- [C3D-03 malla 3D real aceptada](C3D_03_RESULTADO_NATIVO_20261118_ES.md).
- [C3D-04 bloque curvo](../cases_3d/C3D_04_rounded_multiblock_pilot/README.md).
- [C3D-05 CAD STEP y Gmsh](../cases_3d/C3D_05_step_gmsh_conformal/README.md).
- [Gmsh tutorial 16, fragment](https://gmsh.info/doc/texinfo/gmsh.html#t16).
- [Gmsh tutorial 20, import STEP](https://gmsh.info/doc/texinfo/gmsh.html#t20).
