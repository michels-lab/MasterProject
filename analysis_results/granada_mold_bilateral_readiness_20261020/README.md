# GRANADA GRANDE — Evidencia bilateral, fuente original, 2026-10-20

**Origen:** GitHub Actions run 39397515797 en head ae0431d07a4575f44c1079b4d1154e205491501f. Artefacto quickcup-granada-mold-bilateral-readiness, ID 12253211009. Sintaxis Python PASS, **13 pruebas sintéticas PASS** y auditoría de seis casos reales versionados PASS, source_alert_cases=0. No se ejecutó CFD ni el postprocesador físico.

El reporte JSON del CI conserva rutas y SHA-256 de las cuatro fuentes principales de cada caso: temperatura metal, temperatura molde, blockMeshDict y potencia metalMoldEnergyPower. case_matrix.csv archiva datos derivados para reproducibilidad.

| Caso | Área nominal y reportada de contacto (m²) | Caras reportadas | Resistencia nominal de capa (m²K/W) | Potencia lado metal a 10 s (W) | Medición lado molde |
|---|---:|---:|---:|---:|---|
| B14 | 0.0012 | 240 | 0.002 | 278.7068 | AUSENTE |
| C14 | 0.0012 | 240 | 0.002 | 277.4151 | AUSENTE |
| B15 | 0.0012 | 240 | 0.002 | 278.6469 | AUSENTE |
| C15 | 0.0012 | 240 | 0.002 | 277.3115 | AUSENTE |
| B16 | 0.0012 | 240 | 0.002 | 278.7119 | AUSENTE |
| C16 | 0.0012 | 240 | 0.002 | 277.4430 | AUSENTE |

## Interpretación física restringida

- El área geométrica deriva de los tres lados de contacto de la caja metálica 2D nominal. Coincide con el área declarada de metal_to_mold en archivos originales, pero **no verifica** la malla real Sf, las normales, ni la reciprocidad topológica metal/molde.
- La resistencia de contacto nominal usa espesor 2e-4 m / conductividad 0.1 W/(m K) = **0.002 m²K/W**. El recíproco 500 W/(m²K) no equivale automáticamente a la resistencia efectiva o un coeficiente experimental.
- metal_to_mold y mold_to_metal utilizan coupledTemperature en los seis casos. No se confunde el acoplamiento nominal de condiciones de frontera con una conservación verificada.
- La potencia de la tabla es sum(energyFlux) del **lado metal**, sin otro término ni fuente inferidos y sin atribuirle signos que no se hayan medido.
- **6 de 6 lados molde están ausentes** en las salidas originales: NOT_OBSERVED_NO_MOLD_OUTPUT. No se inventa un flujo opuesto igual, ni un residual de cero, ni una validación experimental.

## Siguiente puerta de aceptación

En copia local sobre Ubuntu/OpenFOAM Foundation 14, confirmar wallHeatFlux region mold y patch mold_to_metal, verificar propiedades y dimensión real, y reconstruir flujo por caras con magSf/Sf y orientación. Solo con el archivo físico original de la región mold y sus hashes puede calcularse un residual bilateral PROVISIONAL. Requiere revisar signos, resistencia de contacto y la conservación del modelo completo. J0/JMatPro, G1 y recalescencia permanecen abiertos.

Código reproducible: analysis_tools/granada_mold_bilateral_readiness.py. Protocolo de captura y peligros de una inferencia prematura: docs/granada/BILATERAL_INTERFACE_READINESS_20261020.md. No se editaron datos históricos, casos ni las áreas de PR #18/#19/#20. Los registros ES/EN existentes deberán reconciliarse cuando sus PRs dejen de modificar los mismos archivos.
