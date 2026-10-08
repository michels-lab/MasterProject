# QuickCup-Solidification — Project Audit Log

**Language:** [🇪🇸 Español](./PROJECT_AUDIT_LOG_ES.md) | 🇬🇧 English | [↩ Language selector](./PROJECT_AUDIT_LOG.md)

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


## 2026-09-25 — Bilingual command manual and historical command backfill

### Documentation change
The OpenFOAM command manual was split into a language selector plus two synchronized versions:

- `OPENFOAM_COMMAND_MANUAL.md` — language selector.
- `OPENFOAM_COMMAND_MANUAL_ES.md` — Spanish.
- `OPENFOAM_COMMAND_MANUAL_EN.md` — English.

Both language versions should preserve the same command set and structure.

### Historical recovery
Earlier project commands were backfilled rather than treating the manual as starting only on 2026-09-25. Recovered workflows include:

- `paraFoam -builtin &` from historical B2/C2 work;
- `foamPostProcess -region metal -solver fluid -latestTime` in the workflow developed after the doctor's suggestion to obtain velocity–temperature line profiles (“plotline”);
- previously considered line-sampling elements `lineUniform`, `graphUniform`, `graphCell`, and fields `U T phaseChangeSource:alpha1`;
- `find . -name "openfoam-solidification.agent.md"`;
- `git check-ignore -v cases_buoyancy/B2_test/10`;
- the project's standard Git pull/status/add/commit/push workflow;
- deliberate `git add -f` use for selected ignored post-processing outputs.

### Attribution rule
Only commands or workflows with explicit historical evidence should be labeled as coming from or motivated by the doctor. Other recovered commands are documented as project-history commands without unsupported attribution.

**Status:** ✅ bilingual selector active; ✅ Spanish and English manuals synchronized; ✅ first historical backfill completed.


---

## 2026-09-25 — Bilingual Project Audit Log

### Documentation change

The Project Audit Log now follows the same bilingual structure as the OpenFOAM command manual:

- `PROJECT_AUDIT_LOG.md` — language selector.
- `PROJECT_AUDIT_LOG_ES.md` — complete Spanish version.
- `PROJECT_AUDIT_LOG_EN.md` — complete English version.

Both versions preserve the same technical record: dates, AUD identifiers, evidence labels, commands, filenames, numerical values, decisions, interpretations, and status. Only the narrative language changes.

### Maintenance rule

Every new technical audit entry must be added to both the Spanish and English versions so neither language becomes more current than the other.

**Status:** ✅ bilingual audit-log structure active.


---

## 2026-09-25 — Advisor observation: `p_rgh` coupling sensitivity to `nOuterCorrectors`
**[ADVISOR-OBSERVATION] [USER-REPORTED] [OPEN]**

### Observation reported during parallel work

The advisor is running his own simulations in parallel with the user's cases. According to the user's report, the advisor observed that increasing `nOuterCorrectors` substantially reduced the initial `p_rgh` residuals.

The user remembers that the advisor may have tested relatively high `nOuterCorrectors` values, possibly around **7**, but the exact value is not confirmed and must not be treated as verified until the corresponding log, configuration, or direct confirmation is available.

### Related evidence from the user's cases

The controlled logs already preserved in the project show an initial `p_rgh` residual close to unity in the first timestep of several cases. For example, B5 shows:

- `p_rgh_0 = 0.973321` at `t = 0.001 s`
- `p_rgh_1 = 0.00750951`
- `p_rgh_2 = 0.00516345`
- `p_rgh_3 = 2.51636e-05`
- `p_rgh_4 = 8.23277e-05`
- `p_rgh_5 = 7.45313e-07`

Thus, although the first pressure correction begins with an order-one residual, the PIMPLE corrections reduce it by several orders of magnitude within the same timestep.

A similar ~0.973 first-timestep spike also appears in B3, B4, C3, and C4, so it should not automatically be interpreted as a failure unique to one physical formulation.

### Hypothesis to reproduce

Run a controlled sensitivity study using:

`nOuterCorrectors = 2, 3, 4, 5, 6, 7`

while keeping all other numerical and physical variables fixed.

Metrics should include:

- maximum initial `p_rgh` residual,
- final `p_rgh` residual after the last corrector,
- total within-timestep residual reduction,
- number of timesteps containing large spikes,
- persistence or disappearance of spikes after startup,
- continuity,
- Courant number,
- CPU/wall time,
- actual effect on temperature and liquid fraction.

### Objective

Identify the **diminishing-returns point**: the smallest number of outer correctors that provides sufficiently robust coupling without unnecessary computational cost.

### OpenFOAM PostPlotter implication

This observation motivates a coupling-diagnostics module that does more than plot `p_rgh_0`, `p_rgh_1`, etc. It should automatically reconstruct residual reduction within each timestep and across outer-corrector cycles.

**Status:** 🟡 advisor observation documented; advisor's maximum tested value unconfirmed; controlled reproduction in the user's cases pending.


---

## 2026-09-25 — Full Initial-residual audit: the relevant coupling behaviour is concentrated in `p_rgh`
**[RUN-VERIFIED] [GIT-VERIFIED] [COUPLING-DIAGNOSTIC]**

The available `foamLog` Initial-residual files were audited for controlled cases B3/B4/B5 and C3/C4/C5. Persistent behaviour was analysed separately from startup by excluding the first transient when appropriate (`t >= 0.1 s`).

### Residual families audited

Available Initial-residual families are:

- `p_rgh`
- `h`
- `e`
- `rho`

### `rho`

All `rho_*` files in B3/B4/B5/C3/C4/C5 have the same blob SHA and contain zero values. They do not provide a useful convergence signal in these cases.

### `h` — metal enthalpy

The first `h` solve starts around 1.67–1.69e-3 at 0.1 s and decreases smoothly with simulation time.

Later solves within the timestep reduce the residual to much smaller orders. No intermediate spike family comparable to `p_rgh` was found.

Examples:

- B3 `h_0`: maximum for t>=0.1 s = 1.67278e-3 at 0.1 s; median ≈ 1.029e-4.
- B5 `h_0`: 1.67354e-3 at 0.1 s; median ≈ 1.028e-4.
- C3/C5 `h_0`: 1.69063e-3 at 0.1 s; median ≈ 1.158e-4.

Additional correctors reduce later `h` residuals to approximately 1e-7–1e-9 depending on configuration.

### `e` — mold energy

`e_0` decreases smoothly from approximately 1.84e-3 at 0.1 s.

Later corrections are typically in the 1e-8–1e-10 range. No pressure-like intermediate instability was found.

### `p_rgh` — non-monotonic and persistent behaviour

`p_rgh` is the numerically interesting coupling family.

The ~0.973 residual at t=0.001 s is treated as a startup transient and is not the only relevant evidence. Elevated residuals reappear throughout the run after 0.1 s.

#### B family

B3 (`nOuterCorrectors=2`), `p_rgh_0`:
- post-startup maximum: **0.0343238 at 0.592 s**
- 2–4 s maximum: **0.0118509**
- 4–6 s maximum: **0.0153241 at 5.781 s**
- 6–8 s maximum: **0.012815 at 6.249 s**
- 8–10 s maximum: **0.00976308**

B5 (`nOuterCorrectors=3`), `p_rgh_0`:
- post-startup maximum: **0.0317178 at 0.573 s**
- 2–4 s maximum: **0.0107382**
- 4–6 s maximum: **0.015842 at 5.791 s**
- 6–8 s maximum: **0.0128389 at 6.250 s**
- 8–10 s maximum: **0.0095283**

Thus the B family contains meaningful pressure-residual events around 5.3–6.25 s in addition to early transients.

#### C family

C3 `p_rgh_0`:
- 0.1–2 s maximum: **0.0112909**
- 2–4 s: **0.0100891**
- 4–6 s: **0.0121034**
- 6–8 s: **0.0121384**
- 8–10 s: **0.0173881 near 9.985 s**

C5 `p_rgh_0`:
- 0.1–2 s: **0.0105247**
- 2–4 s: **0.0105513**
- 4–6 s: **0.0120312**
- 6–8 s: **0.0122043**
- 8–10 s: **0.0178995 near 9.981 s**

The C branch shows a different pattern, with pressure residuals increasing again toward the end of the 0–10 s window.

### Persistence of elevated residuals

For t>=0.1 s:

B3:
- `p_rgh_0 > 0.01` in 2100 of 9901 timesteps.
- `p_rgh_3 > 0.01` in 430 of 9901.

B5:
- `p_rgh_0 > 0.01` in 2036 of 9901.
- `p_rgh_5 > 0.01` in 428 of 9901.

C3:
- `p_rgh_0 > 0.01` in 1366 of 9901.
- `p_rgh_3 > 0.01` in 404 of 9901.

C5:
- `p_rgh_0 > 0.01` in 1427 of 9901.
- `p_rgh_5 > 0.01` in 245 of 9901.

### Actual effect of increasing nOuterCorrectors from 2 to 3

A descriptive within-timestep ratio was defined:

`R = p_rgh_last / p_rgh_0`

for t>=0.1 s.

- B3 (2 outer): median R = **0.6054**
- B5 (3 outer): median R = **0.5975**
- C3 (2 outer): median R = **0.8127**
- C5 (3 outer): median R = **0.8010**

Adding a third outer corrector therefore produces only a small improvement in the typical reduction of the `p_rgh` Initial residual.

There are also timesteps where the final pressure-solve Initial residual is larger than the first:

- B3: ~2.62% of audited timesteps.
- B5: ~3.62%.
- C3: ~10.08%.
- C5: ~8.22%.

Examples:

- B5 at 6.126 s: `p_rgh_0 = 0.00621936` and `p_rgh_5 = 0.00841035`, ratio ≈ **1.35**.
- C5 around 8.0 s includes events where later outer corrections end with residuals approximately **1.5–1.56×** the first residual in the timestep.

### Relation to previous numerical tests

B4/C4 (`nEnergyCorrectors=2`) retains essentially the same `p_rgh` behaviour as B3/C3. Extra energy correctors do not resolve the pressure-coupling behaviour.

B5/C5 (`nOuterCorrectors=3`) already showed negligible thermal/phase change relative to B3/C3 at a higher computational cost. This audit additionally shows that the third outer corrector does not substantially improve the typical pressure residual reduction.

### Interpretation

The correct diagnostic is not simply “the initial residual is high.” It must separate:

1. startup transient,
2. persistent spikes during the run,
3. reduction across outer correctors,
4. stagnation (`R≈1`),
5. deterioration (`R>1`),
6. formulation-specific B/C behaviour.

An isolated absolute Initial-residual value must not automatically be labelled an error; its within-timestep and temporal evolution must be examined.

### Next critical test

V7 with `nOuterCorrectors=4` will show whether a meaningful reduction begins beyond the 2→3 range.

If the advisor's larger-`nOuterCorrectors` runs truly show a strong improvement, a later controlled 4→5→6→7 series should use fixed timestep and otherwise identical settings before an optimum is claimed.

### OpenFOAM PostPlotter implication

The app should evolve from a viewer of individual `p_rgh_0`, `p_rgh_1`, etc. files into a coupling diagnostic that reconstructs, for every timestep:

- outer corrector,
- internal pressure corrector,
- `p_rgh_0 → ... → p_rgh_last`,
- `R = last/first`,
- orders-of-magnitude reduction,
- `R≈1` stagnation events,
- `R>1` deterioration events,
- worst-timestep ranking,
- configurable startup exclusion,
- cross-case comparison by `nOuterCorrectors`.

**Status:** ✅ B3–B5/C3–C5 Initial residuals audited; ✅ `p_rgh` identified as the primary coupling signal; 🟡 B7/C7 pending for the `nOuterCorrectors=4` test.


---

## 2026-09-25 — Distinguishing linear-solver convergence from PIMPLE coupling convergence
**[RUN-VERIFIED] [COUPLING-DIAGNOSTIC]**

After auditing the `p_rgh` Initial residuals, B5 and C5 `p_rghFinalRes_*` data were also analysed to separate two different phenomena:

1. convergence of each linear pressure solve;
2. convergence of the outer PIMPLE coupling.

### B5

For t>=0.1 s:

- `p_rghFinalRes_1`: median ≈ **6.68e-8**
- `p_rghFinalRes_3`: median ≈ **5.00e-8**
- `p_rghFinalRes_5`: median ≈ **3.91e-8**

The second pressure solve in each outer cycle consistently finishes near the 1e-8–1e-7 range.

However, the Initial residual of the next outer cycle can return to the 1e-3–1e-2 range.

### C5

For t>=0.1 s:

- `p_rghFinalRes_1`: median ≈ **6.76e-8**
- `p_rghFinalRes_3`: median ≈ **5.55e-8**
- `p_rghFinalRes_5`: median ≈ **5.09e-8**

Again, each linear solve can finish with a small residual while the following coupling cycle starts with a much larger Initial residual.

### Interpretation

A persistent `p_rgh` Initial residual should therefore not automatically be interpreted as failure of the linear pressure solver.

In the audited cases, the linear solver reduces its residual correctly, but coupled updates of velocity, pressure, energy, density/phase and model sources can cause the next pressure correction to start from a materially different state.

The diagnostic must explicitly separate:

- **linear-solver convergence:** Initial residual → Final residual within one pressure solve;
- **PIMPLE/nonlinear coupling convergence:** Initial residual from one outer cycle → Initial residual in the next outer cycle.

### App implication

OpenFOAM PostPlotter should display these two metrics separately. A small `Final residual` must not hide persistent coupling behaviour, and a high `Initial residual` must not be labelled a linear-solver failure when that pressure solve itself converges successfully.

**Status:** ✅ linear-solver and PIMPLE-coupling convergence separated using real B5/C5 data.


---

## 2026-09-25 — Vertical centerline profile added to the controlled series
**[POST-PROCESSING] [CONFIG-VERIFIED] [GIT-VERIFIED]**

A second sampling function object, `verticalProfiles`, was added to all ten controlled cases:

- B3_reference / C3_reference
- B4_energy2 / C4_energy2
- B5_outer3 / C5_outer3
- B6_adaptiveDt / C6_adaptiveDt
- B7_outer4 / C7_outer4

### Geometry

New line:

`line_x20mm`

with:

- x = **0.020 m**
- z = **0.005 m**
- y = **0.00025 → 0.03975 m**
- 80 uniformly distributed points
- `axis y`

The line crosses the geometric center of the metal and the central probe location in x-z.

### Fields

The same fields as the horizontal profiles are sampled:

- `U`
- `T`
- `phaseChangeSource:alpha1`

Therefore Ux, Uy, Uz and |U| can be analysed from the sampled vector field.

### Physical rationale

Gravity acts in the Y direction:

`g = (0, -9.81, 0)`

and the previous spatial analysis showed that B and C can have opposite signs of `Uy` at the center during part of solidification.

The existing `line_y20mm` and `line_y30mm` horizontal profiles cut through the circulation at fixed heights. The vertical centerline instead resolves the full bottom-to-top structure and can show:

- where `Uy > 0`,
- where `Uy < 0`,
- where `Uy` changes sign,
- how the velocity structure relates to T(y),
- how it relates to alpha_l(y),
- whether a recirculation cell exists and how it differs between B and C.

### Impact

This is strictly a post-processing change. It does not alter:

- mesh,
- material properties,
- boundary conditions,
- phase-change model,
- timestep,
- correctors,
- physical solution.

### Execution note

B6/C6/B7/C7 had already started running locally before this repository configuration was added. Therefore the Git change does not alter local runs already in progress. Their vertical profiles can be generated later from saved times after the local configuration is synchronized.

**Status:** ✅ vertical profile configuration added to B3–B7/C3–C7; 🟡 extraction/analysis pending.


---

## 2026-09-26 — Full solidification-diagnostics package added to V3–V7
**[POST-PROCESSING] [CONFIG-VERIFIED] [GIT-VERIFIED] [NOT-YET-RUN-VERIFIED]**

A common diagnostics package based only on native OpenFOAM Foundation v14 function objects was added to all ten controlled B3–B7/C3–C7 cases.

Main implementation commit:

`bd77587a4bf8c813c40512cfdfc3a27ae4e0168f`

This is strictly a post-processing modification. It does not alter the mesh, material properties, boundary conditions, phase-change model, timestep, PIMPLE settings or governing equations.

### Expanded central probe

The probe at `(0.020 0.020 0.005) m` now records every timestep:

- `U`
- `T`
- `p_rgh`
- `rho`
- `phaseChangeSource:alpha1`

This enables direct time correlation of modified pressure, density, velocity, temperature and liquid fraction at the same location.

### Thermal gradient

Added:

- `gradT = grad(T)`
- `magGradT = |grad(T)|`

The spatial maximum of `magGradT` and its location are also recorded through `metalMaxThermalGradient`.

### Local thermal rate

The native `ddt` function object is used to generate:

- `dTdt = dT/dt`
- `coolingRate = -dTdt`

Convention:

- `coolingRate > 0`: local cooling
- `coolingRate < 0`: local heating

`metalMeanCoolingRate` is also written.

### Density gradient

Added:

- `gradRho = grad(rho)`
- `magGradRho = |grad(rho)|`
- `metalMaxDensityGradient` with location

Purpose: directly compare the B/C buoyancy routes.

B uses temperature-dependent density and its density gradient participates in the native `p_rgh` buoyancy route.

C uses constant `rho`, so `gradRho` should remain approximately zero, providing a useful internal formulation check.

### Phase-change rate

Added:

- `dAlphaLdt = d(alpha_l)/dt`
- `solidificationRate = -dAlphaLdt`

Convention:

- `solidificationRate > 0`: local solidification
- `solidificationRate < 0`: local remelting

OpenFOAM v14 source was checked and `solidificationMeltingSource` explicitly updates `alpha1_.oldTime()`, so the liquid-fraction field has the temporal history required by the runtime derivative.

### Latent-heat rate

All ten cases were verified to use:

`L = 2.286e5 J/kg`

A native uniform field named `latentHeat` is generated with physical dimensions `J/kg`. Native `multiply` then evaluates:

`latentHeatRateVol = rho * L * solidificationRate`

with dimensions:

`W/m3`

Convention:

- positive: latent-heat release during solidification
- negative: heat absorption during local remelting

The field is also integrated over the metal domain:

`metalLatentHeatPower = integral(latentHeatRateVol dV)`

giving watts.

### Spatial Courant number

The native v14 field:

`CoCell`

is generated from `phi` and `rho`. For mass-flux `phi`, OpenFOAM v14's `CourantNo` implementation divides by density internally when required.

`metalMaxCourant` records the maximum and its location.

### Expanded spatial profiles

Both horizontal lines and the vertical centerline now sample:

- `U`
- `T`
- `p_rgh`
- `rho`
- liquid fraction
- `vorticity`
- `flowType`
- `magSqrDevGradU`
- `gradT`
- `magGradT`
- `dTdt`
- `coolingRate`
- `gradRho`
- `magGradRho`
- `dAlphaLdt`
- `solidificationRate`
- `latentHeatRateVol`
- `CoCell`

This allows flow, pressure, buoyancy, thermal gradients, cooling, phase advance/remelting, latent-heat release and local numerical loading to be studied on exactly the same spatial cuts.

### Existing energy diagnostics retained

The package also retains:

- `energyAdvectiveFlux`
- `heatFlux`
- `energyFlux`
- `metalTop` power
- metal-to-mold power
- total boundary power
- `metalSensibleEnthalpy`
- `metalMeanLiquidFraction`
- `vorticity`
- `flowType`

### Important OpenFOAM v14 limitation

OpenFOAM v14's own `functionObjects::ddt` source explicitly states that **`ddt` is not supported by `foamPostProcess`**.

Therefore:

- `dTdt`
- `coolingRate`
- `dAlphaLdt`
- `solidificationRate`
- `latentHeatRateVol`

must be generated DURING solver execution.

They cannot be retrospectively reconstructed through standard v14 `foamPostProcess` from an already completed run.

For older runs, PostPlotter can later estimate temporal derivatives from stored data, but those estimates must be distinguished from the native runtime `fvc::ddt` evaluation.

### Status

- ✅ configuration added to B3–B7/C3–C7
- ✅ availability and syntax of `grad`, `mag`, `ddt`, `uniform`, `multiply` and `CourantNo` checked against official OpenFOAM Foundation v14 source/caseDicts
- ✅ identical L verified in all ten cases
- ✅ dependent diagnostics placed before `lineProfiles`
- 🟡 not yet validated by an actual solver run with the full package enabled
- 🟡 B6/C6/B7/C7 local runs already in progress before this repository change will not automatically contain the newly added function objects



---

## 2026-09-26 — Real B3 validation of diagnostics package and `flowType` naming fix
**[RUN-VERIFIED] [BUG-FOUND] [FIXED]**

`B3_reference` was run from 0 to 10 s with the expanded diagnostics package.

The run completed successfully and `foamLog` executed at the end.

### Fields verified in `10/metal`

Found:

- `CoCell`
- `coolingRate`
- `dAlphaLdt`
- `dTdt`
- `gradRho`
- `gradT`
- `latentHeat`
- `latentHeatRateVol`
- `magGradRho`
- `magGradT`
- `magSqrDevGradU`
- `solidificationRate`
- `vorticity`

### Verified post-processing outputs

Successfully generated:

- `horizontalProfiles`
- `verticalProfiles`
- `metalBoundaryEnergyPower`
- `metalLatentHeatPower`
- `metalMaxCourant`
- `metalMaxDensityGradient`
- `metalMaxThermalGradient`
- `metalMeanCoolingRate`
- `metalMeanLiquidFraction`
- `metalMeanSolidificationRate`
- `metalMoldEnergyPower`
- `metalSensibleEnthalpy`
- `metalTopEnergyPower`
- `temperatureProbe`

### Finding

No file named `flowType` appeared.

Inspection of the official OpenFOAM Foundation v14 source showed that the `flowType` function object uses the **function-object block name** as its default result field name unless `result` is explicitly specified.

The configuration used:

`flowTopology { type flowType; ... }`

so the generated field was named `flowTopology`, while the profile samplers requested `flowType`.

### Fix

The following was added to all ten cases:

`result flowType;`

inside the `flowTopology` block.

Commit:

`c92c282ca7cb549b4efdd88b402191163c706066`

This makes the field name canonical and consistent with `lineProfiles` and the future PostPlotter parser.

**Status:** ✅ B3 validated the diagnostics package; ✅ naming inconsistency identified and fixed; 🟡 rerun B3 with the final batch so all datasets are fully homogeneous.


---

## 2026-09-26 — Final V3–V7 numerical audit after complete rerun
**[RUN-DATA-COMMITTED] [NUMERICAL-AUDIT] [COUPLING] [ADAPTIVE-DT]**

Final logs for all ten controlled cases were synchronized after executing the V3–V7 matrix. Result commits include `5d5ccb00f1b3` (final logs) and `54182ef3cab9` (remaining local synchronization).

The following analysis uses the versioned `foamLog` files directly from GitHub. For `p_rgh` coupling metrics, startup was excluded using `t >= 0.1 s`.

### Summary

| Case | Configuration | Steps | Parsed final time (s) | Exec. (s) | Max Co | max `p_rgh_0` post-startup | Median R | P95 R | R>1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | outer=2, fixed dt | 10000 | 10.000000 | 202.005 | 0.175912 | 0.0343238 @ 0.592 s | 0.605438 | 0.945131 | 2.62% |
| C3_reference | outer=2, fixed dt | 10000 | 10.000000 | 196.543 | 0.0700709 | 0.0173881 @ 9.985 s | 0.812747 | 1.059338 | 10.08% |
| B4_energy2 | outer=2, energy=2 | 10000 | 10.000000 | 250.984 | 0.176643 | 0.0307308 @ 0.591 s | 0.604283 | 0.943883 | 2.92% |
| C4_energy2 | outer=2, energy=2 | 10000 | 10.000000 | 220.093 | 0.0700709 | 0.0179951 @ 9.999 s | 0.813191 | 1.063103 | 10.62% |
| B5_outer3 | outer=3, fixed dt | 10000 | 10.000000 | 282.222 | 0.175874 | 0.0317178 @ 0.573 s | 0.597503 | 0.950764 | 3.62% |
| C5_outer3 | outer=3, fixed dt | 10000 | 10.000000 | 273.060 | 0.0700712 | 0.0178995 @ 9.981 s | 0.800997 | 1.041475 | 8.22% |
| B6_adaptiveDt | outer=3, adaptive dt | 2810 | 9.999657 | 80.778 | 0.287759 | 0.0186405 @ 0.784957 s | 0.374538 | 0.764803 | 1.59% |
| C6_adaptiveDt | outer=3, adaptive dt | 1584 | 10.003410 | 47.336 | 0.287049 | 0.0223995 @ 9.983344 s | 0.794831 | 1.034915 | 7.58% |
| B7_outer4 | outer=4, fixed dt | 10000 | 10.000000 | 381.367 | 0.175849 | 0.0362977 @ 0.731 s | 0.603163 | 0.950615 | 2.96% |
| C7_outer4 | outer=4, fixed dt | 10000 | 10.000000 | 365.418 | 0.0700710 | 0.0174552 @ 9.996 s | 0.808822 | 1.082497 | 10.65% |

where:

`R = p_rgh(last outer Initial residual) / p_rgh(first outer Initial residual)`.

### Linear solver vs coupling

Across all ten cases, the `Final residual` of the last `p_rgh` solve remains extremely low:

- median approximately `3.9e-8 → 5.7e-8`;
- P99 approximately `< 1e-7`;
- observed maximum approximately `< 1e-7`.

This reinforces the established distinction: the pressure linear solver converges strongly within each solve, while the evolution of the **Initial residual across outer corrections** describes nonlinear coupling behavior. `R>1` does not by itself mean linear-solver failure.

### Outer-corrector sensitivity: diminishing returns

For the fixed-timestep branches:

- B: median R = 0.6054 (outer2), 0.5975 (outer3), 0.6032 (outer4).
- C: median R = 0.8127 (outer2), 0.8010 (outer3), 0.8088 (outer4).

The 2→3 change is small and 3→4 is **not monotonically better**; outer4 returns toward values close to outer2.

Cost rises clearly in this rerun:

- B5 outer3 costs ~39.7% more than B3.
- B7 outer4 costs ~88.8% more than B3.
- C5 outer3 costs ~38.9% more than C3.
- C7 outer4 costs ~85.9% more than C3.

Thus, for these cases over 0–10 s, outer4 adds substantial cost without evidence of proportional improvement in `p_rgh` coupling. This is evidence of **diminishing returns**, not a universal OpenFOAM rule.

### Energy-corrector sensitivity

B4/C4 retain coupling metrics essentially equal to B3/C3, while execution time in this rerun rises by ~24.2% for B and ~12.0% for C.

This is consistent with the previous thermal conclusion: `nEnergyCorrectors=2` does not materially change the monitored solution and also shows no clear coupling improvement that justifies the added cost in this matrix.

### Adaptive timestep V6

Relative to V5, which also uses `nOuterCorrectors=3`:

- B6 reduces steps 10000→2810 and runtime 282.222→80.778 s: ~3.49× faster.
- C6 reduces steps 10000→1584 and runtime 273.060→47.336 s: ~5.77× faster.
- Median `deltaT`: B6 ≈ 0.003954 s; C6 ≈ 0.005902 s.
- Maximum observed `deltaT`: B6 ≈ 0.005321 s; C6 ≈ 0.026623 s.
- Maximum Co: B6 = 0.287759; C6 = 0.287049, above configured `maxCo=0.25`.

Source inspection of OpenFOAM Foundation v14, `src/finiteVolume/cfdTools/general/include/setDeltaT.H`, confirms that `adjustTimeStep` computes the **next** `deltaT` from the observed Co and limits timestep growth to 1.2× per adjustment. Therefore `maxCo` acts as a timestep-control target and is not a mathematical guarantee that no reported Co can transiently exceed it.

The reported final cumulative continuity value is also higher in V6:

- B6: 2.44980e-4 vs B5: 1.65205e-4.
- C6: 2.71897e-4 vs C5: 1.78172e-4.

This deserves follow-up; it is not by itself evidence of physical invalidity. Before adopting V6 as the production configuration, its thermal histories, phase behavior, profiles, and physical diagnostics should be compared against V5.

### B/C coupling difference

Fixed-timestep B branches show stronger relative Initial-residual reduction (median R ~0.60) and fewer `R>1` events (~2.6–3.6%) than C (~0.80 and ~8.2–10.6%).

At the same time, B can show larger `p_rgh_0` maxima than C. Two questions must therefore remain separate:

1. mismatch magnitude at the start of the solve;
2. relative reduction achieved during coupling.

The difference may be related to the B/C physical formulations, but it is not labelled here as “better/worse stability” without further evidence.

**Status:** ✅ final V3–V7 logs versioned; ✅ outer2/3/4 audited; ✅ V6 adaptive timestep numerically audited; ✅ linear convergence separated from coupling; 🟡 complete physical comparison of V6/V7 using the new `researchDiagnostics` outputs remains pending.


---

## 2026-09-26 — Final V3–V7 numerical audit from synchronized results
**[RUN-VERIFIED] [GIT-VERIFIED] [NUMERICAL-AUDIT]**

Final results for all ten controlled V3–V7 cases were synchronized from the local workstation to the repository and audited directly from the versioned `log.foamMultiRun` and `logs/` data.

Result commits:
- `5d5ccb00f1b3...` — final V3–V7 log update.
- `54182ef3cab9...` — remaining local-data synchronization.

### Cost and `p_rgh` coupling comparison (startup excluded: t < 0.1 s)

| Case | Steps | Max p0 | Median p0 | Median R | p95 R | R>1 | Max Co | Exec. s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | 10000 | 0.0343238 | 0.00835789 | 0.605438 | 0.945131 | 2.62% | 0.175912 | 202.005 |
| C3_reference | 10000 | 0.0173881 | 0.00748726 | 0.812747 | 1.05934 | 10.08% | 0.0700709 | 196.543 |
| B4_energy2 | 10000 | 0.0307308 | 0.00835290 | 0.604283 | 0.943883 | 2.92% | 0.176643 | 250.984 |
| C4_energy2 | 10000 | 0.0179951 | 0.00751839 | 0.813191 | 1.06310 | 10.62% | 0.0700709 | 220.093 |
| B5_outer3 | 10000 | 0.0317178 | 0.00825669 | 0.597503 | 0.950764 | 3.62% | 0.175874 | 282.222 |
| C5_outer3 | 10000 | 0.0178995 | 0.00775813 | 0.800997 | 1.04147 | 8.22% | 0.0700712 | 273.060 |
| B6_adaptiveDt | 2810 | 0.0186405 | 0.00236917 | 0.374538 | 0.764803 | 1.59% | 0.287759 | 80.778 |
| C6_adaptiveDt | 1584 | 0.0223995 | 0.00898528 | 0.794831 | 1.03491 | 7.58% | 0.287049 | 47.336 |
| B7_outer4 | 10000 | 0.0362977 | 0.00831734 | 0.603163 | 0.950615 | 2.96% | 0.175849 | 381.367 |
| C7_outer4 | 10000 | 0.0174552 | 0.00759476 | 0.808822 | 1.08250 | 10.65% | 0.0700710 | 365.418 |

Here `R = p_rgh,last(initial) / p_rgh,first(initial)` within each timestep. `R>1` means the Initial residual increased across coupling; it does not by itself imply linear-solver failure.

The final pressure solves still terminate with final residuals typically of order `10^-8` to `10^-7` in all cases, so linear convergence and PIMPLE-coupling convergence must remain separate interpretations.

### Outer-corrector result

Comparing V3, V5 and V7:

- B: median R = 0.6054 → 0.5975 → 0.6032 for outer 2 → 3 → 4.
- C: median R = 0.8127 → 0.8010 → 0.8088.
- B7 cost increases from 202.0 s to 381.4 s relative to B3 (~89%).
- C7 cost increases from 196.5 s to 365.4 s relative to C3 (~86%).

The fourth outer correction does not provide a monotonic improvement in median R relative to outer3 while computational cost increases strongly. This supports the previously observed diminishing-return behavior over the tested range. It is not a physical-model selection.

### Energy-corrector result

B4/C4 retain coupling metrics close to B3/C3 while increasing cost, consistent with the previously small central thermal/phase sensitivity.

### Adaptive timestep V6

V6 strongly reduces step count and execution time:

- B6: 2810 steps, 80.78 s.
- C6: 1584 steps, 47.34 s.

Observed `deltaT`:
- B6: median 0.003954 s, maximum 0.005321 s.
- C6: median 0.005902 s, maximum 0.026623 s.

Recorded maximum Courant reaches ~0.288 in both cases, above the configured `maxCo=0.25`, while final values are approximately 0.25. This is recorded as an observed overshoot of the adaptation target and requires interpretation in the context of the timestep-adjustment algorithm; it is not automatically labeled instability.

Final cumulative continuity is larger in V6:
- B6: 2.4498e-4.
- C6: 2.71897e-4.

V6 should not be accepted as a replacement for fixed timestep until the physical outputs (T, phase, profiles, gradients and energy) are compared, not merely cost and residuals.

**Status:** final V3–V7 numerical audit completed from versioned data. Next stage: physical comparison of postProcessing outputs.


---

## 2026-09-26 — Validation matrix and experimental Quick-Cup parity audit
**[VALIDATION-GATE] [SOURCE-AUDIT] [NO-PHYSICS-CHANGE]**

The controlled V3–V7 configuration was audited against the hypoeutectic Quick-Cup benchmark described by Chiumenti et al.

Main findings:

- V3–V7 remain frozen as the numerical-sensitivity and buoyancy-formulation study.
- The C3/C4/C5 thermal rebound (+5.35 K) is reproduced with essentially the same Tmin and liquid-fraction recovery under the tested numerical changes. In the current model it coincides with local remelting and is not labelled nucleation-driven recalescence.
- The current case is not yet an aligned experimental benchmark: initial metal temperature is 1500 K versus 1573.15 K in the paper Quick-Cup, external HTC is 10 versus 50 W/m2K, and mould properties differ.
- The current 0.2 mm interface layer with k=0.1 W/mK corresponds to an effective resistance of approximately 500 W/m2K and therefore matches the paper's casting–mould HTC.
- The current initial temperature (1226.85 °C) is about 33 °C below the T_start_L=1260 °C used by the paper's hypoeutectic model.
- Standard `solidificationMelting` uses a single melt-fraction variable tied to an equilibrium relation, whereas the paper model separates dendritic and eutectic transformations with time-dependent kinetic laws and undercooling.
- No raw/CSV experimental time series was found in the repository or available files, so RMSE/MAE values are not fabricated.

Added:
- `VALIDATION_MATRIX.md`
- `VALIDATION_MATRIX_ES.md`
- `VALIDATION_MATRIX_EN.md`

**Decision:** construct an experiment-aligned equilibrium case before writing a kinetic fvModel. The kinetic branch is opened only if that case demonstrates a structural limitation of the equilibrium model.


---

## 2026-09-26 — Direct `solidificationMeltingSource` momentum-term diagnostics
**[POSTPROCESSING] [PHYSICS-DIAGNOSTICS] [NO-PHYSICS-CHANGE]**

After completing the V3–V7 numerical audit, a dedicated diagnostic was added to determine whether the observed velocity and mushy-zone differences originate from pressure–velocity coupling, buoyancy, or Darcy damping from `solidificationMeltingSource`.

The new `solidificationMeltingMomentumDiagnostics` block was added to all ten controlled cases:

- B3_reference through B7_outer4
- C3_reference through C7_outer4

The diagnostic reads `Cu`, `q`, `beta`, `rhoRef`, `Tsol`, `Tliq`, and `alpha1e` directly from `constant/metal/fvModels`, avoiding duplicated manual parameter definitions.

It reconstructs the Darcy damping coefficient:

`D = Cu (1-alpha_l)^2 / (alpha_l^3 + q)`

and its acceleration contribution:

`a_D = -D U`.

It also reconstructs the model temperature departure, Boussinesq acceleration/source, the `p_rgh` pressure-gradient acceleration, and local drag-to-buoyancy / drag-to-pressure ratios.

Written fields:

- `phaseChangeSolidFraction`
- `phaseChangeDarcyCoeff`
- `phaseChangeDarcySp`
- `phaseChangeDarcyAcceleration`
- `phaseChangeModelDeltaT`
- `phaseChangeBuoyancyAcceleration`
- `phaseChangeBuoyancySu`
- `pRghAcceleration`
- `magPhaseChangeDarcyAcceleration`
- `magPhaseChangeBuoyancyAcceleration`
- `magPRghAcceleration`
- `phaseChangeDragToBuoyancy`
- `phaseChangeDragToPressure`

### Relation to the already documented V6/V7 results

This addition does not replace the previous numerical conclusions:

- V6 remains the adaptive-timestep branch: much lower computational cost, but physical equivalence must still be demonstrated.
- V7 remains the four-outer-corrector test: substantially higher cost without a clear monotonic coupling improvement over V5.
- Linear pressure solves still typically end around 10^-8–10^-7 final residuals; the open issue is not a simple linear-solver failure.
- The next physical comparison must combine the existing V3–V7 results with the new force/damping fields.

### Validation status

The diagnostic code is versioned but the new fields still require a short B7/C7 runtime validation under OpenFOAM Foundation v14 before the full matrix is rerun.

**Next gate:** compile/run B7 and C7, verify all new fields are written, then use the diagnostic for the V3–V7 physical comparison.


### Compatibility correction found during B7 validation

The first B7 validation failed before solver execution while compiling the `coded` function object:

`fatal error: fvCFD.H: No such file or directory`

This was confirmed to be a dynamic-code include-path compatibility issue under OpenFOAM Foundation v14, not a physical or numerical failure of the case.

`fvCFD.H` was replaced by specific compatible headers (`fvMesh.H`, `volFields.H`, `uniformDimensionedFields.H`, `IOdictionary.H`, `zeroGradientFvPatchFields.H`, `fvcGrad.H`) in all ten V3–V7 cases. B7 must be revalidated before C7 or the full matrix is executed.


### Second B7 compatibility correction

The second diagnostic-compilation validation exposed two additional OpenFOAM Foundation v14 API differences:

- `Time::timeName()` requires an explicit time argument in this dynamic-code context.
- `gMax(field)` returns a `scalar` directly, so `.value()` must not be called.

Corrections applied to all ten V3–V7 cases:

- `m.time().timeName()` → `m.time().timeName(m.time().timeOutputValue())`
- `gMax(...).value()` → `gMax(...)`

This remains a dynamic post-processing compilation issue, not solver instability or a physical-model failure.


### Third B7 compatibility correction

The third validation showed that `Time::timeOutputValue()` is not part of the installed OpenFOAM Foundation v14 API. The OpenFOAM 14 `Time` interface confirms that `timeName` accepts an explicit scalar time, so the code was changed to:

`m.time().timeName(m.time().value())`

The correction was applied to all ten controlled V3–V7 cases. This remains strictly a dynamic post-processing compilation issue.


### Compact export of momentum diagnostics to postProcessing

Added `system/momentumPostProcessing` to B3–B7 and C3–C7 and integrated it into `Allrun` after a solver run that reaches `End`.

Purpose: preserve useful scientific evidence from `solidificationMeltingMomentumDiagnostics` in Git without versioning every OpenFOAM time directory.

The post-processing stage reloads the written volumetric fields and generates:

- `momentumMean`: volume averages of solid fraction, Darcy coefficient, model deltaT, and Darcy, buoyancy and `p_rgh`-gradient acceleration magnitudes.
- `momentumMax`: maxima and their locations for the same fields.
- `momentumHorizontalProfiles`: profiles at y=20 mm and y=30 mm.
- `momentumVerticalProfiles`: profile at x=20 mm.
- Profiles include vectors, magnitudes, and local Darcy/buoyancy and Darcy/pressure ratios.

Ratios are retained as local diagnostics; physical dominance must not be inferred from ratios of unrelated global maxima or from very large ratios caused by near-zero denominators.

`Allrun` performs this reduction only when `log.foamMultiRun` contains `End`, preventing a failed run from being packaged as valid results.

Full calculated time directories remain ignored by Git; `postProcessing/` remains tracked.


### Fix to batch post-processing validation

The first corrected version of `postprocess_momentum_all.sh` still used `grep "^End$"` on `log.foamMultiRun` as its validity criterion. Valid controlled-case runs do not necessarily contain a line matching that exact pattern, so every case was incorrectly skipped.

That dependency was removed. The helper now requires:
1. an existing `log.foamMultiRun`; and
2. locally available `phaseChangeDarcyCoeff` fields in calculated time directories.

For future runs, `Allrun` captures the exit status of `foamMultiRun` immediately and performs the momentum reduction only when the solver returns status 0.

This issue affected only post-processing automation and does not invalidate the completed simulations.


### Region fix in momentumPostProcessing

The first real `foamPostProcess` execution failed in every case with:

`request for objectRegistry region0 from objectRegistry <case> failed; available objects: metal`.

Diagnosis: the function objects in `system/momentumPostProcessing` (`momentumMean`, `momentumMax`, `momentumHorizontalProfiles`, `momentumVerticalProfiles`) did not explicitly declare `region metal;`. Even though `foamPostProcess` was launched with `-region metal`, the region-aware function objects still resolved the default region as `region0`.

Fix: added `region metal;` to all four function objects in B3–B7 and C3–C7.

The failure occurred before statistics/profiles were evaluated and does not affect the CFD simulations or the already-written volumetric fields.


## Vertical velocity Uy profile analysis — B3–B7 / C3–C7

An explicit comparison of the vertical velocity component `Uy` was performed on all three available spatial profiles:
- horizontal `y = 20 mm`;
- horizontal `y = 30 mm`;
- vertical centerline `x = 20 mm`.

Fixed cases were compared at `t = 10 s`. Adaptive V6 cases were compared with V5 linearly interpolated to the same physical time.

### Fixed-version sensitivity — B family

Using B3 as reference at `t = 10 s`:

- B4 vs B3:
  - y=20 mm: NRMSE/RMS(Uy) = 4.44%, corr = 0.9990;
  - y=30 mm: 9.45%, corr = 0.9955;
  - vertical: 0.42%, corr = 0.999996.

- B5 vs B3:
  - y=20 mm: 4.00%;
  - y=30 mm: 8.55%;
  - vertical: 0.45%.

- B7 vs B3:
  - y=20 mm: 5.47%;
  - y=30 mm: 11.64%;
  - vertical: 0.45%.

The B fixed cases retain the same qualitative Uy structure. Differences are modest and largest near the upper horizontal profile. Increasing outer correctors does not produce monotonic convergence toward a different velocity profile.

### Fixed-version sensitivity — C family

Using C3 as reference at `t = 10 s`, C4/C5/C7 are practically indistinguishable:

- y=20 mm: NRMSE/RMS < 0.007%;
- y=30 mm: < 0.010%;
- vertical: < 0.004%;
- correlations ≈ 1.

### Adaptive effect — B6 vs B5

At `t = 9.946515 s`:

- y=20 mm:
  - NRMSE/RMS(Uy) = 50.18%;
  - corr = 0.865;
  - 4/80 sampled points change sign.

- y=30 mm:
  - NRMSE/RMS = 80.60%;
  - corr = 0.716;
  - B5 Uy_min = -0.01933 m/s, Uy_max = +0.01354 m/s;
  - B6 Uy_min = -0.01027 m/s, Uy_max = +0.00306 m/s.

- vertical x=20 mm:
  - NRMSE/RMS = 99.26%;
  - corr = 0.121;
  - 20/80 points change sign;
  - B5 Uy_min = -0.01953 m/s, Uy_max = +0.00400 m/s;
  - B6 Uy_min = -0.00150 m/s, Uy_max = +0.00237 m/s.

B6 therefore does not preserve the vertical velocity field of B5. The strong descending centerline component is suppressed by roughly an order of magnitude.

### Adaptive effect — C6 vs C5

At `t = 9.182456 s`:

- y=20 mm: NRMSE/RMS = 3.33%, corr = 0.999964;
- y=30 mm: 1.69%, corr = 0.999867;
- vertical: 3.42%, corr = 0.999787;
- no sign changes in any profile.

C6 preserves the Uy structure of C5 much more closely.

### B vs C formulation difference

B3 vs C3 at `t = 10 s`:

- y=20 mm: corr = 0.284, 28/80 sign changes;
- y=30 mm: corr = -0.715, 57/80 sign changes;
- vertical: corr = -0.689, 46/80 sign changes.

Vertical centerline:
- B3: Uy_min = -0.01945 m/s, Uy_max = +0.00401 m/s;
- C3: Uy_min = -0.000239 m/s, Uy_max = +0.01209 m/s.

Thus B and C exhibit qualitatively different vertical circulation structures rather than merely different velocity magnitudes.

### Uy conclusion

1. Fixed V4/V5/V7 do not qualitatively change Uy relative to V3.
2. C is essentially insensitive to the tested corrector changes.
3. B shows moderate lateral sensitivity, strongest at y=30 mm.
4. B6 adaptive strongly alters Uy and is not equivalent to B5 when convection matters.
5. C6 adaptive preserves Uy much more closely.
6. The B-vs-C formulation difference is substantially larger than the fixed-version differences within either family.


## Exhaustive temporal Uy sweep — all controlled runs

The script `analysis_tools/uy_temporal_analysis.py` was executed over every stored sample of:
- horizontal `y=20 mm`;
- horizontal `y=30 mm`;
- vertical `x=20 mm`.

Fixed cases were compared at exact common physical times (101 samples from 0 to 10 s). Adaptive cases were evaluated at every native stored adaptive time, with the fixed reference linearly interpolated to the same physical time.

Complete outputs:
- `analysis_results/uy_temporal/uy_temporal_metrics.csv`
- `analysis_results/uy_temporal/uy_temporal_summary.md`

### Fixed B family

B4/B5/B7 preserve the qualitative Uy structure of B3 throughout the run.

Median / peak NRMSE relative to RMS(Uy):
- B4 vs B3:
  - y20: 4.21% / 12.95%;
  - y30: 4.43% / 9.47%;
  - vertical: 0.80% / 3.08%.
- B5 vs B3:
  - y20: 3.57% / 11.53%;
  - y30: 3.91% / 8.57%;
  - vertical: 0.82% / 4.00%.
- B7 vs B3:
  - y20: 5.20% / 16.02%;
  - y30: 5.44% / 11.65%;
  - vertical: 0.79% / 3.96%.

Adding correctors does not produce monotonic convergence toward a distinct Uy profile; B7 can differ more from B3 than B5 does.

### Fixed C family

C4/C5/C7 are effectively indistinguishable from C3 over the full transient:
- NRMSE/RMS medians and peaks below roughly 0.03%;
- correlations ~1;
- no meaningful sign changes.

### B6 adaptive vs B5 fixed

Divergence starts early and then accumulates/reorganizes.

y20:
- first >=5% at 0.223624 s;
- >=10% at 1.76685 s;
- >=25% at 2.31438 s;
- >=50% at 2.60859 s;
- median NRMSE/RMS = 33.10%;
- peak = 80.09% at 7.500923 s.

y30:
- >=10% already at 0.223624 s;
- >=25% and >=50% at 1.254542 s;
- median = 59.12%;
- peak = 84.81% at 1.76685 s.

vertical:
- >=25% from 0.223624 s;
- >=50% at 0.763943 s;
- median = 75.23%;
- peak = 99.26% at 9.946515 s;
- correlation falls to 0.1211 at the last stored time;
- maximum sign disagreement = 53/80 points at 9.422639 s.

B6 therefore does not preserve the B5 vertical convection structure.

### C6 adaptive vs C5 fixed

C6 shows an early relative discrepancy but then remains close to C5.

At 0.953122 s:
- y20: NRMSE/RMS = 13.81%, absolute RMSE = 8.13e-4 m/s;
- y30: 13.70%, RMSE = 6.80e-4 m/s;
- vertical: 22.26%, RMSE = 5.08e-4 m/s.

Across the run:
- medians = 3.03% (y20), 4.79% (y30), 3.42% (vertical);
- at 9.182456 s: 3.33%, 1.69%, 3.42%;
- final correlations >0.9997;
- 25% and 50% thresholds are never reached.

### B3 vs C3

The formulation difference appears almost immediately:
- all profiles exceed 25% NRMSE/RMS by 0.1 s;
- peak NRMSE/RMS: 189.3% (y20), 145.7% (y30), 190.4% (vertical);
- minimum correlations: -0.352, -0.731, -0.794.

Overall:
1. Additional correctors do not qualitatively change Uy in fixed cases.
2. C is extremely stable to the tested numerical changes.
3. B6 adaptive is not equivalent to B5 and changes vertical convection from early times.
4. C6 adaptive preserves Uy reasonably well after the initial transient.
5. The B-vs-C difference is structural and much larger than fixed-version sensitivity.


## Exhaustive OF14 diagnostics: vorticity, flow topology, energy transport and coupling

Reproducible analysis was executed across all 10 controlled cases with:

- `analysis_tools/physics_diagnostics_analysis.py`
- `analysis_tools/coupling_analysis.py`

Permanent summaries:

- `analysis_results/physics_diagnostics/physics_diagnostics_summary.md`
- `analysis_results/coupling/coupling_summary.md`

### Energy

Fixed B3/B4/B5/B7 are energetically almost indistinguishable. The same is true for C3/C4/C5/C7.

Approximately 94.8% of the evaluated diffusive boundary energy transport occurs through `metal_to_mold`, with only ~5.2% through `metalTop`. Diffusive heat extraction is therefore dominated by the metal-mold interface.

Fixed C:
- integrated boundary advective contribution ≈ +6.8 J;
- diffusive ≈ 7057.8 J;
- advective magnitude share ≈ 0.1%.

Fixed B:
- integrated boundary advective contribution ≈ -970 J;
- diffusive ≈ 7100 J;
- advective magnitude share ≈ 12%.

The B advective contribution is associated with `metalTop`; metal-to-mold advection is essentially zero. Since `metalTop` combines `U: slip` and `p_rgh: totalPressure`, this B top mass/enthalpy flux must be investigated as a boundary-flux consistency issue before interpreting it as physical convective heat loss.

### Vorticity and flowType

Foundation v14 convention:
- +1 rotational;
- 0 parallel shear;
- -1 pure-shear/deformation.

Reported percentages are sampled-line fractions, not volume fractions.

Fixed B:
- y=20 mm: typical RMS omega_z ≈ 7.34 1/s, ~10% rotational samples;
- y=30 mm: RMS ≈ 5.82 1/s, ~45% rotational samples;
- vertical centerline: much smaller vorticity.

Fixed C:
- y=20 mm: RMS ≈ 3.52 1/s, ~40% rotational samples and ~37% sampled strength associated with rotational classification;
- y=30 mm: ~12.5% rotational;
- vertical centerline: near-zero vorticity.

B and C therefore exhibit distinct sampled circulation topologies.

B6 strongly reorganizes the B flow:
- y=30 rotational fraction ~45% -> ~20%;
- rotational-strength share ~12.9% -> ~2.5%;
- vertical-centerline vorticity nearly collapses.

C6 preserves Uy much better than B6 but still alters derivative/topology metrics at y=20.

### Coupling

`R_p_outer` is defined as the initial residual of the first p_rgh solve in the final outer corrector divided by the corresponding initial residual in the first outer corrector.

Lower values indicate stronger typical contraction across the outer loop; R>1 is not a linear-solver failure.

Fixed median Rp:

B:
- B3 0.6104;
- B4 0.6084;
- B5 0.5976;
- B7 0.5989.

C:
- C3 0.8054;
- C4 0.8054;
- C5 0.7951;
- C7 0.8019.

V5 only modestly improves typical pressure coupling versus V3. V7 adds no further improvement.

The second energy corrector dramatically reduces the h residual:
- B3 Rh≈2.16e-3 -> B4≈1.92e-6;
- C3 Rh≈1.05e-3 -> C4≈3.10e-7.

However it does not materially improve Re, physical fields, vorticity or integrated energy transport, indicating over-convergence of h without observed physical benefit.

B6 has a much lower Rp (~0.372) but worse continuity, higher Courant and a substantially changed Uy/vorticity solution; lower coupling residual alone is therefore insufficient to call it better.

Adopted rule: coupling is numerically preferable only when contraction improves consistently while linear residuals and continuity remain acceptable, timestep/Courant constraints are respected, the physical solution is preserved, and extra cost is justified.


## Audit of `metalTop`: impermeable-wall / open-pressure inconsistency

**[GIT-VERIFIED] [OPENFOAM-v14-SOURCE-VERIFIED] [INTERPRETATION]**

The `metalTop` boundary was audited after observing an integrated `energyAdvectiveFlux` of about -970 J in the fixed B cases, compared with only ~+6.8 J in the fixed C cases.

### Geometry

In `system/blockMeshDict`, `metalTop` is declared as a `wall`.

### Velocity

All controlled cases use:

```
metalTop
{
    type slip;
}
```

In OpenFOAM Foundation v14, `slip` inherits the symmetry projection and removes the velocity component normal to the patch. For a static mesh this imposes `U·n = 0`: tangential motion is allowed, normal penetration is not.

### Pressure

However, `p_rgh` currently uses:

```
metalTop
{
    type totalPressure;
    p0 uniform 1e5;
}
```

OpenFOAM v14 documents `totalPressure` as an inflow/outflow/entrainment pressure condition. It is intended for pressure-open boundaries where flux may enter or leave the domain.

By contrast, `fixedFluxPressure` sets the pressure gradient such that the boundary flux matches that prescribed by the velocity boundary condition. It is therefore the consistent pressure condition for an impermeable slip wall.

### Advective-flux evidence

OpenFOAM v14 calculates `energyAdvectiveFlux` using `alphaRhoPhi` and sensible enthalpy `hs`.

Therefore, a non-zero `energyAdvectiveFlux` across `metalTop` demonstrates that the solver surface mass flux used for advection (`alphaRhoPhi`) is non-zero even though the `slip` velocity condition imposes zero normal velocity.

This is a pressure/flux-boundary inconsistency.

### Why the effect is much larger in B

B uses:
- `heRhoThermo`;
- `icoTabulated` EOS;
- temperature-dependent density;
- `beta=0` in `solidificationMeltingSource`.

C uses:
- `heRhoThermo`;
- `rhoConst` EOS;
- `rho=6820 kg/m3`;
- explicit buoyancy via `beta=1.13e-4`.

Both use the same `metalTop` settings and h=10 W/(m2 K), but the variable-density flux formulation in B makes the inconsistency much more visible in `alphaRhoPhi`. This is consistent with the large B boundary advective-energy term, but should be confirmed with a controlled rerun.

### Physical implication

If the current model intends the upper metal surface to be a fixed free surface with no mass loss and no interface deformation, the consistent approximation is:

- U: `slip`
- p_rgh: `fixedFluxPressure`
- T: `externalWallHeatFluxTemperature`

If the patch were intended to be a truly open boundary with metal inflow/outflow, then `totalPressure` could be appropriate, but `U: slip` would not; a pressure-compatible inlet/outlet velocity condition would be required.

### Methodological consequence

The B-vs-C differences in Uy, vorticity and advective energy transport should not be attributed solely to buoyancy formulation until a controlled test is repeated with only the `metalTop/p_rgh` condition changed from `totalPressure` to `fixedFluxPressure`.

Recommended controlled test:
- clone B5 and C5;
- change only `metalTop/p_rgh`: `totalPressure` -> `fixedFluxPressure`;
- keep U=slip, T, mesh, material properties, PIMPLE and timestep unchanged;
- compare top mass/advective-energy flux, Uy, vorticity, phase fraction, continuity and energy.

Historical cases were not modified by this audit.


## V8 adaptive + 4 outer correctors — final result

A complete physical-time-aligned comparison was performed for B8/C8 against V6 adaptive and V5 fixed, covering Uy, T, alphaL, vorticity, flowType, Darcy acceleration, p_rgh acceleration, coupling, continuity, Courant and cost.

Permanent summary:
- `analysis_results/v8_comprehensive/summary.md`

### B family

B8 is practically indistinguishable from B6:
- median Uy NRMSE: 0.04% (y20), 0.13% (y30), 0.17% (vertical);
- final T RMSE ~0.004–0.005 K;
- alphaL essentially identical;
- horizontal vorticity differences <0.2%;
- no flowType class disagreement;
- Darcy and p_rgh acceleration differences ~0.1% or less;
- phase-front locations indistinguishable.

B8 remains strongly different from B5:
- final Uy NRMSE: 50.2% (y20), 80.5% (y30), 99.2% (vertical);
- flowType disagreement: 40% at y20 and 85% at y30;
- Darcy acceleration: 42–71%;
- p_rgh acceleration: 20–50%;
- vertical mushy width: B5 16.916 mm vs B8 18.493 mm (+9.3%).

Coupling/cost:
- B6 median Rp=0.3721, clock=119 s;
- B8 median Rp=0.3882, clock=220 s;
- continuity remains ~2.45e-4;
- Co remains ~0.29.

B conclusion: the fourth outer corrector does not recover the fixed-step solution and nearly doubles cost. The V6 discrepancy is not caused by insufficient root-level PIMPLE outer coupling.

### C family

C8 is likewise essentially identical to C6:
- median Uy NRMSE ~0.01–0.03%;
- T RMSE ~0.003–0.004 K;
- alphaL essentially identical;
- horizontal vorticity differences <=0.08%;
- no flowType class disagreement;
- Darcy <=0.06%;
- p_rgh acceleration <=0.20%.

C8 preserves the same adaptive-vs-fixed differences already observed in C6:
- Uy remains close to C5 (~1.7–4.8%);
- Darcy differs ~10–16%;
- vertical p_rgh acceleration differs ~56%;
- vertical mushy width: C5 17.679 mm vs C8 19.622 mm (+11.0%).

Coupling/cost:
- C6 median Rp=0.7900, clock=65 s;
- C8 median Rp=0.7765, clock=121 s;
- Rp>1 improves modestly from 6.25% to 5.10%;
- continuity and Co are essentially unchanged.

C conclusion: the fourth outer corrector modestly improves pressure-coupling statistics but does not change the physical solution and nearly doubles runtime.

### Decision

V8 is a diminishing-return case and is not recommended as a production configuration. The V5↔V6/V8 differences arise from the adaptive timestep trajectory/time discretization, not from insufficient outer-corrector count.

V5 fixed remains the physical reference. V6 may be retained only as an explicit speed/accuracy trade-off study. V8 is retained as evidence of independence with respect to the number of outer correctors.


## Audit of PIMPLE hierarchy in foamMultiRun (OpenFOAM Foundation v14)

**[SOURCE-VERIFIED] [LOG-VERIFIED]**

The effective source of each PIMPLE control in the multi-region `foamMultiRun` cases was audited.

### Actual OF14 architecture

`foamMultiRun` constructs:

```
pimpleMultiRegionControl pimple(runTime, solvers);
```

and executes the global outer loop with:

```
while (pimple.loop())
```

`pimpleMultiRegionControl` derives from `multiRegionSolutionControl`, whose `dict()` reads the root `system/fvSolution/PIMPLE` dictionary. Its `pimpleLoop::read()` obtains `nOuterCorrectors` from that root dictionary.

Therefore:

- root `system/fvSolution/PIMPLE/nOuterCorrectors` controls the effective **multi-region outer correctors**;
- root `nEnergyCorrectors` controls the effective **global energy-corrector loop**.

Each regional solver also owns a `pimpleNoLoopControl` based on that region's own `fvSolution`. For the metal region:

- `system/metal/fvSolution/PIMPLE/nCorrectors` controls the effective PISO pressure correctors per global outer iteration;
- regional `nNonOrthogonalCorrectors` controls non-orthogonal pressure corrections;
- regional `momentumPredictor`, pressure-reference entries, and solver-specific controls are effective there;
- linear-solver dictionaries/tolerances are regional.

The `nOuterCorrectors 1` entry in `system/metal/fvSolution` does **not** create or control a second outer loop under `foamMultiRun`.

Likewise, duplicated root `nCorrectors` and `nNonOrthogonalCorrectors` entries do not control the metal's internal pressure loop.

### Verification from actual logs

- B3: root outer=2 × metal nCorrectors=2 -> **4** p_rgh solve series.
- B5: 3 × 2 -> **6** series.
- B7: 4 × 2 -> **8** series.
- B8: 4 × 2 -> **8** series.

Energy:
- B3: outer=2 × energyCorrectors=1 -> **2** h/e series.
- B4: outer=2 × energyCorrectors=2 -> **4** h/e series.
- B5: outer=3 × energyCorrectors=1 -> **3** h/e series.

### Methodology correction

The V3/V5/V7 interpretation as 2/3/4 outer-corrector tests remains correct because those values were changed in the root dictionary, which is the effective multi-region outer-loop control.

The complete method should however distinguish:
- multi-region outer correctors: root;
- metal PISO/pressure correctors: regional;
- metal non-orthogonal correctors: regional;
- energy correctors: root.

The effective metal settings in the current cases are:
- nCorrectors = 2;
- nNonOrthogonalCorrectors = 0;
- momentumPredictor = no.

Thus root `nNonOrthogonalCorrectors = 1` must not be reported as the effective metal setting.

Historical cases were not modified. Future cases should avoid duplicated root entries that are not effective for the regional solver to reduce ambiguity.


## B9 topFixedFlux — closed-domain mass incompatibility

**[RUN-VERIFIED] [SOURCE-VERIFIED]**

B9 started correctly with `fixedFluxPressure` and the internal pressure reference, but aborted near t=0.016 s when T reached 1782.04 K, above the `icoTabulated rho(T)` upper limit of 1773.15 K. C9 completed successfully.

In OF14, `icoTabulated` uses `rho=rho(T)` and `psi=d(rho)/d(p)=0`. The `fluid` solver enforces continuity with `ddt(rho)+div(phi)=source(rho)`.

In a rigid, closed, impermeable domain with no mass source, total mass must remain constant. Cooling, however, makes the B density table demand an increase in density. Because pressure cannot modify rho and the top no longer permits mass flux, the model has no mechanism to accommodate thermal contraction.

This explains the rapid early growth of cumulative continuity error and the subsequent out-of-range temperature failure.

Historical B cases with `metalTop: totalPressure` allowed mass exchange through the top. The previously observed ~-970 J top advective-energy term should therefore be interpreted as evidence of that exchange, not as a fixed impermeable free surface.

For the current fixed-volume geometry without moving free-surface or shrinkage physics, C (`rhoConst` + beta buoyancy) is internally consistent. B would require additional volume-change, free-surface, feeding, or shrinkage physics. Artificially extending the rho table is not recommended merely to force B9 to continue.


## Later correction: B9 completed 10 s with the extended rho(T) table

**[RUN-VERIFIED BY USER OUTPUT] [INTERPRETATION UPDATE]**

The earlier interpretation that B9 could not continue as a closed-domain case was too strong. After diagnostically extending rho(T) beyond 1773.15 K, B9 completed the full 10 s.

Reported final values:
- metalTopPhiSum = 0;
- metalTop energyAdvectiveFlux = 0;
- metal_to_mold energyAdvectiveFlux ~ 7.3e-15 W;
- metalTop heatFlux = 36.603 W;
- metal_to_mold heatFlux = 342.301 W;
- total boundary heatFlux = 378.904 W;
- max Co ~ 0.0301;
- cumulative continuity = -0.0460268.

Updated interpretation:
1. fixedFluxPressure + slip does eliminate top mass/advective-energy flux;
2. B9 can evolve to 10 s if the rho(T) table covers the early thermal overshoot;
3. cumulative continuity is far worse than B5, indicating a significant mismatch between thermodynamic rho(T) and continuity;
4. cumulative continuity is not a literal final 4.6% mass loss; in OF14 it accumulates the normalized rho-vs-thermo.rho mismatch over corrections;
5. the original 1782.04 K failure should be treated as a table-range failure during an early overshoot, not proof of irreversible thermal runaway.

A full B9-vs-B5 transient comparison remains required after the run results are pushed.


## V9 metalTop fixedFlux — final comparative result

**[RUN-VERIFIED] [ANALYSIS-VERIFIED]**

B9-vs-B5 and C9-vs-C5 were compared over the full 0–10 s profiles, including boundary energy, metalTop phi, coupling, continuity, Uy, T, alphaL, vorticity, flowType, Darcy and p_rgh acceleration.

Reproducible summary:
- `analysis_results/v9_top_fixedflux/summary.md`
- analyzer: `analysis_tools/v9_top_fixedflux_analysis.py`

Main result:
- `fixedFluxPressure + slip` makes `metalTop` impermeable: B9 max |sum(phi)| = 2.54e-21 and integrated top advective energy ~0; C9 is exactly zero at stored precision.
- C9 remains physically very close to C5: median Uy differences ~1.1–2.9% horizontally and 1.76% vertically; final T RMSE <=0.15 K; mushy width changes +1.4%.
- B9 changes strongly relative to B5: median Uy differences ~56% (y20), 95% (y30), 112% (vertical); mushy width +15%; center-T RMSE 14.6 K.
- B5 had -970.358 J integrated top advective energy; B9 ~0. C5 had only +6.841 J; C9 0.
- B9 pressure residual contraction becomes extremely strong (median Rp~0.0021), but accumulated transient rho-vs-thermo.rho mismatch reaches -0.046; this is not a literal 4.6% final mass loss.
- C9 improves coupling and continuity without materially changing the physical solution.

Conclusion: historical `totalPressure` had negligible physical impact on C but major impact on B. Historical B-vs-C differences are therefore not a clean buoyancy-formulation comparison. For the current fixed-volume Quick-Cup model, C9 is the cleaner baseline for continued physical validation.

Caveat: B9 required a diagnostic linear rho(T) extension above 1773.15 K, so B9-vs-B5 is no longer a strict single-change test.


## V9 — causality of Uy reversals

**[ANALYSIS-VERIFIED]**

All resolved Uy sign reversals in B9 and C9 were correlated with alphaL, grad(rho), vorticity, flowType, Darcy acceleration and p_rgh acceleration.

Important methodological correction: B9 uses beta=0 in solidificationMeltingSource, so its buoyancy cannot be evaluated with phaseChangeBuoyancyAcceleration. For B9 the solver variable-density term was reconstructed as a_rho=-(gh/rho)grad(rho), with hRef=0 and gh=-9.81*y.

Result:
- B9 y30 mainly preserves the classical symmetric reversal pair in predominantly liquid metal. Across all resolved y30 crossings, a_rho is the largest of the sampled density/pressure/Darcy acceleration scales in 72% of samples; Darcy is never the largest. This supports a physical variable-density-convection origin.
- B9 y20 develops a transient secondary structure. Four resolved reversals already occur at 5 s while liquid; at 10 s all four lie near alphaL~0.94. The outer 10-s reversals have strong vorticity and large Darcy magnitude; the inner reversals show near cancellation a_rho,y ~ -0.073 and a_p,y ~ +0.0735 m/s2, with comparable Darcy magnitude. The structure is symmetric and systematic rather than consistent with simple random numerical noise.
- B9 centerline vertical Uy reversals occur, but centerline vorticity is nearly zero. They should not be called additional vortices/cells without 2-D fields.
- C9 keeps the simpler two-cell structure. Its late cell boundaries are also strongly influenced by Darcy as the phase-change region advances.
- The earlier B9 y30 interpretation is corrected: several tiny extra sign flips detected without a velocity threshold occur near Uy=0 and should not be counted as dynamically resolved cells.

Limitation: versioned results contain line profiles but not the complete final volumetric fields, so geometric closure of each cell by streamlines cannot be proven from the current repository.

Reproducible summary: analysis_results/v9_flow_causality/summary.md
Analyzer: analysis_tools/v9_flow_causality_analysis.py


## 2026-10-03 — V14-CONFIG-001 — Explicit pressure reference + direct topFlow requested by supervisor

**Objective.** Create V14 as a controlled test derived from V11, retaining the `fixedFluxPressure + slip` top boundary while applying the requested pressure-reference and direct `metalTop` flow-recording configuration.

**New cases.**
- `B14_topFixedFlux_explicitRef`
- `C14_topFixedFlux_explicitRef`

**Controlled changes relative to V11.**
- `system/metal/fvSolution`: `pRefPoint (0.02 0.04 0.005)`;
- `system/metal/fvSolution`: `pRefValue 1e5`;
- `system/metal/fvSolution`: add `nEnergyCorrectors 2`;
- `system/functions`: add `topFlow`, a `surfaceFieldValue` on `metalTop`, with `operation none`, `writeFields true`, fields `(U phi)`, and `writeControl writeTime`.

**Pressure boundary.** `0/metal/p_rgh` remains unchanged: `metalTop = fixedFluxPressure` with `value $internalField`.

**OF14 compatibility finding.** The metal region uses the modular `fluid` solver. In OpenFOAM Foundation v14, `fluid::thermophysicalPredictor()` assembles and solves one energy equation per call and does not read `nEnergyCorrectors`. That keyword is implemented by `multiphaseEuler`. The requested setting is retained exactly for traceability, but V14 must audit the run log to determine its actual operational effect rather than assuming that it changes the number of energy solves.

**Startup risk to verify.** The requested point `(0.02 0.04 0.005)` lies on the geometric top plane. The pressure-reference routine must associate the reference point uniquely with a cell, so the first V14 check is whether OF14 accepts this point without a reference-cell error.

**Preparation verification.** The two new cases contain input/documentation files only: 138 blobs total and zero inherited `postProcessing/`, `logs/`, `log.*`, or solved-time directories.

**Status.** CONFIG-VERIFIED / NOT-RUN. Pending: run B14/C14 to 10 s and compare directly with B11/C11 for face-wise `phi`, `sum(abs(phi))`, T, alphaL, Courant number, continuity, and the effective number of energy solves.


---

## 2026-10-03 — V14-RUN-002 — Impermeability and explicit pressure-reference validation

**[RUN-VERIFIED] [GIT-VERIFIED] [ANALYSIS-VERIFIED]**

`B14_topFixedFlux_explicitRef` and `C14_topFixedFlux_explicitRef` were run to **10 s** and both completed successfully. OpenFOAM 14 accepted `pRefPoint (0.02 0.04 0.005)` without a reference-cell error.

### Face-wise metalTop audit

`topFlow` recorded all **80 faces** of `metalTop`. At representative times 0.1, 5 and 10 s:

- B14: `max |Uy| = 0`; `max |phi| = 8.47033e-22` at 0.1 s and 0 at 5/10 s.
- C14: `max |Uy| = 0`; `max |phi| = 0` at all three times.
- Non-zero tangential `Ux` remains, as expected for a `slip` boundary.

Across all **100 writeTimes from 0.1 to 10 s**:

- B14: maximum `sum(abs(phi)) = 8.47033e-22`;
- C14: `sum(abs(phi)) = 0` at every stored writeTime.

This rules out hidden cancellation between local inflow and outflow. The `fixedFluxPressure + slip` top remains impermeable face by face.

### V11 -> V14 comparison

Central probe, 10,001 steps:

- B: `max |ΔT| = 0.01 K`; `max |ΔalphaL| = 7e-6`; T(10 s)=1470.07 K in both; alphaL(10 s)=0.988421 (B11) and 0.988414 (B14).
- C: T is identical at stored precision for the full series; `max |ΔalphaL| = 1e-6`; T(10 s)=1464.19 K and alphaL(10 s)=0.964815 in both.
- Velocity differences are small and do not indicate a change of physical regime.

### Regional nEnergyCorrectors

V11 and V14 produce the same energy-series structure in `foamLog`: `h_0..2` and `e_0..2`, with the same number of pressure series. Therefore the `nEnergyCorrectors 2` entry added to `system/metal/fvSolution` **did not add energy corrections** under the current `foamMultiRun` architecture. The effective multi-region energy loop remains controlled by the global/root setting rather than the regional duplicate.

### Conclusion

V14 does not introduce new physics relative to V11. It is validated as the **supervisor-reference case**: it preserves V11's physically consistent impermeable top and demonstrates that the requested explicit pressure reference does not materially change T, alphaL or the flow pattern.

**Status:** ✅ RUN-VERIFIED / ANALYSIS-VERIFIED.


---

## 2026-10-03 — V14-BC-003 — B14/C14 comparison with common impermeable top

**[RUN-VERIFIED] [GIT-VERIFIED] [ANALYSIS-VERIFIED]**

B14 and C14 were compared after removing the historical `metalTop` flux inconsistency. Both cases reached 10 s and have a face-wise impermeable top.

Key results:

- maximum `sum(abs(phi))` on `metalTop`: B14 = 8.47033e-22; C14 = 0;
- maximum Courant: B14 = 0.0673434; C14 = 0.0650864;
- final cumulative continuity: B14 = **-3.10190e-02**; C14 = **4.44346e-13**;
- central T at 10 s: B14 = 1470.07 K; C14 = 1464.19 K;
- volume-mean liquid fraction: B14 = 0.9606902; C14 = 0.9620593;
- total boundary heat power: B14 = 316.1799 W; C14 = 313.9750 W;
- boundary advective power: approximately zero in both.

At 10 s the profiles still show substantial velocity differences and moderate thermal differences. At y=20 mm, for example, B14/C14 RMSE is 3.7677e-3 m/s for Uy and 3.2461 K for T; at y=10 mm it is 5.2355e-3 m/s and 7.8166 K.

**Interpretation:** because boundary heat extraction is similar and the top no longer permits mass flux, the B/C separation is mainly associated with the density/buoyancy formulation. In the current rigid, fixed-volume, impermeable domain, B's rho(T) formulation accumulates a major continuity mismatch, whereas C's constant-density + explicit-buoyancy formulation preserves continuity near machine precision.

**Current decision:** C14 is recommended as the physical/production baseline for the thesis's rigid Quick-Cup model. B14 is retained as a controlled sensitivity/alternative-formulation case and may become physically relevant again if shrinkage, feeding, a moving free surface, or other volume-change physics is introduced.

Reproducible summary: `analysis_results/v14_bc_comparison/summary.md`.

**Status:** ✅ ANALYSIS-VERIFIED. No V15 was created.


---

## 2026-10-03 — ENERGY-004 — C11 with 2 effective energy correctors

**[RUN-VERIFIED] [GIT-VERIFIED] [ANALYSIS-VERIFIED]**

`C11_energy2_test` was run from `C11_topFixedFlux_airGapOF14`, changing only root `system/fvSolution/PIMPLE/nEnergyCorrectors = 2`.

The case reached 10 s and generated `h_0..5` and `e_0..5`, confirming 6 energy solves per timestep (3 outer correctors × 2 energy correctors). Normal C11 generates `h_0..2` and `e_0..2`.

Comparison:
- central T(t): RMSE 0 K; byte-identical 10,001-point file;
- central alphaL: RMSE 4.80e-8; max |Δ| 1e-6;
- central U: RMSE 7.70e-9 m/s; max |Δ| 1e-7 m/s;
- mean liquid fraction: RMSE 2.22e-8; max |Δ| 1e-7;
- y=20 mm profile at 10 s: T and alphaL identical; Uy RMSE 4.04e-9 m/s;
- max Courant 0.0650864 in both;
- final continuity: 4.44517e-13 (C11) vs 4.58617e-13 (energy2);
- executionTime: 289.433 s vs 387.542 s;
- clockTime: 302 s vs 398 s.

The second corrector reduces the enthalpy residual further but does not change the physical solution within stored resolution. It is classified as extra numerical convergence with additional cost.

**C14 correction:** C14's `nEnergyCorrectors 2` is located in `system/metal/fvSolution` and does not control the global energy loop. C14 generated only `h_0..2/e_0..2`; therefore it had 1 effective energy corrector.

**Decision:** retain 1 energy corrector in the current baseline.

Results: `cases_controlled_buoyancy/C11_energy2_test/`.  
Summary: `analysis_results/c11_energy2_test/summary.md`.

**Status:** ✅ RUN-VERIFIED / ANALYSIS-VERIFIED.

---

## 2026-10-08 — B11-E2-PREFLIGHT-005 — Remove inherited outputs from controlled test

**[GIT-VERIFIED] [OPEN / NOT RUN-VERIFIED]**

The October 5 addition of `B11_energy2_test` accidentally tracked B11's previously generated `logs/`, `postProcessing/` and `log.*`. The central temperature probe had exactly the same Git blob SHA in the parent and test: `8e5b4c39dade992897df864f8d4f3dce135dcf24`. These copied files do **not** establish an independent run.

An input-blob comparison under `0/`, `constant/` and `system/` confirmed that **only root `system/fvSolution` differs**, setting `nEnergyCorrectors=2`. The test's tracked tree was rebuilt using only inputs, `Allrun`, `Allclean`, and test-specific notes. The original B11 results remain untouched.

**Pending:** run B11-energy2 locally with OF14; verify six energy solves per timestep; compare T, U, alphaL, face-wise `metalTop` flux, continuity, residuals, Courant and computational cost against B11. Do not confuse this open B-family test with the already verified `C11_energy2_test`.

The current experimental-validation baseline remains C14. The J0 provenance gate remains OPEN.

---

## 2026-10-08 — RUN-PROTOCOL-006 — Complete case roster and independent cross-run update protocol

**[GIT-VERIFIED] [OPEN / CONSOLIDATION PENDING]**

The `cases_controlled_buoyancy/` directory has 30 case folders. `analysis_results/full_campaign_audit/` contains only the historical V3–V13 campaign: 26 `case_metrics.csv` case rows, 13 B/C pairs in `bc_pair_metrics.csv`, and 104 profile rows in `profile_inventory.csv`. It omits B14/C14 and C11-energy2, despite their separate RUN-VERIFIED/ANALYSIS-VERIFIED summaries. B11-energy2 remains PREPARED_NOT_RUN.

Added the independent `RUN_MASTER_PROTOCOL.md`, 30-case `RUN_CASE_REGISTRY.csv`, read-only `analysis_tools/check_run_registry.py`, historical scope README, and entry-point references in agent, guide and validation matrix. Coverage checks do not treat copied outputs as a new run.

**Open:** extend/reverify the campaign metric generator before including the three later verified cases in all consolidated CSVs. No physical results were recomputed or changed in this documentation-only update. J0/G1 experimental validation remains open.

**Decision:** every future simulation and MAZAPÁN flow must update the inventory and audit coverage without relying on an external master repository.


---

## 2026-10-08 — AGENTS-007 — Scientific agents, postprocessing interpretation and local live watcher

**[GIT-VERIFIED] [CONFIG-VERIFIED / RUNNER PENDING]**

Four specialized agent profiles were introduced under .github/agents/ for runtime observations, postprocessing forensics, independent physics/numerical checks and documentation synchronization. Added analysis_tools/live_run_watch.py, analysis_tools/audit_postprocessing_config.py and a scheduled/manual/push GitHub workflow. The local log watcher only becomes active when explicitly launched beside a live solver; GitHub checks repository contents, not local runtime.

Created POSTPROCESSING_FIELD_GUIDE_ES.md with actual V14 definitions, units, sources and interpretation limitations; updated both command manuals and case guide. No physical solver input or historical output was changed.

**Caution:** the initial GitHub Actions invocation may fail before a runner starts. Do not claim verified automation until a successful job has been observed. Historical campaign CSVs still omit B14/C14 and C11-energy2.


### 2026-10-08 — AGENTS-008 — Guarded local monitored run launcher and actual Actions status

**[GIT-VERIFIED] [RUNNER NOT VERIFIED]**

Added analysis_tools/run_with_agents.py: launches a prepared case through its existing Allrun and starts a read-only observer thread; refuses cases with pre-existing output unless explicitly overridden, offers --dry-run, and saves a screening report. Full MAZAPÁN remains required.

The newly scheduled GitHub Actions workflow failed in two attempted runs with no executed steps in returned job data. Hosted automatic auditing is therefore NOT yet confirmed operational; investigate runner/Actions availability in GitHub UI. This does not prevent local live monitoring via the guarded launcher.


### 2026-10-08 — AGENTS-009 — Complete V14 functionObject documentation coverage

**[GIT-VERIFIED] [STATIC-CONFIG AUDIT]**

Four C14 dictionaries declare 37 function objects. The initial field guide explicitly named 20; a comprehensive inventory has now been added for system/functions (2), researchDiagnostics (29), lineProfiles (2) and momentumPostProcessing (4), with role, type, meaning and limitations.

The static auditor now requires every declared function-object name to appear in the scientific field guide. Name coverage alone does not prove correct scientific explanation, successful runtime execution or physical validation; those require independent source/result analysis.

---

## 2026-10-08 — AGENTS-010 — Architecture correction: user's laptop runs CFD; GitHub audits only after push

**[GIT-VERIFIED] [WORKFLOW NOT YET RUN-VERIFIED]**

Clarified explicit user ownership: all OpenFOAM simulations are carried out on the laptop, and completed outputs are pushed to GitHub. Removed mistakenly introduced local simulation launchers (`run_with_agents.py`, `live_run_watch.py`). Updated four agent-role specifications for post-push committed-evidence inspection and added `analysis_tools/audit_pushed_results.py`, which reads stored logs/postProcessing without starting CFD and generates review artifacts when Actions jobs successfully run.

Aligned ES/EN manuals, postprocessing guide, protocol, agent index and README. No scientific cases or historical run outputs were modified. Agent instruction files are not autonomous LLM processes merely because they exist.

---

## 2026-10-08 — RESEARCH-011 — Supervisor meeting; clean C15/C16 cases and 3D/free-surface roadmap

**[GIT-VERIFIED INPUTS] [PREPARED_NOT_RUN] [NO CFD EXECUTION]**

Following the supervisor meeting, 3D development from C14 became a near-term goal. Initial studies will probe adaptive time-stepping and phase-fraction relaxation. In C14, `maxCo=0.25`, root `relaxationFactors=1.0` and the distinct solidificationMelting `relax=0.1` were verified. New independent variants of C14 were prepared with clean inputs only: **C15_adaptiveDt_fromC14** changes `system/controlDict` (adaptive and 0.1 s physical output schedule); **C16_phaseRelax025_fromC14** changes only `constant/metal/fvModels` (phase `relax:0.1→0.25`). Neither has been run.

The parallel plans include a genuine 3D mesh (C14 remains an 80x80x1 planar `empty` model) and, separately, a metal-air free-surface and mass-conserving solidification-shrinkage/feeding B-family formulation. Investigate OF14 multiphase/solidification model compatibility before specifying new solver inputs; do not infer B14 mismatch is cured by an open pressure boundary. Both experimental J0/G1 gates remain open.

All runs are performed exclusively on the researcher's laptop. GitHub performs post-push audits. See NEXT_RESEARCH_ROADMAP_ES.md.
