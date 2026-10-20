# GRANADA GRANDE — V14–V16: energía y fracción líquida

2026-10-20 · **Estado: candidato en rama, auditoría numérica de solo lectura; no CFD ni validación física o experimental.**

## Objetivo

Examinar en seis casos reales B14/C14/B15/C15/B16/C16 los archivos postProcessing de potencia latente, entalpía sensible, energía por frontera y fracción líquida media. La evidencia térmica de una sola sonda no prueba que toda la física de solidificación esté correcta. El análisis diferencia observaciones numéricas de inferencias físicas condicionadas.

## Paquete amplio de tres entregables

1. **Procedencia y parser científico:** analysis_tools/granada_energy_phase_evidence.py. Lee seis functionObjects documentados, rechaza columnas no reconocidas, datos no finitos, tiempos repetidos, fuentes ausentes y periodos incompatibles. Registra cada SHA-256 de fuente, último tiempo y cobertura temporal común real (sin extrapolar).
2. **Integridad energética y cambio de fase:** comprueba energyFlux=energyAdvectiveFlux+heatFlux; comprueba el desglose por parches boundary=top+mold dentro de la precisión de los archivos ASCII; calcula ∫potencia latente dt, ∫potencia de frontera dt, Δentalpía sensible y αL media. Registra el **residual condicional** ΔH_sensible + ∫energyFlux_boundary dt − ∫potencia_latente dt. Su valor NO demuestra conservación hasta verificar formulación, signos, fuentes adicionales, malla y el otro lado de la interfaz. Compara por separado cuatro pares B14→B15, C14→C15, B14→B16 y C14→C16.
3. **Entrega auditable y pruebas:** exporta energy_phase_evidence.json (formato quickcup-energy-phase-evidence-v1), energy_phase_metrics.csv y summary.md a un destino nuevo fuera de casos originales. Nueve pruebas sintéticas reproducibles cubren datos válidos, missing, doble conteo, fracción fuera de 0–1, columnas falsas, orden temporal, falta de cobertura y no sobreescritura. CI exclusivo analiza los archivos ya versionados en Ubuntu, sin ningún paso de malla o solver.

## Reproducción en raíz del checkout

    python3 -m unittest discover -s analysis_tools -p test_granada_energy_phase_evidence.py -v
    python3 analysis_tools/granada_energy_phase_evidence.py --root . --out /tmp/quickcup-granada-energy-20261020 --strict

Destino vacío y fuera de los casos. --strict sale con error ante datos incompletos o incoherencia numérica; un fallo no autoriza modificar archivos del investigador. La prueba sintética local tiene 9/9 correctas. La validación exact-head GitHub Actions, su SHA y las métricas reales deben verificarse por separado.

## Interpretación y precauciones

- Fracción líquida es promedio del dominio, no localización de frente dendrítico ni evidencia de recalescencia.
- Potencia latente [W], entalpía sensible [J], flujos [W] y fracción [1] siguen la guía POSTPROCESSING_FIELD_GUIDE_ES.md; el DAT no certifica por sí solo esas unidades.
- energyFlux es suma de energía advectiva y térmica, no un tercer sumando.
- No se prueba balance de energía metal+molde, reciprocidad en interfaz, campo tridimensional, conservación global ni experimento. J0/JMatPro y G1 siguen abiertos.
- La exportación propone un formato explícito reutilizable para un futuro importador de FoamLens. No implica que FoamLens ya lo soporte.
- Estos análisis no cambian RUN_CASE_REGISTRY.csv ni las etiquetas de verificación científica.

## Granada / no interferencia

Los PR de C3D-01 #18 y #19, así como el de sondas/Courant V15/V16 #20, permanecen independientes y abiertos. No modificar geometrías, mallas, datos históricos, solver, ni sus archivos reclamados. Evitar editar PROJECT_AUDIT_LOG_ES/EN que son propiedad compartida de otro PR; reconciliarlos solo tras resolver las ramas y revisar resultados reales.

**Reentrada:** examinar resultado exact-head de CI, contrastar valores originales y publicar informe de observaciones físicas limitadas. Siguiente bloque grande que no choque: inspección bilateral de transferencia en interfaz metal/molde y morfología de fase con datos de malla verdaderos.
