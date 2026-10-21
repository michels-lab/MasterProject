# File steward: repository file audit

All tracked files classified; Markdown/text docs inspected with size cap. Binary/research-content validity and untracked files not assessed.
No file is auto-deleted or declared unused.

## Coverage

Tracked: 38760; classified: 38756; readable documents: 126; above read cap: 0; findings: 118.

## File roles

| Role | Count |
|---|---:|
| agent | 6 |
| analysis_tool | 1 |
| bitacora | 5 |
| config | 7 |
| data | 19 |
| document | 99 |
| index | 22 |
| license | 1 |
| simulation_case_file | 92 |
| simulation_input | 2570 |
| simulation_log | 3142 |
| simulation_output | 32610 |
| source | 41 |
| test | 10 |
| unknown | 115 |
| web_ui | 1 |
| workflow | 15 |

## Findings (human review required)

- **CONFIRMED / BROKEN_RELATIVE_LINK** PROJECT_AUDIT_LOG.md: Missing: docs/granada/V15_V16_SOURCE_EVIDENCE_20261020.md. Next: Fix link or restore target (ID 7aa831f782018e41)
- **REVIEW / DUPLICATE_DOC_CONTENT** cases_controlled_buoyancy/B11_energy2_test/CASE_VARIANT.md: Identical tracked text: cases_controlled_buoyancy/B11_energy2_test/CASE_VARIANT.md, cases_controlled_buoyancy/B11_topFixedFlux_airGapOF14/CASE_VARIANT.md. Next: Confirm aliases or translated/historical copies before consolidation (ID 4790b4f6be1b7e0f)
- **REVIEW / DUPLICATE_DOC_CONTENT** cases_controlled_buoyancy/C11_energy2_test/CASE_VARIANT.md: Identical tracked text: cases_controlled_buoyancy/C11_energy2_test/CASE_VARIANT.md, cases_controlled_buoyancy/C11_topFixedFlux_airGapOF14/CASE_VARIANT.md. Next: Confirm aliases or translated/historical copies before consolidation (ID c4728d9d269368a5)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 921b247eab730699)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/U: No reliable purpose category from path. Next: Declare role after reviewing usage (ID f18afb9ccc23c764)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/alphat: No reliable purpose category from path. Next: Declare role after reviewing usage (ID cf16c3f9efd56671)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/epsilon: No reliable purpose category from path. Next: Declare role after reviewing usage (ID b1952aebd02e69be)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/k: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 8ee17050c3045323)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/nut: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4b507afe4eaf7257)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/omega: No reliable purpose category from path. Next: Declare role after reviewing usage (ID c9729d76539bd278)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/p: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 849b1a5c94c07491)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/metal/p_rgh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 523e7215813b455d)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/0/mold/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID d93274b8690f4a8e)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/Allclean: No reliable purpose category from path. Next: Declare role after reviewing usage (ID df43a560d552cc10)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/Allrun: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 5287113aa822695e)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/metal/fvModels: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 52fc79735d0be78e)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/metal/g: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6a1569123ea74e15)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/metal/materials/castIron: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 44bbbb66606fd2a3)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/metal/momentumTransport: No reliable purpose category from path. Next: Declare role after reviewing usage (ID a3212cf3b9cb7f64)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/metal/pRef: No reliable purpose category from path. Next: Declare role after reviewing usage (ID fbaf39d61109140f)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/metal/physicalProperties: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 1f71e430d6556ff7)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/mold/materials/silica: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 467fa6716b15375d)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/mold/materials/steel4140: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 35af006cd3957e7e)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/mold/materials/steel4140cons: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 9678332df06fa8a4)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/constant/mold/physicalProperties: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 670f21187797446d)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/log.blockMesh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 24d9a48fd2e1e4ed)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/log.foamMultiRun: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 31a64527bbeaf0ef)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/log.splitMeshRegions: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4681a233e9142909)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/postProcessing/metal/temperatureProbe/0/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6cae9712e31c8aa6)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/blockMeshDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID baad0d6508674a67)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/controlDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 17819d17b8e6c9be)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/createZonesDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 2024fa94ded7a5fd)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/functions: No reliable purpose category from path. Next: Declare role after reviewing usage (ID cd8fca6c9155f36b)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID d14c3d16afc557ca)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/metal/fvSchemes: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 71ace997964ed29c)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/metal/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID aef34948c2cecc18)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/mold/fvSchemes: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 955e83ad50bcda5e)
- **REVIEW / UNKNOWN_PURPOSE** cleanproy/system/mold/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 37593339720d15ed)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 06784237364bc4e5)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/U: No reliable purpose category from path. Next: Declare role after reviewing usage (ID fd1147a65908afa5)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/alphat: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 3fe7a286800ad6f1)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/epsilon: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 311cf45c5f5da4ec)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/k: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 2224c04bf351a7ef)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/nut: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 8a7c60733fe222e9)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/omega: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 06c3489412bbc945)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/p: No reliable purpose category from path. Next: Declare role after reviewing usage (ID ef306999c1253008)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/0/p_rgh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID aee1c29877d63686)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/Allclean: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4333fabb9a271563)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/Allrun: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4d4288ee18f5c448)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/constant/fvModels: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 690c0ce3e2b60442)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/constant/g: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 86d0a17f3a9209e7)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/constant/momentumTransport: No reliable purpose category from path. Next: Declare role after reviewing usage (ID a262eae8b6d79b07)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/constant/pRef: No reliable purpose category from path. Next: Declare role after reviewing usage (ID cd62acadb69bde0e)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/constant/physicalProperties: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 575050cdb92c4b51)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/log.blockMesh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID fb9b02f8dfd31bd4)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/log.foamRun: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4435d5da9789e313)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/postProcessing/temperatureProbe/0/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6aa8bc5302a524e0)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/system/blockMeshDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 7250c39d2572e65d)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/system/controlDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4638c535e179811e)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/system/functions: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4e84e4d8f154feb7)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/system/fvSchemes: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 9e4b27e491bcb803)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/bcFourier/system/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4fca1001350c1ddf)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID db48d4aae69d7821)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/U: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 51361afa46da578a)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/alphat: No reliable purpose category from path. Next: Declare role after reviewing usage (ID b54d514d7226fe8c)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/epsilon: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 2c516fe31cf845fe)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/k: No reliable purpose category from path. Next: Declare role after reviewing usage (ID be55fe59be16cb15)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/nut: No reliable purpose category from path. Next: Declare role after reviewing usage (ID a1e41f9b012edf6b)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/omega: No reliable purpose category from path. Next: Declare role after reviewing usage (ID dcf3c3b227d4cbd4)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/p: No reliable purpose category from path. Next: Declare role after reviewing usage (ID d6696892e47554b2)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/metal/p_rgh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 8566e8d0be1a5224)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/0/mold/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 10c635c3d4cb8cab)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/Allclean: No reliable purpose category from path. Next: Declare role after reviewing usage (ID de6c3e87a11a76db)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/Allrun: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 06bcad537776d187)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/metal/fvModels: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 86d39dd1fbd65bd5)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/metal/g: No reliable purpose category from path. Next: Declare role after reviewing usage (ID bf33ec84f19ae6c7)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/metal/materials/castIron: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 50b8e372f310caff)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/metal/momentumTransport: No reliable purpose category from path. Next: Declare role after reviewing usage (ID a6ae885aadfd4c04)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/metal/pRef: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 5d5f4abff0a1ea3f)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/metal/physicalProperties: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 8aecfc920c39d704)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/mold/materials/silica: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 8cb02364a225a95f)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/mold/materials/steel4140: No reliable purpose category from path. Next: Declare role after reviewing usage (ID b6fb449e07c36608)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/mold/materials/steel4140cons: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 51b7d132d74ce71e)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/constant/mold/physicalProperties: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 2a6725427e23215a)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/log.blockMesh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID b602866582b4bda3)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/log.createZones: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 84c99525f48b4dd9)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/log.foamMultiRun: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 1fda8f7fe4f85c92)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/log.splitMeshRegions: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 80e3e440a966a2ef)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/postProcessing/metal/temperatureProbe/0/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 69490dfb5f44dc3a)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/blockMeshDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 7c102c43dd30e129)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/controlDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID dbeb3bd8fd4dc178)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/createZonesDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 96e723f47532d09b)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/functions: No reliable purpose category from path. Next: Declare role after reviewing usage (ID a90ce4c3f9941565)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 903d702f90cde4e6)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/metal/fvSchemes: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 25dcb643d9f8c919)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/metal/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 71a1068e63a9971f)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/mold/fvSchemes: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6e6d926a215dafe0)
- **REVIEW / UNKNOWN_PURPOSE** doctor_original/cht/system/mold/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID ad107d0b6a66ad37)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/T: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 1606844240338591)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/U: No reliable purpose category from path. Next: Declare role after reviewing usage (ID ca8f3ced7c5dc109)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/alpha.water: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6da9e7caad14f922)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/epsilon: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6c0e8fefa0aafd92)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/k: No reliable purpose category from path. Next: Declare role after reviewing usage (ID d730b2c99f3b6a78)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/nuTilda: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 3a260a548cbe834e)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/nut: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 3c1dd374dab9296e)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/omega: No reliable purpose category from path. Next: Declare role after reviewing usage (ID c5a2b3ac0c5ef4f6)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/p: No reliable purpose category from path. Next: Declare role after reviewing usage (ID b4ba018a79bea5f9)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/0/p_rgh: No reliable purpose category from path. Next: Declare role after reviewing usage (ID baf3d719d4a21cf6)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/constant/fvModels: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 3fcb8b663577c36e)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/constant/g: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 22c2d34452e04f51)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/constant/momentumTransport: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 5c6b445c585ea1de)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/constant/phaseProperties: No reliable purpose category from path. Next: Declare role after reviewing usage (ID c6ccb2b36d558c1e)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/constant/physicalProperties.air: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 4b20d7c38eddd222)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/constant/physicalProperties.water: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 029f7d6b23a40221)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/system/blockMeshDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 468fff4ea29a84c2)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/system/controlDict: No reliable purpose category from path. Next: Declare role after reviewing usage (ID c0086dc2d013e178)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/system/fvSchemes: No reliable purpose category from path. Next: Declare role after reviewing usage (ID f23359b3492691ef)
- **REVIEW / UNKNOWN_PURPOSE** freesurface/FS-C01/system/fvSolution: No reliable purpose category from path. Next: Declare role after reviewing usage (ID 6b368bdf0d07f7c2)

Complete path → purpose/role/certainty list lives in FILE_GOVERNANCE.json. SUMMARY.json has counts only for master polling.
A dated file, duplicate, or suspicious name is an **investigation candidate**, not unwanted material.
No historical science cases, audit logs or evidence may be deleted automatically.
