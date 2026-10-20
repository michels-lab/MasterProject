# GRANADA GRANDE — paquete independiente de evidencia V15/V16

Fecha: 2026-10-20. Estado: **CANDIDATO EN RAMA, SOLO LECTURA**. No ejecuta OpenFOAM, no modifica casos históricos ni confirma validación física/experimental.

## Motivo y objetivos

Después del push del investigador del 15 de octubre hay salidas de B15/B16/C15/C16 y sus padres B14/C14. La inspección preliminar en `analysis_results/v15_v16_postpush_20261015/README.md` encontró desviaciones pequeñas en temperatura central; B15 y C15 superaron ligeramente el valor configurado `maxCo = 0.25`. La continuidad acumulada en B exige interpretación física aparte. No cerrar J0 (JMatPro), G1 experimental, ni aprobar una simulación solamente porque llega a 10 s.

Los PR activos #18/#19 poseen C3D-01, roadmap, malla y ciertas bitácoras. Este bloque no toca sus archivos ni crea resultados nuevos en carpetas CFD.

## Entregables relacionados

**A — Auditoría numérica reproducible**: `analysis_tools/granada_v15v16_postrun.py`. Compara las cuatro parejas B14→B15, C14→C15, B14→B16 y C14→C16 usando sondas originales y una grilla común de 0.01 s **sin extrapolar**; calcula RMSE, máximo |ΔT| y diferencia final. Cada caso registra hash SHA-256, número de muestras y último tiempo para la sonda `T`, `CourantMax_0` y `contCumulative_0`. Revisa `maxCo` activo del diccionario, cuenta excedencias y registra continuidad final sin presentarla como conservación demostrada. Los campos ausentes/malformados se registran como **null y alerta**, nunca como cero medido.

**B — QA regresivo**: `analysis_tools/test_granada_v15v16_postrun.py` contiene cinco tests sintéticos que inspeccionan cuatro parejas, exportación, exceso de Courant, fuentes faltantes, tiempos repetidos/invertidos, multisondeos ambiguos, rechazo de extrapolación y protección de las carpetas de simulación. Estos tests son numéricos/sintéticos, no validación contra casos reales.

**C — Contrato exportable e integración CI**: el archivo `evidence.json` expone `format = quickcup-foamlens-openfoam-evidence-v1`, identidad de casos, métricas y rutas relativas + hashes de fuentes; `pair_metrics.csv` contiene las cuatro comparaciones por tiempo físico. Es un **contrato de intercambio propuesto** para que FoamLens analice y eventualmente consuma la evidencia, **no un importador ya implementado en FoamLens**. El workflow `.github/workflows/quickcup-v15v16-evidence.yml` ejecuta pruebas de Python y el análisis de salidas versionadas en un runner Ubuntu; solo crea un artefacto efímero, no simula CFD ni sobreescribe entradas.

## Ejecutar y revisar

Desde la raíz de la copia local o un checkout de GitHub:

```bash
python3 -m unittest discover -s analysis_tools -p 'test_granada_v15v16_postrun.py' -v
python3 analysis_tools/granada_v15v16_postrun.py \
  --root . --out /tmp/quickcup-granada-evidence-20261020
```

Usar una carpeta de salida **vacía** y fuera de los casos. `--strict` devuelve código no cero si hay faltantes, incompatibilidades o excedencias de Courant; su fallo es un indicador diagnóstico y no autoriza corrección automática de la física.

## Restricciones y criterios para completar

1. Revisar comparaciones **contra datos efectivamente leídos de los archivos versionados** y su SHA. Comparar los valores con la inspección histórica de 2026-10-15 sin copiarlos ciegamente.
2. Verificar en GitHub Actions el resultado exacto del nuevo PR/head; un test agregado no prueba que el CI acabó bien.
3. Completar auditoría de logs de fin/retorno, cara por cara `metalTop`, presión/PIMPLE, conservación térmica y fracción líquida por región. Este nuevo programa no los interpreta ni declara `ANALYSIS_VERIFIED`.
4. Mantener registros B/C V15/V16 y bitácoras ES/EN coherentes al cerrar auditoría tras resolver conflicto de ownership con PR #18. No actualizar estados como `RUN_VERIFIED` solo por este cribado.
5. FoamLens debe leer las referencias de fuentes originales o importar explícitamente este formato mediante una función futura comprobada; no afirmar que la app ya lo entiende.

## Punto de reentrada

Revisar la ejecución exact-head del PR de este paquete, contrastar las métricas con los archivos originales, y continuar con el siguiente paquete independiente de **energía, flujos cara a cara y fracción de fase** que requerirá análisis físico/experimental separado. No tocar C3D-01 #18/#19 mientras sus ramas sigan abiertas.

**Estado de QA al registrar:** cinco pruebas sintéticas ejecutadas localmente en el entorno de preparación; éxito. El workflow GitHub todavía debe ejecutarse en el head del PR. No hay validación CFD, energía, malla Ubuntu, ni experimento en esta ejecución.
