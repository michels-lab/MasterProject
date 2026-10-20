# Investigación técnica GRANADA — B-FS / B-SH: superficie libre, solidificación y contracción

Fecha: 2026-10-20. Estado: **investigación documental y revisión del código oficial, NO implementación, NO ejecución CFD, NO validación experimental**. Esta propuesta complementa la hoja de ruta NEXT_RESEARCH_ROADMAP_ES.md, sección B-FS/B-SH, sin cambiar las simulaciones originales ni dar por terminada la auditoría V15/V16.

## Descubrimiento principal en OpenFOAM Foundation v14

**La arquitectura candidata más cercana a los tres fenómenos existe parcialmente en la distribución oficial.**

1. **compressibleVoF**: módulo de dos fluidos inmiscibles, compresible y no isotérmico, con captura VOF, gravedad, presión, transporte y energía. Código: https://cpp.openfoam.org/v14/classFoam_1_1solvers_1_1compressibleVoF.html y https://cpp.openfoam.org/v14/compressibleVoF_8H_source.html
2. **VoFSolidificationMelting**: modelo fvModel específico del módulo compressibleVoF. Introduce una fracción sólida dependiente de T definida como Function1 alphaSolidT, sumidero de momentum Darcy/porosidad y término de entalpía latente; escribe un campo alpha(phase).solid. Código oficial: https://cpp.openfoam.org/v14/classFoam_1_1fv_1_1VoFSolidificationMelting.html y https://cpp.openfoam.org/v14/VoFSolidificationMelting_8C_source.html
3. **foamMultiRun + solid**: el proyecto B14/C14 ya utiliza dos regiones metal y molde con CHT, pero la región de fluido actual NO tiene aire ni VOF. Cambiar metal fluid → compressibleVoF y conservar mold solid es una **HIPÓTESIS DE INTEGRACIÓN, aún no probada**: incluye interfaces térmicas y bibliotecas compatibles, campos, phaseProperties y región sólida.

**Hallazgo crucial del código fuente:** VoFSolidificationMelting.C agrega términos a la ecuación de energía y de momentum, y actualiza la fracción sólida desde temperatura y alphaVoF. No contiene por sí mismo una fuente de contracción volumétrica sólido/líquido ni un modelo de gas en porosidad interdendrítica. No presentar energía latente o resistencia Darcy como modelo automático de rechupe. El modelo previo solidificationMeltingSource de B14 tampoco crea una superficie libre.

**Alternativa como referencia física:** el repositorio experimental de la propia organización OpenFOAM/OpenFOAM-Solidification, aún señalado como evaluación y fuera de OpenFOAM-dev, contiene solidificationFoam basado en mezcla continuo para solidificación columnar de aleaciones binarias, con densidades sólido/líquido diferentes y flujo inducido por contracción/expansión. NO es un solver VOF gas-metal listo para usarse ni se ha verificado compatibilidad/compilación Foundation v14. Referencias:
- https://github.com/OpenFOAM/OpenFOAM-Solidification
- https://github.com/OpenFOAM/OpenFOAM-Solidification/blob/master/applications/solvers/solidificationFoam/solidificationFoam.C

## Tres problemas diferentes; no mezclarlos

**Superficie libre B-FS**: volumen de metal ocupa parte de una región fluida con aire arriba. Una fracción volumétrica alpha_metal entre 0 y 1 define el frente metal/aire. Cambios de nivel requieren conservación y redistribución de volumen; el aire ocupa el espacio exterior liberado, no sustituye automáticamente masa metálica en la zona pastosa.

**Contracción macroscópica B-SH**: por efecto de densidad rho(T, f_s), con masa metálica conservada, el volumen puede disminuir y la superficie descender cuando las condiciones lo permitan. No basta con que el aire sea compresible ni con cambiar la BC del metalTop por una de presión. Se requiere ley metalúrgica diferenciada para sólido/líquido, transitorio de momentum/energía y cierre de masa que incluya el cambio de fase.

**Alimentación y porosidad interna B-POR**: si el metal líquido no puede alimentar regiones que solidifican, puede haber caída de presión, rechupe localizado o microporosidad. Se necesita permeabilidad de mush y ecuación de alimentación, criterios de nucleación/gas/cavitación y/o evaluación de riesgo. VOF metal-aire exterior + Darcy NO garantiza automáticamente nucleación de cavidades internas. Criterios tipo Niyama pueden servir para screening de susceptibilidad, no para certificación de volumen de poros; ver https://pmc.ncbi.nlm.nih.gov/articles/PMC5452498/

## Datos reales existentes en QuickCup y cuidado específico de hierro fundido

- B14 usa una tabla icoTabulated rho(T) en constant/metal/materials/castIron; cerca de liquidus 1473.15 K figura 6820 kg/m³ y del solidus 1423.15 K figura 6900 kg/m³. Son **dos temperaturas diferentes** y su diferencia NO prueba, por sí sola, densidad sólida/líquida isoterma, contracción del cambio de fase ni comportamiento con grafito. C14 usa rhoConst 6820 kg/m³. Debe conocerse rho_l(T), rho_s(T), fracción sólida y cómo modifica el volumen el grafito durante solidificación: algunas fundiciones presentan expansión por grafitización. No fijar monotonía de contracción sin composición/JMatPro.
- B14 tiene 40×40×10 mm nominales de metal y 80×80×1 celdas, frontAndBack empty. No incluye aire. La fracción de líquido original phaseChangeSource:alpha1 es diferente de la nueva fracción VOF metal/aire y de alpha.metal.solid. Mantener nombres, unidades y procedencia separados.
- El desbalance de continuidad de B (~−0.031) no demuestra que el mero VOF lo cure ni cuánta contracción real habría. Investigar cómo se define esa continuidad en foamLog antes de atribuirle masa o volumen.
- Tsol, Tliq, L y parámetros alpha1e, Cu, q, relax del viejo modelo NO se trasladan ciegamente al nuevo VoFSolidificationMelting: este solicita alphaSolidT (ley térmica de fracción sólida), no replica la ecuación de fase específica de B14. J0/JMatPro continúa abierto.

## Arquitectura de desarrollo propuesta, por etapas independientes

**B-FS-00 — Revisión del ejemplo/compilación oficial.** En una copia de trabajo de Foundation 14 verificar que compressibleVoF y VoFSolidificationMelting estén instalados, ver qué tutoriales realmente corresponden a esas clases, sus bibliotecas, campos y ecuaciones alpha, rho, h/e y p. Verificar combinación multi-región con solid en foamMultiRun y CHT de metal–molde **antes de suponer que cambiar una línea de controlDict basta**.

**B-FS-01 — Banco hidrodinámico 2D, SIN solidificación.** Crear geometría fluida separada con metal abajo y volumen de gas arriba; estado inicial de alpha.metal y alpha.air, gravedad, presión del gas, tensión superficial/contact angle cuando sean pertinentes; pared metálica inferior/lateral, límite externo atmosférico. Comparar volumen metal inicial/final, conservación de masa por fase, acotamiento 0≤alpha≤1, Courant y deformación interfacial. Como control sin fuentes de masa ni variación de densidad, el metal debe mantener su masa y no experimentar descenso ficticio por cambio de fase. No tocar el bloque B14 histórico.

**B-FS-02 — Temperatura y acoplamiento arena.** Activar compressibleVoF no isotérmico con propiedades físicamente justificadas de metal y aire. Integrar mold solid/CHT en la interfaz metal/molde y considerar que una pared expuesta al gas tiene distinto contacto térmico a una mojada por metal. Auditar energía de ambas caras e intercambio variable con mojado. Añadir VoFSolidificationMelting con tabla alphaSolidT derivada de propiedades de aleación comprobadas; medir masa y energía, y conservar los campos VOF y sólido por separado.

**B-SH-01 — Densidad y cambio de volumen.** Separar densidad térmica de la contracción durante solidificación, construir rho_l(T) y rho_s(T) / volumen específico de mezcla en función de fase según definiciones claras; implementar/seleccionar ecuaciones conservativas acopladas. Comparar masa metal constante, volumen metal calculado desde rho, descenso libre y transferencia de energía. Usar problemas benchmark con solución de inventario de masa/volumen antes de QuickCup. Confirmar que termo/VOF admite esa ley; si no, derivar extensión de solver explícita, con pruebas de masa/energía.

**B-SH-02 — Feeding, cavidad y eventual microporosidad.** Alimentación como condición física diferenciada (reservorio, ruta abierta/cerrada, Darcy/permeabilidad en mush), presión interdendrítica, posible formación de cavidad si se aísla líquido; criterios de porosidad separados. Sensibilidad a malla, dt, viscosidad/permeabilidad y propiedades. Predicción de porosidad requiere constitutiva/validación adicional; no inferirla de alpha.air salvo presencia de interfaz realmente resuelta.

**B-V — Comparación física:** B14 cerrado vs B-FS vs B-SH con geometría/masa inicial/propiedades consistentes. Monitorizar T(t) en termopar, presión, alpha metal, fracción sólida, masa por fase, volumen, altura de superficie, energía, frente sólido, cavidad y eventualmente recalescencia. No comparar directamente variables alpha distintas sin definir su significado.

## Dos ecuaciones guía, sin pretensión de discretización terminada

1. Balance conservativo global de metal sin alimentación externa: d/dt ∫_dominio α_m ρ_m dV = 0; con feeding, el cambio equivale al flujo de masa entrante menos saliente. Si ρ_m cambia, el volumen ∫α_m dV no tiene por qué ser constante.
2. Para un metal que pasa de estado líquido a sólido con masas iguales, ΔV = m(1/ρ_s−1/ρ_l). La contracción positiva definida como fracción de volumen inicial es 1−ρ_l/ρ_s, bajo condiciones comparables. Esto NO sustituye leyes de rho(T, f_s) ni el efecto de expansión grafítica y localización de cavidad.

## Decisión de investigación y estado

Prioridad: **probar primero compressibleVoF + VoFSolidificationMelting de Foundation 14, aprovechando la posibilidad multirregión**, con banco de superficie libre sin solidificación, después física térmica y cambio de fase, y por último contracción/feed. Estudiar solidificationFoam de OpenFOAM-Solidification como referencia de flujo inducido por diferencia de densidad, no como sustituto probado de un solver VOF. La ruta C3D puede continuar en PRs separados sin que sea padre obligatorio de B-FS.

No se ha creado caso B-FS ni ejecutado OpenFOAM, no hay resultados físicos, mesh QA, parámetros experimentales nuevos, releases o comparaciones contra termopar. Esta investigación documental NO cierra Granada funcional, V15/V16, J0 ni G1.
