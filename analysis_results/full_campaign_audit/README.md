# Alcance del consolidado histórico (2026-10-08)

Los cinco archivos de esta carpeta reflejan **solo la campaña V3–V13 de 26 casos**, no todas las carpetas `cases_controlled_buoyancy/`.

- `case_metrics.csv`: **26 filas de casos**.
- `bc_pair_metrics.csv`: **13 pares B/C**.
- `bc_profile_metrics.csv`: comparación espacial de ese conjunto histórico.
- `profile_inventory.csv`: **104 perfiles = 26 casos × 4**.
- `summary.md`: texto derivado de los anteriores.

**Aún fuera de esta carpeta:** B14, C14 (ambos verificados; ver `../v14_bc_comparison/summary.md`) y C11-energy2 (ver `../c11_energy2_test/summary.md`). B11-energy2 sigue `PREPARED_NOT_RUN`; no incluir resultados copiados.

El generador `../../analysis_tools/full_campaign_audit.py` usa listas fijas de 26 casos y 13 pares. No afirmar cobertura completa hasta extender el generador, regenerar las cinco salidas con evidencia validada y ajustar el registro.

Archivo rector: `../../RUN_MASTER_PROTOCOL.md`. Registro íntegro de 30 casos: `../../RUN_CASE_REGISTRY.csv`.

Chequeo de cobertura: `python3 analysis_tools/check_run_registry.py` desde raíz. `--require-consolidated` no pasará hasta integrar todos los casos verificados.
