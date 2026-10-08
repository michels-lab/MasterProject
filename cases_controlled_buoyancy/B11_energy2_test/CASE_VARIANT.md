# CASE_VARIANT — B11_energy2_test

**Parent:** `B11_topFixedFlux_airGapOF14`
**Status (2026-10-08):** CLEAN INPUTS / PREPARED / NOT RUN-VERIFIED.

## Controlled experiment

Only root `system/fvSolution/PIMPLE/nEnergyCorrectors` changes from 1 to 2.
Global `nOuterCorrectors = 3`, so the run is expected to show six energy equation solves per timestep (`h_0..h_5` and `e_0..e_5`) if the change is effective.

All input files under `0/`, `constant/` and `system/` were checked against B11 by Git blob SHA: the only input difference is root `system/fvSolution`.

## Evidence warning

The original copied directory included B11's pre-existing outputs: both central temperature probe files had Git blob SHA `8e5b4c39dade992897df864f8d4f3dce135dcf24`. Such inherited files cannot validate B11-energy2. They were removed from the variant's tracked tree on 2026-10-08; source B11 results remain intact.

A fresh local OpenFOAM Foundation 14 run and a documented B11-vs-energy2 analysis are still required. This variant does not create a new V generation, change material physics or supersede C14.
