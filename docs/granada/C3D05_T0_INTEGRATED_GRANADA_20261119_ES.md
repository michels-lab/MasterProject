# Operación Granada — C3D-05 / Caso B: entrega integrada T0
**2026-11-19 · código nuevo, sin simulación ejecutada ni validación material**

## Etapa y avance
**Etapa 3/7 (T0); 2/7 hitos completados = 29% de hitos técnicos del Caso B, NO de la tesis, validez física o CFD.**
G1 CAD/STEP aceptado; G2 malla 270,788 HEX8/contacto aceptados con 1,826 caras >70°; G3 todavía **ABIERTO** por ausencia de valores y fuentes reales. El aporte de este bloque **no** cierra G3 sin validación en laptop.

## Qué elimina la repetición
El antiguo flujo requería `run_t0_preflight.sh` y luego `run_t0_materialize.sh`, cuyo primer paso volvía a ejecutar preflight, tests y revisión de malla. En lugar de pedir varias rondas, `scripts/run_t0_granada.py` es un **único ejecutor** que:
1. valida todo el JSON y rechaza campos/supuestas fuentes sintéticas ANTES de tocar WSL o la malla;
2. reutiliza únicamente los logs/JSON ya preservados (sin regenerar STEP, Gmsh, checkMesh o CFD) para confirmar procedencia/interfaz;
3. confirma Foundation14 y sus herramientas; prepara una COPIA del caso en carpeta temporal única;
4. analiza nueve diccionarios con `foamDictionary`, guarda SHA256 del JSON y huella conjunta del polyMesh regional y evidencias nativas, corrige la ruta definitiva en el reporte generado y produce resumen explícito sin CFD;
5. instala el caso materializado solo si todas las etapas pasan; bloquea sobrescrituras, concurrencia y cambios de entrada. Si se repite la misma invocación y SHA tanto de entradas como de malla/evidencia, informa `ALREADY_PREPARED` sin reconstrucción ni nuevas pruebas.

Comando único **solo cuando la matriz de propiedades esté completada con datos documentados**:
```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_t0_granada.py
```
Para usar JSON externo a Git: `C3D05_T0_INPUTS=/ruta/segura/parametros.json` en el entorno. Si falta un campo, el mismo comando devuelve lista única de bloqueadores y **no crea nada**. **No pedir al investigador ejecutarlo para verificar solamente el código**: la CI prueba el flujo con mocks sintéticos y sin OpenFOAM.

## Alcance científico
**Conducción transitoria idealizada de dos sólidos adiabáticos**, no hierro líquido ni solidificación. Ni la existencia de fuentes como cadenas de texto ni el éxito de `foamDictionary` prueban propiedades reales, estabilidad con ángulos hasta 76.8°, conservación de energía, corrección de flujo, independencia de malla o validez experimental. El ejecutor no llama `foamMultiRun` ni crea resultados CFD. Antes de cualquier corrida real, hay que comprobar la documentación de propiedades y una hipótesis térmica defendible.

## Evidencia de QA
Pruebas automáticas: rechazo de datos faltantes o sintéticos, preservación ante WSL no disponible, rechazo de salida existente, materialización sintética + idempotencia + detección de cambios. Un test simulado jamás se cita como una corrida térmica real.
