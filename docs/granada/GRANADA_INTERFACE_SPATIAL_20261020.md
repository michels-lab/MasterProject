# GRANADA GRANDE — metalTop, interfaz metal/molde, perfiles de fase

Fecha: 2026-10-20. Estado: **revisión de evidencia original**, no nueva CFD, no validación experimental.

## Diagnóstico y datos

La campaña B14/C14/B15/C15/B16/C16 guarda salidas del lado metal para topFlow, topPatchFaceFields, metalTopPhiSum y metal{Mold,Top,Boundary}EnergyPower, además de cuatro líneas espaciales con alphaL. No se dispone en Git de la potencia interfacial complementaria del lado mold: **reciprocidad metal↔molde NO OBSERVADA**. Las cantidades de fracción líquida por perfil son estadísticas de puntos muestreados, no volumen metal solidificado, no morfología dendrítica ni recalescencia.

## Paquete de tres entregables

**A. Frontera superior, face-by-face:** analysis_tools/granada_boundary_spatial_gate.py recupera original topFlow por tiempo físico, centroides, velocidad por componentes y phi de cada cara. Compara con diagnóstico independiente topPatchFaceFields (solo columnas presentes) y reduce máximo abs(phi), suma abs(phi) y suma firmada, contrastándola con metalTopPhiSum. La cancelación de flujos opuestos se señala como riesgo; suma(phi)=0 no es certificación de impermeabilidad. Uy se usa como componente normal de la tapa orientada en Y de este caso, pero no como sustituto de la normal Sf calculada de la malla.

**B. Interfaz y perfiles científicos:** verifica que boundary=top+mold para los tres canales energéticos por tiempo y que energyFlux=energyAdvectiveFlux+heatFlux, sin contar un tercer mecanismo. Conserva solo el flujo del lado metal hacia el molde; no afirma reciprocidad bilateral. Resume fracción líquida de los perfiles originales y usa thresholds de visualización operativos alphaL<=0.05 (sólido), 0.05<alphaL<0.95 (pastoso) y alphaL>=0.95 (líquido), advirtiendo explícitamente que los puntos no son volúmenes.

**C. QA, trazabilidad e interoperabilidad:** JSON exportable de esquema quickcup-boundary-spatial-evidence-v1, CSV summary, hashes de fuentes y pruebas sintéticas para datos erróneos, ausentes, cancelación por cara, discrepancias energéticas y salida no destructiva. El workflow específico usa solamente Python 3 y los archivos OpenFOAM ya versionados; **nunca ejecuta malla, solver ni limpia resultados**.

## Ejecutar y proteger datos

Desde la raíz del clon:

    python3 -m unittest discover -s analysis_tools -p test_granada_boundary_spatial_gate.py -v
    python3 analysis_tools/granada_boundary_spatial_gate.py --root . --out /tmp/quickcup-boundary-spatial-evidence

Opción --strict exige ausencia de alertas para devolver cero. El destino debe estar vacío y fuera de la carpeta de casos CFD. El esquema constituye un contrato diagnóstico QuickCup, no prueba de que FoamLens ya lo importe.

## Evidencia de aceptación

Separar: tests sintéticos; auditoría read-only de casos originales; validación física de malla/flujo; comparación experimental. Nunca convertir los dos primeros en los dos últimos. Revisar el número real de ejecución GitHub Actions y el SHA exacto del PR antes de integrar. La ausencia del lado molde requiere datos de esa región proporcionados desde Ubuntu del investigador para estudiar reciprocidad, normales y superficies.

## No interferencia

Los PR #18 y #19 son de mallado C3D-01; #20 es V15/V16, Courier/sondas. No modificar sus rutas, CASE_NOTES, RUN_CASE_REGISTRY, PROJECT_AUDIT_LOG_ES/EN ni resultados CFD. J0/G1 permanecen abiertos. La reconciliación de bitácoras bilingües debe hacerse tras liberar ownership en ramas.

**Punto de reentrada:** revisar evidencia real de 6 casos, corregir exclusivamente falsos positivos del parser con pruebas, y proseguir otro paquete independiente de intercambio energético bilateral cuando exista postProcessing del molde, sin inventar datos de esa región.
