> **27-11-2026 — Uva + Granada:** este archivo y sus CSV son un corte histórico, no el catálogo vigente. El [catálogo independiente de 51 casos](../evidence_catalog_20261127/README.md) registra 31 con métricas importadas y documenta 40 métricas espaciales con tiempos distintos y la insuficiencia de muestras comunes V6/V8. No usar sus RMSE de alpha media cero como concordancia temporal. El generador legacy exige ahora `--out` nuevo, por ejemplo `python3 analysis_tools/full_campaign_audit.py --out /tmp/c14_legacy_reproduction_01`; no sobrescribe este archivo. Su algoritmo no constituye el comparador corregido. Los estados antiguos de B11-energy2 y 30 casos que figuran abajo pertenecen al corte histórico.

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
