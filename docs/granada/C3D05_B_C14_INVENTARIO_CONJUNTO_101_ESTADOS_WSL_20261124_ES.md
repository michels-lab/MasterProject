# Caso B C3D-05 — metal, molde y contenido líquido: 101 estados reales contabilizados (NO conservación)

**Evidencia WSL proporcionada por el investigador, 24 de noviembre de 2026.** Los datos proceden de la simulación original Foundation14 C14 de 10s del Caso B, STEP–Gmsh HEX8 aceptada (92,200 celdas metal, 178,588 celdas arena), y de su postprocesamiento sin ejecutar CFD.

## 1. Resultado auténtico en WSL y pruebas

Se ejecutó el módulo existente `quantify_existing_case_b_c14_mold_and_combined_inventory.py`. **8/8 pruebas PASARON** (`Ran 8 tests in 0.014s / OK`). El módulo leyó **101/101 estados nativos**, `0...10s`, preservó CFD original y generó la salida separada:

`/home/michel/OpenFOAM/C3D05_B_C14_MOLD_COMBINED_REFERENCE_STORAGE_01`

Datos entregados por la herramienta:

| Parámetro WSL | Valor |
| --- | ---: |
| Celdas del molde | 178,588 HEX8 |
| Puntos nativos del molde | 211,219 |
| Caras nativas del molde | 553,893 |
| Caras internas del molde | 517,635 |
| Volumen del molde reconstruido | 0.00010284340553162189 m³ |
| Volumen `checkMesh` | 0.000102843380345 m³ |
| Discrepancia relativa | 2.4490270351713404 × 10⁻⁷ |
| Volumen celular min/max | 3.8391302052481435 × 10⁻¹¹ / 3.895640983437516 × 10⁻⁹ m³ |

**Importante:** la concordancia del volumen GLOBAL es excelente, pero el código detecta que la equivalencia con el método nativo de OpenFOAM **por celda** aún no fue demostrada y puede haber cuadriláteros no planos.

## 2. Desglose energético: variación relativa al instante inicial

| Inventario de referencia original C14 | Δ a 10 s (J) | Interpretación |
| --- | ---: | --- |
| Arena `rho_mold*Cv_mold*sum Vi*[Ti(t)-Ti(0)]` | **+20,323.651945808975** | incremento de energía sensible referencial de la arena |
| Hierro `rho_metal*Cp_metal*sum Vi*[Ti(t)-Ti(0)]` | **−13,576.397936155232** | disminución de energía sensible referencial del metal |
| Contenido **latente líquido** de metal `rho_metal*L*sum Vi*[alpha1(t)-alpha1(0)]` | **−8,100.198210984614** | cambio de contenido líquido referencial, no integral del `fvModel` |
| **Cambio combinado de referencia**, suma de tres cambios | **−1,352.9442013308708** | NO es error de conservación ni fuga de calor cuantificada |

```text
ΔE_C14,ref(0→10s)
 = ΔE_molde,sensible + ΔE_metal,sensible + ΔE_metal,latente-líquido
 = 20323.651945808975 − 13576.397936155232 − 8100.198210984614
 = −1352.9442013308708 J
```

La equivalente de solidificación **positiva** presentada en el paso anterior, `+8100.198210984614 J`, es la magnitud de referencia de `rho L [alpha(t0) - alpha(t)]`; **el contenido latente del líquido disminuyó**, `−8100.198210984614 J`. No son dos energías que se puedan sumar a la vez, y **no significa** que OpenFOAM haya liberado exactamente 8100 J mediante `solidificationMeltingSource` durante las 10 s.

Los coeficientes son **de la referencia C14 original**: hierro `rho=6820 kg/m³, Cp=827 J/kgK, L=228600 J/kg`; molde `rho=1500 kg/m³, Cv=700 J/kgK`. No provienen de JMatPro/QuickCup ni son `rho(T),cp(T),k(T)` para 8 composiciones.

## 3. Qué impide interpretar el −1.353 kJ como fuga

El modelo real incluye hierro **fluid / heRhoThermo / sensibleEnthalpy** con `solidificationMeltingSource`, y molde **solid / heSolidThermo / sensibleInternalEnergy**. El cálculo anterior es un inventario físico-referencial basado en `T, alpha1, V_i`, no reconstruye exactamente la discretización temporal ni el trabajo/source de `h` del solver. Falta cuantificar con fuente real y misma convención de signos:

- Flujo térmico de ambas caras de contacto `metal_to_mold` y `mold_to_metal` (**12,636 caras cada una**): auditar el pareado de caras, el transporte y el acoplamiento por capa/contacto.
- Intercambio exterior sobre `metalTop` y `moldOuterUnclassified` (convección/radiación, parámetros originales).
- Advección, trabajo/presión/otras fuentes conforme a las ecuaciones realmente resueltas; emisión o extracción de energía del `solidificationMeltingSource`.
- Integración temporal apropiada: **101 snapshots a Δguardado=0.1s** no son todos los **10,000 pasos Δt=0.001s**; las derivadas/trapecios no equivalen necesariamente a integrales del solver.
- Efectos numéricos de 1,826 caras severamente no ortogonales y ausencia de estudio de convergencia espacial/temporal.

**Advertencia específica para reutilización de código:** el extractor de flujo del antiguo **T0 de dos sólidos** `t0_conduction/native_flux/c3d05PatchFlux.C` crea explícitamente `solidThermophysicalTransportModel` en **ambas regiones**. Eso NO es fiel al modelo C14: el metal es un fluido. Cualquier extractor de `q` del Caso B **debe usar la selección y el transporte real de fluido para el metal**, más la ruta real del sólido para arena, y conservar ambos modelos de frontera originales. No renombrar o reutilizar el extractor T0 como si fuese prueba del flujo C14.

## 4. Estado de trabajo y siguiente paso real

**Logrado y comprobado:** CFD C14 original completado 10s, 101 campos de `alpha1`/T nativos, primer cambio de fase entre 0.2/0.3 s, primera celda completamente sólida entre 5.0/5.1 s, promedio líquido ponderado por volumen `0.8917029860767621` a 10s, 9/9 tests de cronología, 8/8 de geometría alfa, 9/9 de inventario metal y ahora 8/8 de inventario molde.

**Pendiente:** auditoría de selección nativa de modelos térmicos fluido/sólido en Foundation14, extracción en solo lectura de flujos de ambas regiones y sus límites exteriores, balance de fuente latente, campos adicionales y estudio de propiedades reales/convergencia/contracción. No existe aún evidencia de `q(t)` del C14 metal-fluido original.

Caso B se mantiene en **etapa 3/7 y 2/7 hitos técnicos físicos aceptados (29%)**. No asignar éxito a G3/G4/G5 por inventarios de referencia sin conservación verificada.
