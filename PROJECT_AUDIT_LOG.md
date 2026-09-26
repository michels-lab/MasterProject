# QuickCup-Solidification — Project Audit Log

> Persistent technical audit trail for Michel Duarte's OpenFOAM thesis project.
>
> **Project rule (2026-09-24):** whenever the working Project Audit Log is updated in ChatGPT, the same technical entry must also be added to this Git log. Entries must distinguish verified evidence from interpretation, and must not present assumptions as facts.

## Evidence labels

- **[CHAT-RECOVERED]** Recovered from the prior project conversation/audit history.
- **[RUN-VERIFIED]** Supported by terminal/log output preserved in the project history.
- **[GIT-VERIFIED]** Confirmed against the files currently tracked in this repository.
- **[INTERPRETATION]** Technical interpretation; not itself a directly observed result.
- **[OPEN]** Pending verification or additional simulation.

---

# 0. Pre-audit project context

## 2026-07-27 — Methodological sequence
**[CHAT-RECOVERED]**

The working methodology was defined as:

1. Chemical composition.
2. JMatPro thermophysical/solidification data.
3. OpenFOAM model.
4. Real castings / Quick-Cup thermal curves.
5. Numerical–experimental comparison and model adjustment.

JMatPro was intended to supply quantities such as (c_p(T)), (k(T)), (ho(T)), liquidus (T_L), solidus (T_S), latent heat and liquid-fraction information for the OpenFOAM model.

## 2026-07-28 — Initial numerical architecture
**[CHAT-RECOVERED]**

The starting numerical architecture was identified as conjugate heat transfer (metal + mold) based on the doctor's case, with phase change through the enthalpy–porosity / `solidificationMeltingSource` approach.

Recovered baseline characteristics:

- Metal section: approximately 40 × 40 mm.
- Quasi-2D setup using `empty` front/back and one cell through depth.
- Fine mesh later verified as 6400 metal cells + 5480 mold cells.
- (Delta x approx 0.5) mm in the metal.
- (T_{sol} approx 1423) K.
- (T_{liq} approx 1473) K.
- (L = 2.286	imes10^5) J/kg.
- (C_u = 10^5).
- `alpha1e = 0.8`.
- Interfacial layers: thickness (2	imes10^{-4}) m and conductivity (0.1) W/(m·K).

Two early risks were already noted:

1. `createZonesDict` geometries could overlap.
2. `emmisivity` was misspelled in an early temperature boundary condition.

## 2026-07-29 — Doctor's reference cases
**[CHAT-RECOVERED]**

The doctor's material was identified as containing a `bcFourier` case and a CHT metal/mold case. The thesis model was to preserve:

- conjugate heat transfer,
- liquid/solid phase evolution,
- latent heat,
- mushy-zone resistance,
- thermal probes,
- comparison with experimental cooling curves.

## 2026-09-03 — Longer-term recalescence model direction
**[CHAT-RECOVERED]**

A possible future model extension was defined: replace a purely temperature-defined liquid fraction (f_l(T)) by a kinetic evolution (df/dt), while preserving CHT, energy, momentum, porosity resistance and latent heat.

This was treated as a later physics extension, not as a justification for changing the validated baseline prematurely.

## 2026-09-07 — Recalescence interpretation rule
**[CHAT-RECOVERED]**

The audit established that numerical temperature rebound alone is not sufficient evidence of physical recalescence.

Recovered interpretation rule:

- A real recalescence model should arise from transformation kinetics / undercooling / latent-heat release.
- The standard OpenFOAM phase-fraction formulation can remelt when temperature increases.
- `relax` in `solidificationMeltingSource` is a numerical relaxation parameter, not a physical kinetic constant.
- Validation should first be demonstrated in the reduced model before moving to a full 3D case.

## 2026-09-11 — Latent-heat source dimensional check
**[CHAT-RECOVERED]**

For a future kinetic formulation, the latent-heat source was written as

[
S_L=-ho Lrac{partial f_l}{partial t}
]

with required units of W/m³.

A simple (f_s(T)) law was explicitly considered insufficient to reproduce genuine undercooling/recalescence physics by itself.

---

# 1. Numbered Project Audit Log

## 2026-09-15

### AUD-001 — OpenFOAM version
**[CHAT-RECOVERED] [GIT-VERIFIED current case headers]**

Working environment identified as **OpenFOAM Foundation v14**, patch **20260724**.

Current repository files still contain a mixture of v13-era headers and v14-updated files; runtime configuration audited in September targeted Foundation v14.

**Impact:** commands and dictionary behavior must be checked against Foundation v14, not assumed from v13 or OpenCFD documentation.

**Status:** ✅ confirmed.

---

### AUD-002 — Independent working project structure
**[CHAT-RECOVERED]**

An independent working case structure under `QuickCup_Solidification/cleanproy` was established instead of modifying the doctor's original source case directly.

**Status:** ✅ historical baseline established.

---

### AUD-003 — Mesh-size documentation discrepancy
**[CHAT-RECOVERED]**

A documented value of **0.05 mm** did not match the executed mesh.

The actual metal discretization corresponded to approximately:

[
Delta x = Delta y = 0.0005 	ext{m} = 0.5 	ext{mm}
]

**Impact:** previous written documentation overstated spatial resolution by a factor of 10.

**Status:** ✅ discrepancy identified; documentation must use the executed mesh unless the mesh is changed.

---

### AUD-004 — Global mesh size
**[CHAT-RECOVERED]**

Mesh contained **11,880 cells**.

Recovered domain bounding dimensions were approximately:

- 54 mm in x,
- 55 mm in y,
- 10 mm in z.

**Status:** ✅ confirmed during mesh audit.

---

### AUD-005 — Quasi-2D character
**[CHAT-RECOVERED] [GIT-VERIFIED]**

The case has one cell through the z direction with front/back patches of type `empty`.

The numerical problem is therefore quasi-2D even though the block has finite 10 mm depth.

**Status:** ✅ confirmed.

---

### AUD-006 — Pre-existing cellZones
**[CHAT-RECOVERED]**

Before running `createZones`, the mesh already contained the `metal` and `mold` cellZones.

This triggered a specific check to determine whether `createZones` was actually changing them.

**Status:** ✅ investigated in AUD-012–014.

---

### AUD-007 — blockMesh on OpenFOAM 14
**[CHAT-RECOVERED]**

`blockMesh` completed cleanly under the audited OpenFOAM 14 environment.

**Status:** ✅.

---

### AUD-008 — checkMesh
**[CHAT-RECOVERED]**

`checkMesh` returned:

`Mesh OK.`

Recovered mesh totals included:

- 24,198 points,
- 47,738 faces,
- 11,880 hexahedral cells.

**Status:** ✅.

---

### AUD-009 — Geometric solution directions
**[CHAT-RECOVERED]**

`checkMesh` identified active geometric directions equivalent to:

`(1 1 0)`

consistent with the intended 2D x-y solution.

**Status:** ✅.

---

### AUD-010 — Mesh quality
**[CHAT-RECOVERED]**

Recovered mesh-quality metrics:

- non-orthogonality: **0°**,
- maximum skewness: approximately **6.94×10⁻¹⁴**.

**Impact:** poor geometric mesh quality was ruled out as a likely source of the numerical behavior being investigated.

**Status:** ✅.

---

### AUD-011 — Connectivity and zones
**[CHAT-RECOVERED]**

The unsplit mesh was one connected region containing two cellZones (`metal` and `mold`).

**Status:** ✅.

---

### AUD-012 — Zone cell counts before createZones
**[CHAT-RECOVERED]**

Before `createZones`:

- `metal` = **6400 cells**,
- `mold` = **5480 cells**,
- total = **11,880 cells**.

The counts exactly matched the global mesh total.

**Status:** ✅.

---

### AUD-013 — createZones did not alter cellZones
**[CHAT-RECOVERED]**

`createZones` completed without a runtime error, but the `cellZones` file had the same MD5 hash before and after:

`6b858d42fedaa8f291432cd603c1c890`

**Conclusion:** the executed `createZones` step did **not** modify the existing cellZones in that test.

**Status:** ✅ verified in the historical run.

---

### AUD-014 — createZonesDict overlap risk
**[CHAT-RECOVERED] [GIT-VERIFIED]**

`createZonesDict` defined:

- metal box: `(-0.001 -0.001 -0.001)` to `(0.041 0.041 0.011)`,
- mold box: `(-0.008 -0.016 -0.001)` to `(0.048 0.041 0.011)`.

These boxes geometrically overlap.

In the currently tracked `Allrun`, `runApplication createZones` is commented out, and the cellZones are already created by `blockMesh`, which makes the overlap dormant in the present workflow.

**Status:** ⚠️ dictionary remains potentially unsafe if re-enabled; currently not part of `Allrun`.

---

### AUD-015 — splitMeshRegions syntax changed in OF14
**[CHAT-RECOVERED]**

Historical command:

`splitMeshRegions -cellZones metal mold`

failed in OpenFOAM 14 with:

`Wrong number of arguments, expected 0 found 1`

Because splitting failed, the subsequent `foamMultiRun` lacked the expected region mesh (`metal/polyMesh`); that downstream error was therefore not an independent solver failure.

Corrected command:

`splitMeshRegions -cellZones all`

**Status:** ✅ corrected.

---

### AUD-016 — Region split verified
**[CHAT-RECOVERED] [GIT-VERIFIED workflow]**

`splitMeshRegions -cellZones all` succeeded and produced:

- metal: **6400 cells**,
- mold: **5480 cells**,
- metal/mold interface: **240 faces**.

The current `Allrun` scripts use this corrected syntax.

**Status:** ✅.

---

### AUD-017 — Initial foamMultiRun boundary read failure
**[CHAT-RECOVERED]**

`foamMultiRun` failed while reading `0/metal/T`, specifically the `metalTop/h` entry, with an `attempt to read beyond EOF`-type dictionary read failure.

This was traced to boundary-condition syntax rather than to CHT or phase-change physics.

**Status:** ✅ root cause identified.

---

### AUD-018 — externalWallHeatFluxTemperature syntax correction
**[CHAT-RECOVERED]**

Entries written as scalar tokens:

`h 50;`

`Ta 300;`

were corrected to field/function syntax compatible with the audited boundary condition:

`h uniform 50;`

`Ta constant 300;`

After correction, the case could run.

**Status:** ✅.

---

### AUD-019 — emissivity spelling
**[CHAT-RECOVERED] [GIT-VERIFIED historical cases]**

Early cases contained:

`emmisivity`

instead of:

`emissivity`

Later B2–B5/C2–C5 temperature files use the corrected spelling.

**Status:** ✅ corrected in later cases; historical B1/C1-style files retain the old spelling as part of the audit trail.

---

### AUD-020 — Baseline 0–300 s run
**[CHAT-RECOVERED]**

After the dictionary corrections, the baseline OpenFOAM 14 case ran from 0 to **300 s** and terminated with:

`End`

Region counts remained:

- metal 6400,
- mold 5480,
- interface 240 faces.

**Status:** ✅ baseline executable.

---

### AUD-021 — Buoyancy inside solidificationMelting
**[CHAT-RECOVERED]**

Source inspection confirmed that `solidificationMelting` adds an explicit thermal-buoyancy contribution of the form

[
S_b=ho_{ref},mathbf g,eta,Delta T
]

(recovered reference: `solidificationMelting.C`, around line 379 in the inspected source).

**Impact:** `beta` inside the phase-change model is dynamically important; it is not merely metadata.

**Status:** ✅ source behavior identified.

---

### AUD-022 — Double-buoyancy route identified
**[CHAT-RECOVERED]**

Two independent routes to momentum were identified in the original formulation:

1. `icoTabulated → rho(T) → -gh∇rho → netForce → U`
2. `solidificationMelting → rhoRef*g*beta*ΔT → fvModels().source(rho,U) → U`

**Conclusion:** the original setup represented thermal buoyancy twice.

**Controlled-action decision:** separate the two formulations rather than leaving both active simultaneously.

**Status:** ✅ diagnosis established.

---

### AUD-023 — B formulation: density-driven buoyancy only
**[CHAT-RECOVERED] [GIT-VERIFIED descendants]**

Historical controlled case: `B_icoTabulated_only`.

Configuration:

- `icoTabulated` / tabulated (ho(T)) active,
- `beta = 0` in `solidificationMeltingSource`,
- mushy drag and latent heat remain active,
- Boussinesq source from the phase-change model disabled.

The historical test completed 0–300 s.

The current B-family descendants preserve this physical split: tabulated density + `beta 0`.

**Status:** ✅.

---

## 2026-09-21

### AUD-024 — C formulation: Boussinesq-only
**[CHAT-RECOVERED] [GIT-VERIFIED descendants]**

Historical controlled case: `C_Boussinesq_only`.

Configuration:

- `rhoConst`,
- (ho = 6930) kg/m³,
- `beta = 1.13e-4 1/K` in `solidificationMeltingSource`,
- temperature-dependent-density buoyancy route disabled,
- Boussinesq phase-change-source buoyancy active.

Historical case completed 0–300 s.

Current C-family descendants preserve this physical split.

**Status:** ✅.

---

### AUD-025 — Initial A/B/C thermal comparison
**[CHAT-RECOVERED]**

Probe location:

`(0.02 0.02 0.005)`

Recovered comparison:

| Metric | A | B | C |
|---|---:|---:|---:|
| (T=1473) K | ~0.00918 s | ~0.00918 s | ~0.00923 s |
| (T=1423) K | ~4.901 s | ~4.901 s | ~5.000 s |
| nominal mushy interval | ~4.892 s | ~4.892 s | ~4.991 s |
| (Tapprox1422) K | ~21.45 s | ~21.50 s | ~21.85 s |
| (T(300s)) | ~1144.46 K | ~1144.50 K | ~1144.96 K |

Recovered maximum curve differences:

- max (Delta T_{A-B}) ≈ **0.22 K**,
- max (Delta T_{A-C}) ≈ **2.05 K**.

**Interpretation at that stage:** changing the buoyancy formulation had relatively little effect on the central thermal curve compared with the much larger initialization error found next.

**Status:** ✅ historical comparison recovered.

---

### AUD-026 — Unphysical initial thermal collapse
**[CHAT-RECOVERED]**

All A/B/C formulations showed an extremely fast initial cooling from approximately:

[
1500 	ext{K} ightarrow 1473 	ext{K}
]

in about **0.009 s**.

Because it appeared independently of buoyancy formulation, buoyancy was ruled out as the primary cause.

**Status:** ✅ anomaly isolated; investigated in AUD-027.

---

### AUD-027 — alpha1 initial-state inconsistency
**[CHAT-RECOVERED]**

The phase-change state was inconsistent at startup:

- (T_0=1500) K,
- (T_0>T_{liq}=1473) K,
- but liquid fraction was effectively initialized as (alpha_l=0) when the `phaseChangeSource:alpha1` field was absent/not initialized consistently.

Recovered source reasoning: `solidificationMelting::update` recomputes liquid fraction from temperature and introduces the corresponding latent-energy correction.

With the audited parameters

- (L=2.286	imes10^5) J/kg,
- (C_p=827) J/(kg·K),
- `alpha1e=0.8`,
- `relax=0.1`,

the first liquid-fraction correction was estimated at (Deltaalphaapprox0.02786), corresponding to an artificial latent-energy temperature change of about **7.70–7.72 K**.

**Status:** ✅ primary cause of the initial collapse identified.

---

### AUD-028 — alpha1 initialized as liquid
**[CHAT-RECOVERED] [GIT-VERIFIED current normal cases]**

A corrected case initialized:

`phaseChangeSource:alpha1 = 1.0`

for metal initially above the liquidus.

Result: the ~7.7 K artificial startup collapse disappeared.

Current B1–B5/C1–C5 normal cases tracked in Git contain an initial `phaseChangeSource:alpha1` field with `internalField uniform 1.0`.

**Status:** ✅ correction adopted.

---

### AUD-029 — Thermodynamically consistent initial phase
**[CHAT-RECOVERED]**

With (alpha_l(0)=1) and (T_0>T_{liq}), the simulation no longer begins with artificial solid fraction above liquidus.

This became the required initial-state convention for the normal phase-change cases.

**Status:** ✅.

---

### AUD-030 — No recovered entry
**[CHAT-RECOVERED]**

No historical content was found for AUD-030. The original conversation numbering jumped from AUD-029 to AUD-031.

This identifier is intentionally left unused rather than inventing an entry retroactively.

**Status:** — preserved numbering gap.

---

### AUD-031 — Temperature rebound was accompanied by remelting
**[CHAT-RECOVERED]**

In corrected case D:

- local minimum (Tapprox1455) K near **4.90 s**,
- temperature rose to approximately **1461.18 K** around **11.6 s**,
- during the rebound, liquid fraction increased approximately **0.9283 → 0.9527**.

**Conclusion:** the rebound involved **partial remelting** in the standard equilibrium/relaxed `solidificationMelting` formulation.

It must **not** automatically be labelled physical recalescence.

**Status:** ✅ interpretation corrected.

---

### AUD-032 — Corrected long-run solidification behavior
**[CHAT-RECOVERED]**

For corrected case D with (alpha_l(0)=1):

- liquidus crossing (1473) K: approximately **3.2506 s**,
- (alpha_l=0.99): approximately **3.5624 s**,
- solidus-temperature crossing (1423) K: approximately **104.9 s**,
- (alpha_l=0.50): approximately **207.56 s**,
- (alpha_l=0.01): approximately **227.59 s**,
- by 300 s: (alpha_l=0),
- (T(300s)approx1329.77) K.

**Impact:** correcting the phase initialization transformed the apparent solidification timescale from an unrealistically immediate collapse into a long phase-change process.

**Status:** ✅.

---

# 2. Additional recovered chronology after the numbered audit

## 2026-09-18 — Validation architecture
**[CHAT-RECOVERED]**

Three model levels were separated conceptually:

1. **Level 1:** (f_s(T)) baseline.
2. **Level 2:** JMatPro/Scheil-informed (f_s(T)).
3. **Level 3:** kinetic (f_s(T,t,Delta T,	ext{nucleation/growth})).

Validation should not rely only on RMSE. Target quantities include:

- liquidus / transformation temperatures,
- minimum temperature before rebound,
- recovered/rebound temperature,
- (Delta T_{rec}),
- (dT/dt),
- start time,
- duration,
- phase-fraction evolution.

Parameters must not be tuned merely to force agreement.

---

## 2026-09-21 — B2/C2 convergence and solver-loop audit
**[CHAT-RECOVERED] [RUN-VERIFIED historical logs]**

A multi-region control distinction was established:

- root `system/fvSolution` controls the global `foamMultiRun` PIMPLE coupling (`nOuterCorrectors`, `nEnergyCorrectors`),
- regional `system/metal/fvSolution` and `system/mold/fvSolution` control regional linear solvers and local corrector settings.

Recovered C2-era configuration included root `nOuterCorrectors 1`, while metal had its own pressure/velocity correctors.

Representative C2 log values around (tapprox0.1) s included:

- Courant mean ≈ 0.00054–0.00057,
- Courant max ≈ 0.00466–0.00488,
- energy residuals driven to ~10⁻¹⁰–10⁻⁸ in the sampled steps,
- pressure final residuals around ~10⁻⁷ after correction.

Recovered B2 end-of-run evidence:

- metal energy approximately (4.68	imes10^{-5}ightarrow1.42	imes10^{-11}),
- mold energy approximately (3.73	imes10^{-5}ightarrow3.69	imes10^{-10}),
- cumulative continuity error approximately (-1.7486	imes10^{-7}),
- run terminated with `End`.

A B2 flow diagnostic also found volume-mean (|U|) of approximately:

- **0.0115–0.0116 m/s** near 2 s,
- **0.0079 m/s** around 6.5 s.

Velocity peaks preceding thermal rebounds were noted, but a causal convective interpretation was **not** considered proven.

---

## 2026-09-22 — B3_docFV / C3_docFV
**[CHAT-RECOVERED] [GIT-VERIFIED configuration]**

B3/C3 were created as convergence/documentation descendants of B2/C2 with revised `fvSolution` structure.

Recovered B3 run:

- 0–10 s,
- (Delta t=0.001) s,
- 10,000 time steps,
- ~189.5 s CPU / ~197 s wall time,
- no failure,
- `nOuterCorrectors=2` at root,
- `nEnergyCorrectors` omitted → default 1,
- approximately 2 h solves, 2 e solves and 4 p_rgh solves per timestep,
- maximum Courant ≈ **0.175912**,
- final Courant ≈ **0.0607**,
- cumulative continuity ≈ **1.66260×10⁻⁴**.

Recovered C3 run:

- 0–10 s,
- same (Delta t=0.001) s structure,
- ~192.6 s CPU,
- no failure,
- same 2 h / 2 e / 4 p_rgh solves per timestep,
- maximum Courant ≈ **0.0701958**,
- final Courant ≈ **0.0245**,
- cumulative continuity ≈ **1.78365×10⁻⁴**.

**Status:** ✅ B3/C3 completed and became the convergence reference for the next controlled tests.

---

## 2026-09-22 — B4_energy2 / C4_energy2
**[CHAT-RECOVERED] [GIT-VERIFIED configuration]**

B4/C4 were created by copying B3/C3 and changing the root multi-region coupling to include:

`nEnergyCorrectors 2;`

while preserving the other B3/C3 settings.

**Experimental purpose:** isolate the effect of repeating the energy correction in the global multi-region coupling.

**Important:** no recovered historical evidence currently establishes quantitative B4/C4 run results. Do not invent a conclusion until the actual logs/results are inspected.

**Status:** 🟡 configuration verified; quantitative outcome pending/requires recovered logs if available.

---

# 3. Current repository audit — 2026-09-24

## Repository state
**[GIT-VERIFIED]**

Repository:

`realmichelduarte/QuickCup-Solidification`

Latest audited commit:

`614ee6e186a3dfbbbec159b27c4d89015703a95f`

Message:

`Add convergence tests and update buoyancy cases`

The `cases_buoyancy` directory contains **12 cases** and **382 tracked case files**.

Normal B1–B5/C1–C5 cases contain 32 tracked files each; the two control cases contain 31 each.

### Current case lineage

- `B1_alphaini`
- `B2_test`
- `B3_docFV`
- `B4_energy2`
- `B5_outer3`
- `B_betazero`

and

- `C1_alphaini`
- `C2_test`
- `C3_docFV`
- `C4_energy2`
- `C5_outer3`
- `C_rhoconstant`

---

## 2026-09-24 — Full SHA audit of all buoyancy cases
**[GIT-VERIFIED]**

All tracked files under `cases_buoyancy` were compared by relative path and blob SHA.

Only these relative paths vary across the case generations:

1. `0/metal/T`
2. `0/metal/phaseChangeSource:alpha1` (absent in the two control cases)
3. `constant/metal/fvModels`
4. `constant/metal/materials/castIron`
5. `system/controlDict`
6. `system/functions`
7. `system/fvSolution`
8. `system/metal/fvSolution`
9. `system/mold/fvSolution`

All other corresponding tracked files are identical across their SHA groups.

---

## 2026-09-24 — Current B/C physical split
**[GIT-VERIFIED]**

### B family

Current B5 configuration preserves:

- `equationOfState icoTabulated`,
- tabulated (ho(T)),
- `beta 0` in `solidificationMeltingSource`,
- (g=(0,-9.81,0)),
- laminar momentum model,
- metal-top external heat-transfer coefficient (h=10) W/(m²·K).

### C family

Current C5 configuration preserves:

- `equationOfState rhoConst`,
- (ho=6930) kg/m³,
- `beta 1.13e-04` in `solidificationMeltingSource`,
- same gravitational acceleration,
- metal-top external heat-transfer coefficient (h=50) W/(m²·K).

---

## 2026-09-24 — Current convergence sequence
**[GIT-VERIFIED]**

### B3/C3 — reference
Root `system/fvSolution`:

- `nOuterCorrectors 2`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

### B4/C4 — energy-corrector experiment
Same reference structure plus:

- `nEnergyCorrectors 2`

### B5/C5 — current outer-corrector experiment
Root `system/fvSolution`:

- `nOuterCorrectors 3`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

Thus B5/C5 are **not** cumulative descendants of the B4/C4 energy-corrector change. They are a separate controlled experiment relative to the B3/C3 reference: energy correction returns to default while global outer coupling is increased from 2 to 3.

Regional metal settings in B5/C5 remain:

- `momentumPredictor no`
- `nOuterCorrectors 1`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 0`

---

## 2026-09-24 — startFrom asymmetry in B5/C5
**[GIT-VERIFIED]**

- B5: `startFrom latestTime;`
- C5: `startFrom startTime;`

If both cases are cleaned before execution, this difference should not change a fresh run starting from directory `0`. However, without cleaning, B5 can resume a previous solution whereas C5 explicitly starts from the configured start time.

**Impact:** this must be controlled when comparing B5 and C5.

**Status:** ⚠️ known reproducibility difference.

---

## 2026-09-24 — Current probe configuration
**[GIT-VERIFIED]**

Normal B1–B5/C1–C5 cases contain a `temperatureProbe` at:

`(0.02 0.02 0.005)`

recording:

- `T`
- `phaseChangeSource:alpha1`

at every timestep.

The two control cases only record `T`.

---

## 2026-09-24 — Line-profile request from thesis advisor
**[CHAT-RECOVERED] [GIT-VERIFIED absence in current cases]**

The advisor requested velocity/temperature profiles directly through OpenFOAM rather than ParaView.

Current cases contain **no line-sampling function object yet**.

OpenFOAM v14 provides line/graph sampling mechanisms suitable for extracting fields along a line. Candidate outputs for the thesis include:

[
T(x,t),quad mathbf U(x,t),quad |mathbf U|(x,t),quad alpha_l(x,t)
]

and derived relationships such as:

[
|mathbf U|=f(T)
]

at matched sampled locations.

Potential center lines of the 40 × 40 mm metal section include:

- horizontal: ((0,0.020,0.005)ightarrow(0.040,0.020,0.005))
- vertical: ((0.020,0,0.005)ightarrow(0.020,0.040,0.005))

**Status:** 🟡 requested; implementation not yet added.

---

# 4. Standing interpretation and reproducibility rules

1. **Do not call a temperature rebound “recalescence” solely because (dT/dt>0).** Check phase evolution and whether the model is actually solidifying or remelting.
2. **Do not mix physical-model changes with numerical-convergence changes in the same controlled comparison.**
3. **Always record the exact case name, parent case, modified files, numerical parameter changed, run interval and relevant diagnostics.**
4. **For B/C comparisons, preserve the intended buoyancy separation:** B = density-driven route; C = Boussinesq-source route.
5. **Initial liquid metal above (T_{liq}) must be initialized consistently with (alpha_l=1).**
6. **A successful solver exit is not sufficient validation.** Track Courant number, residual behavior, continuity, energy evolution, phase fraction and comparison with experimental thermal curves.
7. **Whenever this audit log is updated in the working ChatGPT thread, update this Git file as well.**
8. **If an old entry cannot be recovered exactly, mark the uncertainty explicitly instead of filling the gap by inference.**

---

# 5. Open items

- [ ] Inspect/recover quantitative B4/C4 results if their run logs still exist outside Git.
- [ ] Execute/analyze B5/C5 and compare against B3/C3 and B4/C4 using the same metrics.
- [ ] Add OpenFOAM-native line sampling for (U), (T) and (alpha_l) without changing solver physics.
- [ ] Define a reproducible plotting pipeline for velocity/temperature profiles.
- [ ] Continue experimental/JMatPro validation and keep recalescence interpretation separate from equilibrium remelting.

---

## 2026-09-24 — AUD-033 — B/C comparison contains an additional thermal-boundary difference
**[GIT-VERIFIED]**

A repository audit found that the current B2–B5 and C2–C5 descendants differ not only in the buoyancy formulation, but also in the external heat-transfer coefficient at `metalTop`:

- B2–B5: `h = 10 W/(m²·K)`
- C2–C5: `h = 50 W/(m²·K)`

This difference was already present in the initial repository commit (`206f9594`) and remains present in the current files.

**Impact:** if B and C are intended as a controlled comparison of buoyancy formulations, the B/C thermal curves cannot be attributed uniquely to buoyancy while `h` also differs.

**Required action before interpretation:** determine whether the B/C heat-transfer coefficient difference is an intentional representation of two different physical/experimental conditions or an unintended confounding variable. Until that is resolved, report B/C comparisons as multi-parameter comparisons rather than buoyancy-only comparisons.

**Status:** ⚠️ open methodological issue; do not change historical cases retroactively.

---

## 2026-09-24 — AUD-034 — B2 thermal-boundary change has no recovered design justification
**[CHAT-RECOVERED] [GIT-VERIFIED]**

Historical conversation context confirms that:

- `B2_test` was created by copying `B1_alphaini`.
- `C2_test` was created by copying `C1_alphaini`.
- B2/C2 were intended as short (~10 s) numerical/convergence tests.
- Subsequent documented changes concerned timestep stability, e.g. an attempted `deltaT=0.1` that failed and a return to `deltaT=0.001`, plus output cadence.

Current Git history shows:

- `B1_alphaini/0/metal/T`: `metalTop h = 50 W/(m²·K)`
- `B2_test/0/metal/T`: `metalTop h = 10 W/(m²·K)`
- `C1_alphaini/0/metal/T`: `metalTop h = 50 W/(m²·K)`
- `C2_test/0/metal/T`: `metalTop h = 50 W/(m²·K)`

No recovered Project Audit Log entry or conversation decision documents a deliberate physical reason for changing the B branch heat-transfer coefficient from 50 to 10 when creating B2.

**Interpretation rule:** the B1→B2 change in `h` is therefore an **undocumented model change**, not a validated design decision. It must not be assumed intentional or accidental without further evidence.

**Impact:** B2–B5 vs C2–C5 comparisons are thermally confounded unless a controlled common-`h` comparison is created.

**Status:** ⚠️ unresolved origin; preserve historical cases and investigate before physical interpretation.

---

## 2026-09-24 — AUD-035 — Common convection coefficient recommended for controlled B/C rerun
**[GIT-VERIFIED] [LITERATURE-SUPPORTED] [DECISION]**

For the planned controlled B/C comparison, the top free-surface convection coefficient should be made identical in both branches.

Recommended baseline:

`metalTop h = 10 W/(m²·K)`

Rationale:

- OpenFOAM treats `h` as the external convective heat-transfer coefficient and `emissivity` as a separate radiative contribution to the ambient boundary.
- The Quick-Cup geometry represents a small open-top molten-metal sample exposed to ambient air.
- Natural-convection correlations for a hot upward-facing horizontal plate place the expected convection coefficient in the order of magnitude of ~10 W/(m²·K) for this small characteristic length; `h = 50 W/(m²·K)` would be more consistent with significant forced airflow or with an effective coefficient that lumps additional heat-transfer modes.
- Because radiation is already represented explicitly with `emissivity = 0.3`, the convective `h` should not be inflated to account for radiation.

**Implementation rule:** preserve historical B5/C5 unchanged. Create a new controlled comparison derived from B5/C5 in which the only intended B/C physical difference is the buoyancy formulation and both cases use the same `metalTop h = 10 W/(m²·K)`.

**Status:** ✅ baseline choice established; new controlled cases not yet created/run.

---

## 2026-09-24 — AUD-036 — Controlled B/C series must be rerun with common thermal boundary
**[METHODOLOGICAL DECISION] [GIT-VERIFIED BASIS]**

Because the B2–B5 and C2–C5 lineages use different `metalTop` convection coefficients (`h=10` in B and `h=50` in C), those historical cases are not valid for a direct controlled comparison between the B and C buoyancy formulations.

### Consequence

- Historical B2–B5/C2–C5 cases remain useful as development history and for within-family numerical observations.
- They are **not** suitable for attributing B-vs-C differences uniquely to buoyancy formulation.
- The numerical-convergence sequence must be repeated with a common `metalTop h` if the thesis requires an objective B-vs-C comparison.

### New controlled-series rule

Use the same thermal boundary in both families, with the current baseline recommendation:

`metalTop h = 10 W/(m²·K)`

Then reproduce the intended numerical sequence symmetrically for B and C:

1. common baseline / test case,
2. documented reference with `nOuterCorrectors=2`,
3. energy-corrector test with `nEnergyCorrectors=2`,
4. outer-corrector test with `nOuterCorrectors=3`.

All other intended physical and numerical settings must remain matched except for the buoyancy formulation itself.

### Preservation rule

Do not overwrite or delete historical B2–B5/C2–C5 cases. Preserve them as an auditable development record and create a new clean controlled lineage for thesis comparison.

**Status:** ✅ methodological correction established; reruns pending.

---

## 2026-09-24 — AUD-037 — Pairwise B/C audit identifies the clean comparison series
**[GIT-VERIFIED] [METHODOLOGICAL CORRECTION]**

A full pairwise SHA audit was performed for:

- `B2_test ↔ C2_test`
- `B3_docFV ↔ C3_docFV`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

### B2/C2

B2 and C2 differ in **six** tracked files:

1. `0/metal/T`
2. `constant/metal/fvModels`
3. `constant/metal/materials/castIron`
4. `system/controlDict`
5. `system/fvSolution`
6. `system/metal/fvSolution`

Important numerical mismatch:

- B2 root: `nOuterCorrectors 1`
- C2 root: `nOuterCorrectors 4`, `nEnergyCorrectors 1`

Therefore B2/C2 were transitional development cases, not a controlled B-vs-C pair.

### B3/C3

B3/C3 differ in only **four** tracked files:

1. `0/metal/T`
   - B3: `h = 10 W/(m²·K)`
   - C3: `h = 50 W/(m²·K)`
2. `constant/metal/fvModels`
   - B3: `beta = 0`
   - C3: `beta = 1.13e-04`
3. `constant/metal/materials/castIron`
   - B3: `icoTabulated` temperature-dependent density
   - C3: `rhoConst = 6930 kg/m³`
4. `system/controlDict`
   - B3: `startFrom latestTime`
   - C3: `startFrom startTime`

All other tracked files are identical by SHA.

### B4/C4

B4/C4 also differ in exactly the same four files listed above.

Both use the same numerical experiment:

- `nOuterCorrectors 2`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`
- `nEnergyCorrectors 2`

All other tracked files are identical by SHA.

### B5/C5

B5/C5 also differ in exactly the same four files listed above.

Both use the same numerical experiment:

- `nOuterCorrectors 3`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

All other tracked files are identical by SHA.

### Classification of the four B3–B5 / C3–C5 differences

**Intended physical differences to preserve:**

1. `fvModels/beta`
2. `castIron/equationOfState`

These define the two alternative buoyancy formulations.

**Non-physical differences to normalize:**

3. `metalTop/h`
4. `controlDict/startFrom`

For the controlled rerun, use:

- `metalTop h = 10 W/(m²·K)` in both families.
- `startFrom startTime` in both families.
- run each case from a clean state.

### Corrected rerun plan

The scientifically useful convergence series begins at B3/C3. B2/C2 should remain historical transitional cases and should **not** be recreated as if they were a controlled pair.

The controlled rerun therefore requires **six cases**, not eight:

- B3-controlled / C3-controlled — reference
- B4-controlled / C4-controlled — `nEnergyCorrectors=2`
- B5-controlled / C5-controlled — `nOuterCorrectors=3`

Within each pair, every tracked input must be identical except for the two intended buoyancy-model differences.

This entry supersedes the earlier broad wording in AUD-036 that suggested rerunning B2–B5/C2–C5 as a single controlled sequence.

**Status:** ✅ complete pairwise audit; canonical controlled-case construction pending.

---

## 2026-09-24 — AUD-038 — Controlled C branch will use rhoConst = 6820 kg/m³
**[USER DECISION] [GIT-CONTEXT VERIFIED] [SOURCE-CHECKED]**

For the new controlled buoyancy-comparison series, the C-family constant-density equation of state will use:

`rho = 6820 kg/m³`

instead of the historical `6930 kg/m³`.

Rationale from the current B-family material definition:

- B-family `icoTabulated` uses `rho0 = 6820 kg/m³` at `T0 = 1473 K`.
- The tabulated density also gives approximately `rho = 6820 kg/m³` at the liquidus reference temperature (~1473 K).

This makes `6820 kg/m³` the selected constant-density reference for the new C controlled cases.

### Important coupled parameter

OpenFOAM's `solidificationMelting` momentum buoyancy source uses:

`Sb = rhoRef * g * beta * deltaT`

so `rhoRef` directly scales the Boussinesq buoyancy source. OpenFOAM documents `rhoRef` as the reference density used by this model.

Therefore, if the controlled C branch is intended to use a self-consistent single reference density of 6820 kg/m³, `constant/metal/fvModels` should also use:

`rhoRef 6820;`

rather than leaving the historical `rhoRef 6930;`.

This change should be made deliberately in the new controlled lineage, not retroactively in historical cases.

**Status:** ✅ `rhoConst=6820` decided; `rhoRef=6820` recommended for internal Boussinesq consistency in the new C cases.

---

## 2026-09-24 — AUD-039 — Controlled buoyancy comparison series created
**[GIT-VERIFIED] [IMPLEMENTED]**

A new controlled case family was created outside the historical `cases_buoyancy/` directory:

`cases_controlled_buoyancy/`

The historical buoyancy-development cases remain unchanged.

### Controlled cases

- `B3_reference` — derived from historical `B3_docFV`
- `C3_reference` — derived from historical `C3_docFV`
- `B4_energy2` — derived from historical `B4_energy2`
- `C4_energy2` — derived from historical `C4_energy2`
- `B5_outer3` — derived from historical `B5_outer3`
- `C5_outer3` — derived from historical `C5_outer3`

### Normalizations applied to all controlled B/C pairs

1. `metalTop h = 10 W/(m²·K)`
2. `startFrom startTime`
3. Historical numerical settings for the 3/4/5 experiments are otherwise preserved.

### C-family reference-density update

The controlled C cases use:

- `equationOfState rhoConst`
- `rho = 6820 kg/m³`
- `beta = 1.13e-04 1/K`
- `rhoRef = 6820 kg/m³`

### B-family buoyancy formulation

The controlled B cases preserve:

- `equationOfState icoTabulated`
- temperature-dependent density
- `beta = 0` in `solidificationMeltingSource`

### Reproducibility rule

The controlled 3/4/5 pairs are intended to be identical in all tracked inputs except the files defining the two buoyancy formulations:

- `constant/metal/fvModels`
- `constant/metal/materials/castIron`

A pairwise SHA audit must be performed after creation and before the cases are run.

**Status:** ✅ controlled series created; pairwise SHA verification follows.

---

## 2026-09-24 — AUD-040 — Controlled series passes pairwise SHA verification
**[GIT-VERIFIED] [VALIDATED INPUT SET]**

The newly created `cases_controlled_buoyancy/` series was audited pair-by-pair after construction.

### Pairwise SHA result

For all three controlled pairs:

- `B3_reference ↔ C3_reference`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

the only differing tracked case files are:

1. `constant/metal/fvModels`
2. `constant/metal/materials/castIron`

No other case-input file differs within each B/C pair.

### Normalized common settings verified

Both B and C branches now use:

- `metalTop h = 10 W/(m²·K)`
- `startFrom startTime`

### Controlled C density settings verified

The C branch now uses:

- `equationOfState rhoConst`
- `rho = 6820 kg/m³`
- `beta = 1.13e-04 1/K`
- `rhoRef = 6820 kg/m³`

### Controlled B formulation verified

The B branch preserves:

- `equationOfState icoTabulated`
- temperature-dependent density
- `beta = 0` in `solidificationMeltingSource`

### Conclusion

The controlled 3/4/5 series is suitable for objective B-vs-C numerical comparison because each pair is identical in all tracked inputs except the intended buoyancy/density formulation files.

**Status:** ✅ input-set audit passed; simulations may now be run from a clean state.

---

## 2026-09-24 — AUD-041 — README and Audit Log synchronization rule established
**[PROCESS RULE] [IMPLEMENTED]**

The controlled-series documentation now follows a two-document maintenance rule:

1. `PROJECT_AUDIT_LOG.md` preserves the chronological technical history: what changed, why, evidence, impact and status.
2. `cases_controlled_buoyancy/README.md` describes the current accepted configuration and workflow of the controlled thesis cases.

Whenever a relevant model change is made — including physics, material properties, boundary conditions, numerical settings, mesh, timestep controls, probes, post-processing, naming or comparison methodology — both documents must be updated.

The controlled-series README was expanded to include:

- purpose of the clean B/C series,
- case matrix,
- common B/C settings,
- current B and C buoyancy formulations,
- `h = 10 W/(m²·K)`,
- `startFrom startTime`,
- C-family `rho = rhoRef = 6820 kg/m³`,
- pairwise SHA validation,
- recommended run order,
- quantities to compare,
- planned OpenFOAM line-profile work,
- this maintenance rule.

**Status:** ✅ documentation synchronization rule active.

---

## 2026-09-24 — AUD-042 — Controlled solver logs are now versioned
**[PROCESS RULE] [IMPLEMENTED]**

The repository log policy was refined for the controlled thesis simulations.

General OpenFOAM logs remain ignored by default, but the following path is now explicitly tracked:

`cases_controlled_buoyancy/**/log.foamMultiRun`

### Rationale

The primary `foamMultiRun` log is part of the numerical evidence for each controlled case because it contains diagnostics needed for reproducibility and convergence review, including Courant numbers, residual behavior, continuity information, solver progress and timing.

Calculated time directories, generated meshes, general logs and other large runtime outputs remain ignored unless deliberately selected for a specific analysis.

The controlled-series README was updated with the same policy.

**Status:** ✅ controlled `log.foamMultiRun` files are part of the versioned scientific record.

---

## 2026-09-24 — AUD-043 — Simulation logs are tracked by default
**[PROCESS RULE] [IMPLEMENTED]**

The repository log-retention policy was broadened.

Previous policy:

- general logs were ignored,
- only `cases_controlled_buoyancy/**/log.foamMultiRun` was explicitly exempted.

Current policy:

- simulation and runtime logs are **not ignored by default**,
- broad ignore rules such as `**/log.*`, `**/*.log` and `**/nohup.out` were removed,
- logs are treated as part of the numerical/scientific evidence,
- editor-specific temporary logs such as `.vscode/*.log` may remain ignored because they are unrelated to solver reproducibility.

Generated solution-time directories, meshes, post-processing folders, media and build artifacts remain ignored unless deliberately selected.

**Impact:** future OpenFOAM logs can be added to Git normally without `git add -f`.

**Status:** ✅ repository-wide simulation-log retention rule active.

---

## 2026-09-24 — AUD-044 — Controlled B3/C3 simulation logs committed
**[GIT-VERIFIED] [RUN ARTIFACTS PRESERVED]**

The controlled reference cases `B3_reference` and `C3_reference` were run locally and their primary OpenFOAM solver logs were committed to Git.

Verified tracked files:

- `cases_controlled_buoyancy/B3_reference/log.foamMultiRun`
- `cases_controlled_buoyancy/C3_reference/log.foamMultiRun`

Git commit containing the logs:

`d6c307c8ac62755bf103fc15f4505874904c9bb9`

Approximate tracked log sizes:

- B3: 19.61 MB
- C3: 19.61 MB

No quantitative convergence or thermal interpretation is recorded in this entry yet. Courant number, residuals, continuity, execution time, temperature and phase-fraction metrics must be extracted from the preserved logs/post-processing data before comparison.

The controlled-series README was updated to mark B3/C3 as completed with quantitative review pending.

**Status:** ✅ B3/C3 run artifacts preserved; quantitative analysis pending.

---

## 2026-09-24 — AUD-045 — Controlled B3/C3 solver-log analysis
**[RUN-VERIFIED] [GIT-VERIFIED]**

The committed `log.foamMultiRun` files for `B3_reference` and `C3_reference` were parsed over the complete controlled 0–10 s simulations.

Both cases:

- executed 10,000 time steps at `deltaT = 0.001 s`,
- reached `Time = 10`,
- terminated with `End`,
- contained no `FOAM FATAL` entries,
- contained no `WARNING` entries.

### Courant number

B3:

- peak metal `Co_max = 0.175912` at approximately `t = 0.283 s`,
- mean Co at that instant = `0.00742715`,
- last reported `Co_max = 0.0606638` near 10 s.

C3:

- peak metal `Co_max = 0.0700709` at approximately `t = 2.510 s`,
- mean Co at that instant = `0.0205809`,
- last reported `Co_max = 0.0241928` near 10 s.

Both peaks remain below the case's documented `maxCo = 0.25`; because `adjustTimeStep no`, this value is a comparison threshold rather than an active timestep controller.

### Continuity

B3:

- largest absolute cumulative continuity value observed: approximately `1.70032e-4`,
- final cumulative continuity: `1.66260e-4`.

C3:

- largest absolute cumulative continuity value observed: approximately `1.78360e-4`,
- final cumulative continuity: `1.78349e-4`.

At the final reported correction, the global continuity terms were approximately:

- B3: `-1.14209e-11`,
- C3: `1.25471e-13`.

### Final solver residuals at 10 s

B3:

- metal enthalpy `h`: `8.73216e-11`,
- mold energy `e`: `3.73694e-10`,
- final `p_rgh`: `3.88108e-8`.

C3:

- metal enthalpy `h`: `2.46231e-11`,
- mold energy `e`: `3.76994e-10`,
- final `p_rgh`: `2.68792e-8`.

After the initial transient (t >= 0.1 s), the maximum final residuals observed for the thermal equations were below approximately:

- B3: `4.27e-7` for metal `h`, `6.03e-8` for mold `e`,
- C3: `3.76e-7` for metal `h`, `6.01e-8` for mold `e`.

### Computational cost

B3:

- ExecutionTime = `249.556 s`,
- ClockTime = `258 s`.

C3:

- ExecutionTime = `224.372 s`,
- ClockTime = `225 s`.

In these specific runs, B3 used approximately 11.2% more execution time and 14.7% more wall-clock time than C3. This timing difference is descriptive for these runs and should not yet be treated as a general model-cost conclusion without repetitions or comparable machine-load conditions.

### Interpretation boundary

The solver logs support that both controlled reference cases completed numerically without solver failure. They do **not** by themselves establish the thermal/phase difference between the two buoyancy formulations.

The next required evidence is the controlled probe output for:

- central `T(t)`,
- central `phaseChangeSource:alpha1(t)`.

Those files are generated under `postProcessing/`, which remains ignored by the repository's default generated-output rule and has not yet been committed for these runs.

**Status:** ✅ B3/C3 solver-log audit complete; 🟡 thermal/phase comparison pending probe data.

---

## 2026-09-24 — AUD-045 — Controlled B3/C3 reference runs quantitatively reviewed
**[RUN-VERIFIED] [GIT-VERIFIED]**

The versioned `log.foamMultiRun` files for the controlled reference pair were parsed and reviewed.

### Completion

Both cases reached:

`Time = 10s`

and terminated with:

`End`

No solver failure was observed in either log.

### B3_reference

- CPU time: **249.556 s**
- Clock time: **258 s**
- Maximum observed Courant number: **0.175912**
- Final Courant number: mean **0.0154644**, max **0.0606638**
- Final cumulative continuity error: **1.66260e-4**

Representative final solves:

- metal energy `h`: initial residual `4.54417e-05` → final `9.91429e-09`
- final second metal energy solve: `8.43592e-08` → `8.73216e-11`
- final pressure correction: `p_rgh` final residual **3.88108e-08**

### C3_reference

- CPU time: **224.372 s**
- Clock time: **225 s**
- Maximum observed Courant number: **0.0700709**
- Final Courant number: mean **0.00934688**, max **0.0241928**
- Final cumulative continuity error: **1.78349e-4**

Representative final solves:

- metal energy `h`: initial residual `5.6893e-05` → final `9.49871e-09`
- final second metal energy solve: `3.18791e-08` → `2.46231e-11`
- final pressure correction: `p_rgh` final residual **2.68792e-08**

### Controlled comparison

Relative to C3, B3 used approximately **11.2% more CPU time** and reached a maximum Courant number approximately **2.51×** larger.

Both cases remain comfortably below Courant number 1 and completed without numerical divergence.

The final cumulative continuity errors are of the same order (~`1e-4`), with C3 slightly higher.

### Interpretation limit

The higher Courant number in B3 is consistent with stronger velocity magnitudes somewhere in the domain, but the log alone does not establish the spatial flow mechanism or its thermal significance. Velocity fields/profiles, central temperature and phase-fraction histories must be examined before making a physical buoyancy interpretation.

**Status:** ✅ B3/C3 solver-level comparison complete; thermal/phase/velocity comparison pending.



---

## 2026-09-24 — AUD-046 — Controlled B3/C3 central thermal/phase probe analysis
**[RUN-VERIFIED] [GIT-VERIFIED]**

The central probe outputs committed for `B3_reference` and `C3_reference` were compared directly:

- `postProcessing/metal/temperatureProbe/0/T`
- `postProcessing/metal/temperatureProbe/0/phaseChangeSource:alpha1`

Each file contains 10,001 samples from 0 to 10 s at `deltaT = 0.001 s` for the central location `(0.02 0.02 0.005) m`.

### Main thermal/phase metrics

B3:
- first downward liquidus crossing (1473 K): **6.666 s**,
- first departure of `alpha1` from 1: **6.668 s**,
- `alpha1 = 0.99`: approximately **9.619 s**,
- final center temperature at 10 s: **1467.45 K**,
- final `alpha1`: **0.978184**.

C3:
- first downward liquidus crossing (1473 K): **3.386 s**,
- first departure of `alpha1` from 1: **3.388 s**,
- `alpha1 = 0.99`: approximately **3.654 s**,
- minimum center temperature: **1456.25 K at 4.822 s**,
- minimum `alpha1`: **0.932983 at 4.878 s**,
- final center temperature at 10 s: **1461.60 K**,
- final `alpha1`: **0.954394**.

Controlled-pair differences:
- C3 reaches liquidus approximately **3.280 s earlier** than B3.
- Maximum absolute central-temperature difference: approximately **33.42 K at 4.644 s**.
- Maximum absolute central liquid-fraction difference: approximately **0.067017 at 4.878 s**.
- At 10 s B3 is **5.85 K hotter** and its central liquid fraction is higher by approximately **0.02379**.

### Non-monotonic behavior

C3 shows a clear local rebound after its minimum:
- `T`: 1456.25 K at 4.822 s → 1461.60 K at 10 s (**+5.35 K**),
- `alpha1`: 0.932983 at 4.878 s → 0.954394 at 10 s (**+0.021411**).

The simultaneous increase in temperature and liquid fraction is direct evidence of **local remelting in the numerical model**.

B3 shows a smaller transient reversal:
- first downward liquidus crossing: 6.666 s,
- local `alpha1` minimum in the first phase-change episode: **0.997042 at 7.045 s**,
- `alpha1` returns to **1.0 at 7.460 s**,
- center temperature crosses upward through 1473 K at approximately **7.447 s**,
- a second downward liquidus crossing occurs at approximately **9.069 s**.

### Interpretation boundary

The probe comparison demonstrates that the two controlled buoyancy/density formulations produce materially different central thermal and phase histories even though their solver settings and boundary conditions are controlled.

However, the observed rebounds must **not** be called physical recalescence from these data alone. The present equilibrium enthalpy-porosity formulation can show non-monotonic local temperature through convective transport/mixing and can locally remelt material. Velocity-field/profile analysis and comparison with experimental thermal curves are required to identify the mechanism and judge physical validity.

**Status:** ✅ B3/C3 solver + central thermal/phase comparison complete; 🟡 velocity/profile and experimental validation pending.


---

## 2026-09-24 — AUD-047 — B4/C4 energy-corrector convergence test
**[RUN-VERIFIED] [GIT-VERIFIED]**

The controlled `B4_energy2` and `C4_energy2` simulations and central probe data were committed in Git commit `2e49c91a` and compared directly against the B3/C3 reference pair.

The only intended convergence change from the corresponding B3/C3 cases is the increase of root `nEnergyCorrectors` from 1 to 2.

### Solver completion

Both B4 and C4:
- reached 10 s,
- terminated with `End`,
- contained no `FOAM FATAL` entries,
- contained no warnings.

B4:
- peak metal `Co_max = 0.176643` near 0.290 s,
- final metal `Co_max = 0.0602696`,
- final cumulative continuity = **1.67018e-4**,
- ExecutionTime = **240.667 s**,
- ClockTime = **248 s**.

C4:
- peak metal `Co_max = 0.0700709` near 2.510 s,
- final metal `Co_max = 0.0241928`,
- final cumulative continuity = **1.78349e-4**,
- ExecutionTime = **225.476 s**,
- ClockTime = **226 s**.

The energy corrector increase doubled the number of metal-`h` and mold-`e` solver calls from 20,000 to 40,000 in each 10 s run.

Single-run timing did not scale monotonically: B4 was approximately 3.6% faster than B3, while C4 was approximately 0.5% slower than C3. These differences are treated as machine/run variability rather than a model-cost conclusion.

### Central thermal/phase convergence

B3 vs B4:
- maximum absolute center-temperature difference: **0.19 K**,
- maximum absolute center liquid-fraction difference: **5.22e-4**,
- first liquidus crossing: 6.666 s vs **6.678 s**,
- `alpha_l = 0.99`: 9.619 s vs **9.636 s**.

C3 vs C4:
- maximum absolute center-temperature difference: **0.01 K**,
- maximum absolute center liquid-fraction difference: **1.0e-6**,
- first liquidus crossing: **3.386 s in both**,
- `alpha_l = 0.99`: **3.654 s in both**,
- center minimum temperature: **1456.25 K at 4.822 s in both**,
- center minimum `alpha_l`: **0.932983 at 4.878 s in both**.

B4 vs C4 still shows a maximum absolute center-temperature difference of **33.42 K** and a maximum absolute center liquid-fraction difference of **0.067017**.

### Interpretation

Increasing `nEnergyCorrectors` from 1 to 2 does **not** materially change the controlled central thermal/phase solution over 0–10 s. The large B-vs-C difference and the C-series temperature rebound/local-remelting behavior persist essentially unchanged.

Thus the B/C difference observed in B3/C3 is robust to this tested energy-corrector increase and is not explained by insufficient `nEnergyCorrectors = 1`.

This is a numerical-convergence statement only; it does not establish which buoyancy formulation is physically correct.

**Status:** ✅ B4/C4 energy-corrector convergence test complete; 🟡 B5/C5 outer-corrector test and velocity/experimental validation pending.


---

## 2026-09-24 — AUD-047 — B4/C4 energy-corrector convergence check
**[RUN-VERIFIED] [GIT-VERIFIED]**

The controlled `B4_energy2` and `C4_energy2` cases were completed to 10 s and compared against the B3/C3 reference pair.

### Verification that the energy-corrector change was active

Log counts show:

- B3/C3: 20,000 metal `h` solves and 20,000 mold `e` solves,
- B4/C4: 40,000 metal `h` solves and 40,000 mold `e` solves,
- all four cases: 40,000 `p_rgh` solves.

Thus `nEnergyCorrectors = 2` in B4/C4 was active and doubled the energy-equation solve count.

### Solver metrics

B4:
- peak metal Courant number: **0.176643**,
- final metal Co max: **0.0602696**,
- final cumulative continuity: **1.67018e-4**,
- ExecutionTime: **240.667 s**,
- ClockTime: **248 s**,
- no fatal errors or warnings.

C4:
- peak metal Courant number: **0.0700709**,
- final metal Co max: **0.0241928**,
- final cumulative continuity: **1.78349e-4**,
- ExecutionTime: **225.476 s**,
- ClockTime: **226 s**,
- no fatal errors or warnings.

### Central-probe convergence relative to B3/C3

B3 → B4:
- maximum absolute temperature change: **0.19 K**,
- maximum absolute liquid-fraction change: **5.22e-4**,
- first downward liquidus crossing: 6.666 s → **6.678 s**.

C3 → C4:
- maximum absolute temperature change: **0.01 K**,
- maximum absolute liquid-fraction change: **1e-6**,
- first downward liquidus crossing remains **3.386 s**.

### Controlled B4/C4 difference

B4 vs C4:
- maximum absolute central-temperature difference: **33.42 K at 4.637 s**,
- maximum absolute central liquid-fraction difference: **0.067017 at 4.878 s**,
- first downward liquidus crossing: **6.678 s vs 3.386 s**.

The C4 center history reproduces the same non-monotonic temperature/liquid-fraction behavior documented for C3. B4 retains the smaller transient reversal observed in B3.

### Interpretation

Doubling the energy-correction count does not materially change the central thermal/phase solution in either controlled formulation. The B-vs-C difference therefore survives this convergence test and is not explained by insufficient root energy correction in the B3/C3 reference configuration.

Single-run wall/CPU timings are descriptive only; the fact that B4 was slightly faster than B3 despite more energy solves indicates that these timings are not suitable for a strict performance conclusion without repeated runs under controlled machine load.

**Status:** ✅ B4/C4 energy-corrector convergence check complete; B3/C3 result is thermally robust to `nEnergyCorrectors = 2`. Next controlled test: B5/C5 outer-corrector comparison.


---

## 2026-09-24 — AUD-047 — Controlled B4/C4 energy-corrector comparison
**[RUN-VERIFIED] [GIT-VERIFIED]**

The controlled `B4_energy2` and `C4_energy2` cases were completed to 10 s and their solver logs and central temperature/phase probes were committed to Git.

These cases test the effect of setting root `nEnergyCorrectors = 2` relative to the B3/C3 reference configuration.

### Solver behavior

B4:
- peak metal Courant number: **0.176643**,
- final Co: mean **0.0154719**, max **0.0602696**,
- final cumulative continuity: **1.67018e-4**,
- ExecutionTime: **240.667 s**,
- ClockTime: **248 s**,
- no `FOAM FATAL` and no `WARNING` entries,
- normal `End`.

C4:
- peak metal Courant number: **0.0700709**,
- final Co: mean **0.0093469**, max **0.0241928**,
- final cumulative continuity: **1.78349e-4**,
- ExecutionTime: **225.476 s**,
- ClockTime: **226 s**,
- no `FOAM FATAL` and no `WARNING` entries,
- normal `End`.

### Central thermal/phase effect of the extra energy corrector

B3 → B4:
- maximum absolute central-temperature difference: approximately **0.19 K**,
- maximum absolute central liquid-fraction difference: approximately **5.22e-4**,
- first downward 1473 K crossing shifts only from **6.666 s** to **6.678 s**,
- final center temperature changes from **1467.45 K** to **1467.53 K**,
- final `alpha1` changes from **0.978184** to **0.978506**.

C3 → C4:
- maximum absolute central-temperature difference: approximately **0.01 K**,
- maximum absolute central liquid-fraction difference: approximately **1e-6**,
- first downward 1473 K crossing remains **3.386 s**,
- final center state remains **1461.60 K**, `alpha1 = 0.954394` at recorded precision.

### Controlled B4/C4 difference

- maximum absolute central-temperature separation: approximately **33.42 K**,
- maximum absolute central liquid-fraction separation: approximately **0.067017**,
- C4 retains the same non-monotonic thermal/phase behavior as C3, with center `T_min = 1456.25 K` at 4.822 s and `alpha1_min = 0.932983` at 4.878 s, followed by warming/remelting.

### Conclusion

For this 0–10 s controlled series, increasing `nEnergyCorrectors` from 1 to 2 has negligible effect on the central temperature and liquid-fraction histories. The large B-versus-C thermal separation and C-series rebound/remelting are therefore robust to this specific convergence change.

Timing differences are descriptive single-run observations only and should not be generalized as a computational-cost conclusion without repeated benchmarking.

**Status:** ✅ B4/C4 comparison complete; proceed to B5/C5 outer-corrector test.


---

## 2026-09-24 — AUD-048 — B5/C5 outer-corrector convergence and 3/4/5 series conclusion
**[RUN-VERIFIED] [GIT-VERIFIED]**

The controlled `B5_outer3` and `C5_outer3` simulations, solver logs and central probe data were committed in Git commit `0619b7af` and compared against the B3/C3 reference pair and the B4/C4 energy-corrector pair.

Both B5 and C5:
- completed 10,000 steps to 10 s,
- terminated with `End`,
- contained no `FOAM FATAL` entries,
- contained no warnings,
- executed 30,000 metal-`h` solves and 30,000 mold-`e` solves, confirming that the third outer correction was active.

### Solver metrics

B5:
- peak metal Courant number: **0.175874 at 0.284 s**,
- final metal Co: mean **0.0154835**, max **0.0602937**,
- largest absolute cumulative continuity value: approximately **1.70120e-4**,
- final cumulative continuity: **1.65205e-4**,
- final metal-`h` residual: **4.72045e-12**,
- final mold-`e` residual: **5.80792e-10**,
- final `p_rgh` residual: **9.77911e-8**,
- ExecutionTime: **291.137 s**,
- ClockTime: **298 s**.

C5:
- peak metal Courant number: **0.0700712 at 2.510 s**,
- final metal Co: mean **0.0093466**, max **0.0241931**,
- largest absolute cumulative continuity value: approximately **1.78180e-4**,
- final cumulative continuity: **1.78172e-4**,
- final metal-`h` residual: **1.19093e-10**,
- final mold-`e` residual: **5.78841e-10**,
- final `p_rgh` residual: **5.2433e-8**,
- ExecutionTime: **272.125 s**,
- ClockTime: **273 s**.

After 0.1 s, maximum final residuals observed for the thermal equations remained on the same order as the reference runs:
- B5: metal `h` approximately **4.27e-7**, mold `e` approximately **6.02e-8**,
- C5: metal `h` approximately **3.76e-7**, mold `e` approximately **6.01e-8**.

### Central thermal/phase sensitivity

B3 → B5:
- maximum `|Delta T|`: **0.22 K** at 7.443 s,
- maximum `|Delta alpha_l|`: **6.48e-4** at 7.399 s,
- first liquidus crossing: 6.666 s → **6.683 s**,
- `alpha_l = 0.99`: 9.619 s → **9.633 s**,
- final center temperature: 1467.45 K → **1467.52 K**,
- final `alpha_l`: 0.978184 → **0.978433**.

C3 → C5:
- maximum `|Delta T|`: **0.01 K**,
- maximum `|Delta alpha_l|`: **4e-6**,
- first liquidus crossing remains **3.386 s**,
- `alpha_l = 0.99` remains approximately **3.654 s**,
- minimum center temperature remains **1456.25 K at 4.822 s**,
- minimum `alpha_l` is **0.932984 at 4.876 s**,
- final center temperature remains **1461.60 K**,
- final `alpha_l` is **0.954397**.

B5 vs C5:
- maximum absolute center-temperature difference: **33.42 K**,
- maximum absolute center liquid-fraction difference: approximately **0.067016**.

Thus the B-vs-C thermal/phase separation and C-series warming/remelting behavior survive the outer-corrector sensitivity test.

### 3/4/5 convergence conclusion

The complete controlled numerical-sensitivity sequence shows:
1. B4/C4 (`nEnergyCorrectors = 2`) produces negligible thermal/phase changes relative to B3/C3.
2. B5/C5 (`nOuterCorrectors = 3`) also produces negligible thermal/phase changes relative to B3/C3.
3. B5/C5 requires substantially more solve calls and, in these runs, approximately **16.7%** more B-series CPU time and **21.3%** more C-series CPU time than B3/C3.
4. The large controlled B-vs-C difference is reproduced by all three numerical configurations.

For the present 0–10 s calculations, the B3/C3 reference solver configuration is accepted as the efficient numerical baseline. The additional energy or outer corrections tested here do not materially improve the monitored center solution.

This conclusion addresses numerical sensitivity only. It does not establish whether the B or C buoyancy formulation is physically superior. That requires velocity-field/profile analysis and validation against experimental cooling curves.

**Status:** ✅ B3/B4/B5 and C3/C4/C5 controlled numerical-sensitivity series complete; 🟡 velocity/profile analysis and experimental physical validation remain.


---

## 2026-09-24 — AUD-049 — Horizontal OpenFOAM line profiles configured
**[CONFIG-VERIFIED] [GIT-VERIFIED]**

A common line-sampling function object was added to `system/functions` in all six controlled cases:

- `B3_reference`
- `C3_reference`
- `B4_energy2`
- `C4_energy2`
- `B5_outer3`
- `C5_outer3`

The implementation uses the OpenFOAM v14 sampling `sets` function object with `lineUniform` sets, which is the underlying mechanism used by the packaged `graphUniform` graph function.

### Profile geometry

Both lines lie in the metal mid-plane at `z = 0.005 m` and run horizontally in x from `0.00025` to `0.03975 m`.

1. `line_y20mm`
   - `y = 0.020 m`,
   - geometric mid-height of the 40 mm metal domain.

2. `line_y30mm`
   - `y = 0.030 m`,
   - 10 mm below the top metal surface at `y = 0.040 m`.

Each line uses 80 uniformly distributed sample points and `axis x`. With the controlled 80-cell / 40-mm x mesh, the x spacing between the first and last cell-centre positions is 0.5 mm.

### Sampled fields

The function object samples:

- `U` — the vector output contains `Ux`, `Uy` and `Uz`,
- `T`,
- `phaseChangeSource:alpha1` — liquid fraction.

Velocity magnitude is intentionally derived from the sampled components during analysis:

`|U| = sqrt(Ux^2 + Uy^2 + Uz^2)`.

This avoids introducing an additional derived field dependency into the line sampler while preserving all velocity-direction information.

### Output control and impact

- region: `metal`,
- interpolation: `cellPoint`,
- format: `raw`,
- `writeControl writeTime`.

This is a post-processing-only addition. No mesh, material property, boundary condition, phase-change model, timestep, or solver-corrector setting was changed.

The configuration has been checked against the OpenFOAM Foundation v14 `graphUniform` / `lineUniform` implementation. Runtime generation of the profile files from the already completed controlled solutions is still pending.

**Status:** ✅ common profile configuration committed; 🟡 runtime profile extraction and B-vs-C velocity interpretation pending.


---

## 2026-09-25 — AUD-050 — Controlled horizontal profile execution and spatial B3/C3 analysis
**[RUN-VERIFIED] [GIT-VERIFIED]**

The OpenFOAM horizontal line profiles configured in AUD-049 were executed for all saved times from 0 to 10 s in all six controlled cases.

Each case generated:
- 101 saved times,
- 2 horizontal lines per time,
- 202 profile files per case.

Total controlled profile files: 1,212.

The raw profile columns are:
- x,
- Ux,
- Uy,
- Uz,
- T,
- phaseChangeSource:alpha1.

Observed Uz is zero in the inspected profiles, consistent with the quasi-2D setup.

### B3/C3 center-flow reversal

At x ≈ 19.75 mm, the B and C formulations show opposite vertical-flow directions during the early phase-change interval.

At 3.4 s:
- 20 mm: B3 Uy = -0.01437 m/s; C3 Uy = +0.00962 m/s.
- 30 mm: B3 Uy = -0.02419 m/s; C3 Uy = +0.00357 m/s.

At 4.8 s:
- 20 mm: B3 Uy = -0.01104 m/s; C3 Uy = +0.01821 m/s.
- 30 mm: B3 Uy = -0.01492 m/s; C3 Uy = +0.00299 m/s.

Thus B3 has downward center flow at both sampled heights while C3 has upward center flow at both heights over this interval.

### Vertical thermal stratification

At 4.8 s and x ≈ 19.75 mm:
- B3: T(20 mm) = 1489.50 K; T(30 mm) = 1485.99 K.
- C3: T(20 mm) = 1456.46 K; T(30 mm) = 1483.24 K.

C3 therefore has approximately 26.78 K vertical separation between the two sampled heights at the center, compared with only about 3.51 K in B3 (with the opposite sign).

At the same 4.8 s time, the maximum B3/C3 temperature difference on the 20-mm profile is approximately 33.05 K near x ≈ 20.25 mm.

### Velocity-profile differences

Representative maximum absolute B3/C3 Uy differences:
- 3.4 s, 20 mm: ~0.02399 m/s,
- 3.4 s, 30 mm: ~0.02776 m/s,
- 4.8 s, 20 mm: ~0.02925 m/s,
- 6.7 s, 30 mm: ~0.02949 m/s,
- 10 s, 30 mm: ~0.02916 m/s.

The B formulation can have higher local and upper-layer speeds even though the C formulation cools/solidifies the center earlier. Therefore global Courant number or peak velocity alone is not an adequate proxy for thermal transport at the center.

### Spatial convergence check

At representative 4.8 s and 10 s profiles:
- C3/C4/C5 are effectively coincident at the sampled precision, with temperature differences ≤ ~0.01 K and velocity differences generally around 1e-6 m/s or smaller.
- B3/B4/B5 show small but measurable spatial sensitivity: checked temperature differences are up to ~0.6–0.7 K and checked Uy differences up to ~0.0015 m/s.
- These B-family spatial differences remain much smaller than the B-vs-C formulation differences and do not change the qualitative circulation structure.

### Interpretation

The controlled B-vs-C thermal difference is associated with a materially different flow topology and vertical heat redistribution, not simply a scalar increase or decrease in velocity magnitude.

The C-series develops persistent upward center flow and strong early vertical thermal stratification, consistent with a different convective transport pathway that can explain why the center reaches liquidus and begins phase change much earlier than in B.

This is a mechanistic numerical interpretation, not physical validation. Experimental thermal curves and further field-level comparison are still required before selecting a physically preferred buoyancy formulation.

**Status:** ✅ profile generation and initial spatial B3/C3 interpretation complete; 🟡 graphical thesis figures and experimental validation remain.


---

## 2026-09-25 — AUD-051 — Source-level buoyancy implementation audit
**[SOURCE-VERIFIED] [INTERPRETATION-CORRECTION]**

A source-level audit was performed after observing large B-vs-C differences in temperature and velocity.

### Verified B implementation

`B3_reference/constant/metal/materials/castIron` uses:

- `equationOfState icoTabulated`
- temperature-dependent density table
- density from 6900 kg/m3 at 1423.15 K to 6820 kg/m3 at 1473.15 K.

`B3_reference/constant/metal/fvModels` uses:

- `beta 0`
- `rhoRef 6930`.

OpenFOAM Foundation v14's buoyant pressure correction for `p_rgh` explicitly includes:

`ghGradRhof = -ghf*fvc::snGrad(rho)*mesh.magSf()`

and adds this density-gradient contribution to the pressure/velocity correction.

Therefore B is **not a zero-buoyancy case**. Its buoyancy is generated through the temperature-dependent density field and the native `p_rgh` buoyancy formulation. Setting `beta=0` only disables the additional explicit buoyancy source inside `solidificationMelting`.

### Verified C implementation

`C3_reference/constant/metal/materials/castIron` uses:

- `equationOfState rhoConst`
- `rho = 6820 kg/m3`.

`C3_reference/constant/metal/fvModels` uses:

- `beta = 1.13e-4 1/K`
- `rhoRef = 6820 kg/m3`.

For constant density, the native `-ghf*snGrad(rho)` buoyancy term is zero apart from numerical roundoff.

OpenFOAM Foundation v14's `solidificationMelting` momentum source adds:

`Sb = rhoRef*g*beta*deltaT`

Hence C is **not a double-buoyancy case**. Its thermal buoyancy is supplied by the explicit `solidificationMelting` source while the native density-gradient buoyancy is inactive because density is constant.

### Why B and C differ strongly

The two formulations are not equivalent.

The B density table gives an effective thermal-expansion strength that changes with temperature. Across 1423.15–1473.15 K:

- rho decreases by 80 kg/m3 over 50 K,
- effective beta is approximately 2.3e-4 1/K.

This is roughly twice the constant `beta = 1.13e-4 1/K` used in C.

Across 1473.15–1573.15 K:

- rho decreases by 80 kg/m3 over 100 K,
- effective beta is approximately 1.2e-4 1/K,

which is much closer to C.

Additionally, the C source uses the phase model's internal `deltaT`, which is defined relative to the current phase-equilibrium relation and therefore depends on the liquid-fraction state. It is not simply a globally linear Boussinesq `T-Tref` term.

### Impact

Previous B-vs-C flow and thermal differences remain numerically real, but they must be interpreted as consequences of **two different buoyancy models**, not as evidence of "no buoyancy" in B or "double counting" in C.

A physically preferred thesis formulation cannot be selected solely from numerical convergence. The next model-selection step must compare the intended physical approximation (variable-density vs Boussinesq/phase-source buoyancy) against experimental cooling curves and the expected thermophysical behavior of the cast iron.

**Status:** ✅ implementation mechanism verified in OpenFOAM v14 source; 🟡 physical model selection still pending experimental validation.


---

## 2026-09-25 — AUD-052 — Post-advisor configuration divergence audit
**[CONFIGURATION-AUDIT] [TRACEABILITY] [CONTROLLED-SERIES]**

The six controlled cases were re-audited after local changes made during/after the advisor session were synchronized to `main`.

### Current configuration matrix

| Case | `nOuterCorrectors` | `nEnergyCorrectors` | `adjustTimeStep` | Metal EOS | `solidificationMelting beta` |
|---|---:|---:|---|---|---:|
| B3_reference | 2 | default (1) | **yes** | `icoTabulated` | 0 |
| C3_reference | 2 | default (1) | no | `rhoConst` | 1.13e-4 |
| B4_energy2 | 2 | 2 | no | `icoTabulated` | 0 |
| C4_energy2 | 2 | 2 | no | `rhoConst` | 1.13e-4 |
| B5_outer3 | 3 | default (1) | no | `icoTabulated` | 0 |
| C5_outer3 | 3 | default (1) | **yes** | `rhoConst` | **0** |

### B3 is no longer the original fixed-time-step reference on the current branch

`B3_reference/system/controlDict` currently has `adjustTimeStep yes`.

The newly generated `B3_reference/logs/Time_0` contains 2811 reported time values. The first reported time is 0.0012 s and the final reported time is 9.999798 s. `logs/deltaT_0` confirms adaptive stepping: the first reported time-step value is 0.0012 s and it evolves during the run, reaching about 0.00532 s near 10 s.

Therefore the current B3 run output is an adaptive-time-step rerun and is not the same numerical experiment as the original B3 fixed-`deltaT=0.001` dataset used in the earlier B3/C3 convergence comparison. The original fixed-step data remain recoverable from Git history.

### C5 current configuration does not match the C5 run previously analysed

The C5 foamLog data were generated and committed before the latest configuration edits. At that time C5 used:

- `rhoConst = 6820 kg/m3`
- `beta = 1.13e-4 1/K`
- `adjustTimeStep no`
- `nOuterCorrectors = 3`

The current `C5_outer3` configuration now contains:

- `rhoConst = 6820 kg/m3`
- `beta = 0`
- `adjustTimeStep yes`
- `nOuterCorrectors = 3`

Thus the current C5 dictionaries must **not** be assumed to describe the historical C5 results already analysed. With `rhoConst` and `beta=0`, thermal buoyancy is disabled in the presently configured C5 case; this is a different physical problem from the original C-family Boussinesq case.

### B3 mold fvSolution change

Only B3 currently has an explicit final solid-energy solver block:

```
"(h|e)Final"
{
    solver          PCG;
    preconditioner  DIC;
    tolerance       1e-06;
    relTol          0;
}
```

A root-level `fvSolution.txt` contains the same block. The other five cases use `$h; relTol 0;`.

OpenFOAM Foundation v14's own multi-region CHT templates use the `$h; relTol 0;` form for `"(h|e)Final"`. The explicit B3 block reproduces the same PCG/DIC/tolerance values used by the base `"(h|e)"` solver and sets the final relative tolerance to zero. It should therefore be treated as an explicit restatement of the final solver settings rather than as a meaningful controlled numerical variable unless a future test demonstrates otherwise.

### Controlled-series implication

Do not create the next case by blindly copying the current C5 directory.

The next controlled experiment must preserve the intended physical formulation of each family:

- B-family: `icoTabulated`, `beta=0`.
- C-family: `rhoConst=6820`, `beta=1.13e-4`.

Only one numerical variable should then be changed at a time. If the advisor's repeated `adjustTimeStep yes` change is to be tested, it should be isolated from `nOuterCorrectors`. A separate no-buoyancy case (`rhoConst` + `beta=0`) should be given its own explicit name if intentionally studied rather than being silently folded into C5.

**Status:** ✅ six-case configuration divergence identified; 🟡 next controlled-case definition pending.


---

## 2026-09-25 — AUD-053 — Controlled V6/V7 definition and foamLog workflow
**[CONFIGURATION-RESTORE] [CONTROLLED-SERIES] [POST-PROCESSING]**

### Historical-case restoration

The temporary advisor-session edits were removed from the historical cases:

- B3: `adjustTimeStep` restored to `no`; mold `(h|e)Final` restored to the inherited `$h; relTol 0;` form.
- C5: `adjustTimeStep` restored to `no`; `solidificationMelting beta` restored to `1.13e-04 1/K`.

B3 generated data that belonged to the later adaptive-time-step rerun were replaced by the pre-advisor fixed-step B3 outputs from repository history. The adaptive B3 `logs/` set was removed because it did not correspond to the restored B3 reference configuration.

The original C5 `foamLog` parsed `logs/` data were restored from repository history after having been accidentally removed during synchronization.

### V6 controlled test

Created `B6_fvSolution` and `C6_fvSolution` from the clean V5 basis.

Controlled change: the mold-region final energy solver is written explicitly as:

```
"(h|e)Final"
{
    solver          PCG;
    preconditioner  DIC;
    tolerance       1e-06;
    relTol          0;
}
```

Everything else remains at the V5 controlled configuration.

### V7 controlled test

Created `B7_outer4` and `C7_outer4` from the clean V5 basis.

Controlled change:

`nOuterCorrectors 4;`

Everything else remains at the V5 controlled configuration.

### Standardized solver-log post-processing

All controlled cases V3-V7 now execute:

`foamLog log.foamMultiRun`

automatically from `Allrun` after the solver finishes. Before parsing, any previous `logs/` directory and `log.foamLog` are removed so diagnostics cannot be mixed across runs.

The generated case-level `logs/` directory is now part of the standard post-processing record and is intended to be tracked in Git. `Allclean` explicitly removes this directory.

**Status:** ✅ V3/V5 restored; ✅ V6 fvSolution cases defined; ✅ V7 outer-corrector=4 cases defined; ✅ foamLog standardized for V3-V7.


---

## 2026-09-25 — AUD-054 — Remove stale restored C5 foamLog outputs
**[CORRECTION] [POST-PROCESSING] [TRACEABILITY]**

The historical `C5_outer3/logs/` directory that had been restored from an earlier commit in AUD-053 was removed. Restoring those derived files was inconsistent with the standardized workflow, which requires `logs/` to be regenerated from the tracked case-level `log.foamMultiRun`.

The source solver log `C5_outer3/log.foamMultiRun` remains unchanged and tracked. New C5 `logs/` must be produced with:

`foamLog log.foamMultiRun`

This ensures the parsed diagnostics are derived explicitly from the current tracked solver log rather than copied from a historical `logs/` snapshot.

**Status:** ✅ stale C5 parsed logs removed; source solver log retained.


---

## 2026-09-25 — AUD-055 — Enable adaptive time stepping in V7
**[CONFIGURATION-CHANGE] [V7] [TIME-STEPPING]**

By user decision, both V7 cases now combine:

- `nOuterCorrectors = 4`
- `adjustTimeStep = yes`

The initial time-step remains:

- `deltaT = 0.001 s`

Adaptive control remains bounded by:

- `maxCo = 0.25`
- `maxDeltaT = 0.1 s`

This applies to:

- `B7_outer4`
- `C7_outer4`

The B/C physical formulations are unchanged.

Because V7 now changes both the number of outer correctors and the time-step strategy relative to V5, it is **not** a single-variable convergence test. Any V7-vs-V5 difference must be interpreted as the combined effect of `nOuterCorrectors=4` and adaptive time stepping.

**Status:** ✅ V7 adaptive time stepping enabled and documented.


---

## 2026-09-25 — AUD-056 — Finalize V6 adaptive timestep and V7 outer-corrector tests
**[CONFIGURATION-CHANGE] [CONTROLLED-SERIES] [SUPERSEDES-AUD-055]**

The V6/V7 experimental design was revised to preserve one numerical variable per comparison.

### V6 — adaptive time stepping

The previous `B6_fvSolution` and `C6_fvSolution` directories were removed before execution and replaced by:

- `B6_adaptiveDt`
- `C6_adaptiveDt`

Both are copied from the clean V5 configuration and change only:

`adjustTimeStep yes;`

They retain:

- `nOuterCorrectors = 3`
- initial `deltaT = 0.001 s`
- `maxCo = 0.25`
- `maxDeltaT = 0.1 s`

The B/C physical formulations are unchanged.

### V7 — outer-corrector sensitivity

The temporary AUD-055 setting that combined `nOuterCorrectors=4` with adaptive time stepping was reverted before execution.

Final V7 configuration:

- `B7_outer4`
- `C7_outer4`
- `nOuterCorrectors = 4`
- `adjustTimeStep = no`
- fixed `deltaT = 0.001 s`

Thus V7 changes only the number of outer correctors relative to V5.

### Interpretation

- V5 vs V6 isolates time-step strategy.
- V5 vs V7 isolates outer-corrector count.

AUD-055 remains in the history as a transient configuration decision but is superseded by this entry.

**Status:** ✅ V6 adaptive-timestep cases defined; ✅ V7 restored to fixed timestep with outerCorrectors=4; ✅ one-variable-at-a-time design restored.


## 2026-09-25 — Parallel documentation workflow: Audit Log + practical OpenFOAM manual

### Decision
From this date onward, project documentation is maintained in two parallel layers:

1. **PROJECT_AUDIT_LOG.md** — chronological technical record of changes, tests, discrepancies, evidence, results, impact, and status.
2. **OPENFOAM_COMMAND_MANUAL.md** — practical tutorial-style command reference with copy-ready terminal blocks, explanations of what each command does, and project-specific recipes.

### Rationale
The audit log answers **what happened and why**. The command manual answers **how to reproduce it quickly**. Reusable commands introduced during the project should be added to the manual when they are useful beyond a single isolated action.

### Case 6/7 execution-chain path issue

A sequential shell block was launched from:

```text
~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy
```

B6 completed its scripted sequence through `foamLog`, but the next subshell attempted:

```bash
cd ../C6_adaptiveDt
```

and failed with:

```text
-bash: cd: ../C6_adaptiveDt: No such file or directory
```

### Cause
Each parenthesized block such as:

```bash
(cd B6_adaptiveDt && ./Allclean && ./Allrun)
```

runs in a subshell. When that subshell ends, the parent shell remains in `cases_controlled_buoyancy`. Therefore the next case must be addressed as `C6_adaptiveDt`, not `../C6_adaptiveDt`.

### Correct sequential pattern

```bash
(cd B6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

If B6 has already completed:

```bash
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

### Impact
No evidence from the pasted terminal output indicates that B6 itself failed; its `Allrun` reached the `foamLog` stage. The chain stopped only when attempting to enter the incorrectly referenced C6 path.

### Status
- Practical command manual created at repository root.
- Correct subshell/path behavior documented.
- Future reusable OpenFOAM/Linux commands should be added to the command manual in parallel with technical events being recorded here.
