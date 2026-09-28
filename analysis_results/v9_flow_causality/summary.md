# V9 flow-reversal causality analysis

This analysis correlates resolved Uy sign reversals with liquid fraction, density gradient, vorticity, pressure acceleration, Darcy acceleration and the appropriate buoyancy representation for each V9 formulation.

## Method

A sign reversal is considered resolved only when at least one of the two adjacent sampled points has |Uy| >= 1e-4 m/s. This suppresses sign changes produced only by near-zero numerical velocity.

For B9, beta=0 in solidificationMeltingSource. Its buoyancy is therefore not represented by phaseChangeBuoyancyAcceleration. The variable-density solver contribution is reconstructed from the OpenFOAM buoyant-pressure formulation as:

a_rho = -(gh/rho) grad(rho)

with hRef=0 and gh=-9.81*y.

For C9, rho is constant and beta=1.13e-4 1/K, so the sampled phaseChangeBuoyancyAcceleration is used.

Pressure acceleration is:
a_p = -grad(p_rgh)/rho

Darcy acceleration is the sampled:
a_D = -D U

The reported "dominant" term means only the largest local sampled acceleration magnitude among buoyancy/density-gradient, pressure and Darcy. Viscous diffusion and material acceleration are not included, so this is an association diagnostic rather than a complete momentum balance.

A Uy zero crossing on a line also does not by itself prove a closed 2-D recirculation cell.

## B9 temporal structure

### y = 20 mm

Resolved Uy crossings:

| time s | positions mm | local state | largest sampled acceleration scale |
|---:|---|---|---|
| 0.1 | 2.17, 37.83 | liquid / liquid | pressure / pressure |
| 1.0 | 4.40, 35.60 | liquid / liquid | density-buoyancy / density-buoyancy |
| 2.5 | 5.29, 34.72 | liquid / liquid | pressure / pressure |
| 5.0 | 3.42, 12.96, 27.02, 36.58 | liquid at all four | density-buoyancy at all four |
| 7.5 | 9.94, 30.09 | liquid / liquid | Darcy / Darcy |
| 10.0 | 3.63, 15.16, 24.91, 36.38 | mushy at all four | Darcy / pressure / Darcy / Darcy |

The first stored time with four or more resolved crossings is 2.6 s. The number is not permanently four; the profile reorganizes with time. Thus B9 develops a transient/migrating secondary structure rather than a fixed four-cell pattern.

At 10 s all four y20 crossings lie in the phase-change region, alphaL ~0.941-0.946.

Detailed 10 s values:

| x mm | alphaL | |grad rho| kg/m4 | omega_z 1/s | flowType | a_rho,y m/s2 | a_p,y m/s2 | a_D,y m/s2 | |a_rho| | |a_p| | |a_D| |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3.63 | 0.946 | 2.66e3 | +5.47 | 0.106 | -0.0725 | +0.0792 | -0.0137 | 0.0735 | 0.0800 | 0.396 |
| 15.16 | 0.941 | 2.61e3 | -0.836 | 0.752 | -0.0730 | +0.0736 | -0.00205 | 0.0749 | 0.0753 | 0.0698 |
| 24.91 | 0.942 | 2.61e3 | +0.828 | 0.738 | -0.0729 | +0.0735 | -0.00225 | 0.0748 | 0.0752 | 0.0773 |
| 36.38 | 0.946 | 2.66e3 | -5.45 | 0.105 | -0.0726 | +0.0792 | -0.0133 | 0.0736 | 0.0800 | 0.395 |

Interpretation:
- The outer reversals (3.63 and 36.38 mm) coincide with strong, opposite-signed vorticity and very large Darcy magnitude. These are strongly associated with phase-change/mushy resistance redirecting the circulation.
- The inner reversals (15.16 and 24.91 mm) are symmetric and occur where density-gradient buoyancy and p_rgh acceleration nearly cancel vertically: about -0.073 versus +0.0735 m/s2. Darcy magnitude is of comparable order, although its vertical component is small at the exact Uy zero. This is a structured momentum balance, not an isolated random sign flip.
- The symmetry of positions and opposite vorticity signs argues against treating the y20 secondary structure as simple numerical noise.

Across all resolved B9 y20 crossings for t>=0.1 s:
- 343 crossing samples;
- 88.3% are in alphaL>0.95 regions and 11.7% in alphaL=0.05-0.95;
- largest sampled acceleration scale: density-buoyancy 39.4%, pressure 34.1%, Darcy 26.5%;
- median |omega_z| = 2.74 1/s;
- median |grad rho| = 2.74e3 kg/m4.

Therefore the secondary behavior begins before the final mushy layer reaches every reversal and cannot be attributed exclusively to Darcy damping.

### y = 30 mm

Selected resolved crossings:

| time s | positions mm | state | largest sampled scale |
|---:|---|---|---|
| 0.1 | 2.00, 37.99 | liquid | density-buoyancy |
| 1.0 | 4.06, 35.93 | liquid | density-buoyancy |
| 2.5 | 5.07, 34.94 | liquid | density-buoyancy |
| 5.0 | 4.27, 35.75 | liquid | density-buoyancy |
| 7.5 | 8.02, 31.96 | liquid | density-buoyancy |
| 10.0 | 3.54, 36.47 | liquid | density-buoyancy |

Although brief additional crossings occur during the full transient (first >=4 at 3.6 s), at the selected representative times and at 10 s the dynamically resolved structure is the main symmetric pair.

At 10 s:
- alphaL ~0.992 at both crossings;
- |grad rho| ~2.59e3 kg/m4;
- omega_z = +3.58 and -3.60 1/s;
- |a_rho| ~0.111 m/s2;
- |a_p| ~0.109 m/s2;
- |a_D| ~0.011 m/s2.

The vertical components of density buoyancy and pressure nearly oppose each other. This is consistent with a buoyancy-pressure recirculating flow in predominantly liquid metal, not a Darcy-created secondary cell.

Across all B9 y30 crossings for t>=0.1 s:
- 225 crossing samples;
- 100% are alphaL>0.95;
- largest sampled scale: density-buoyancy 72.0%, pressure 28.0%, Darcy 0%;
- median |omega_z| = 1.88 1/s;
- median |grad rho| = 1.70e3 kg/m4.

### vertical x = 20 mm

Selected resolved crossings:
- 0.1 s: 37.71 and 38.41 mm, pressure-scale dominated;
- 1.0 s: none;
- 2.5 s: 6.19 mm, mushy/Darcy associated;
- 5.0 s: 3.14 mm (mushy/Darcy) and 27.88 mm (liquid/pressure);
- 7.5 s: none;
- 10.0 s: 13.17 mm (mushy) and 31.76 mm (liquid).

At 10 s:
- y=13.17 mm: alphaL=0.897, a_rho,y=-0.0653, a_p,y=+0.0683, a_D,y=-0.0138 m/s2.
- y=31.76 mm: alphaL=1.000, a_rho,y=-0.0448 and a_p,y=+0.0449 m/s2, with essentially zero Darcy.

The centerline vorticity is very small, as expected near a symmetry line. Therefore these vertical-line sign changes should not be called separate vortices from line data alone; they primarily show vertical momentum redistribution and near cancellation of density and pressure forcing.

## C9 control

C9 remains much simpler at representative times.

### y = 20 mm
At 10 s the resolved crossings are 12.10 and 27.90 mm, symmetric about x=20 mm. alphaL~0.977 and omega_z is +2.45/-2.45 1/s. The local Darcy magnitude is ~0.298 m/s2, larger than the pressure scale (~0.0091 m/s2) and the explicit beta-buoyancy scale (~1.1e-5 m/s2) at the crossing. This shows that even at alphaL close to 1, the enthalpy-porosity Darcy term can strongly set the cell boundary.

### y = 30 mm
At 10 s the crossings are 11.97 and 28.03 mm, alphaL~0.967 and omega_z +2.44/-2.44 1/s. Darcy magnitude is ~0.607 m/s2 and again sets the local reversal region.

### centerline
No resolved Uy crossing remains at 10 s. The few centerline crossings seen during the transient are all associated with the phase-change/Darcy region.

## Scientific conclusion

1. B9 is **not** supported as mere random numerical oscillation by these line diagnostics. Its resolved reversals are highly symmetric and systematically associated with finite density gradients, pressure response, vorticity and later phase-change/Darcy resistance.

2. B9 y30 is the clearest variable-density natural-convection signature: resolved crossings remain predominantly liquid, density-gradient buoyancy is the largest sampled acceleration scale in 72% of crossing samples, and Darcy is never the largest scale there.

3. B9 y20 develops an additional, time-dependent secondary structure. Early/mid-transient additional reversals can occur while still liquid and are associated with density-buoyancy/pressure. By 10 s all four resolved crossings sit in alphaL~0.94 and the outer pair is strongly shaped by Darcy resistance. Thus the late multicell-looking profile is a coupled buoyancy-pressure-mushy phenomenon, not simply a pure-buoyancy cell pattern.

4. The B9 centerline sign reversals are not sufficient evidence for extra vortices because centerline vorticity is near zero. They should be described as vertical velocity reversals/momentum redistribution until a 2-D streamline field is available.

5. C9 exhibits the cleaner two-cell symmetry, but its final cell boundaries are also strongly influenced by Darcy resistance as the phase-change region develops. Therefore "C9 looks classical" does not mean Darcy is negligible.

6. The current repository stores line diagnostics but not the full final volumetric fields, so closed recirculation cells cannot yet be proven geometrically from streamlines. A future run that stores or exports 2-D U/vorticity/alphaL fields would permit direct streamline/topology confirmation.
