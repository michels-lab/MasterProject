# V15/V16 — auditoría de paridad de entradas (15 de octubre de 2026)

**Tipo de evidencia:** GIT-VERIFIED INPUTS. **Sin ejecución de CFD.**
Los cuatro ensayos continúan \`PREPARED_NOT_RUN\`.

## Auditoría del árbol de Git

Se compararon los árboles \`0/\`, \`constant/\` y \`system/\` de cada
variante con su respectivo padre usando hashes de Git del repositorio.
Los archivos no controlados se mantuvieron idénticos:

| Padre | Variante | Único archivo distinto |
|---|---|---|
| B14_topFixedFlux_explicitRef | B15_adaptiveDt_fromB14 | system/controlDict |
| C14_topFixedFlux_explicitRef | C15_adaptiveDt_fromC14 | system/controlDict |
| B14_topFixedFlux_explicitRef | B16_phaseRelax025_fromB14 | constant/metal/fvModels |
| C14_topFixedFlux_explicitRef | C16_phaseRelax025_fromC14 | constant/metal/fvModels |

De las entradas leídas:
- V15: \`adjustTimeStep: no → yes\`;
  \`writeControl: timeStep → adjustableRunTime\`;
  \`writeInterval: 100 → 0.1\`. \`deltaT=0.001\`,
  \`maxCo=0.25\`, \`maxDeltaT=0.1\` se conservan.
- V16: \`phaseChangeSource/relax: 0.1 → 0.25\`;
  sin cambiar \`maxCo\`, el esquema de paso fijo ni
  \`relaxationFactors\` de PIMPLE.
- Las variantes no contienen \`logs/\`, \`postProcessing/\`, \`log.*\`
  ni estados temporales copiados en el árbol rastreado al verificarse.

## Control reproducible previo a una corrida

Desde la raíz del repositorio:

\`\`\`bash
python3 -m unittest discover -s analysis_tools -p 'test_preflight_sensitivity.py' -v
python3 analysis_tools/preflight_sensitivity_cases.py --strict
\`\`\`

El preflight lee únicamente los archivos y detecta archivos faltantes,
entradas adicionales, cambios ajenos a la hipótesis controlada, variaciones
inesperadas en parámetros activos, alteraciones de los scripts de corrida,
y evidencia heredada. Está conectado al workflow de auditoría post-push,
sin instalar ni ejecutar OpenFOAM.

**Límites:** este check no demuestra convergencia, ausencia de errores del
solver, conservatividad, reproducibilidad temporal ni validez metalúrgica.
B15/C15 y B16/C16 siguen esperando ejecución local hasta 10 s y MAZAPÁN
completo. No habilitar automáticamente C3D ni B-FS hasta cerrar V16 B/C.
