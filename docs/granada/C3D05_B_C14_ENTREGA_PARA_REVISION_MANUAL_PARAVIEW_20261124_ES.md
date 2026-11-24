# C3D05 Caso B C14 — entrega directa para revisión manual en OpenFOAM / ParaView

**24 de noviembre de 2026.** Prioridad solicitada por el investigador: **dejar el caso listo para abrir y comprobar personalmente los resultados; no crear más tandas de pruebas**. Se implementó y publicó un flujo práctico de visualización. La ejecución del nuevo lanzador en la WSL del investigador **todavía no está confirmada**.

## ¿Qué está verdaderamente terminado?

La simulación C14 real Foundation14 del Caso B de hierro fluido + arena sólida llegó a **10 segundos** y se conservaron **101 estados originales**. La malla documentada tiene **92,200 celdas metal + 178,588 celdas molde**, con 12,636 caras de contacto en cada lado. Se obtuvieron los campos nativos de **T, U, p, p_rgh y phaseChangeSource:alpha1**, y 100 estados de rho/phi metal. Existen resultados reales aparte de flujo conductivo metal/arena de cuatro parches, fracción sólida ponderada por volumen, inventarios energéticos referenciales y cruce temporal de 101 tiempos.

La fracción líquida ponderada por volumen a 10 s fue **0.8917029860767621**. q saliente instantánea metal→molde a 10 s: **+1581.564663 W**; molde→metal **−1581.538327 W**; salida exterior **+151.449213 W**. Conducción exterior acumulada mediante 101 muestras: **+1341.507907 J**; ΔE referencial del dominio **−1352.944201 J**, comparación parcial **−11.436294 J**. **Ninguna de estas comparaciones es conservación global verificada**, ni se ha validado QuickCup/JMatPro ni contracción.

## Entrega de revisión manual sin pruebas

Se publicaron en `main` dos archivos nuevos:

- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/ABRIR_CASO_B.sh`
- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/open_case_b_review.py`

**Una sola orden desde Ubuntu WSL, dentro de `~/OpenFOAM/MasterProject`:**

```bash
git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/ABRIR_CASO_B.sh
```

El script crea de forma aislada (solo si no existe) el workspace:

```text
~/OpenFOAM/C3D05_B_C14_PARAVIEW_REVIEW/
├── OPEN_IN_PARAVIEW/
│   ├── CASE_B_C14_10S.foam      <-- abrir en ParaView
│   ├── 0/ ... 10/               <-- 101 directorios reales de tiempo
│   ├── constant                 <-- enlace a la malla/constantes originales
│   └── system                   <-- enlace al sistema original
├── RESULTADOS_CSV/              <-- enlaces a análisis reales que ya existan
├── CASE_B_C14_MANUAL_REVIEW.json
└── LEEME_REVISION_MANUAL.txt
```

**No duplica los archivos de campos gigantes:** crea enlaces simbólicos hacia los campos reales en la carpeta CFD de solo lectura intencional. El tiempo 0–10s, las dos regiones y sus campos quedan disponibles para el lector OpenFOAM de ParaView. Los CSV de flujos y fracción de fase que ya existen aparecen enlazados en `RESULTADOS_CSV`. No recalcula ni ejecuta solver; no llama `foamMultiRun`, `wmake`, `foamToVTK` ni `unittest`. Si se puede ejecutar `paraview` desde WSL, abre automáticamente el marcador `.foam`; si no, imprime su ubicación exacta para abrirlo manualmente.

Para preparar el workspace **sin abrir ventana**:

```bash
bash cases_3d/C3D_05_step_gmsh_conformal/c14_physics/ABRIR_CASO_B.sh --prepare-only
```

Apertura manual después de la preparación:

```bash
paraview --data="$HOME/OpenFOAM/C3D05_B_C14_PARAVIEW_REVIEW/OPEN_IN_PARAVIEW/CASE_B_C14_10S.foam"
```

## Qué revisar personalmente

1. En ParaView, seleccionar `metal/internalMesh` y `mold/internalMesh` en **Mesh Regions**; activar las matrices T, U, p_rgh, p y `phaseChangeSource:alpha1` disponibles, y **Apply**.
2. Revisar la geometría 3D y contacto con **Surface With Edges**.
3. Colorear hierro y arena por **T**, desplazarse en el tiempo 0–10s, revisar la velocidad con **U** y la solidificación mediante `phaseChangeSource:alpha1` (**1 líquido, 0 sólido**).
4. Abrir las curvas existentes de `RESULTADOS_CSV` y comprobar manualmente las tendencias. Se pueden aplicar filtros **Slice, Glyph, Stream Tracer**, y usar **Plot Over Line**.
5. Informar errores concretos observados en la interfaz gráfica si falta un bloque/campo o si la instalación de ParaView no puede abrir la vista. El archivo C14 original sigue intacto.

La interfaz gráfica de WSL puede requerir que el usuario tenga ParaView instalado y soporte GUI. **El lanzador está implementado en GitHub, pero no consta todavía una ejecución exitosa de ParaView en el equipo del usuario.** Por ello no declarar que la ventana ya se abrió.

**No hay nuevas pruebas solicitadas ni entregadas en este bloque.** Caso B sigue etapa **3/7, hitos científicos formales 2/7**, porque evidencia experimental, convergencia y cierre de energía son requisitos independientes de poder visualizar la solución 3D.
