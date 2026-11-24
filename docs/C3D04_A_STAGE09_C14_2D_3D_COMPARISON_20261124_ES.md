# Caso A — comparación C14 2D y 3D-A
24-11-2026. Etapa 09/10, 8/10=80% hitos operativos. El investigador confirmó visualización del caso A y solicitó comparar curvas de enfriamiento y perfiles con C14 2D antes de nuevos CFD.

## Entrega funcional
Ejecutor `cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/compare_c14_2d_3d_a.py` (publicado, ejecución WSL no observada). Busca snapshots reales del C14 2D en MasterProject/OpenFOAM, o acepta --case2d explícito. Exige identidad de parámetros físicos originales del C14; registra controlDict. Nunca corre solver. No crea datos ficticios si falta el 2D.

- Usa centros X/Z de bounding box nativo de metal (referencia 2D x=20,z=5 mm; 3D usa su propio centro), alturas físicas 10/20/30 mm desde base; y=−30/−20/−10 mm en A. No implica idéntica geometría.
- Cuatro líneas homologadas: tres horizontales y una vertical central, 80 posiciones nominales separadas 0.5 mm en el intervalo 0.25–39.75 mm de coordenada común. Registra coordenadas reales de cada caso y puntos válidos; no extrapola.
- Temperatura, U componentes y magnitud, p_rgh, alpha1, gradT componentes y magnitud si disponibles/reconstruidos nativamente. Misma interpolación cellPoint de OpenFOAM. Extrae curvas centrales a 10/20/30 mm y medias volumétricas; tasas de enfriamiento calculadas sobre tiempos guardados comunes, no dt solver.
- CSV completos de perfiles, curvas, cobertura, medias y RMSE térmico; dashboard HTML autónomo interactivo con selector de tiempo/variable. Preserva archivos originales T del probe 2D si existen, sin mezclar su resolución temporal con los tiempos comunes.
- Caso visual original intacto: se usan copias de muestreo independientes. No se afirma independencia de malla o validación experimental. Cobertura parcial se etiqueta como tal. Si hay múltiples C14 igualmente completos, debe elegirse explícitamente el correcto.

## Una orden WSL, sin micropruebas
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/compare_c14_2d_3d_a.py" \
  --out "$HOME/OpenFOAM/C3D04_A_C14_2D_3D_COMPARISON_01" &&
explorer.exe "$(wslpath -w "$HOME/OpenFOAM/C3D04_A_C14_2D_3D_COMPARISON_01/Comparacion_C14_2D_3D.html")"
```

Estado: código publicado, datos numéricos C14 2D local no inspeccionados todavía. Si no existen snapshots nativos no se promete comparación espacial ni se relanza CFD automáticamente. Caso B/FS no modificados.
