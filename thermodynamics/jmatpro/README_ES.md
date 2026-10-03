# JMatPro data area

> **Actualización 2026-10-03:** `C11_topFixedFlux_airGapOF14` permanece como referencia histórica congelada; `C14_topFixedFlux_explicitRef` es el baseline actual de trabajo/validación después de verificar impermeabilidad, continuidad y equivalencia física con C11. La incorporación de datos JMatPro no debe modificar C11 ni C14; cualquier nueva física se introducirá después de cerrar J0.


Este directorio está reservado para la trazabilidad de la simulación termodinámica previa a OpenFOAM.

## Regla

No etiquetar una propiedad como **JMatPro-derived** si no existe un archivo/exportación que permita reconstruirla.

## Estructura propuesta

```
thermodynamics/jmatpro/
  raw/
    CE3p9_S0p05/
    CE3p9_S0p13/
    CE4p2_S0p05/
    CE4p2_S0p13/
  processed/
  README_ES.md
```

Cada carpeta raw debe conservar:
- composición completa;
- Mn utilizado;
- tipo/configuración de cálculo;
- exportaciones numéricas;
- fecha/versión de JMatPro cuando se conozca.

`processed/` contendrá únicamente tablas derivadas reproducibles para OpenFOAM: beta, rhoRef, TL, TS, L, Cp(T), k(T), comparación fL(T), etc.

La baseline C11 no se modifica al incorporar estos archivos. Los cambios físicos se harán en una nueva rama/caso G1 después de cerrar la puerta J0.
