# Caso B C3D-05 — inventario energético real de metal confirmado y auditoría térmica del molde preparada

**24 de noviembre de 2026**. Esta nota distingue explícitamente **(1) los cálculos realmente ejecutados en WSL**, **(2) el código nuevo publicado todavía no ejecutado**, y **(3) el balance energético físico pendiente**.

## 1. Datos nuevos CONFIRMADOS en WSL

El investigador ejecutó **9/9 tests** del módulo `quantify_existing_case_b_c14_energy_inventory.py`, todos `ok` (`Ran 9 tests in 0.014s`) y el módulo de lectura sobre **101 estados nativos** del cálculo completo original C14 de 10 s con hierro fluido+arena sólida:

```json
{
  "status": "C3D05_B_C14_REAL_METAL_C14_SENSIBLE_LATENT_EQUIVALENT_INVENTORY_NO_ENERGY_CLOSURE",
  "out": "/home/michel/OpenFOAM/C3D05_B_C14_SENSIBLE_LATENT_EQUIVALENT_01",
  "states": 101,
  "reference_metal_sensible_delta_from_t0_J": -13576.397936155232,
  "modeled_latent_equivalent_solid_change_from_t0_J": 8100.198210984614,
  "final_alpha1_liquid_volume_weighted": 0.8917029860767621,
  "actual_CFD_native_fvModel_source_integral_computed": false,
  "interfacial_external_energy_balance_validated": false,
  "experimental_validation": false,
  "NO_NEW_CFD": true
}
```

Interpretación:
- **Sensible de metal = −13.5763979 kJ**, cambio calculado respecto de los campos nativos t0 con `rho_C14=6820 kg/m³`, `Cp_C14=827 J/(kg K)` y volumen real nativo individual de 92,200 celdas HEX8.
- **Latente EQUIVALENTE por aumento de complemento sólido = +8.1001982 kJ** según `rho_C14 L_C14 sum_i(V_i [alpha_i(0)-alpha_i(t)])`, con `L_C14=228600 J/kg`. **No** es integral directa de `solidificationMeltingSource` en el solver.
- **Signo termodinámico:** si se define el inventario latente del metal líquido `E_latente_contenido∝rho L sum(V alpha)`, entonces su **cambio respecto a t0 es −8.1001982 kJ**, no +8.1001982 kJ. No confundir «equivalente positivo de solidificación» con energía latente almacenada, ni inferir `Q` real liberado.
- El resultado volumen-ponderado previo se conserva: `alpha1_V(t=10s)=0.8917029860767621`, complemento sólido del modelo = `0.10829701392323787` = **10.8297%** (distinto al 15.7579% por celdas). Ninguna es medición experimental QuickCup.
- Faltan en este reporte la energía del molde, las condiciones de intercambio completas, `q_{metal→mold}`, energía del aire/exterior, efectos advectivos y la integral nativa del término `fvModel`. **No se ha cerrado la conservación energética.**

## 2. Código NUEVO publicado y aún no ejecutado en WSL

Script:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/quantify_existing_case_b_c14_mold_and_combined_inventory.py`

Pruebas negativas/de geometría:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_mold_and_combined_inventory.py` (**8 tests en código; ejecución real/CI todavía no confirmada**).

Este código nuevo recupera **solo en lectura** la corrida completa C14, el postrun nativo SHA y el inventario metal original y sus firmas, y calcula:

1. Para la arena/molde, volúmenes de cada una de las **178,588 celdas** desde `constant/mold/polyMesh/points,faces,owner,neighbour` originales, exigiendo caras quad y volúmenes individuales positivos. Compara el volumen total contra `0.000102843380345 m³` aceptado por `checkMesh` (tolerancia de integridad 0.5%, no certificación de volumen nativo por celda).
2. A cada una de las 101 salidas `t=0..10s`, calcula `Delta E_molde,sensible(t)=rho_molde Cv_molde sum_i Vi[T_i(t)-T_i(0)]` con el **C14 original**, `rho_molde=1500 kg/m³`, `Cv_molde=700 J/kg/K`. No altera los campos ni la geometría.
3. Recicla **los números del inventario metálico ya verificado y archivado**: `Delta E_metal,sensible(t)` y `Delta E_equivalente_solidificación(t)`.
4. Genera una cantidad exclusivamente **de referencia de almacenamiento térmico del modelo**, con signos consistentes:
```text
Delta E_referencia_almacenado(t) =
  Delta E_molde,sensible(t)
  + Delta E_metal,sensible(t)
  - Delta E_equivalente_solidificación(t)
```
El último término es negativo porque la energía latente **contenida en la fracción líquida** disminuye al solidificar. Esta suma NO es verificación de energía `fvModel`, ni balance global aceptado, ni error de conservación hasta conocer flujos y términos de las ecuaciones que realmente resolvió OpenFOAM.
5. Genera CSV de 101 estados, JSON y SHA en nueva carpeta aislada, sin reejecutar `foamMultiRun`.

Destino aislado `~/OpenFOAM/C3D05_B_C14_MOLD_COMBINED_REFERENCE_STORAGE_01`, preserva la carpeta CFD original y anteriores análisis.

### Próxima orden WSL (SOLO LECTURA, NO CFD)

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B -m unittest discover -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests -p "test_existing_case_b_c14_mold_and_combined_inventory.py" -v && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/quantify_existing_case_b_c14_mold_and_combined_inventory.py
```

**No se ha observado ejecución de este bloque en WSL** y NO se conoce `Delta E_sensible_molde(10s)` ni la suma de almacenamiento todavía. Si las pruebas fallan o la malla no cumple, el segundo comando no corre por `&&`, y los datos existentes quedan preservados.

## 3. Pendientes científicos y hitos

Todavía hay que integrar en realidad los flujos térmicos en la interfaz `metal_to_mold / mold_to_metal`, la salida por `metalTop`, el exterior del molde, los términos advectivos/energía del flujo y el aporte temporal nativo de `solidificationMeltingSource`; después comparar contra cambios de inventario, con discretización temporal compatible. **La aparente diferencia entre términos no es fuga ni error si no se han incluido todos los flujos de frontera o fuentes**.

No se han incorporado `rho(T),Cp(T),k(T)` JMatPro para las ocho fundiciones, curvas experimentales QuickCup, recalescencia validada, corrección/sensibilidad de las **1,826 caras severamente no ortogonales**, convergencia de malla/dt ni contracción/alimentación.

**Estado canónico: Caso B etapa 3/7, 2/7 hitos técnicos cerrados (29%), G3–G7 físicos abiertos.** El 10 s CFD C14 y `alpha1` sí se ejecutaron y observaron, pero aún no hay validación energética global o experimental.
