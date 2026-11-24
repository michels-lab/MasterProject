# Caso B C3D-05 — flujos de conducción vs inventario: 101 tiempos CONFIRMADOS; auditoría siguiente preparada

**24 de noviembre de 2026.** Esta nota documenta el **resultado real compartido por el investigador desde WSL**, separado del **nuevo código publicado que aún no se ha ejecutado allí**.

## 1. Resultado real y reproducible observado

Comando `git pull --ff-only`, las **12 pruebas** `test_existing_case_b_c14_q_storage_join.py` y `compare_existing_case_b_c14_native_q_and_storage.py` finalizaron `OK` y `C3D05_B_C14_101_SAVED_Q_VS_REFERENCE_STORAGE_DIAGNOSTIC_NOT_ENERGY_CLOSURE`, respectivamente.

- 12/12 pruebas pasadas en 0.033 s.
- 101/101 estados de `t=0...10s` combinados, sin error de SHA de la corrida original ni divergencia entre tiempos.
- Salida real publicada: `/home/michel/OpenFOAM/C3D05_B_C14_Q_VS_REFERENCE_STORAGE_01`.
- Sin `foamMultiRun`, sin `wmake`, sin volver a extraer flujos ni modificar la solución.
- El origen de `q` es **Foundation14 nativo en un caso sombra que añadió `interpolate(kappa) harmonic;` SOLO a la copia del diccionario del molde**, preservando la intención de `interpolate((kappa|Cv)) harmonic;` del C14 original. La historia de `q` tiene 101 muestras guardadas cada 0.1 s; no es la integral exacta sobre `deltaT=0.001s` del solver.

### Potencia conductiva en t=10s

| Potencia saliente de la región | W |
| --- | ---: |
| Hierro → interfaz | +1581.5646631744044 |
| Molde → interfaz (normal opuesta) | −1581.5383267429747 |
| Desajuste firmado instantáneo de interfaz | +0.026336431429626828 |
| Cara superior hierro | +117.06292503343666 |
| Exteriores molde | +34.38628817469787 |
| Exteriores totales | +151.44921320813452 |

### Integrales trapezoidales de 101 muestras (0.1s) + inventario original

| Magnitud | J |
| --- | ---: |
| Salida conductiva hierro hacia interfaz, integral de muestras | +20283.45236535595 |
| Salida conductiva molde hacia interfaz, integral de muestras | −20283.567648522097 |
| Suma firmada de intercambio de interfaz | **−0.11528316616279427** |
| Salida conductiva hierro superior | +1212.0952906419318 |
| Salida conductiva molde exterior | +129.41261637931336 |
| Total conducción saliente exterior | **+1341.5079070212457** |
| ΔE sensible hierro de referencia C14 | −13576.397936155232 |
| ΔE contenido latente líquido de referencia C14 | −8100.198210984614 |
| ΔE sensible molde de referencia C14 | +20323.651945808975 |
| **ΔE combinado de referencia** | **−1352.9442013308708** |
| **ΔE combinado + conducción exterior integrada** | **−11.436294309625055 — NO RESIDUO DE ENERGÍA** |

La última diferencia equivale a **0.8525 %** de la integral de conducción exterior `1341.5079 J`, pero este porcentaje NO demuestra conservación, convergencia ni fidelidad física. Es una comparación parcial entre magnitudes que no proceden de la misma integración discreta de entalpía del solver. La equivalencia numérica cercana puede ser real, accidental o compensada por fuentes y términos omitidos. No significa calor perdido de `11.436 J`.

El control de interfaz (12,636 pares de caras/normal opuesta) demuestra coincidencia geométrica y concordancia global entre los dos lados, **no** igualdad térmica por cada cara: la suma de diferencias absolutas cara por cara a t10 es `1.8703362871771045 W`.

## 2. Nueva descomposición numérica por región (aritmética a partir de resultados WSL)

Se pueden calcular sin nueva CFD, utilizando solo datos observados:

```text
Metal:
  ΔE_referencia_metal = -13576.397936155232 - 8100.198210984614
                      = -21676.596147139848 J
  Q_conductivo_saliente_metal = 20283.45236535595 + 1212.0952906419318
                             = +21495.547655997885 J
  Diferencia parcial = -181.0484911419626 J        (NO RESIDUO)

Molde:
  ΔE_referencia_molde = +20323.651945808975 J
  Q_conductivo_saliente_molde = -20283.567648522097 + 129.41261637931336
                              = -20154.155032142786 J
  Diferencia parcial = +169.49691366618936 J       (NO RESIDUO)

Suma de diferencias parciales (INCLUYE interfaz interna): ≈ -11.5515774758 J
Suma de comparación de DOMINIO exterior (SIN doble conteo interfaz):
  ΔE_referencia_combinada + Q_conductivo_exterior = -11.436294309625055 J
```

La diferencia entre ambas sumas (~−0.115283 J) es precisamente la integral firmada de las dos caras internas. No mezclar una integral de frontera interna con la exterior al intentar evaluar un único dominio.

## 3. Próximo avance preparado y publicado en código

Nuevo módulo:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/audit_existing_case_b_c14_energy_closure_readiness.py`

Con **9 pruebas nuevas de código**:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_energy_closure_readiness.py`

**Aún no ejecutados en WSL**, por lo que no afirmar aprobación de estas nueve pruebas ni conocimiento actual de los archivos `h,e,rho,phi` guardados.

Su tarea:

1. Reabrir únicamente los informes y CSV originales, SHA-verificar `q(t)` y el inventario de 101 tiempos contra el informe de unión y contra el stage/log original de CFD.
2. Emitir descomposición de conducción e inventarios numéricos por metal y molde con etiqueta `NOT_ENERGY_RESIDUAL`, respetando signos.
3. Cuantificar sensibilidad *del trapezoide entre muestras guardadas* para intervalos `0.1/0.2/0.5/1.0s`: **no extrapola** ni estima un error del integrador original de `0.001s`.
4. Revisar existencia de `T,alpha1,U,h,he,rho,p,p_rgh,phi` en metal y `T,e,he,rho` en molde, para cada uno de los 101 directorios originales, sin inventar campos ausentes; verificar que el `fvModels` original del C14 especifica `solidificationMeltingSource` para `h` y deja explícito que **no está integrado temporalmente**.
5. Preservar todas las carpetas anteriores y escribir un directorio NUEVO aislado con JSON de disponibilidad, CSV de sensibilidad y manifiesto SHA. Nunca invocar el solver ni el extractor q de nuevo.

**Comando único para WSL (nada de CFD ni C++):**

```bash
git pull --ff-only && \
python3 -B -m unittest discover \
  -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests \
  -p "test_existing_case_b_c14_energy_closure_readiness.py" -v && \
python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/audit_existing_case_b_c14_energy_closure_readiness.py
```

Destino previsto:

`/home/michel/OpenFOAM/C3D05_B_C14_ENERGY_TERMS_READINESS_01`

## 4. Lo que separa esto de una demostración de conservación

El C14 original contiene hierro fluido con `heRhoThermo/hConst/sensibleEnthalpy`, molde sólido con `heSolidThermo/eConst/sensibleInternalEnergy`, `solidificationMeltingSource` sobre todas las celdas del metal (`energy h`, `L=228600 J/kg`), `alpha1e=0.8` y `relax=0.1`. Son hechos del contrato y código fuente C14, NO significa que el término latente aplicado por `fvModels` se haya integrado numéricamente.

Antes de llamar conservación al balance se requieren las ecuaciones discretas reales, la integral de `fvModels` en cada paso, entalpía/advección y trabajo de presión, tratamiento del flujo térmico radiativo/convectivo exterior, conservación geométrica y de masa, sensibilidad temporal y de malla, y QuickCup/JMatPro experimental. El solver guardó campos cada 0.1 s, no los 10,000 pasos completos.

**Estado canónico C3D05-B: etapa 3/7; 2/7 hitos técnicos aceptados (29 %); G3–G7 abiertos.**
