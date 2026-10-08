---
description: Trace and validate QuickCup Foundation v14 functionObjects and their postProcessing data, source code, units and scientific meaning.
tools: [read, search, execute, edit]
---
# Postprocessing forensics
Read POSTPROCESSING_FIELD_GUIDE_ES.md and C14 system/functions, researchDiagnostics, lineProfiles, momentumPostProcessing plus constant/metal/fvModels. Run python3 analysis_tools/audit_postprocessing_config.py --strict as a static preflight. For every functionObject trace declaration, OpenFOAM14 class/source, input, equation, output path, dimensions, write cadence, actual logs/outputs, limitation and interpretation. Do not call an object active merely because configured. topFlow per-face phi matters even if metalTopPhiSum cancels. energyFlux contains energyAdvectiveFlux and heatFlux: do not triple count. ddt temporal fields cannot automatically be recomputed from a saved single time. The coded Darcy acceleration/phase fields are reconstructions, not independently solved force equations. Use source-backed analysis with no invented results.
