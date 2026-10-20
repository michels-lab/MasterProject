# GRANADA GRANDE — Balance bilateral metal–molde: preparación sin modificar CFD

Fecha: 2026-10-20. Paquete nuevo: analysis_tools/granada_mold_bilateral_readiness.py.

## Problema físico

Los seis casos B14/C14/B15/C15/B16/C16 contienen la potencia metalMoldEnergyPower del **lado metal** y BC térmicas acopladas, pero falta un postProcessing/mold que mida la cara contraria de la interfaz. Un reporte del lado metal NO prueba conservación bilateral ni balance termodinámico completo. La continuidad acumulada de la familia B, J0/JMatPro y G1 experimental tampoco quedan resueltos.

## Tres entregables conectados

**A — Auditoría de fuentes y geometría:** lectura de 0/metal/T y 0/mold/T, comprobando las parejas coupledTemperature metal_to_mold y mold_to_metal. Auditoría de la capa de contacto de metal: wallLayersHeatTransferCoefficient, espesores/conductividades y resistencia NOMINAL Σ(t/k), no resistencia efectiva medida. Lectura del blockMeshDict y estimación del área en las tres paredes de la caja rectangular de metal, expresamente no equivalente a Sf/normales reales. Comparación del área y caras de fuente metalMoldEnergyPower, inspección de columnas y tiempos y SHA256 de cada fuente original.

**B — Preparación de captura mold:** genera una propuesta independiente mold_wall_heat_flux_CANDIDATE.foam basada en wallHeatFlux de OpenFOAM Foundation v14, region mold, patches (mold_to_metal). NO se instala ni se ejecuta sobre casos. Requiere copiar a un caso de prueba en la laptop y validar syntax/version/malla/resultados con el solver original. El objeto calcula flujo térmico de pared: **no puede tratarse automáticamente como potencia en W** sin las áreas reales magSf, normales y convenciones de signo.

**C — Comparación condicional con procedencia y pruebas:** salida JSON, CSV y guía CAPTURE_README.md. Futuro insumo auténtico por caso: mold_interface_W.csv (time_s,outward_power_W) y provenance.json con case, patch=mold_to_metal, units=W, orientation=outward_from_mold, quantity=integrated_interface_power, source_method=OpenFOAM_Foundation14, measured_area_m2 y SHA256 íntegro del CSV. Exige coincidencia exacta de tiempos medidos y reporta P_metal_out+P_mold_out como diagnóstico PROVISIONAL. Ni hash ni etiqueta garantizan que la física sea correcta; el chequeo de Sf y normales es independiente. Si falta el lado mold, se informa NOT_OBSERVED_NO_MOLD_OUTPUT, nunca 0.

12 pruebas sintéticas comprueban seis casos, BC, geometría nominal, resistencia de capa, áreas incompatibles, hashes alterados, tiempos diferentes, fuentes faltantes, exportación protegida y fallo cuando se exige bilateralidad sin medidas.

## Ejecutar sin tocar la simulación

    python3 -m unittest discover -s analysis_tools -p test_granada_mold_bilateral_readiness.py -v
    python3 analysis_tools/granada_mold_bilateral_readiness.py --root . --out /tmp/quickcup-mold-readiness --strict

La salida solo va a una carpeta nueva FUERA de casos: bilateral_readiness.json, case_matrix.csv, mold_wall_heat_flux_CANDIDATE.foam, CAPTURE_README.md. La opción --require-bilateral debe indicar fallo con archivos mold ausentes. No se ejecuta blockMesh, foamMultiRun ni foamPostProcess en CI.

## Pruebas reales faltantes

1. En Ubuntu Foundation v14, en un clon del caso y tras decidir los cambios de instrumentación, confirmar que wallHeatFlux de la región mold calcula y escribe valores correctos. Referencia Foundation 14: https://cpp.openfoam.org/v14/classFoam_1_1functionObjects_1_1wallHeatFlux.html
2. Inspeccionar constant/metal/polyMesh y constant/mold/polyMesh reales y patch correspondence, Sf, magSf, topología, orientación y área. blockMeshDict+Area de un reporte no constituyen checkMesh.
3. Convertir el resultado auténtico del lado mold a potencia integrada en W con orientación documentada, archivo fuente y checksum, sin cambios silenciosos de unidades. Confirmar misma fecha/tiempos originales y continuidad de series.
4. Evaluar el signo de interfaz y el efecto de la resistencia térmica; solo después estudiar conservación integral metal+molde y la recalescencia contra curvas experimentales.

## GRANADA / no interferencia

Los PR #18 y #19 poseen C3D-01, #20 posee revisión de sondas y Courant V15/V16. Este bloque utiliza módulos nuevos y bitácora paralela; no toca casos originales, CASE_NOTES, PROJECT_AUDIT_LOG_ES/EN, RUN_CASE_REGISTRY ni archivos de los PR. Código candidato y verificación CI NO son validación física, corrida CFD o publicación.

Punto de reentrada: consultar el resultado CI en exact HEAD y el reporte generado de las seis parejas; corregir anomalías verificables sin modificar datos originales; integrar si pasa; luego avanzar con captura real mold o con otro frente científico independiente mientras espera la laptop.
