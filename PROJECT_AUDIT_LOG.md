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

