/* C3D-05 B T0: direct face-wise heat-flux diagnostic in Foundation14.
 * EXACT isotropic solid transport (OpenFOAM/OpenFOAM-14):
 * src/ThermophysicalTransportModels/solid/isotropic/isotropic.C
 * q() = -interpolate(kappa)*snGrad(T), oriented outward per patch.
 *
 * CRITICAL: both meshes and both thermos stay registered at the SAME instant.
 * mappedWall/coupledTemperature may require neighbour region lookup during
 * q()/boundary-field evaluation. Never run this on one region in isolation.
 *
 * This tool does NOT solve CFD, change meshes or validate flux continuity.
 */
#include "fvMesh.H"
#include "surfaceFields.H"
#include "Time.H"
#include "argList.H"
#include "timeSelector.H"
#include "solidThermo.H"
#include "solidThermophysicalTransportModel.H"
#include <cstdio>
#include <cmath>

using namespace Foam;

static label interfacePatch(const fvMesh& mesh, const word& patchName)
{
    const label patchi = mesh.poly().boundary().findPatchID(patchName);
    if (patchi < 0 || mesh.poly().boundary()[patchi].size() != 12636)
    {
        FatalErrorInFunction
            << "C3D05 accepted interface missing or count != 12636: "
            << patchName << exit(FatalError);
    }
    return patchi;
}

static void writeFaceFlux
(
    FILE* fp,
    const scalar t,
    const fvMesh& mesh,
    const label patchi,
    const solidThermophysicalTransportModel& transport
)
{
    // Use Foundation14's exact solid-isotropic flux, not wallHeatFlux.
    const tmp<surfaceScalarField> qAll = transport.q();
    const fvsPatchScalarField& q = qAll().boundaryField()[patchi];
    const fvsPatchVectorField& faces = mesh.Sf().boundaryField()[patchi];
    const fvsPatchVectorField& centers = mesh.Cf().boundaryField()[patchi];

    if (q.size() != 12636 || faces.size() != q.size()
        || centers.size() != q.size())
    {
        FatalErrorInFunction << "Native interface q/geometry shape mismatch"
            << exit(FatalError);
    }

    forAll(q, facei)
    {
        const scalar area = mag(faces[facei]);
        const vector n = faces[facei]/area;
        const vector c = centers[facei];
        const scalar heat = q[facei];
        if (!(area > 0) || !std::isfinite(area) || !std::isfinite(heat)
         || !std::isfinite(c.x()) || !std::isfinite(c.y())
         || !std::isfinite(c.z()))
        {
            FatalErrorInFunction << "Nonfinite q/area/center in native patch"
                << exit(FatalError);
        }
        if (std::fprintf(fp,
              "%.17g,%lld,%.17g,%.17g,%.17g,%.17g,"
              "%.17g,%.17g,%.17g,%.17g\n",
              t, static_cast<long long>(facei),
              c.x(), c.y(), c.z(), area,
              n.x(), n.y(), n.z(), heat) < 0)
        {
            FatalErrorInFunction << "CSV write failed" << exit(FatalError);
        }
    }
}

int main(int argc, char *argv[])
{
    timeSelector::addOptions();
    argList::addOption("outMetal", "path", "Exclusive metal face CSV");
    argList::addOption("outMold", "path", "Exclusive mold face CSV");
    #include "setRootCaseNoFunctionObjects.H"
    #include "createTimeNoFunctionObjects.H"
    fileName outMetal;
    fileName outMold;
    if (!args.optionReadIfPresent("outMetal", outMetal)
     || !args.optionReadIfPresent("outMold", outMold))
    {
        FatalErrorInFunction << "Required -outMetal and -outMold"
            << exit(FatalError);
    }
    if (outMetal == outMold)
    {
        FatalErrorInFunction << "Cannot write both native regions into one file"
            << exit(FatalError);
    }

    const instantList timeDirs = timeSelector::select0(runTime, args);
    if (timeDirs.size() < 2)
    {
        FatalErrorInFunction << "Missing transient time fields"
            << exit(FatalError);
    }
    fvMesh metal
    (
        IOobject("metal", runTime.name(), runTime, IOobject::MUST_READ)
    );
    fvMesh mold
    (
        IOobject("mold", runTime.name(), runTime, IOobject::MUST_READ)
    );
    const label mp = interfacePatch(metal, "metal_to_mold");
    const label dp = interfacePatch(mold, "mold_to_metal");

    // "wx" is Linux/WSL exclusive creation. No input or prior CSV overwrite.
    FILE* fm = std::fopen(outMetal.c_str(), "wx");
    if (!fm)
    {
        FatalErrorInFunction << "Cannot exclusively create " << outMetal
            << exit(FatalError);
    }
    FILE* fd = std::fopen(outMold.c_str(), "wx");
    if (!fd)
    {
        std::fclose(fm);
        FatalErrorInFunction << "Cannot exclusively create " << outMold
            << exit(FatalError);
    }
    const char* header =
        "time_s,face_local,center_x_m,center_y_m,center_z_m,area_m2,"
        "normal_x,normal_y,normal_z,q_out_W_m2\n";
    std::fputs(header, fm);
    std::fputs(header, fd);

    forAll(timeDirs, timei)
    {
        runTime.setTime(timeDirs[timei], timei);
        if (metal.readUpdate() != fvMesh::UNCHANGED
            || mold.readUpdate() != fvMesh::UNCHANGED)
        {
            std::fclose(fm);
            std::fclose(fd);
            FatalErrorInFunction << "Mesh changed during postrun, stop"
                << exit(FatalError);
        }
        // Instantiate BOTH regional thermos before evaluating EITHER q().
        autoPtr<solidThermo> tm = solidThermo::New(metal);
        autoPtr<solidThermo> td = solidThermo::New(mold);
        autoPtr<solidThermophysicalTransportModel> cm =
            solidThermophysicalTransportModel::New(tm());
        autoPtr<solidThermophysicalTransportModel> cd =
            solidThermophysicalTransportModel::New(td());

        writeFaceFlux(fm, runTime.value(), metal, mp, cm());
        writeFaceFlux(fd, runTime.value(), mold, dp, cd());
        Info<< "C3D05 native bilateral q at t=" << runTime.value()
            << " faces each=" << 12636 << endl;
    }
    const int closeM = std::fclose(fm);
    const int closeD = std::fclose(fd);
    if (closeM != 0 || closeD != 0)
    {
        FatalErrorInFunction << "Native q CSV flush/close failed"
            << exit(FatalError);
    }
    Info<< "NATIVE_BILATERAL_PATCH_FLUX_EXTRACTED_NOT_VALIDATED" << endl;
    return 0;
}
