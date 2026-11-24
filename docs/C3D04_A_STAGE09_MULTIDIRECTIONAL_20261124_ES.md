# C3D04-A — barridos tridimensionales, etapa 09
24-11-2026. 8/10 hitos operativos (80%). El investigador solicita ampliar la comparación después de observar diferencias entre 2D y 3D.

## Entrega
Ejecutor `cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/analyze_c14_a_multidirectional.py`, basado en los 101 estados del caso visual verificado. No modifica el CFD ni el caso visual; copia únicamente los campos requeridos y verifica sus SHA y los diccionarios al final. No ejecuta solver.

- 12 diámetros XZ: 0°, 45°, 90°, 135° en alturas físicas de 10, 20, 30 mm. 81 puntos nominales por diámetro, radio máximo 20 mm, paso 0.5 mm. 135° se orienta con X creciente (el signo del eje se invierte respecto a +135°); coordenadas reales documentadas.
- 5 verticales: centro y desplazamientos de ±10 mm en X y Z, 80 puntos de 0.25 a 39.75 mm de altura desde base.
- Estadística radial por 0.5 mm: media, mínimo, máximo, desviación estándar poblacional y conteo de puntos válidos, hasta ocho direcciones angulares (centro contado una vez). No es promedio azimutal continuo ni se presupone axisimetría. U radial y tangencial proyectadas en base local, no definidas en el centro.
- Cuadratura seccional uniforme XZ de 41×41 puntos candidatos por altura (1681), en centros de cuadrículas del bounding box real. Solo puntos dentro del metal. Peso igual ΔxΔz: media de área APROXIMADA, no integral exacta de corte de poliedros. Se informa área estimada, número válido y valores T, alpha y U. La resolución puede configurarse con --grid impar entre 11 y 81. No constituye convergencia de cuadratura ni de malla.
- T, Ux/Uy/Uz, |U|, p_rgh, alpha1, gradT para líneas; CSV y panel HTML autónomo. Los resultados fuera del metal son vacíos, nunca cero ni extrapolados.
- Conserva líneas previas y comparador 2D–3D separado; no mezcla el promedio volumétrico con promedio de sección. Los barridos no validan el modelo experimentalmente.

## Orden WSL
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/analyze_c14_a_multidirectional.py" \
  --out "$HOME/OpenFOAM/C3D04_A_C14_MULTIDIRECTIONAL_01" &&
explorer.exe "$(wslpath -w "$HOME/OpenFOAM/C3D04_A_C14_MULTIDIRECTIONAL_01/Barridos_C14_3D_A.html")"
```

Código publicado; ejecución WSL y datos nuevos no observados. No se solicita prueba manual previa. La comparación cuantitativa con C14 2D sigue pendiente de acceso a los snapshots reales de referencia. No se altera B ni FS.
