# Physics diagnostics summary

Generated from the controlled QuickCup cases using `analysis_tools/physics_diagnostics_analysis.py`.

## Main findings

### Energy transport

For all fixed-step B cases (B3/B4/B5/B7), the integrated energy transport is essentially identical over 0–10 s:

- boundary total energyFlux ≈ 6129.7–6129.8 J
- boundary advective contribution ≈ -970.4 J
- boundary diffusive contribution ≈ 7100.2 J
- metal-to-mold diffusive contribution ≈ 6732.0 J
- top diffusive contribution ≈ 368.2 J
- mold share of absolute diffusive boundary transport ≈ 94.81%
- integrated latent-heat diagnostic ≈ 3098 J
- sensible enthalpy change ≈ -3468.3 J

For all fixed-step C cases (C3/C4/C5/C7), the integrated energy transport is also essentially identical:

- boundary total energyFlux ≈ 7064.6–7064.7 J
- boundary advective contribution ≈ +6.84–6.88 J
- boundary diffusive contribution ≈ 7057.8 J
- metal-to-mold diffusive contribution ≈ 6686.9 J
- top diffusive contribution ≈ 370.9 J
- mold share of absolute diffusive boundary transport ≈ 94.75%
- integrated latent-heat diagnostic ≈ 3128.3 J
- sensible enthalpy change ≈ -4249.1 J

Therefore, in the fixed cases, approximately 95% of the diffusive heat extraction represented by these boundary diagnostics occurs through the metal-to-mold interface, while only about 5% occurs through the exposed top.

The C-family boundary advective sensible-energy transport is negligible (~0.1% by the integrated magnitude metric).

The B-family reports a much larger signed advective boundary contribution (~-970 J, ~12% by the integrated magnitude metric). This contribution is associated with `metalTop`; the metal-to-mold advective contribution is essentially zero.

**Important:** `metalTop` uses `U: slip` together with `p_rgh: totalPressure`. Because OpenFOAM's `energyAdvectiveFlux` is based on the mass flux multiplied by sensible enthalpy, the non-zero B-family top advective term implies a non-zero mass-flux contribution at that boundary. This must be treated as a boundary-flux consistency issue to investigate before interpreting the B top advective term as a physical convective heat-loss mechanism.

### Vorticity and flow topology

OpenFOAM Foundation v14 `flowType` convention:
- +1: rotational flow
- 0: parallel shear
- -1: pure-shear/deformation flow

The classifications below use:
- `flowType > 0.2`: rotational-dominated
- `|flowType| <= 0.2`: near parallel shear
- `flowType < -0.2`: deformation-dominated

These are sampled-line fractions, not volume fractions.

#### Fixed B cases

B3/B4/B5/B7 have very similar horizontal vorticity structure.

Representative B5:
- y=20 mm: median RMS(omega_z) = 7.34 1/s; peak = 8.846 1/s at 2.2 s; rotational sample fraction ~10%
- y=30 mm: median RMS(omega_z) = 5.825 1/s; peak = 8.19 1/s at 1.8 s; rotational sample fraction ~45%
- vertical x=20 mm: median RMS(omega_z) = 0.0557 1/s; rotational fraction ~0%

Thus the strongest rotational-type sampled structure in fixed B intersects the upper horizontal profile much more strongly than the center vertical line.

#### B6 adaptive

Relative to fixed B5:
- y=20 mm: median RMS(omega_z) falls from ~7.34 to ~7.00 1/s; rotational sample fraction 10% -> 7.5%
- y=30 mm: median RMS(omega_z) falls from ~5.83 to ~4.86 1/s; rotational sample fraction 45% -> 20%; rotational-strength share ~12.9% -> 2.5%
- vertical x=20 mm: median RMS(omega_z) collapses from ~5.6e-2 to ~1.5e-4 1/s

This supports the Uy result: B6 reorganizes/suppresses the fixed-step vertical circulation rather than merely perturbing its magnitude.

#### Fixed C cases

C3/C4/C5/C7 are essentially identical.

Representative C5:
- y=20 mm: median RMS(omega_z) = 3.515 1/s; rotational sample fraction ~40%; rotational-strength share ~37.4%
- y=30 mm: median RMS(omega_z) = 3.227 1/s; rotational sample fraction ~12.5%; rotational-strength share ~1.1%
- vertical x=20 mm: vorticity is essentially zero on the center line

The sampled rotational topology is therefore spatially different from the B family: it intersects y=20 mm much more strongly in C, while in B the stronger rotational classification appears at y=30 mm.

#### C6 adaptive

C6 preserves Uy much better than B6, but its derivatives/topology are not identical:
- y=20 mm: median RMS(omega_z) rises to ~4.31 1/s
- rotational sample fraction falls from ~40% to ~17.5%
- rotational-strength share falls from ~37.4% to ~10.5%

This shows that similar velocity-component profiles do not guarantee identical vorticity/flow topology.

### Adaptive energy diagnostics

B6 and C6 cover shorter stored physical-time ranges, so their integrated energies are not directly comparable to the 0–10 s fixed integrals without time alignment.

B6 (0–9.9465 s):
- boundary total energyFlux = 5801.6 J
- diffusive = 6792.4 J
- advective = -990.8 J
- latent diagnostic = 2911.4 J

C6 (0–9.1825 s):
- boundary total energyFlux = 5598.5 J
- diffusive = 5577.6 J
- advective = 20.9 J
- latent diagnostic = 2528.9 J

The current finite-difference closure diagnostic is noticeably worse in the adaptive cases, particularly C6. This is not by itself proof of energy-conservation failure because the stored adaptive sampling is coarse/non-uniform and the closure reconstruction uses sampled sensible enthalpy rather than the solver's fully discrete equation balance.
