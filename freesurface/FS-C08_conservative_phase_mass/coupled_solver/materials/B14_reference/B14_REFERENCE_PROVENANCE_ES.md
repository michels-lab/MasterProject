# FS-C08 — B14 como baseline de referencia (24-11-2026)

Decisión explícita del investigador: utilizar las propiedades del caso B14, no una aleación bibliográfica nueva. No se localizaron exportaciones JMatPro en las dos búsquedas por nombre del investigador; no repetirlas. La fuente versionada es [B14 castIron](https://github.com/michels-lab/MasterProject/blob/49c3ede24c0aadfbc9fce9fcb4e9963c87f096ec/cases_controlled_buoyancy/B14_topFixedFlux_explicitRef/constant/metal/materials/castIron) y [B14 fvModels](https://github.com/michels-lab/MasterProject/blob/49c3ede24c0aadfbc9fce9fcb4e9963c87f096ec/cases_controlled_buoyancy/B14_topFixedFlux_explicitRef/constant/metal/fvModels).

## Traducción y límites

- B14 original: icoTabulated con una única curva rho(T), Cp=827 J/kg/K, mu=0.0055 Pa s, Pr=.14, Tsol=1423 K, Tliq=1473 K, L=228600 J/kg, alpha1e=.8, Cu=100000 1/s, q=.001, relax=.1, rhoRef=6930 kg/m3, beta=0 en fvModels. No se cambia B14.
- FS-C08 requiere dos densidades; la curva B14 no permite identificarlas de forma única. La nueva hipótesis separa rama sólida hasta 1423.15 K y líquida desde 1473.15 K, preservando los puntos originales de cada rama. La parte líquida se extiende con pendiente -0.8 hasta 1423.15 K (6860); la sólida con -0.2 hasta 1473.15 K (6890). Fuera de la zona donde la rama puede coexistir se mantiene su extremo constante (extensión de fase inactiva). El rho efectivo en la zona pastosa no reproduce exactamente la curva B14 original. Por encima de 1773.15 K se hereda la extrapolación diagnóstica original.
- Ley de equilibrio: aproximación volumétrica B14 alpha1e=.8 (20% sólido al inicio eutéctico), lineal entre 1423 y 1473 K; conversión a fracción másica por rho_s y rho_l cada 1 K. Salto eutéctico regularizado entre 1422 y 1423 K (ancho numérico 1 K, no subenfriamiento medido). No reproduce el parámetro de relajación por iteración .1; equilibrium es una decisión provisional y no cinética calibrada.
- Cv_l=Cv_s=827 es aproximación explícita Cp≈Cv. k_l=k_s=Cp*mu/Pr=32.489285714 W/m/K. L de entalpía usado como aproximación de diferencia de energía interna en Tref=1423 K. Cu y q transferidos directamente.
- La viscosidad y termo nativo de gas/metal, BC, malla y molde provienen del caso FS-C07 al preparar el nuevo caso. Verificar que mu metálica nativa es 0.0055 Pa s; no se modifica a ciegas el archivo origen. El diccionario de fase no controla la viscosidad. No afirmar fidelidad integral a B14 hasta comprobarlo.
- No hay curva de expansión grafítica ni propiedades por CE/S certificadas. Este material no es un resultado JMatPro, ni un hierro gris calibrado, ni evidencia experimental. Se permite solamente como referencia de ingeniería para la primera ejecución real de código CFD y estudio numérico; no permite atribuir la contracción calculada a la composición experimental ni hacer una validación física.

## Ejecutar desde WSL

```bash
cd ~/OpenFOAM/FS_C08_WORKTREE
git fetch origin research/fs-c08-conservative-phase-mass-20261123
git switch --detach FETCH_HEAD
python3 -B analysis_tools/run_fs_c08_real_cfd.py \
  --source "$HOME/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4" \
  --material "$PWD/freesurface/FS-C08_conservative_phase_mass/coupled_solver/materials/B14_reference/fsC08Material"
```

No ejecutar si el ambiente Foundation14 no está activo o la viscosidad nativa es distinta de B14. El runner crea caso aislado y conserva logs. Ninguna ejecución física se ha realizado al publicar este diccionario. Una corrida completa y balances de masa no equivalen a validación energética o experimental; verificar evolución de interfaz y separar contribuciones de fase y temperatura.
