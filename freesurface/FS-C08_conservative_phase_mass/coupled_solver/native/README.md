# FS-C08 — Integración de física en el solver CFD, no shadow

**Estado 24-11-2026:** código nativo de solver incorporado a la rama de investigación. **NO compilado con wmake Foundation14, NO ejecutado en WSL, NO validación de contracción.** Los dos antiguos PASS sintéticos/read-only están cerrados y no deben repetirse.

## Archivos implementados

- FS_C08_PhaseMassTransport.H/.C: dos ecuaciones de volumen finito nativas de masa física por celda rhoAlpha.liquid y rhoAlpha.solid. El flujo de líquido recorre todas las caras y fronteras de la malla CFD mediante alphaPhiMetal del predictor MULES. Sólido estacionario. Gamma(T) intercambia masas iguales y opuestas. Usa Function1 para densidades de líquido/sólido y fracción sólida por MASA, no números sintéticos.
- fsC08ConservativeVoF.H/.C: módulo derivado del solver real compressibleVoF e incluido en el PIMPLE nativo de foamMultiRun. Reconstruye alpha_metal desde masas/densidades, mantiene phi de líquido y gas, reconcilia rho de mezcla y registra inventario metálico, gas y flujos másicos por todas las fronteras. Bloquea balances metálicos incumplidos.
- fsC08PressureCorrector.C: adaptación GPL del pressureCorrector de Foundation14; utiliza rhoMetalEffective calculada de masas líquido+sólido, la convección másica real del líquido, continuidad y presión PIMPLE. No introduce un sumidero falso de metal. SvolPhaseChange = Gamma*(1/rhoSolid-1/rhoLiquid) es diagnóstico. La compresibilidad del metal sigue aproximada por el EOS líquido.
- fsC08ThermophysicalPredictor.C: adaptación GPL de energía Foundation14 con capacidad calorífica efectiva ponderada por masas, calor latente Gamma*L una sola vez y transporte térmico conjugado fluido-arena. El viejo VoFSolidificationMelting no debe coexistir: duplicaría L. El cierre energético es todavía aproximado; pendiente la formulación estrictamente conservativa de entalpías separadas.
- Make/files y Make/options: nueva biblioteca de usuario libfsC08ConservativeVoF (wmake libso Foundation14), sin modificar el sistema instalado.

## Datos requeridos y caso

El archivo fsC08Material.template es SOLO un esquema NO EJECUTABLE: no contiene ni pretende inventar JMatPro. Requiere materialId, propertySource, Tmin_K, Tmax_K, metalPresenceThreshold, phaseRelaxation, rhoLiquidT(T), rhoSolidT(T), solidMassFractionT(T), latentHeat y cpSolid.

El programa analysis_tools/stage_fs_c08_coupled.py crea una COPIA independiente FS_C08_COUPLED_* desde FS-C07 t=0, sin copiar las 20 salidas históricas. Selecciona fluid fsC08ConservativeVoF y mold solid, conserva amortiguamiento turbulento, retira el antiguo modelo de calor latente y exige archivo de propiedades con procedencia. NO ejecuta CFD; no debes repetir los read-only/shadow anteriores.

## Límites científicos aún abiertos

1. No se ha compilado este nuevo módulo en Foundation14, ni validado que sus condiciones de frontera e integración PIMPLE sean correctas en WSL.
2. La mezcla metálica usa masas distintas pero la compresibilidad psi y termo1 continúan aproximados por el líquido. Falta presión termodinámicamente consistente de líquido+sólido+gas.
3. El calor latente está una vez, pero la ecuación entálpica estrictamente conservativa requiere h_liquid(T), h_solid(T), cp(T) integrales, términos p*dV y cierre térmico global.
4. La selección de cinética por relajación de fracción sólida a equilibrio requiere calibración para austenita primaria y eutéctico, no basta un número C14. Temperaturas menores de Tmin en aire/trazas VOF no deben generar Gamma.
5. Alimentación, permeabilidad mushy, volumen real de rechupe, efecto del grafito y validación con ocho fundiciones y QuickCup siguen pendientes.
6. Ni la variación anterior de alpha.metal FS-C07 ni la nueva Svol algebraica demuestran contracción de la pieza sin una CFD conservativa y validación física.

**Próxima puerta que merece tiempo en WSL:** compilar biblioteca real, resolver API y cierre energético/EOS y ejecutar una única CFD aislada con datos metalúrgicos trazables. No se solicitan más tests sintéticos al investigador.
