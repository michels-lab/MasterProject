# Caso 3D-A C3D-04 — física fuente exacta de C14

**Decisión del investigador (20 de noviembre de 2026):** el Caso A debe usar **las variables, el modelo termofísico, la formulación del solver y el cambio de fase del C14 2D original**, ajustando sólo la dimensionalidad/topología y la sintaxis mínima que requiere OpenFOAM Foundation 14. **No** sustituir el hierro fluido por dos sólidos, añadir constantes escogidas sin fuente, copiar física VOF de FS-C06, o atribuir validación al T0 auxiliar.

## Fuente científica y parámetros: no escogidos por el asistente

Archivo base: `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/`. Contrato legible por máquina: [C14_3D_PHYSICS_CONTRACT.json](C14_3D_PHYSICS_CONTRACT.json). La fidelidad se compara directamente contra los archivos fuente originales, incluidos ocho Git blob SHA-1 previamente fijados, por el [auditor y ensamblador](c14_source_fidelity.py). **Los originales no se modifican.**

| Magnitud/modelo | C14 exacto | Qué debe hacer la versión 3D-A |
|---|---|---|
| Regiones | metal = `fluid`; mold = `solid` | Conservar; metal no es `solid` |
| Termofísica hierro | `heRhoThermo / hConst / sensibleEnthalpy` | Conservar Cp, energía `h` |
| Termofísica arena | `heSolidThermo / eConst / sensibleInternalEnergy` | Conservar Cv, energía `e` |
| Densidad metal / arena | 6820 / 1500 kg/m³ | Conservar las constantes originales |
| Capacidad calorífica | Cp hierro 827 / Cv arena 700 J/(kg K) | **No hacer Cp→Cv en metal** |
| Transporte metal | mu 5.5×10⁻³ Pa·s, Pr 0.14 | Conservar `const`, no inventar k(T) |
| Conductividad arena | 2 W/(m K) | Conservar |
| Iniciales | metal 1500 K, arena 300 K; U=(0 0 0), p=p_rgh=1e5 Pa | Conservar, llevar a geometría 3D |
| Cambio de fase | `solidificationMeltingSource`, `energy h` | No reemplazar por un modelo distinto |
| Solidus / liquidus | 1423 K / 1473 K | Conservar |
| Calor latente / alpha1e | 228600 J/kg / 0.8 | Conservar ambos |
| Enthalpy–porosity | relax 0.1, Cu 1e5, q 0.001 | Conservar |
| Flotación del modelo | beta 1.13×10⁻⁴ K⁻¹, rhoRef 6820 kg/m³ | Conservar |
| Gravedad / momento | g=(0,-9.81,0) m/s²; laminar | Conservar |
| U en tapa/contacto | slip / noSlip | Conservar topología física impermeable de C14 |
| p_rgh en tapa/contacto | fixedFluxPressure | Conservar |
| Calor exterior | h=10 W/(m²K), Ta=300 K, emissivity metal .3 / arena .5 | Conservar; sólo usar sintaxis F14 `externalTemperature` con `h uniform 10` |
| Contacto | coupledTemperature, 0.0002 m / 0.1 W/(m K) | Conservar resistencia original |
| Tiempo | deltaT 0.001 s; fin 10 s; write cada 100 | Conservar controles base originales; reducción futura sólo para ensayo aislado y explícito |
| Configuración | maxCo .25, adjustTimeStep=no, PIMPLE root 3/2/1 | Conservar; **.25 no es Courant observado** |
| `nEnergyCorrectors` | 2 escrito regionalmente, 1 efectivo según bitácora/logs C14 | **No** promocionarlo erróneamente como 2 efectivos |

## Diferencias 2D→3D que requieren evidencia, no parámetros arbitrarios

1. `frontAndBack empty` es exclusivo de la representación 2D original; en C3D-04 hay que imponer BC a **todos** los parches físicos no vacíos de V4/T02. La fuente tiene `metalTop`, `metal_to_mold`, `moldTop`, `moldExterior`, `moldBottom`, `moldRecessWall`, `moldRecessRoof`.
2. `system/metal/fvSolution` trae `pRefPoint (0.02 0.04 0.005)` de la geometría 2D. No es seguro reutilizarlo en el nuevo dominio y; no elegir una coordenada 3D sin verificar su pertenencia a una celda metálica real. Conservar `pRefValue=1e5`.
3. `constant/metal/fvModels` apunta a `cellZone metal`. Antes de arrancar, exigir una selección **verificada** de todas las celdas reales de metal en la región 3D; si el zone local no existe, no saltar ni desactivar el cambio de fase.
4. **No se ha materializado ni ejecutado** el modelo fluido–sólido sobre V4/T02. El auditor genera en memoria ocho campos de arranque y ensambla en memoria **22 entradas** (14 archivos originales C14 sin transformación y ocho campos iniciales con BC 3D adaptadas). Ésta es una comprobación de proveniencia y cobertura, **no un nuevo CFD**.

## Relación con el T0 anterior

El T0 de **dos sólidos** sigue siendo una prueba numérica separada de arranque/acoplamiento térmico, no representa la física principal del Caso A exigida aquí. Las pruebas 3D sintéticas anteriores con `foamMultiRun` sólo demostraron que dos regiones sólidas podían iniciar y transferir calor. **No** justifican usar `heSolidThermo` para el hierro de C14 ni desactivar `U,p_rgh,alpha1e,L,beta`.

**Estado canónico del plan operativo anterior:** etapa **6/10**, **5/10 hitos = 50 %**, que mide hitos de geometría/preparación incluyendo T0 auxiliar. **Avance físico de la transferencia C14 fluido–sólido:** aún sin corrida 3D ni validación. El siguiente bloque real es resolver la referencia de presión/cellZone sobre malla V4/T02 preservada y materializar/ejecutar el modelo original adaptado sin otros parámetros.

