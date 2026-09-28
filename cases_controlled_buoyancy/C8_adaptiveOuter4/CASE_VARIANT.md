# C8_adaptiveOuter4

Parent case: `C6_adaptiveDt`.

Controlled change: root-level `system/fvSolution` `nOuterCorrectors` changed from 3 to 4.

Purpose: test whether the V6 adaptive-timestep flow differences are caused by insufficient outer PIMPLE coupling rather than timestep size itself.

Everything else is inherited unchanged from the parent input case. No calculated results from the parent were copied.
