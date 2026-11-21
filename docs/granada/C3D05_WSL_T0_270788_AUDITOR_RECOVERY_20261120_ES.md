# Caso B C3D-05 — primer solver real en WSL y recuperación del falso negativo T0

**2026-11-20 (hora local del investigador).** **Etapa 3/7 · 2/7 hitos técnicos = 29 %**. Este porcentaje no representa avance de tesis ni validación física.

## Evidencia aportada por el investigador

Fragmento de consola correspondiente a la invocación de `run_c14_numerical_granada.sh --solve` desde la WSL del investigador (original **fuera del repositorio**). La preparación identificó correctamente:

- QuickCup CAD/STEP y malla aceptada: **270,788 HEX8**, metal **92,200**, molde **178,588**.
- Interfaz recíproca **12,636 caras por lado**, 1,826 caras severamente no ortogonales (advertencia).
- 10/10 diccionarios OpenFOAM Foundation14 reconocidos.
- Temperatura de equilibrio **teórica** adiabática calculada de la referencia C14: **1157.70809 K**, **no** temperatura medida/simulada a 0.1 s.
- En el final del log `foamMultiRun` aparecen `Time = 0.098s`, `0.099s`, `0.1s`, iteraciones PIMPLE y solucionadores `DICPCG` para `e` en metal/molde, residuales numéricos finitos y marcador `End`. Tiempo de cómputo reportado al final: **45.296436 s**, reloj **46 s**.

El **ejecutor devolvió 6** con `NUMERICAL_ONLY_SOLVER_NOT_VERIFIED_COMPLETE` *después* del cierre del solucionador. No implica de por sí fallo del solver. El log completo original y el JSON de intento permanecen únicamente en la WSL hasta que se recuperen/verifiquen con su SHA.

## Causas raíz del rechazo

En `t0_conduction/scripts/audit_t0_numerical_run.py`:

1. La expresión del tiempo aceptaba `Time = 0.1`, pero no el formato **nativo F14 `Time = 0.1s`**.
2. La detección fatal coincidía con la línea informativa **`Enabling floating point exception trapping (FOAM_SIGFPE)`**, que no significa una excepción ocurrida. El smoke sintético del 20/11 ya había visto una falsa alarma similar, pero el auditor productivo seguía sin corregirse.

Se ajustó el parser para aceptar sufijo `s` opcional y excluir **solamente** la línea estándar de habilitación de detección FPE; permanece el rechazo de `FOAM FATAL ERROR`, `FOAM FATAL IO ERROR`, `Floating point exception`, señales SIGFPE reales, datos no finitos, tiempo no monótono, falta de `End`, sin solves `e` o código de salida no cero. Hay regresiones de éxito/fallo.

## Reentrada sin repetir la corrida de 100 pasos

Se agregó `scripts/review_preserved_t0_run.py`. Si existen el log y el estado de auditoría original, el ejecutor **no vuelve a lanzar `foamMultiRun`**. Para un falso negativo con exit code nativo 0, verifica SHA-256 de entradas, log y JSON originales; vuelve a auditar *los mismos bytes* con las reglas reparadas y solo si el resultado es positivo publica el archivo **nuevo**:

`T0_NUMERICAL_RUN_STATUS_REVIEWED.json`

**No modifica** ni el log `log.foamMultiRun.C14_NUMERICAL_T0` ni el histórico `T0_NUMERICAL_RUN_STATUS.json`. El reporte nuevo guarda el SHA del JSON anterior. Las fases 4/6, 5/6 y 6/6 leen el reporte revisado: temperatura/energía real por volumen, q bilateral de 12,636 pares por tiempo y expediente final SHA. El finalizador exige explícitamente el vínculo entre ambos reportes. Si la revisión falla, todo se detiene **sin sobreescribir ninguna evidencia ni repetir solver**.

**Única orden de continuación autorizada, ejecutable por el investigador en la WSL:**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve
```

Esta orden **reutiliza** la corrida si encuentra ambos artefactos originales. Si cualquiera falta o su SHA difiere, se detiene conservando la evidencia. El shell no ejecuta Gmsh ni rehace la malla aceptada.

## Límite científico / bloqueo actual

- **Sí observado en el fragmento enviado**: solver llegó a 0.1 s, `End`, iteraciones de energía sobre malla real aceptada; fuente: consola proporcionada por el investigador.
- **NO observado aún**: verificación SHA del log completo, temperatura volumétrica de metal/molde, conservación energética, extracción `q` en 12,636 pares ni desempeño del postprocesador en esta malla.
- **No validado**: parámetros físicos JMatPro, curvas QuickCup, calor latente, frente de solidificación, sensibilidad temporal/espacial y estabilidad ante las 1,826 no ortogonales severas.
- **G3 y G4 siguen abiertos, 2/7=29 % técnico** hasta evidencia íntegra para las condiciones exigidas.

**Siguiente entrega integral:** recuperar la corrida WSL original mediante SHA sin ejecutarla nuevamente, extraer T/energía/q en ambas regiones, auditar residuos, registrar trazabilidad y visualizar los campos reales en ParaView. Posteriormente incorporar datos físicos y comparación QuickCup.

## Segunda reentrada WSL y diagnóstico de la segunda causa (20-11-2026)

El investigador volvió a ejecutar el mismo comando después de `git pull`, esta vez sobre el HEAD de WSL `ace1d2630`. El ejecutor confirmó `ALREADY_GENERATED_IDENTICAL`, `ALREADY_PREPARED`, `ALREADY_PRESENT_IDENTICAL` y `Reuse previous native solver evidence ... NO rerun`. Sin rehacer la malla, al revisar el log original se produjo `ValueError: original native run STILL fails corrected auditor`. Se detuvo antes de las fases 4/6–6/6. El final del log volvió a mostrar `Time = 0.1s`, `e` resuelto en ambas regiones y `End`; la excepción provino de `review_preserved_t0_run.py`, no de una nueva corrida `foamMultiRun`.

**Fallo adicional confirmado en nuestro código, y formato nativo verificado:** la exclusión informativa anterior solo reconocía `Enabling floating point exception trapping (FOAM_SIGFPE)` sin prefijo ni punto. La fuente original de OpenFOAM Foundation14, `src/OSspecific/POSIX/signals/sigFpe.C`, imprime exactamente `sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).` (véase https://cpp.openfoam.org/v14/sigFpe_8C_source.html, líneas fuente 189–190). El detector antiguo, al buscar libremente `sigfpe`, volvía a marcar como fatal ese encabezado **normal**. Esta discrepancia no podía detectarse con el fixture anterior, que había omitido el prefijo y la puntuación.

**Corrección integrada:** los dos módulos del auditor/revisor ahora reconocen exclusivamente el formato real F14 (admitiendo además la variante sin prefijo ya cubierta), excluyen solo la línea informativa, mantienen señalamiento de verdaderos errores y muestran diagnósticos estructurados (`audit_failure_reasons`, tiempos, `e`, `End`, coincidencias fatales) si otra condición impide recuperar. Se sustituyeron los fixtures antiguos por el encabezado completo y se añadieron negativos para señales fatales. Un chequeo local aislado del patrón F14 y ecuaciones `e` pasó; **las pruebas integradas y la revisión del log WSL completo no se han acreditado en este documento**.

No hay nuevas propiedades físicas ni motivos para rehacer QuickCup. La restauración sigue siendo de solo lectura sobre log/estado anteriores, y si falta cualquier prueba SHA, se bloquea. **Estado: G3/G4 abiertos; etapa 3/7 · 2/7=29 % de hitos técnicos.** El siguiente `--solve` debe continuar solo la revisión y el postprocesamiento, sin ejecutar una segunda vez `foamMultiRun`. Si persiste un bloqueo, ahora enumerará la condición exacta para depurar de forma fundada.
