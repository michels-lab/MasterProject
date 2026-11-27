# Uva + Granada — presupuesto energético CHT, alcance lado fluido

27-11-2026. Auditoría focalizada de código; sin CFD nueva ni cambios de física. Fuente nativa fsC08ConservativeVoF.C blob 644d771c61f3e6cf1c039b481328463e9bc8a75f, líneas 480–590 y 700–750. El preparador stage_fs_c08_coupled.py (c82293c6164595cbcf010477278e45da86b3c27b) hereda controlDict del caso fuente, sustituye módulo fluid e introduce biblioteca; no se inspeccionó el caso WSL efectivo. No inferir nombres de interfaz de un caso distinto.

## Contrato observado

El solver integra energía interna por fases del fluido, incluyendo metal líquido, sólido y gas. El latente reside en las referencias de energía de fase, no se añade otra vez. Los registros FS_C08_REAL_CFD_PATCH_BUDGET contienen tasas firmadas de calor conductivo y advección de energía salientes, tasas brutas de metal entrante/saliente y gas neto saliente. No clasifican parches como molde, ambiente, entrada o venteo sin geometría. El presupuesto total impreso es Rf = E-E0 + dt*(P_adv + P_cond + P_mech), con los signos de la ecuación nativa. Darcy se registra aparte: no añadirlo otra vez al presupuesto. El salto de energía tras presión es otro diagnóstico, no un término adicional al mismo Rf.

El nuevo analysis_tools/fs_c08_cht_budget.py exige inventario explícito de parches reales, ledger completo de masa/volumen/energía/presión, marca de aceptación de masa y por defecto auditoría final de energía. Rechaza duplicados, no finitos e inventarios incompletos. Reconstruye la expresión impresa y contrasta sumas de parches con globales del fluido; diferencias se informan sin inventar tolerancias de aceptación. Integra tasas impresas por dt desde t=0 solo en prefijo contiguo, sin trapezoide entre pasos faltantes. Mantiene diagnósticos aislados posteriores sin integrarlos. No certifica campos guardados, ni precisión de impresión, ni equivalencia de estas tasas con una nueva auditoría FV. Salida independiente con hash del log; cinco pruebas sintéticas publicadas y añadidas al workflow, sin ejecución comprobada.

## Qué falta para cierre metal + aire + molde

| Término | Disponibilidad |
|---|---|
| Delta E fluido (incluye metal/aire) | Marcador nativo |
| Advección y conducción lado fluido | Marcadores nativos por parche y global |
| Trabajo mecánico según ecuación fluida | Marcador nativo |
| Flujo conductivo de la interfaz lado molde | No demostrado por los marcadores inspeccionados |
| Delta energía del molde y fuentes efectivas | Pendiente de extraer del operador sólido |
| Flujo de fronteras externas del molde | Pendiente |
| Mapeo de interfaz, orientación, sincronización y discretización temporal | Pendiente |

Para una interfaz acoplada con normales salientes opuestas, el contraste debe usar Q_fluid_interface+Q_mold_interface en los mismos pasos, no suponer cancelación. Después contrastar la suma de inventarios, fuentes y flujos externos, sin contar la interfaz dos veces. No usar rho*Cp*T aproximado como inventario certificado si el operador usa otra variable termodinámica; no inferir cierre CHT de un residual pequeño de fluido. El nuevo reporte mantiene global_CHT_energy_verified=false. Los resultados WSL crudos no están disponibles desde el conector; no hay nuevas cifras experimentales ni de simulación. Lote 12 anterior conserva su estado de arranque reportado.

Siguiente: inspeccionar contrato del solver sólido y mapeo de interfaces del caso real; preparar extracción simétrica de energía sólida sin modificar la formulación ni repetir CFD. No mezclar esta rama con los casos C14 de 200 s.
