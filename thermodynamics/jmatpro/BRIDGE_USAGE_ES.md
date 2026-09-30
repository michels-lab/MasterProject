# Cómo usar el bridge JMatPro → OpenFOAM

1. Exportar de JMatPro una tabla numérica por composición.
2. Convertir/guardar las columnas con nombres:
   - `T_K`
   - `rho_kg_m3`
   - `Cp_J_kgK`
   - `k_W_mK`
   - `fL`
3. Ejecutar:

```bash
python3 analysis_tools/jmatpro_property_bridge.py thermodynamics/jmatpro/raw/<caso>/properties.csv
```

Por defecto el ajuste de beta usa 1473.15–1773.15 K. Cambiarlo explícitamente si el rango líquido real de la composición es distinto.

Ejemplo:

```bash
python3 analysis_tools/jmatpro_property_bridge.py \
  thermodynamics/jmatpro/raw/CE3p9_S0p05/properties.csv \
  --beta-min-T 1500 \
  --beta-max-T 1600 \
  --rho-ref-T 1500 \
  --Tsol <TS_JMATPRO> \
  --Tliq <TL_JMATPRO> \
  --alpha1e 0.8
```

El script no modifica OpenFOAM. Solo genera evidencia procesada en:
`analysis_results/jmatpro_openfoam_audit/processed/`.
