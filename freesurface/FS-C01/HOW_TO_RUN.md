# FS-C01 | VOF water-air hydrodynamic analogue (B-FS-01 stage)

This deliberately does NOT model iron, shrinkage, latent heat or CHT.
OpenFOAM Foundation v14 is required. In this new staged directory:

    blockMesh
    checkMesh
    foamRun

Do not invoke Allclean/Allrun in an original QuickCup case.
Only a successful real Ubuntu run can establish runtime viability.
Check mesh patch orientation, alpha bounds, mass closure and solver log.
The postProcessing/waterVolume/0/volFieldValue.dat file is the expected
volume reduction, NOT an integral of rho*alpha, and NOT a mass balance.
Use the audit subcommand on the actual output once generated.
