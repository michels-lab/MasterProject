# B5_airGapOF14

Parent case: `B5_outer3`.

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

B-family density table: the `icoTabulated` table is extended identically through 2273.15 K using the same diagnostic linear continuation already used in B9. Values through 1773.15 K are unchanged; the extension only prevents an out-of-range failure above the historical table limit.

No other mesh, timestep, PIMPLE, phase-change, material, pressure/velocity boundary-condition or diagnostic settings are changed from the parent lineage.
