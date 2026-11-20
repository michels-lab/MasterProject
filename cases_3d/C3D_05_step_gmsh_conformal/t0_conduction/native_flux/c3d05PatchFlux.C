/* C3D-05 B T0 diagnostic: EXACT Foundation14 isotropic solid transport q().
 * Original physics in OpenFOAM/OpenFOAM-14:
 * src/ThermophysicalTransportModels/solid/isotropic/isotropic.C:
 * q() = -fvc::interpolate(alpha*kappa)*fvc::snGrad(thermo.T())
 * Output each interface face with outward normal q [W/m2].
 * NOT a CFD run, NOT an experimental or flux-continuity PASS.
 */
#include "fvCFD.H"
#include "timeSelector.H"
#include "solidThermo.H"
#include "solidThermophysicalTransportModel.H"
#include <cstdio>
#include <cmath>

using namespace Foam;

int main(int argc, char *argv[])
{
    timeSelector::addOptions();
    argList::addOption("region", "region", "Solid region metal or mold");
    argList::addOption("patch", "name", "Interface patch name");
    argList::addOption("out", "path", "Exclusive CSV result path, no overwrite");
    #include "setRootCaseNoFunctionObjects.H"
    #include "createTimeNoFunctionObjects.H"

    word regionName;
    word patchName;
    fileName outputName;
    if (!args.optionReadIfPresent("region", regionName)
     || !args.optionReadIfPresent("patch", patchName)
     || !args.optionReadIfPresent("out", outputName))
    {
        FatalErrorInFunction << "Required -region -patch -out"
            << exit(FatalError);
    }
    if (!((regionName == "metal" && patchName == "metal_to_mold")
       || (regionName == "mold" && patchName == "mold_to_metal")))
    {
        FatalErrorInFunction << "Refuse non-interface patch/region pair"
            << exit(FatalError);
    }

    const instantList selectedTimes = timeSelector::select0(runTime, args);
    if (selectedTimes.size() < 2)
    {
        FatalErrorInFunction << "No valid transient time series selected"
            << exit(FatalError);
    }

    fvMesh mesh
    (
        IOobject(regionName, runTime.name(), runTime, IOobject::MUST_READ)
    );
    const label patchIndex = mesh.boundaryMesh().findPatchID(patchName);
    if (patchIndex < 0)
    {
        FatalErrorInFunction << "Missing native interface patch " << patchName
            << exit(FatalError);
    }
    if (mesh.boundaryMesh()[patchIndex].size() != 12636)
    {
        FatalErrorInFunction << "Unexpected C3D-05 accepted interface face count"
            << exit(FatalError);
    }

    // C11 exclusive-mode "wx" on WSL/Linux prevents overwriting solver evidence.
    FILE* fp = std::fopen(outputName.c_str(), "wx");
    if (!fp)
    {
        FatalErrorInFunction << "Refusing existing or unwritable face CSV "
            << outputName << exit(FatalError);
    }
    std::fprintf(fp,
        "time_s,face_local,center_x_m,center_y_m,center_z_m,area_m2,"
        "normal_x,normal_y,normal_z,q_out_W_m2\n");

    forAll(selectedTimes, timei)
    {
        runTime.setTime(selectedTimes[timei], timei);
        if (mesh.readUpdate() != polyMesh::UNCHANGED)
        {
            std::fclose(fp);
            FatalErrorInFunction << "Mesh changed during T0: cannot pair faces"
                << exit(FatalError);
        }

        // Reconstruct the same Foundation14 solidThermo and solid transport
        // model used by foamMultiRun, at the actual saved field time.
        autoPtr<solidThermo> thermo = solidThermo::New(mesh);
        autoPtr<solidThermophysicalTransportModel> transport =
            solidThermophysicalTransportModel::New(thermo());

        // Isotropic q is an actual native patch-normal field in [W/m2].
        const tmp<surfaceScalarField> tq = transport->q();
        const fvsPatchScalarField& qs = tq().boundaryField()[patchIndex];
        const vectorField& cs = mesh.Cf().boundaryField()[patchIndex];
        const vectorField& areas = mesh.Sf().boundaryField()[patchIndex];

        if (qs.size() != mesh.boundaryMesh()[patchIndex].size())
        {
            std::fclose(fp);
            FatalErrorInFunction << "q patch face count mismatch"
                << exit(FatalError);
        }

        forAll(qs, facei)
        {
            const scalar a = mag(areas[facei]);
            const vector n = areas[facei]/a;
            const vector c = cs[facei];
            const scalar q = qs[facei];
            if (!(a > 0) || !std::isfinite(a) || !std::isfinite(q)
             || !std::isfinite(c.x()) || !std::isfinite(c.y())
             || !std::isfinite(c.z()))
            {
                std::fclose(fp);
                FatalErrorInFunction << "Nonfinite native patch geometry or q"
                    << exit(FatalError);
            }
            std::fprintf(fp,
                "%.17g,%lld,%.17g,%.17g,%.17g,%.17g,"
                "%.17g,%.17g,%.17g,%.17g\n",
                runTime.value(), static_cast<long long>(facei),
                c.x(), c.y(), c.z(), a,
                n.x(), n.y(), n.z(), q);
        }
        Info<< "Extracted actual isotropic q on "
            << regionName << " " << patchName << " time="
            << runTime.value() << " faces=" << qs.size() << endl;
    }
    if (std::fclose(fp) != 0)
    {
        FatalErrorInFunction << "Cannot finalize patch flux CSV"
            << exit(FatalError);
    }
    Info<< "T0_NATIVE_FACE_FLUX_EXTRACTED_NOT_VALIDATED " << outputName << endl;
    return 0;
}
