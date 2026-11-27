> **Operación Uva + Granada — corte vigente 27-11-2026.** El estado canónico es [STATUS.json](../STATUS.json) de esta rama. El lote 12 de arranque nativo Foundation14 (7b3ed1ff4) registró compilación y ejecución WSL, 4/4 variantes y 75/75 pasos aceptados a 5 μs, según las salidas de terminal del investigador; la réplica no se suma. No hay independencia temporal, cierre energético global CHT ni validación física de contracción. Las afirmaciones fechadas 23–24 de noviembre sobre ausencia de compilación/CFD, el EOS incompresible y los comandos shadow describen etapas históricas, no la siguiente acción. El candidato activo usa K provisional de hierro puro (83.761 GPa), no calibración CE/S. Mantener los gates estrictos, no relanzar FS-C07 ni pruebas shadow; investigar dependencia temporal y aceleración de arranque antes de avanzar el horizonte. Los archivos de resultados WSL no se inspeccionaron directamente en esta auditoría.

# FS-C08 — Cambio de rumbo: solver físico, no más shadow tests

> **EVOLUCIÓN DE FUENTE 24-11-2026:** el módulo [native](native/README.md) ya incorpora advección FV líquida por todas las caras seguida de conversión fuente conservativa `±Gamma`, reevaluación en PIMPLE desde el `oldTime` correcto, Darcy en la ecuación de momento (no el viejo modelo latente), metal incompresible respecto a presión y gas EOS compresible, y dos modos de cierre de fase: `equilibrium` con f_s,mass(T) tabulada o `kineticRelaxation` con τ(T) físico, sin relajación arbitraria dependiente del paso. **El texto original de arquitectura describe el diseño al comienzo de esta etapa; el código actual se mantiene en los archivos C++ y [STATUS.json](../STATUS.json).** No hay `wmake`, corrida CFD ni predicción de rechupe validada todavía.


> **ACTUALIZACIÓN 24-11-2026:** La arquitectura de este documento ya pasó de diseño a código parcial de solver: [módulo CFD nativo real](native/README.md), [stager aislado](../../../analysis_tools/stage_fs_c08_coupled.py) y [estado actual](../STATUS.json). Ya existen continuidad líquido/sólido y enlaces a PIMPLE/energía en fuente. **No se ha compilado ni validado en Foundation14 WSL; propiedades metálicas reales, EOS, balance entálpico exacto y feeding están pendientes.** Los párrafos originales que decían «no implementado» reflejan el estado anterior a estos commits.


**Fecha:** 2026-11-24. **Prioridad:** resolver conservación de masa por fase, diferencia de densidades, presión y VOF en la CFD de hierro/aire real.

## Evidencia que queda cerrada

El investigador ejecutó en Ubuntu/WSL el nuevo paso nativo con resultado FS_C08_NATIVE_GAMMA_FV_SHADOW_PASS__SYNTHETIC_NO_CFD (HEAD dd256e9d3). Este resultado verifica una red FV de fuentes prescritas sobre conectividad OpenFOAM, pero NO resuelve flujo, presión, cambio de fase cinético, geometría móvil ni contracción. El puente de solo lectura también pasó antes. **No se volverán a solicitar esas pruebas**. No son evidencia metalúrgica.

## Diagnóstico directamente en el código oficial OpenFOAM Foundation 14

Se inspeccionaron las implementaciones actuales del repositorio OpenFOAM/OpenFOAM-14:

1. applications/modules/compressibleVoF/compressibleVoF.C: prePredictor() llama al transporte VOF de twoPhaseVoFSolver; después forma alphaRhoPhi1/2, rhoPhi y contErr1/2 para **solo dos fases VOF, metal y aire**.
2. applications/modules/twoPhaseSolver/alphaPredictor.C: alphaSolve transporta alpha1 con MULES; no transporta la masa del metal sólido independientemente.
3. applications/modules/compressibleVoF/alphaSuSp.C: calcula fuentes de alpha; no existe una fuente de contracción por Gamma de metal líquido/sólido.
4. applications/modules/compressibleVoF/pressureCorrector.C: p_rghEqnIncomp usa fvc::div(phiHbyA)-fvm::laplacian(rAUf,p_rgh)==p_rghEqnSource, y la corrección de presión actualiza phi, U y rho. Aquí debe aparecer la fuente volumétrica coherente con las masas reales.
5. applications/modules/compressibleVoF/thermophysicalPredictor.C: energía en dos fases, usando alphaRhoPhi1/2 y contErr1/2, sin distinguir entalpía transportada de metal líquido frente a sólido.
6. applications/modules/compressibleVoF/fvModels/VoFSolidificationMelting/VoFSolidificationMelting.C: correct() calcula alpha.metal.solid por ley térmica local y relajación; addSup agrega L*fvc::ddt(rho,alphaSolid) a energía y Darcy a momento. **No crea ecuación de continuidad sólida ni modifica presión por densidad de fase.**
7. applications/solvers/foamMultiRun/foamMultiRun.C: fvModels().correct() ocurre ANTES de prePredictor(). Esta secuencia puede explicar parte de la sobreasignación de sólido en trazas VOF, sin haber probado exclusividad causal.

FS-C07 posee 20 estados nativos reales, 34,368 celdas por estado y cero incidencias alphaSolid>alphaMetal+1e-8 en alphaMetal>=0.5, pero 7,692 incidencias celda-instante en VOF bajo. El VOF original y esos resultados NO se recortan ni se sobrescriben.

## Ecuaciones para el nuevo solver, no para una utilidad de diagnóstico

Guardar MASAS físicas por celda (kg) de líquido, sólido y gas:

- m_liquid = V * alpha_liquid * rho_liquid(T)
- m_solid = V * alpha_solid * rho_solid(T)
- m_gas = V * alpha_gas * rho_gas(p,T)
- alpha_liquid + alpha_solid + alpha_gas = 1
- alpha.metal = alpha_liquid + alpha_solid

Las fuentes Gamma [kg/(m3*s)] deben respetar:

- d/dt(alpha_l * rho_l) + div(alpha_l*rho_l*U_l) = -Gamma
- d/dt(alpha_s * rho_s) + div(alpha_s*rho_s*U_s) = +Gamma
- d/dt(alpha_g * rho_g) + div(alpha_g*rho_g*U_g) = 0

Primer modelo: sólido estacionario U_s=0, líquido alimentando con U_l, gas compresible U_g. La representación del momento debe distinguir fases o justificar correctamente el único U de mezcla, no suponer tres velocidades idénticas.

Cerrar alpha desde m/rho y no obtener alpha.solid por un min() que oculte infracciones. El cambio volumétrico LOCAL debido únicamente a la conversión a densidades constantes durante el subpaso es:

    Svol_phaseChange = Gamma * (1/rho_solid - 1/rho_liquid) [1/s]

- rho_solid > rho_liquid produce término de volumen negativo (contracción).
- rho_solid < rho_liquid produce positivo (expansión).
- La masa total de metal NO debe disminuir por cambio de fase: Gamma se cancela exactamente entre fases.
- La ecuación de presión requiere el término volumétrico y los términos de compresibilidad/presión coherentes; no basta una fuente que extraiga metal de alpha1 para simular rechupe.

Entalpía física:

    H/V = alpha_l*rho_l*h_l(T) + alpha_s*rho_s*h_s(T) + alpha_g*rho_g*h_g(T)

El calor latente se cuenta una sola vez, dentro de h_l-h_s O como Gamma*L. Al reemplazar el cierre físico actual, retirar/sustituir el L*fvc::ddt(rho,alphaSolid) heredado: sumarlo de nuevo al transporte de h_l/h_s duplicaría calor. Conservar el intercambio térmico CHT con la arena y, donde corresponda, trabajo termomecánico.

## Cambios reales de código; orden de implementación

**A. Solver propio en OpenFOAM14:** módulo compilable fsC08ConservativeVoF, registrado para la selección de región fluid en foamMultiRun, mientras mold sigue usando solid. No modificar /opt/openfoam14 ni los resultados FS-C07/C3D.

**B. Campos conservativos:** crear mLiquid, mSolid, mGas, Gamma, rhoLiquid(T), rhoSolid(T), alphaLiquid, alphaSolid, alphaGas, junto con oldTime y condiciones de frontera. Inicialización del caso aislado desde t=0 del caso original, no desde las instantáneas ya contaminadas de FS-C07.

**C. Transporte nativo de TODAS las caras:** usar operadores de volúmenes finitos y flujos compatibles con la advección/MULES; mantener fuentes +Gamma/-Gamma y evitar clipping a posteriori. El módulo shadow que usa una sola cara y flujos artificiales no cumple esta parte.

**D. Volumen/momento/VOF:** cerrar alpha_metal desde las masas y densidades, modelar alimentación líquido al frente de solidificación e inmovilidad sólida; incorporar delta rho de líquido/sólido en densidad efectiva e inercia.

**E. Presión:** adaptar el pressureCorrector del módulo propio y resolver la divergencia por Svol y los términos adicionales de mezcla/gas compresible. Verificar el SIGNO a partir de la ecuación nativa antes de activar y no crear una fuente de masa neta ficticia.

**F. Energía:** adaptar thermophysicalPredictor para entalpía sensible/latente conservativa, calor CHT, y términos mecánicos que aplique. Desactivar la duplicación latente de VoFSolidificationMelting.

**G. Caso CFD nuevo y aislado:** ruta FS_C08_COUPLED_* fuera del repositorio, para una única ejecución con t>0, campos reales evolución m_l/m_s/m_g/T/p/U/alpha y resultados de contracción/feeding; fronteras y tablas de propiedades justificadas.

## Termofísica: lo que todavía NO existe

Las curvas rho_l(T), rho_s(T), cp_l(T), cp_s(T), k(T), la transformación de austenita proeutéctica y el eutéctico de las composiciones deben estar respaldadas por JMatPro/datos experimentales. En FS-C07 la ley Ts=1423 K, Tl=1473 K, L=228600 J/kg es referencia C14: NO corresponde automáticamente a las ocho fundiciones estudiadas. Los valores sintéticos de la red (7000/7300) NO son propiedades del material.

Se puede desarrollar el módulo y preparar su infraestructura, pero NO declarar predicción cuantitativa de contracción sin esas propiedades y validación QuickCup.

## Restricción de proceso a partir de ahora

**CERRADO:** 18 Python, standalone C++17, lector nativo fvMesh, salida Gamma shadow. No volver a gastar tiempo del investigador en esos gates.

**ABIERTO:** integración del solver de continuidad triple, presión, energía y VOF. Mantener estado PHYSICAL_COUPLED_SOLVER_NOT_IMPLEMENTED hasta que el solver haya sido realmente implementado.

**Próximo hito que sí justifica ejecutar Ubuntu:** nueva CFD con balances globales de masa por fase y frontera, calor, interfaz y respuesta al contraste rho_l/rho_s; NO otro PASS__NO_CFD.

Fuentes de ingeniería revisadas: https://github.com/OpenFOAM/OpenFOAM-14/tree/master/applications/modules/compressibleVoF ; https://github.com/OpenFOAM/OpenFOAM-14/tree/master/applications/modules/twoPhaseSolver ; https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/solvers/foamMultiRun/foamMultiRun.C.
