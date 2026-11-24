# FS-C08 — Primer núcleo conservativo líquido–sólido–gas

**Estado:** implementación ejecutable de **referencia de volúmenes finitos**, probada localmente en el contenedor del asistente (12/12 tests sintéticos). **Todavía NO es un módulo del solver OpenFOAM Foundation14**, NO ha sido compilada con `wmake` en WSL, NO es una corrida de contracción 3D de QuickCup ni fue alimentada con tablas reales JMatPro. Separación explícita de los hitos de código y de la validación física.

**Rama:** `research/fs-c08-conservative-phase-mass-20261123`, creada desde `research/fs-c02-metal-air-vof-20261117`. **FS-C07 y sus campos originales permanecen intactos**. No relanzar el antiguo `foamMultiRun` para validar este prototipo.

## Qué se implementó realmente

[`analysis_tools/fs_c08_conservative_reference.py`](../../analysis_tools/fs_c08_conservative_reference.py) es un paso temporal FV conservativo (dominio arbitrario de celdas con caras internas y flujos por frontera suministrados). Actualiza las **masas físicas** `m_liquid`, `m_solid`, `m_gas`, y no solo una fracción sólida no conservativa:

```text
m_liquid^(n+1) = m_liquid^n − Δt Σ(F_liquid outward)
                 − Δt Vcell Γ
m_solid^(n+1)  = m_solid^n  − Δt Σ(F_solid outward)
                 + Δt Vcell Γ
m_gas^(n+1)    = m_gas^n    − Δt Σ(F_gas outward)
```

`Γ` se expresa en kg/(m³·s), **positivo para líquido→sólido**, negativo para fusión. Se calcula `m_liquid + m_solid` con fuentes opuestas, de modo que la solidificación **no crea ni destruye masa metálica**. Las caras internas transportan flujos opuestos a ambos lados; en caras abiertas se exige temperatura de fase entrante para conservar el flujo entálpico. `Γ` y las velocidades/flujos son *entradas*, no una ley termocinética que ya hayamos calibrado.

`rho_l(T)`, `rho_s(T)`, `cp_l(T)`, `cp_s(T)`, `cp_g(T)` son curvas tabuladas en SI, con interpolación lineal **sin extrapolación fuera de rango**. El salto de entalpía `L` se representa una sola vez como `h_liquid(T)=∫cp_l(T)dT+L`; `h_solid(T)=∫cp_s(T)dT`, y la temperatura se recupera por inversión numérica monotónica del presupuesto de entalpía de la celda. Por tanto, convertir masa líquida en sólida conserva la energía del ledger y puede redistribuir energía latente en sensible **sin añadir una segunda fuente ficticia `ΓL`**.

Volúmenes físicos y cierre geométrico:

```text
V_l = m_l / rho_l(T)
V_s = m_s / rho_s(T)
V_g = Vcell − V_l − V_s
alpha_l = V_l/Vcell ; alpha_s = V_s/Vcell ; alpha_g = V_g/Vcell

ΔV_metal|Γ,ρ≈const = Δt Vcell Γ (1/rho_s − 1/rho_l)
```

`rho_s > rho_l` da contracción del volumen metálico por conversión a masa fija; `rho_s < rho_l` expansión. Para densidades dependientes de T, el programa reporta por separado el **cambio geométrico total** (incluye efecto térmico y transporte) y la estimación de conversión a temperatura inicial, sin confundir ambas. Rechaza masas negativas, volumen metálico superior al volumen disponible, propiedades no finitas, temperaturas fuera de tabla, influjos sin entalpía definida, fuente excesiva, y gas atrapado en volumen nulo.

Se calcula además la presión idealizada `p_g=m_g R_g T/V_g` como **diagnóstico de celda a volumen fijo**. **NO se resuelve presión de la mezcla, ecuación de momento, trabajo mecánico `p,dV`, movimiento de interfaz ni alimentación**. El cierre de entalpía implementado es **algebraico** del volumen de control; gas ideal + `cp_g` no constituye por sí solo el cierre termo-mecánico total. Por eso los resultados dicen `pressure_velocity_and_interface_not_solved=true` y `physical_3d_shrinkage_validated=false`.

### Prueba reproducible (no CFD)

```bash
# Usar la rama FS-C08 en un worktree propio para no mover FS-C07
cd ~/OpenFOAM/MasterProject
git fetch origin research/fs-c08-conservative-phase-mass-20261123
git worktree add --detach ~/OpenFOAM/FS_C08_WORKTREE FETCH_HEAD

cd ~/OpenFOAM/FS_C08_WORKTREE
python3 -B -m unittest discover -s analysis_tools -p 'test_fs_c08_conservative_reference.py' -v
python3 -B analysis_tools/fs_c08_conservative_reference.py \
  freesurface/FS-C08_conservative_phase_mass/fixtures/SYNTHETIC_TWO_CELL_REFERENCE.json
```

La configuración de ejemplo está marcada **`purpose=SYNTHETIC_TEST_ONLY`**; `rho_l=7000`, `rho_s=7300 kg/m³`, `L=200000 J/kg` y `Γ=[120,80] kg/(m³·s)` son **números arbitrarios de prueba, NO propiedades de tu hierro, NINGÚN dato JMatPro ni coeficientes físicos validados**. La salida debe preservar los límites `physical_3d_shrinkage_validated=false`, `openfoam_14_solver_executed=false`.

**Ejecución real en el contenedor del asistente (2026-11-23):** `python3 -m unittest discover` informó 12 pruebas, todas `OK`, duración ≈0.02 s. La ejecución del escenario sintético con CLI produjo balances relativos a errores de punto flotante:

```text
initial metal mass = 0.042 kg
final metal mass   = 0.042 kg
liquid → solid     = 0.0002 kg
metal mass residual= 0.0 kg
enthalpy residual  ≈ 2.91e-12 J
ΔV_metal           = −1.1741683e-9 m³  (escenario sintético)
```

Los números anteriores son resultados de **prueba de software**, no evidencia de colada real ni contracción QuickCup.

## Bloques pendientes: paso de ledger a CFD Foundation14

| Hito | Estado |
|---|---|
| Ledger por celda de `m_l/m_s/m_g` y fuentes `±Γ` | **IMPLEMENTADO + 12 pruebas sintéticas locales OK** |
| Transporte entre celdas y flujos abiertos con entalpía | **IMPLEMENTADO en referencia FV** |
| `ρ_l(T),ρ_s(T),cp(T)` tabulados y rechazo de extrapolaciones | **IMPLEMENTADO en referencia FV** |
| Volumen de vacío/gas y EOS idealizada | **DIAGNÓSTICO implementado** |
| Flujos `Γ` a partir de nucleación, solidificación real y mediciones | **PENDIENTE** |
| Propiedades por CE/S/JMatPro y trazabilidad de composición | **PENDIENTE: no inventar valores** |
| 3D `compressibleVoF` + nueva ecuación `α_sρ_s` con transporte conservativo | **PENDIENTE: no compilado/integrado** |
| Presión/velocidad/free-surface, `p,dV`, alimentación/porosidad | **PENDIENTE** |
| Acoplamiento energía CHT + calor latente sin doble conteo | **PENDIENTE nativo** |
| Integración de `alphaRhoPhi.metal` por todas las fronteras | **PENDIENTE nativo** |
| Refinamiento malla/Δt, convergencia, curvas QuickCup | **PENDIENTE** |

### Criterio de integración futuro

El `VoFSolidificationMelting` original actualiza `alpha.metal.solid` antes de `alphaPredictor`, mientras el metal VOF puede transportarse después. FS-C07 confirmó en 20/20 estados **cero violaciones `alpha_s>alpha_m+1e-8` en núcleo (alpha_m≥0.5)**, pero 7,692 incidencias en metal residual, y su **gate físico global FAIL**. La nueva versión nativa NO debe limitarse a introducir un `min(alphaSolid,alphaVoF)` tras el transporte: la conversión debe mantener `Γ` cancelando exactamente en continuidad líquido/sólido, sumar las fracciones de volumen hasta `α_a=1-α_l-α_s`, y recuperar presión/interfaz y entalpía coherentemente. Hasta entonces es **prototipo de balances FV, no CFD de contracción**.

Referencia: [FS-C07 gate 20/20](../../docs/granada/FS_C07_GATE_20DE20_VOF_Y_RUTA_MODELO_CONSERVATIVO_20261123_ES.md).
