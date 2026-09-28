# V9 velocity-profile analysis

Profiles analyzed at t = 0.1, 1, 2.5, 5, 7.5 and 10 s for:
- horizontal y = 20 mm
- horizontal y = 30 mm
- vertical x = 20 mm

## Main result

C9 preserves a highly symmetric broad two-cell circulation pattern over the complete sampled transient. Horizontal Uy is exactly mirror-symmetric about x = 20 mm to stored precision, with negative Uy near both side walls and a central positive-upflow region. The two Uy zero crossings remain symmetric.

B9 is also strongly mirror-symmetric on the horizontal profiles (Uy even-symmetry error generally below 1%), so its difference from C9 is not random lateral asymmetry. Instead B9 undergoes symmetric topology changes: the horizontal profiles alternate between two-zero-crossing and four-zero-crossing states. Four crossings correspond to a sign pattern negative-positive-negative-positive-negative across the width, consistent with a multicellular/four-roll-type circulation rather than C9's persistent broad two-roll pattern. Line profiles alone do not prove the exact full-domain vortex count, but they clearly prove additional vertical-flow bands.

## C9 morphology

At y = 20 mm, Uy zero crossings remain two at every sampled time:
- 0.1 s: x = 2.20, 37.80 mm
- 1 s: 5.11, 34.89 mm
- 2.5 s: 6.52, 33.48 mm
- 5 s: 11.46, 28.54 mm
- 7.5 s: 11.83, 28.17 mm
- 10 s: 12.10, 27.90 mm

This indicates side-wall downflow and a central upflow core. The central/upward velocity grows through the early transient and reaches 0.01778 m/s near x=20 mm at 5 s, then decays to 0.00966 m/s at 10 s.

The strongest y20 downflow occurs earlier: about -0.02468 m/s near x=1.75 mm at 2.5 s.

At y = 30 mm the same two-crossing topology persists. At 10 s:
- Uy minimum = -0.00615 m/s near x=6.25 mm
- Uy maximum = +0.00956 m/s near x=19.75 mm

At x = 20 mm, C9 retains a strong central vertical upflow. At 10 s the maximum Uy is +0.01196 m/s at y=24.75 mm, with only weak negative velocity near the lower solidifying region.

## B9 morphology

B9 horizontal Uy remains nearly mirror-symmetric, but its topology changes.

At y=20 mm:
- 0.1 s: 2 zero crossings
- 1 s: 2
- 2.5 s: 2
- 5 s: 4
- 7.5 s: 2
- 10 s: 4

At 10 s the crossings are x = 3.63, 15.16, 24.91, 36.38 mm. The sign pattern therefore alternates across the width, producing additional up/down bands absent from C9.

At y=30 mm:
- 0.1 s already shows 4 crossings
- 1–7.5 s mostly return to 2
- 10 s again has 4 crossings at x = 3.54, 17.05, 22.91, 36.47 mm

B9 also produces substantially stronger early side-wall downflow:
- y20, 1 s: Uy_min = -0.03578 m/s
- y20, 2.5 s: Uy_min = -0.03135 m/s
- C9 at the same times: -0.01656 and -0.02468 m/s

By 10 s B9 remains downflow-dominated near the walls:
- y20 Uy_min = -0.01264 m/s at x=1.25 mm
- maximum positive Uy = +0.00578 m/s at x=6.25 mm

The x=20 mm vertical line shows the strongest topology difference. B9's centerline circulation repeatedly reverses/reorganizes:
- 2.5 s: strong upward core, Uy_max = +0.02173 m/s at y=14.75 mm
- 5 s: dominant centerline motion becomes downward, Uy_min = -0.00761 m/s at y=15.75 mm
- 7.5 s: upward motion returns, Uy_max = +0.00781 m/s at y=23.75 mm
- 10 s: centerline flow weakens strongly and becomes multi-sign, with only about +/-0.00175 m/s

At 10 s C9 still has +0.01196 m/s central upflow, so the B9 circulation has largely migrated away from the centerline into off-center cells/bands.

## Direct B9 vs C9

At y=20 mm, direct Uy comparison:
- 0.1 s: NRMSE 46.6%, correlation 0.976
- 1 s: 51.4%, corr 0.933
- 2.5 s: 46.8%, corr 0.884
- 5 s: 175.5%, corr -0.289
- 7.5 s: 84.8%, corr 0.742
- 10 s: 180.8%, corr -0.301

Thus early differences are mainly amplitude differences within a broadly similar circulation shape, but by 5 and 10 s the spatial pattern itself has changed.

At y=30 mm:
- differences remain more shape-correlated through 7.5 s
- at 10 s NRMSE rises to 176.8% and correlation falls to -0.062

The upper profile therefore undergoes the major B9 topology divergence later than y20.

On the centerline x=20 mm:
- 1 s: corr 0.975
- 2.5 s: corr 0.951
- 5 s: corr -0.881
- 7.5 s: corr 0.953
- 10 s: corr -0.609

This confirms repeated reorganization/reversal of the B9 central circulation rather than a simple uniform scaling of the C9 velocity field.

## Physical interpretation

C9 behaves like a stable symmetric two-roll natural-convection structure: downflow near the cold side walls, horizontal return flow, and a broad upward core near the center.

B9 generates stronger early wall jets and a less persistent central plume. As solidification proceeds, the variable-density field drives symmetric roll splitting/reorganization, producing additional vertical-flow bands and intermittent reversal of the centerline flow.

The major B9-vs-C9 difference is therefore **topological**, not merely a velocity-magnitude difference.

A full 2D/volume streamline or vorticity-field inspection is the next validation step before assigning an exact vortex count to B9.
