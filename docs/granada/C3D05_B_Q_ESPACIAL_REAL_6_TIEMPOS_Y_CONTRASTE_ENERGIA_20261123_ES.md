# Caso B C3D-05 — flujo interfacial espacial ejecutado en WSL y contraste con energía sensible

**Fecha de evidencia:** 23 de noviembre de 2026 (transcripción de terminal proporcionada por el investigador).  
**Alcance:** banco térmico C14 numérico **metal y arena como dos sólidos, sin solidificación** sobre la malla STEP→Gmsh→HEX8 original.  
**Etapa vigente:** **3/7; 2/7 = 29 % de hitos técnicos**. Los resultados no son porcentajes de tesis ni prueba de exactitud física.

## 1. Ejecución observada y conservación de evidencias

El investigador ejecutó `python3 -B cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/analyze_existing_t0_spatial.py` después de `git pull --ff-only`. La herramienta imprimió:

```text
C3D05_B_SPATIAL_NATIVE_Q_PUBLISHED_NOT_PHYSICALLY_ACCEPTED
NATIVE_REAL_C3D05_HEX8_Q: faces_per_time= 12636 times= 6 vertical_bands= 12
NO_SOLVER_NO_MESH_CHANGE_NO_JMATPRO_NO_EXPERIMENTAL_ACCEPTANCE
```

Esto confirma **publicación de nuevo paquete espacial sobre los CSV de flujo nativos preexistentes**, sin repetir `foamMultiRun`, `wmake`, malla ni extracción de caras. El código verifica la procedencia de los archivos y la cadena SHA de la ejecución original; la sesión del investigador informó éxito. **El asistente no inspeccionó directamente los CSV/JSON locales del WSL ni verificó remotamente sus hashes**.

**Destino local creado:** `~/OpenFOAM/C3D05_B_T0_SPATIAL_DIAGNOSTICS_01/` con:
- `AXIAL_INTERFACE_Q_BY_TIME.csv`: 12 bandas a lo largo de Y por cada uno de los seis tiempos (72 filas, si se completó según el código).
- `FINAL_INTERFACE_FACE_CENTERS.csv`: coordenadas en metros y mm, área, q del metal/molde y residual por pareja para las 12,636 caras del último tiempo.
- `T0_SPATIAL_INTERPRETATION.json`: potencias totales por tiempo, límites de interpretación, fuentes SHA.
- `MANIFEST_SHA256.json`: SHA256 del paquete espacial inmutable.

## 2. Magnitudes de transferencia térmica obtenidas

`metal_outward_W` es la **potencia total instantánea saliente del metal hacia la arena** sobre la interfaz. `mold_outward_W` usa la normal exterior de la región molde: debe ser de signo opuesto. `peak_abs_interface_q_W_m2` es el **máximo absoluto del flujo de una cara** registrado entre las bandas, **no** promedio de área, potencia en W ni máximo temporal continuo.

| Tiempo (s) | Metal hacia arena (W) | Arena hacia metal según su normal exterior (W) | Máximo absoluto de q por cara (W/m²) |
|---:|---:|---:|---:|
| 0.00 | 0 | 0 | 0 |
| 0.02 | 31,964.349507504317 | −31,964.349507504317 | 7,916,666.107165879 |
| 0.04 | 26,922.3326721436 | −26,922.3326721436 | 5,486,496.907724503 |
| 0.06 | 23,539.61552765752 | −23,539.61552765752 | 4,626,412.033997418 |
| 0.08 | 21,098.993690449217 | −21,098.993690449217 | 4,229,733.292677608 |
| 0.10 | 19,247.798718713468 | −19,247.79871871347 | 3,955,033.0061154533 |

Se observó **potencia de interfaz positiva y decreciente entre 0.02 y 0.1 s**; no afirmar que `t=0.02 s` es el pico global durante los 100 pasos del solver, porque solo hay seis campos guardados. La línea `t=0` con `q=0` es la extracción del **campo inicial guardado**; puede depender de la inicialización de gradientes/parches y **NO demuestra que el flujo físico inicial ideal de un contacto entre 1500 K y 300 K deba ser cero**.

## 3. Hallazgo: cierre entre regiones versus integración temporal submuestreada

El ensayo C14 numérico emplea propiedades constantes (metal `ρ=6820 kg/m³, Cv_efectivo=Cp_C14=827 J/(kg K)`; arena `ρ=1500 kg/m³, Cv=700 J/(kg K)`) y volúmenes nativos aceptados (metal `4.79754032229×10⁻⁵ m³`; arena `1.02843380345×10⁻⁴ m³`). De acuerdo con las **temperaturas regionales promedio redondeadas** ya registradas en el expediente previo, de 0 a 0.1 s:

| Diagnóstico aproximado | Valor |
|---|---:|
| `ΔE_metal ≈ ρCvV(1490.2409 − 1500)` | **−2640.695 J** |
| `ΔE_molde ≈ ρCvV(324.45414 − 300)` | **+2640.694 J** |
| `∫Q_metal dt` aproximado con trapezoides en solo 6 tiempos | **+2262.984 J** |
| Diferencia `|ΔE_metal| − ∫Q dt` | **≈377.711 J (14.30 % de |ΔE_metal|)** |

**Interpretación correcta:** el cierre entre metal/molde de la energía sensible es mucho mejor que ese 14.30 %. La diferencia de ≈377.7 J corresponde a usar seis muestras de potencia *instantánea* para aproximar su integral temporal, en particular con un valor inicial `q(0)=0`. No implica por sí solo una pérdida de energía del solver ni invalida el balance volumétrico. El dato no permite identificar inequívocamente qué parte corresponde a submuestreo, inicialización de parches, integración numérica o a otras aproximaciones; es necesario documentar estas fuentes antes de asignar causas.

**Desglose ilustrativo por intervalo de 0.02 s** (temperaturas del informe anterior, cifras aproximadas):

| Intervalo (s) | Calor cedido según ΔE del metal (J) | Integral trapezoidal de q de interfaz (J) | ΔE − trapezoide (J) |
|---:|---:|---:|---:|
| 0–0.02 | 711.40 | 319.64 | **+391.76** |
| 0.02–0.04 | 582.66 | 588.87 | −6.21 |
| 0.04–0.06 | 500.91 | 504.62 | −3.71 |
| 0.06–0.08 | 443.95 | 446.39 | −2.43 |
| 0.08–0.10 | 401.77 | 403.47 | −1.70 |

La **primera banda temporal** explica la mayor parte de la discrepancia (otras bandas compensan en signo). Por ello, **no fijar un umbral de aceptación sobre la integral trapezoidal de seis campos** ni confundir el desajuste bilateral de q (~1.82×10⁻¹⁶) con exactitud de integral temporal. Ambos lados usan la misma condición de contacto y pueden balancearse por pareja aunque el tiempo esté submuestreado.

## 4. Visualización directa sin solver

Conservar el caso T0 abierto en ParaView y añadir `~/OpenFOAM/C3D05_B_T0_SPATIAL_DIAGNOSTICS_01/FINAL_INTERFACE_FACE_CENTERS.csv` como tabla. Aplicar el filtro **Table To Points** con `X Column=x_m`, `Y Column=y_m`, `Z Column=z_m`, de modo que los centros queden sobre la geometría en **metros**, y colorear por `metal_outward_q_W_m2` (usando puntos o `Point Gaussian`). El CSV describe una **nube de centros de caras**, no campos de q volumétricos ni una malla superficial continua.

El archivo de bandas permite comparar `metal_area_mean_q_W_m2` contra `y_lo_mm/y_hi_mm` y tiempo. Todavía **no se proporcionó el contenido de ese CSV**, por lo que no se pueden afirmar las franjas de mayor o menor flujo.

## 5. Decisión científica y puerta siguiente

**Ya cerrado numéricamente:** un T0 de conducción, sólido/sólido, campos de temperatura reales sobre 270,788 HEX8, balance sensible diagnóstico, 12,636 pares q y análisis espacial que descompone interfaz en 12 bandas; `G1/G2` continúan cerrados.

**Pendiente técnico:** revisar los CSV por bandas y mapas de centro de cara en ParaView, analizar gradientes cercanos a zonas de no ortogonalidad, y diseñar una forma de evaluar la integral temporal con resolución suficiente, **sin reejecutar por inercia el mismo T0 C14**. Una corrida nueva solo estaría justificada dentro de un estudio científico controlado de sensibilidad de almacenamiento/tiempo y condiciones físicas.

**Pendiente físico:** propiedades de metal y arena por temperatura con origen real JMatPro/experimental, composición CE/S/Mn, calor latente, Tliq/Tsol, transferencia de calor de contacto, condiciones ambientales/de vaciado y curvas QuickCup. **No usar el C14 sólido/sólido para declarar solidificación**.

**Estado canónico sin cambio:** **Caso B, etapa 3/7, 2/7 = 29 % hitos técnicos**; G3 físico y G4 físico aún abiertos; ninguna independencia de malla ni validación experimental demostrada.
