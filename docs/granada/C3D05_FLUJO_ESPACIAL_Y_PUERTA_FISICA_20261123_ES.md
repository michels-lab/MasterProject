# Caso B C3D-05 — Granada: flujo interfacial espacial y transición al modelo físico

**Fecha de desarrollo:** 23 de noviembre de 2026.  
**Etapa canónica:** 3/7 (T0 materialización física), **2/7 = 29 % de hitos técnicos**, NO porcentaje de tesis ni garantía de precisión.  
**Estado del paquete:** **código y pruebas de regresión publicados**, **análisis nuevo de la malla WSL todavía NO ejecutado**. No afirmar resultados espaciales cuantitativos aún no calculados.

## Punto de partida observado

El investigador terminó el T0 numérico archivado C14 sobre la malla STEP→Gmsh Delaunay→subdivisión HEX8 real, de 270,788 celdas (92,200 metal, 178,588 molde). El código Foundation14 resolvió conducción de dos sólidos en 100 pasos, `Δt=0.001 s`, `t=0.1 s`, con contacto ideal `mappedWall/coupledTemperature`. El expediente conservado `T0_GRANADA_EVIDENCE_SUMMARY.json` registra seis muestras regionales, cierre energético relativo de **4.320292500161304×10⁻⁸** frente a la escala de intercambio inicial, y **12,636 pares de flujo de calor por lado**, con desajuste relativo bilateral máximo agregado de **1.8239733799046786×10⁻¹⁶**. Son diagnósticos **numéricos**, no pruebas de propiedades físicas QuickCup o independencia de malla.

La malla conserva **1,826 caras con no ortogonalidad >70°** (595 metal, 1,231 arena), muchas próximas al contacto metal–arena o a superficies exteriores. La continuidad q calculada en las mismas condiciones acopladas **no mide por sí sola el error de discretización** de esas caras.

## Nueva etapa útil sin remallar ni resolver

El nuevo programa `cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/analyze_existing_t0_spatial.py` aprovecha los datos locales YA guardados bajo:

```text
~/OpenFOAM/C3D05_T0_C14_SHK_01/
    T0_GRANADA_EVIDENCE_SUMMARY.json
    T0_NATIVE_ENERGY_HISTORY.json
    log.foamMultiRun.C14_NUMERICAL_T0
    T0_NATIVE_FACE_FLUX/
        metal.csv
        mold.csv
        bilateral_diagnostics.json
        manifest.sha256
```

Antes de interpretar CSV verifica **de nuevo** los hashes SHA-256 de fuentes, `T0_NUMERICAL_RUN_STATUS_REVIEWED.json`, el expediente original del finalizador, los **12,636 pares recíprocos** por centros/áreas/normales, los tiempos y los totales de `q` de los reportes ya aprobados. **No crea geometría, no llama a `foamMultiRun` ni a `wmake`, no usa parámetros ajenos a la referencia C14, ni sobreescribe el CFD previo.**

### Salida científica propuesta

En un directorio SEPARADO e inmutable, `~/OpenFOAM/C3D05_B_T0_SPATIAL_DIAGNOSTICS_01`:

- `AXIAL_INTERFACE_Q_BY_TIME.csv`: para los seis instantes T0, división automática del contacto en **12 bandas Y** (o número parametrizable), caras por banda, área real sumada [m²], potencia térmica total saliente de metal/molde [W], desbalance bilateral [W], `q` medio por área [W/m²] en cada lado y valor máximo absoluto por banda. Son **bandas sobre centros de caras interfaciales**, no cortes volumétricos ni temperaturas del hierro.
- `FINAL_INTERFACE_FACE_CENTERS.csv`: **12,636 registros** del último instante, con IDs recíprocos, coordenadas de centros en **metros para sobreponer a la geometría OpenFOAM en ParaView**, coordenadas adicionales en mm, área, `q` en ambos lados y diferencia absoluta de potencia por pareja.
- `T0_SPATIAL_INTERPRETATION.json`: secuencia temporal de potencias globales nativas y los límites de interpretación, con hashes de todas las fuentes utilizadas.
- `MANIFEST_SHA256.json`: hashes verificables de las tres salidas, escritos antes de publicar el directorio por renombrado atómico. Una repetición con los mismos datos recupera el informe existente en vez de sobrescribirlo.

Los datos se escriben solo tras comprobar que la suma de las bandas reproduce los **totales del extractor nativo previamente publicados**. La tolerancia aplicada es una tolerancia técnica de suma flotante, **NO** un criterio de aceptación de la física de conducción. El nuevo informe NO puede declarar convergencia ni validación experimental.

### Ejecución local propuesta: una sola orden

Solo después de actualizar el checkout local:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/analyze_existing_t0_spatial.py
```

**Este comando ejecuta exclusivamente Python sobre artefactos existentes.** No ejecuta OpenFOAM, no recompila C++, no altera resultados numéricos. Puede detenerse si falta una fuente o cambió algún SHA; el fallo no debe obviarse.

### Visualización en ParaView 6

Ya se confirmó por captura que ParaView abre el `.foam` original con **Surface With Edges**, muestra `T` y la malla de metal. Para representar el `q` de la superficie:

1. Conservar abierta la malla del Caso B en ParaView; seleccionar `T` cuando se quiera colorear la temperatura del metal.
2. Abrir `FINAL_INTERFACE_FACE_CENTERS.csv` como tabla.
3. Aplicar **Filters → Alphabetical → Table To Points** (o buscar `Table To Points`). Usar columnas **`x_m`, `y_m`, `z_m`**, no las columnas mm, para alinear puntos con la geometría OpenFOAM en SI.
4. Colorear los puntos por `metal_outward_q_W_m2`; opcionalmente usar **Point Gaussian** para visualizar centros interfaciales. El archivo es una nube de puntos de **caras**, no una malla superficial reconstruida; no dibujar un mapa continuo inventado ni confundirlo con gradiente volumétrico `∇T`.
5. Abrir el CSV de bandas en herramienta de gráficas para visualizar `metal_area_mean_q_W_m2` en función de Y en cada tiempo y localizar qué franjas transfieren más calor.

## Puerta científica: lo que falta para pasar del C14 a fundición real

Sin sustituir por números arbitrarios:

1. **Hierro:** composición real (CE, S, Mn), `ρ(T)`, `Cp(T)`, `k(T)`, temperaturas solidus y liquidus, calor latente `L`, fuentes y unidades; registrar qué valores vienen de **JMatPro** y cuáles de medida independiente. Aclarar fase proeutéctica de austenita y región pastosa.
2. **Molde:** propiedades de arena dependientes de temperatura o rango justificado; revisar contacto interfacial real, resistencia térmica y evolución de separación si se pretende modelarla. **El `coupledTemperature` ideal actual no simula automáticamente gap ni contracción.**
3. **Condiciones de frontera e iniciales:** temperatura efectiva de vaciado, ambiente, transferencia externa (convección/radiación), geometría del termopar y condiciones de la pared del molde. No asimilar el C14 de dos sólidos y 0.1 s a un QuickCup real.
4. **Modelo de fase y flujo:** decidir la física `fluid`/solidificación con `solidificationMeltingSource` apropiada y su compatibilidad OpenFOAM Foundation14; no activar enthalpy-porosity en la ecuación de un sólido por asumir que aparece en `fvModels`.
5. **Validación:** comparar curvas `T(t)` a posiciones experimentales y balances con datos QuickCup auténticos; comprobar convergencia `Δt`/malla y sensibilidad a las 1,826 caras altamente no ortogonales antes de concluir superioridad geométrica del Caso B respecto al A.

**Veredicto actual:** G1/G2 cerrados; G3–G7 abiertos. La nueva herramienta crea el análisis espacial de flujo de la prueba C14 y prepara la siguiente decisión física, **sin ascender artificialmente el avance 2/7=29 %**.
