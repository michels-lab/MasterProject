# QuickCup — revisión científica crítica y puntos ciegos

**Meta:** cuestionar la interpretación y las decisiones antes de multiplicar corridas o publicar conclusiones; conservar el control científico íntegramente aquí.

## Doble hipótesis obligatoria

Para una decisión de modelado escribir: hipótesis principal, explicación rival plausible, observación que las distingue, experimento numérico mínimo que puede falsarlas y qué medición experimental sería decisiva. Anotar costo en laptop y riesgo de confundir el resultado.

## Preguntas sistemáticas

| Perspectiva | Pregunta que evita un punto ciego | Verificación necesaria |
| --- | --- | --- |
| Física | ¿La aparente recalescencia procede de nucleación/liberación de calor latente o del modelo temporal/frontera? | Curvas con tiempos alineados, balances y condiciones físicas; comparar contra termopares |
| Numérica | ¿La variación observada es física o depende de dt/malla/PIMPLE? | Estudios separados, sensibilidad Δt/espacial y registros Courant/residuales |
| Propiedades | ¿Cp, k, densidad, calor latente y fracción de fase están trazados a la aleación real? | Procedencia JMatPro o medida, unidades y rango de T; puerta J0 |
| Interfaces | ¿El intercambio metal/molde se conserva y tiene unidades correctas? | Auditoría conjunta de energía sensible/latente y potencia en interfaz |
| Materiales | ¿Es válido asumir molde isotrópico, HTCs fijos o una fase líquida homogénea? | Comparar hipótesis mínimas y discutir su identificación experimental |
| Experimental | ¿La comparación tiene la posición, incertidumbre y fecha del termopar? | Evidencia original, desfase temporal, RMSE/sesgo y eventos de fase |
| Validez | ¿Un log terminado implica conservación, convergencia o validación? | No. Registrar gates separados y explícitos |

## Protocolo por hallazgo

1. **Hecho:** ruta, variante, SHA, tiempo físico y métricas fuente.
2. **Supuesto cuestionado:** explicar la hipótesis y por qué podría ser falsa.
3. **Contrapunto:** una explicación alternativa que no caricaturice la actual.
4. **Prueba más barata:** resultado que confirmaría/refutaría el supuesto.
5. **Decisión:** pendiente, aceptada, rechazada o diferida; justificación y condiciones para reabrir.
6. **Responsable/gate:** validación local y autorización del investigador cuando corresponda.

La ausencia de datos produce **NO_VERIFIED**, no un resultado inventado. No modificar los PR científicos en curso, historial de curvas, CFD o documentación histórica por una simple crítica. Esta lista es una metodología de investigación; su existencia no certifica validación.
