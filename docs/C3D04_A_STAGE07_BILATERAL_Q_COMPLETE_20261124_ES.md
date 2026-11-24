# C3D04-A — cierre operativo etapa 07, flujo bilateral real C14

Fecha: 24-11-2026. Fuente: stdout WSL aportado por el investigador, ejecución desde 8d1b635ba; no se ha descargado el JSON local original. CFD 10 s V4/T02 intacto, no nuevo solver.

## Evidencia
- 101 estados de 0 a 10 s; 808 registros de ocho parches; 2496 pares de caras de interfaz a t=10 s.
- q nativo fluido/sólido: metal→molde +1524.6443291594894 W; molde→metal −1524.670518304915 W. Suma de valores absolutos de residuos por pares: 1.7034725937727646 W. No confundir suma local con desajuste neto.
- Diferencias relativas máximas respecto a heatFlux agrupado del metal: contacto 4.773058032783712e-7; superior 4.748334299565785e-6.
- Integrales trapezoidales 0.1–10 s: metal→molde 19462.897313016172 J; molde→metal −19462.487618875242 J; metal exterior 1207.2580929086996 J; molde exterior 142.45895897494808 J.
- Desajuste firmado interfaz 0.40969414092978695 J; inventario nominal molde más flujo saliente −1.4807794850352707 J; inventario nominal combinado más flujo exterior 0.13051585053227654 J.
- Original y reporte previo SHA intactos. Se añadió interpolate(kappa) harmonic exclusivamente en la copia q-only; no se alteraron los diccionarios originales.
- Reporte local: ~/OpenFOAM/C3D04_A_C14_BILATERAL_NATIVE_Q_01/C3D04_A_C14_BILATERAL_NATIVE_Q_REPORT.json.

## Alcance
Hito 07 operativo DONE (corrida, estabilidad observada, diagnóstico energético nominal). Etapa 08 IN_PROGRESS, 7/10=70% de hitos operativos; no porcentaje de validez física. No se verifica conservación discreta dt=0.001 s: q reconstruido y trapecios sobre 0.1 s; inventario latente nominal. Etapas 09–10 (conservación, sensibilidad de malla/tiempo, QuickCup) pendientes.

## Entrega etapa 08
Publicador de copia visual autónoma C14 101 tiempos, campos nativos originales y derivados, perfiles verticales interiores corregidos, CSV energéticos/flujo bilateral, log y análisis volumétrico de T, alpha, velocidades y aceleraciones Darcy/flotación/presión. No ejecutar CFD ni repetir grupos nativos. Una sola orden funcional, sin exigir pruebas unitarias manuales al investigador. Código publicado; salida WSL y apertura gráfica aún no observadas.

```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/publish_c14_a_visualization_and_solidification.py" \
  --out "$HOME/OpenFOAM/C3D04_A_C14_VISUALIZATION_01"
```

Abrir C3D04_A_C14.foam en ParaView o carpeta completa en FoamLens. Copia de visualización, no para relanzar solver. Los perfiles verticales corregidos son un tramo interior de 14.699706 mm, no equivalencia espacial con toda la altura 2D.
