# GRANADA GRANDE — Hallazgos de metalTop e intervalo pastoso en perfiles

Fecha: 2026-10-20. Evidencia: CI GitHub Actions #39394697220, head 971a2a91550e99f2e00fe46d9718c0ff27585a29, artifact ID 12250858377. Python sintaxis + **9 pruebas** + análisis original de seis casos, SUCCESS. No se ejecutó OpenFOAM ni nueva simulación CFD.

## Cobertura y valores por cara

Se inspeccionaron B14/C14/B15/C15/B16/C16: **101 timestamps entre 0 y 10 s** por caso, 80 caras de metalTop, 404 perfiles/tiempos de fase por caso y 101 potencias de metal_to_mold desde el lado metal. Se leyeron 610 fuentes por caso (su digest de manifiesto SHA256 está en evidence.json). Todos los casos pasaron la consistencia numérica de este cribado, cero alertas.

| Caso | Máximo absoluto phi cara (kg/s) | Máximo absoluto Uy (m/s) |
|---|---:|---:|
| B14 | 8.47033e-22 | 0 |
| C14 | 0 | 0 |
| B15 | 6.77626e-21 | 0 |
| C15 | 0 | 0 |
| B16 | 8.47033e-22 | 0 |
| C16 | 0 | 0 |

La tapa se comporta como impermeable **en estos diagnósticos por cara y dentro de la precisión guardada**; no significa cierre de continuidad del volumen. La acumulación previa de continuidad en B (~-0.031) continúa abierta y debe analizarse de forma independiente de la tapa.

Los totales de energía de boundary, top y metal_to_mold del **lado metal** son coherentes dentro de la precisión del archivo; la diferencia máxima de partición es ~1e-4 W. No existe potencia complementaria de postProcessing/mold versionada aquí: reciprocidad bilateral metal/mold sigue NO OBSERVADA. Nada de lo anterior certifica conservación energética de todo el sistema.

## Comparación espacial a t=10 s

Criterio exploratorio: fracción líquida alphaL > 0.05 y < 0.95 identifica muestras de la zona pastosa. Se clasifican puntos de perfiles 1D, **nunca fracción del volumen o frente dendrítico real**.

| Caso | y10: porcentaje pastoso | y20 | y30 | x20 |
|---|---:|---:|---:|---:|
| B14 | 90% | 2.5% | 0% | 32.5% |
| C14 | 37.5% | 7.5% | 2.5% | 36.25% |
| B15 | 90% | 2.5% | 0% | 31.25% |
| C15 | 37.5% | 7.5% | 2.5% | 36.25% |
| B16 | 90% | 2.5% | 0% | 32.5% |
| C16 | 37.5% | 7.5% | 2.5% | 36.25% |

El contraste espacial B14/C14 en y10 es real en los valores muestreados; la media de alphaL en esa línea a 10 s es 0.937669 (B14) contra 0.955918 (C14), **no** una demostración de mayor precisión experimental.

## Primer instante de escritura con algún punto pastoso

| Caso | y10 (s) | y20 (s) | y30 (s) | x20 (s) |
|---|---:|---:|---:|---:|
| B14 | 2.1 | 7.7 | no observado a 10s | 1.9 |
| C14 | 2.1 | 6.6 | 9.4 | 2.0 |
| B15 | 2.2 | 7.8 | no observado a 10s | 1.9 |
| C15 | 2.2 | 6.7 | 9.6 | 2.0 |
| B16 | 2.1 | 7.7 | no observado a 10s | 1.9 |
| C16 | 2.1 | 6.6 | 9.4 | 2.0 |

Son tiempos de cruce en **snapshots discretos cada 0.1 s**, no tiempos exactos de nucleación, velocidades del frente ni recalescencia. El CSV profile_screen.csv conserva los datos derivados redondeados; evidence.json del artifact y entradas originales preservan evidencia detallada.

## Bloqueadores y acciones siguientes

1. Solicitar en ejecución futura, exclusivamente desde laptop Ubuntu del investigador y con autorización, diagnóstico térmico y malla de lado mold para revisar reciprocidad y signos/áreas/normales auténticos. No reconstruir o inventar el lado ausente.
2. No atribuir la continuidad B al flujo por metalTop cuando este auditado es de magnitud nula; verificar balance de continuidad local/global, ecuación y cambios de densidad.
3. Comparar fase local y temperatura real para estudiar recalescencia; J0 propiedades JMatPro y G1 experimental siguen abiertos.
4. PR #18/#19 poseen trabajos C3D y algunas bitácoras; #20 posee Co/sondas. No modificar casos históricos, inventario ni bitácoras ES/EN durante colisión. Estas evidencias se archivaron independientemente y se reconciliarán cuando sea seguro.
5. El esquema de exportación es un contrato de investigación, NO certificación de que FoamLens ya lo lea.

**Estado:** auditoría numérica/QA completada sobre datos versionados. Verificación física bilateral, validación experimental y CFD de laptop no efectuadas.
