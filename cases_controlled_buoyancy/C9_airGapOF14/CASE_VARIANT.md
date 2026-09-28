# C9_airGapOF14

Parent case: `C9_topFixedFlux`.

## Controlled update

The pre-existing metal-mold air gap is retained with the same physical values but rewritten using the OpenFOAM Foundation v14 syntax:

```
h
{
    type              wallLayersHeatTransferCoefficient;
    thicknessLayers   (2e-4);
    kappaLayers       (1e-1);
}
```

The gap is declared only once, on the metal side of the coupled interface. The old direct `thicknessLayers`/`kappaLayers` entries are removed from the mold side.

No other mesh, timestep, PIMPLE, phase-change, material, pressure/velocity boundary-condition or diagnostic settings are changed from the parent lineage.
