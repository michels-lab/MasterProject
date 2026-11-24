# Caso B C3D05 — disponibilidad energética en WSL confirmada y auditoría auténtica de masa `rho/phi` preparada

**24 de noviembre de 2026.** Evidencia facilitada directamente por el investigador: OpenFOAM Foundation14, Caso B original C14 de hierro fluido + arena sólida, **10 segundos**, **101 estados guardados**, sin repetir CFD en ningún análisis.

## 1. Resultado WSL real, completado

La orden `git pull --ff-only && python3 -B -m unittest discover ... -p "test_existing_case_b_c14_energy_closure_readiness.py" -v && python3 -B .../audit_existing_case_b_c14_energy_closure_readiness.py` terminó con **9/9 pruebas aprobadas, 0 fallas** y estado:

```
C3D05_B_C14_REAL_C14_ENERGY_TERM_COVERAGE_AND_SAVED_Q_QUADRATURE_NOT_CLOSURE
```

Resultado real guardado en:

```
/home/michel/OpenFOAM/C3D05_B_C14_ENERGY_TERMS_READINESS_01
```

### Archivo nativo disponible por campo entre los 101 tiempos

| Región | Archivo de campo | Estados presentes |
|---|---|---:|
| metal | `T`, `U`, `p`, `p_rgh`, `phaseChangeSource:alpha1` | 101 cada uno |
| metal | `rho`, `phi` | 100 cada uno |
| metal | `h`, `he` | 0 |
| molde | `T` | 101 |
| molde | `e`, `he`, `rho` | 0 |

**Precisión importante:** el reporte visible establece 100/101 para `rho` y `phi`, pero no muestra cuáles etiquetas de tiempo faltan. **No asumir ni inventar el estado inicial, densidad inicial nativa o flujo de masa inicial** sin revisar las marcas de tiempo. Tampoco reconstruir `h/e` como si fueran campos conservados por OpenFOAM: no se escribieron.

El contrato C14 original contiene `solidificationMeltingSource` energéticamente enlazado a `h` (`L=228600 J/kg`), pero **no hay integral histórica nativa y explícita de fuente latente `fvModels`** disponible en estos informes.

### Sensibilidad real del trapecio a las muestras temporales

| Intervalo entre muestras guardadas | Número | Energía conductiva exterior integrada `∫q(t)dt` [J] | Diferencia frente a 0.1s [J] |
|---|---:|---:|---:|
| 0.1 s | 101 | 1341.5079070212455 | 0 |
| 0.2 s | 51 | 1335.0700466397634 | −6.437860381482096 |
| 0.5 s | 21 | 1315.8423511587207 | −25.665555862524798 |
| 1.0 s | 11 | 1284.1978120372619 | −57.31009498398362 |

**NO representa el error contra el integrador del solver original de `dt=0.001s`**: el 0.1s es solo la más fina de las salidas guardadas.

El desglose de `ΔE_referencia+∫q_conductivo` comparado con los archivos reales quedó:

- Metal: **−181.0484911419626 J**, comparación incompleta, NO residual de conservación.
- Molde: **+169.49691366618936 J**, comparación incompleta, NO residual de conservación.
- Suma de regiones con doble interfaz: **−11.551577475773229 J**.
- Suma referencial de almacenamiento + solamente conducción exterior: **−11.436294309626874 J** (diferencia ~0.115283 J = integral neta firmada de interfaz). **No calor perdido ni error de conservación.**

## 2. Nuevo trabajo real publicado EN CÓDIGO — no ejecutado todavía

Se implementó el analizador:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/analyze_existing_case_b_c14_metal_mass_phi.py`

Y **11 pruebas nuevas de fuente**:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_metal_mass_phi.py`

El módulo no necesita recompilar ni ejecutar CFD y nunca escribe en las carpetas originales. Se limita a analizar:

1. **Los 100 campos `rho` del hierro disponibles en el CFD original**, cada uno con 92,200 valores si el formato ASCII es legible; volumen por celda estimado mediante `owner/neighbour/faces/points` auténticos, con discrepancia de volumen global contra `checkMesh` ya documentada. Produce masa metálica `M(t)=Σ_i rho_i(t)V_i`, densidad ponderada por volumen y mínimo/máximo de densidad real de cada estado.
2. La fracción líquida `alpha1` original guardada y una fracción sólida **modelada** ponderada por masa `Σrho_iV_i(1−alpha_i)/Σrho_iV_i`. También conserva `L` contractual, pero `rhoL(1−alpha)` es **inventario equivalente del modelo**, NO energía liberada por `fvModels` de solver ni contracción volumétrica.
3. **Los 100 archivos `phi` originales guardados:** inspecciona el encabezado `surfaceScalarField`, dimensiones de masa por tiempo `[1 0 -1 0 0 0 0]`, nombres de parches `metalTop` y `metal_to_mold`, cantidad real de caras, y valores guardados por cara (uniformes o no uniformes). Integra el flujo firmado saliente por parche [kg/s] exclusivamente cuando las unidades y serializaciones son comprobables. Si es binario, inaccesible o el bloque de cara no se puede leer, informa **NO DISPONIBLE**, jamás `0` inventado.
4. Calcula un escrutinio **limitado** de `ΔM+∫phi_exterior dt` usando solo tiempos consecutivos donde existen realmente `rho` y `phi`. No puentea huecos de datos y nunca infiere `t=0` a partir del valor `rhoRef=6820 kg/m³`. Reporta explícitamente `NOT_CONTINUITY_RESIDUAL`: el muestreo 0.1s no equivale a los pasos solver 0.001s, ni incluye fuentes/efectos no auditados.
5. Genera un destino nuevo inmutable con CSV de tiempo, JSON de reporte y manifiesto SHA de malla, campos originales, contrato físico y fuentes de datos térmicos previos. Preserva todos los archivos originales.

### Orden de ejecución en Ubuntu / WSL (NO CFD ni recompilación)

Desde `~/OpenFOAM/MasterProject`:

```bash
git pull --ff-only && \
python3 -B -m unittest discover \
  -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests \
  -p "test_existing_case_b_c14_metal_mass_phi.py" -v && \
python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/analyze_existing_case_b_c14_metal_mass_phi.py
```

El destino nuevo será:

```
~/OpenFOAM/C3D05_B_C14_NATIVE_RHO_PHI_MASS_01
```

**Las 11 pruebas y este nuevo análisis NO tienen resultados observados en WSL**. No citar números reales de `rho`/masa/`phi` hasta ejecutar sobre archivos auténticos. Si el lector de `phi` detecta estructura inesperada, preservará el archivo y reportará indisponibilidad sin inferir flujo de masa cero.

## 3. Restricciones científicas

No se dispone todavía de campos `h/e` guardados, valores directos de la fuente energética `solidificationMeltingSource` en los pasos del solver, convergencia dt/malla, termodinámica `rho(T),Cp(T),k(T)` validada con JMatPro, curva QuickCup calibrada, balance de trabajo y transporte entálpico, ni física de contracción/alimentación. **La comparación térmica pequeña de −11.436 J no cierra el balance**.

**Hitos canónicos:** C3D05-B etapa **3/7**, **2/7 hitos técnicos cerrados (29%)**. G3–G7 permanecen abiertos.
