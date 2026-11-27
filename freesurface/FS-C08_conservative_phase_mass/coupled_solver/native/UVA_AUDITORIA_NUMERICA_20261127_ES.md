# Operación Uva + Granada — Auditoría focalizada del solver FS-C08

Fecha: 2026-11-27. Rama: research/fs-c08-conservative-phase-mass-20261123. Revisión estática de los blobs indicados, no recompilación ni ejecución CFD. Estado previo: lote 12, 75/75 pasos y 4/4 variantes a 5 microsegundos según terminal WSL; sin independencia temporal.

## Fuentes y alcance

| Archivo | SHA | Alcance |
|---|---|---|
| Make/files | 0e93d9ab544f986e683cbbc3acaf942cabf31760 | completo |
| Make/options | 0141abd095269bf073027e4d035a4f54465804ba | completo |
| FS_C08_PhaseMassTransport.C | c70e4bc56a3f55abff2c9af3e08a0dd7f3dd50ff | inicialización, EOS, Gamma, fuentes volumétricas y replay, focalizado |
| FS_C08_VolumeProjection.C | 602873105843c2ecd92c372994d5d38ec35dd725 | limitador, proyección, capacidad donante y búsqueda de paso, focalizado |
| fsC08MushyMomentum.C | c3ef6b05932ac56ac1f094bc7a2194d34718c0e2 | completo |
| fsC08PressureCorrector.C | bfcdcb8dac5b04f7d3f1d6dfe44f5c690842e34c | líneas 56–180, 710–809, 850–987 y estructura, focalizado |
| fsC08ThermophysicalPredictor.C | d2de272c6448271cb4be62238c6a2a7fba9d8567 | líneas 415–479, 535–625 y estructura, focalizado |
| fsC08ConservativeVoF.C | 644d771c61f3e6cf1c039b481328463e9bc8a75f | postSolve líneas 690–780 y estructura, focalizado |

## Hallazgos y criterios

1. PhaseMassTransport::replayTrialFromFlux reinicia ambas masas desde oldTime; resuelve advección líquida y después particiona la masa total local por f_s(T) en equilibrio. En modo cinético usa -expm1(-dt/tau). El sólido es estacionario: no se transporta por advección. La fuente Gamma cancela en masa metálica local, lo que no prueba cierre global discreto. La reconstrucción rechaza exceso de volumen >1e-12; admite pequeñas desviaciones de fracción negativa hasta -1e-12, no debe afirmarse boundedness exacta sin inspeccionar campos.
2. El EOS metálico activo usa exp((p-100000)/K), con K común provisional para líquido y sólido. No se admite reinicio con inventarios guardados en la ruta finita K ni cierre cinético con K finito. Cv/kappa se comprueban en 257 puntos; esto es cribado, no validación de tablas ni procedencia de aleación.
3. limitPredictorMassFlux rechaza MPI y parches coupled() en la región fluida. Distinguir esa llamada del acoplamiento térmico entre regiones: no inferir que CHT esté deshabilitado. pressureCorrector rechaza MPI, malla móvil y modo transónico. La proyección limita movilidad por capacidad donante; el margen es conservador porque ignora entradas simultáneas. Se aplica un factor común al incremento de presión y los flujos; una proyección sin descenso admisible se rechaza.
4. Darcy: R=(mL+mS)*Cu*fS_cond^2/(fL_cond^3+q); Sp(R,U) positivo en lado izquierdo. R ponderado por masa metálica evita tratar aire puro como sólido. Cu/q y supuesto de esqueleto estacionario deben justificarse físicamente.
5. Momentum refreshBeforePressure requiere momentumPredictor=no. La matriz se congela durante el cierre interno. FS_C08_MOMENTUM_FORCE_SPLIT, FS_C08_MOMENTUM_CONSISTENCY y FS_C08_FRESH_MOMENTUM_DEFECT son observacionales, no gates. El último reensambla sin resolver U; es un defecto algebraico equivalente en velocidad, no residuo completo certificado de PDE. El signo y magnitud de su relación con la aceleración todavía deben medirse.
6. Ruta estricta reconstruye phi/rhoPhi/U/K/vDot/Uf/p_rgh y continuidad antes de la auditoría térmica; si falla, vuelve a iterar; al final vuelve a auditar y comprueba volumen. La ruta legacy no tiene el mismo contrato. No mezclar resultados de ambas.
7. La ecuación de energía usa inventario por fases, conducción del operador ensamblado, advección y trabajo mecánico con signo consistente con el residual declarado. AuditOnly no resuelve T. El gate local usa max |residual|/CVvol, mientras relativeL1 es otro indicador. No sustituye el cierre energético global CHT, ni prueba consistencia calórica del EOS finito K.
8. postSolve rechaza residuos de metal no finitos o superiores a 1e-7*max(M,M0), y de gas superiores a 1e-6*max(SMALL,Mgas,Mgas0); ambos son tolerancias de balance por paso. Registra energyResidualNotYetValidated=1; no certificar energía a partir del PASS de masa. Revisar también acumulación de error en el transitorio completo.

## Próxima acción científica, sin cambiar los casos históricos

- Recuperar logs existentes del lote 12, por variante, en tiempos físicos comunes. Extraer FORCE_SPLIT, MOMENTUM_CONSISTENCY, FRESH_MOMENTUM_DEFECT, PREDICTOR_DONOR_CAPACITY, VOLUME_PROJECTION_ITER, FINAL_COUPLED_ENERGY_AUDIT_PASS y MASS_BUDGET.
- Comparar máximos y ubicaciones en metal, aire puro e interfaz; no interpretar Umax global como velocidad de hierro automáticamente. Contrastar defecto de momento, temporalFluxCorrection, presión y capacidad donante con Delta t. No concluir causalidad a partir de una sola correlación.
- Solo si la evidencia respalda el problema de momento congelado, diseñar variante separada de actualización de matriz dentro del acoplamiento, conservando la referencia, los gates y el horizonte fijo. No relajar tolerancias, introducir presión mínima artificial ni pasar a MPI.
- Cierre CHT: integrar energía del molde y flujos externos de ambos dominios; comprobar cancelación del flujo interfacial con orientación y tiempos coherentes; contabilizar trabajo y energía cinética una sola vez.
- Propiedades CE/S y validación QuickCup continúan pendientes. No repetir shadow ni FS-C07; no usar K de hierro puro como calibración del hierro colado.

Se conservan intactos solver, datos y configuraciones. No se inspeccionaron artefactos crudos WSL, ni se completó la revisión línea por línea de los archivos grandes. Este documento es una auditoría focalizada y no un certificado de corrección numérica.
