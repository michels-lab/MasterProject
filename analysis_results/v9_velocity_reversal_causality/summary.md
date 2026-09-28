# V9 velocity reversals: physical-source diagnostic

This analysis tests whether the extra Uy sign reversals in B9 are associated with the mushy front, density gradients, Darcy damping, pressure-gradient acceleration, vorticity, or the transient continuity mismatch.

## Main conclusion

The horizontal multi-cell structure in B9 is **coherent and highly symmetric within the numerical solution**. The evidence does not support interpreting it as random numerical noise or as a direct consequence of the continuity mismatch.

However, the reversals are also **not predominantly attached to the mushy front**. Most horizontal reversals occur in liquid-like material, especially at y=30 mm. Thus the extra cells cannot be explained simply as flow splitting at the solidification front.

The strongest local association is with vorticity and, secondarily, pressure/Darcy structure. This is consistent with real recirculating cells in the computed flow, but it does not by itself prove that those additional cells are physically correct for the real Quick-Cup experiment.

## B9 horizontal profiles

### y = 20 mm

Across all stored times:
- 425 Uy sign reversals were detected.
- 90.6% occurred in liquid-like material (alphaL >= 0.95).
- 9.4% occurred in the mushy range.
- only 0.9% were within 1 mm of an alphaL=0.95 front crossing.
- 61.9% occurred in the top quartile of |vorticity_z|.
- 36.7% occurred in the top quartile of |p_rgh acceleration|.
- 31.3% occurred in the top quartile of |Darcy acceleration|.
- 29.4% occurred in the top quartile of |gradRho|.

Correlation between number of reversals and |final-corrector contGlobal|:
- r = -0.303

This is not evidence that larger continuity mismatch creates more cells.

Selected evolution:
- 0.1 s: 2 symmetric reversals at 2.17 and 37.83 mm.
- 1.0 s: 2 symmetric reversals at 4.40 and 35.60 mm.
- 2.5 s: 2 symmetric reversals at 5.29 and 34.72 mm.
- 5.0 s: 4 reversals at 3.42, 12.96, 27.02 and 36.58 mm.
- 7.5 s: 2 reversals at 9.94 and 30.09 mm.
- 10 s: 4 reversals at 3.63, 15.16, 24.91 and 36.38 mm.

Mirror-pair errors are extremely small (typically 0–0.04 mm), much smaller than the 0.5 mm profile sampling spacing. This is strong evidence that the secondary cells are organized, not random left/right numerical noise.

At 10 s all four y20 reversals lie at alphaL about 0.94–0.95. This late-time profile is entering the mushy regime broadly, rather than the reversals sitting on one sharp alphaL=0.95 interface.

### y = 30 mm

Across all stored times:
- 321 Uy reversals.
- 100% occurred in liquid-like material.
- 0% were within 1 mm of alphaL=0.95.
- 70.7% were in the top quartile of |vorticity_z|.
- 60.7% were in the top quartile of |p_rgh acceleration|.
- 86.3% were in the top quartile of |Darcy acceleration|.
- 48.3% were in the top quartile of |gradRho|.

Correlation between number of reversals and |contGlobal|:
- r = +0.0045

This is essentially zero correlation.

At 10 s the four reversals are at:
- 3.54 mm
- 17.05 mm
- 22.91 mm
- 36.47 mm

with alphaL approximately 0.992, 0.995, 0.995 and 0.992. Therefore the upper multi-cell pattern exists clearly in liquid metal and cannot be attributed to the mushy front.

The mirror-pair error at 10 s is only 0.026 mm.

## B9 vertical centerline

The vertical centerline is more complicated and must be interpreted cautiously because Uy becomes very small in strongly Darcy-damped near-solid regions.

Across all times:
- 39.1% of sign reversals occur in mushy material.
- 47.7% in liquid-like material.
- 13.3% in solid-like material.
- correlation of reversal count with |contGlobal| = -0.359.

At 10 s the crossings occur near 0.87, 1.27, 13.17 and 31.76 mm.

The first two occur at alphaL about 0.024 and 0.112 with Darcy acceleration at approximately the 99th percentile. These near-bottom sign changes occur in nearly solid / strongly damped material and should not be interpreted as independent convection cells without an amplitude threshold.

The crossing near 13.17 mm occurs at alphaL~0.897, with |gradRho| near the 85th percentile: this one is plausibly associated with the mushy/thermal-density structure.

The upper crossing near 31.76 mm is liquid-like and is better interpreted as part of the large-scale recirculation topology.

## C9 comparison

C9 shows the canonical symmetric two-cell natural-convection structure.

At y=20 mm:
- reversals remain a single symmetric pair through the selected times.
- at 10 s: 12.10 and 27.90 mm.
- mirror-pair error is essentially zero.

At y=30 mm:
- at 10 s: 11.97 and 28.03 mm.
- mirror-pair error is essentially zero.

The C9 horizontal reversals also occur in liquid-like material and are strongly associated with high |vorticity_z|. Therefore a velocity zero crossing does not need to coincide with the mushy front to be physically meaningful.

## Interpretation

### What the evidence supports

1. B9's extra horizontal cells are **not random asymmetric numerical noise**: they are strongly mirror-symmetric.
2. They are **not primarily caused by the mushy front**: most horizontal reversals are in liquid-like material; y30 is 100% liquid-like.
3. They are **not directly explained by the continuity mismatch**: reversal count has near-zero or negative correlation with |contGlobal| on the sampled lines.
4. They are strongly associated with **flow topology/vorticity**, consistent with coherent recirculation.
5. Some late/near-bottom vertical sign changes are in nearly solid, strongly Darcy-damped zones and should be treated as low-amplitude sign noise unless a velocity-amplitude threshold is met.

### What remains unproven

The analysis establishes that B9's multi-cell pattern is a coherent solution feature. It does **not** yet establish that the real Quick-Cup should exhibit those extra cells.

The next validation question is therefore not "is B9 numerically random?" but rather:
- does the variable-density formulation produce a Rayleigh/buoyancy regime in which multiple symmetric convection rolls are physically plausible for this geometry and thermal field?

That requires a force/dimensionless-number analysis and, ideally, comparison with experimental or literature flow evidence.
