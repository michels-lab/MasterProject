/* C3D-05 B: original C14 REAL fluid metal + solid sand patch heat-flux.
 *
 * Foundation 14, NO CFD solution, remesh or fvModel changes.
 * Real thermal transport: fluidThermoThermophysicalTransportModel for metal,
 * solidThermophysicalTransportModel for sand. NEVER use T0 two-solid q.
 * Source API:
 * OpenFOAM-14/applications/modules/fluid/fluid.C
 * OpenFOAM-14/src/ThermophysicalTransportModels/fluid/laminar/Fourier/Fourier.C
 *
 * Two time-resolved outputs:
 *   integrated.csv -- q_out [W] of each of four ORIGINAL region boundaries
 *   last_faces.csv -- face-level q_out [W/m2], area, center and normal
 *                     at exactly t=10 s only.
 * Positive q_out means heat LEAVING that REGION through that patch. This is
 * conductive model flux. NOT total enthalpy advection, radiation, latent
 * fvModel source integral or a closed conservation statement.
 */
#include "fvMesh.H"
#include "Time.H"
#include "argList.H"
#include "timeSelector.H"
#include "surfaceFields.H"
#include "volFields.H"
#include "fluidThermo.H"
#include "solidThermo.H"
#include "compressibleMomentumTransportModel.H"
#include "fluidThermoThermophysicalTransportModel.H"
#include "solidThermophysicalTransportModel.H"
#include "linear.H"
#include <cstdio>
#include <cmath>

using namespace Foam;

static label namedPatch(const fvMesh& mesh, const word& name, const label expected)
{
    const label i = mesh.poly().boundary().findIndex(name);
    if (i < 0)
    {
        FatalErrorInFunction << "Original C14 Case B patch absent: "
            << mesh.name() << '/' << name << exit(FatalError);
    }
    const label n = mesh.poly().boundary()[i].size();
    if (n <= 0 || (expected > 0 && n != expected))
    {
        FatalErrorInFunction << "Original C14 patch face count mismatch: "
            << mesh.name() << '/' << name << " = " << n
            << ", required=" << expected << exit(FatalError);
    }
    return i;
}

static void writeFlux
(
    FILE* integral,
    FILE* facesOut,
    const scalar time,
    const fvMesh& mesh,
    const label patchi,
    const surfaceScalarField& q,
    const bool writeFaces
)
{
    const fvsPatchScalarField& qb=q.boundaryField()[patchi];
    const fvsPatchVectorField& sf=mesh.Sf().boundaryField()[patchi];
    const fvsPatchVectorField& cf=mesh.Cf().boundaryField()[patchi];
    const word name=mesh.poly().boundary()[patchi].name();
    if (qb.size()!=sf.size() || qb.size()!=cf.size())
    {
        FatalErrorInFunction << "C14 native patch q/face data count mismatch"
            << mesh.name() << '/' << name << exit(FatalError);
    }
    scalar qOut=0, gross=0, areaTotal=0;
    forAll(qb, i)
    {
        const scalar A=mag(sf[i]);
        const scalar qi=qb[i];
        if (!(A>0) || !std::isfinite(A) || !std::isfinite(qi))
        {
            FatalErrorInFunction << "C14 native nonfinite q/area" << exit(FatalError);
        }
        const scalar facePower=qi*A;
        qOut+=facePower;
        gross+=mag(facePower);
        areaTotal+=A;
        if (writeFaces)
        {
            const vector n=sf[i]/A;
            const vector c=cf[i];
            if (std::fprintf(facesOut,
                    "%.17g,%s,%s,%lld,%.17g,%.17g,%.17g,%.17g,"
                    "%.17g,%.17g,%.17g,%.17g,%.17g\n",
                    time, mesh.name().c_str(), name.c_str(),
                    static_cast<long long>(i),c.x(),c.y(),c.z(),A,
                    n.x(),n.y(),n.z(),qi,facePower)<0)
            {
                FatalErrorInFunction << "C14 native face CSV write error"
                    << exit(FatalError);
            }
        }
    }
    if (std::fprintf(integral,
            "%.17g,%s,%s,%lld,%.17g,%.17g,%.17g\n",
            time,mesh.name().c_str(),name.c_str(),
            static_cast<long long>(qb.size()),areaTotal,qOut,gross)<0)
    {
        FatalErrorInFunction << "C14 integrated patch CSV write error"
            << exit(FatalError);
    }
}

int main(int argc,char* argv[])
{
    timeSelector::addOptions();
    argList::addOption("outIntegrated","file","New exclusive patch q timeline CSV");
    argList::addOption("outLastFaces","file","New exclusive face q at final 10 s CSV");
    #include "setRootCaseNoFunctionObjects.H"
    #include "createTimeNoFunctionObjects.H"
    fileName integratedName,facesName;
    if (!args.optionReadIfPresent("outIntegrated",integratedName)
     || !args.optionReadIfPresent("outLastFaces",facesName)
     || integratedName==facesName)
    {
        FatalErrorInFunction << "Two distinct -outIntegrated and -outLastFaces "
            << "paths required" << exit(FatalError);
    }

    const instantList dirs=timeSelector::select0(runTime,args);
    if (dirs.size()!=101 || mag(dirs[0].value())>1e-10
       || mag(dirs[dirs.size()-1].value()-10.0)>1e-10)
    {
        FatalErrorInFunction << "Require exactly 101 native archived C14 times "
            << "from 0 to 10 seconds; no subsampling as full history"
            << exit(FatalError);
    }
    for (label i=0;i<dirs.size();++i)
    {
        if (mag(dirs[i].value()-0.1*i)>1e-8)
        {
            FatalErrorInFunction << "C14 archived time grid mismatch at index "
                << i << " value=" << dirs[i].value() << exit(FatalError);
        }
    }

    fvMesh metal(IOobject("metal",runTime.name(),runTime,IOobject::MUST_READ));
    fvMesh mold(IOobject("mold",runTime.name(),runTime,IOobject::MUST_READ));
    if (metal.nCells()!=92200 || mold.nCells()!=178588)
    {
        FatalErrorInFunction << "Not accepted 270788 HEX8 real C3D05 B mesh"
            << exit(FatalError);
    }
    const label mp=namedPatch(metal,"metal_to_mold",12636);
    const label mt=namedPatch(metal,"metalTop",-1);
    const label dp=namedPatch(mold,"mold_to_metal",12636);
    const label de=namedPatch(mold,"moldOuterUnclassified",-1);
    if (metal.poly().boundary().size()!=2 || mold.poly().boundary().size()!=2)
    {
        FatalErrorInFunction << "Unexpected additional patch on original C14 B"
            << exit(FatalError);
    }

    FILE* sums=std::fopen(integratedName.c_str(),"wx");
    if (!sums)
    {
        FatalErrorInFunction << "C14 integrated q destination exists / unsafe"
            << exit(FatalError);
    }
    FILE* faces=std::fopen(facesName.c_str(),"wx");
    if (!faces)
    {
        std::fclose(sums);
        FatalErrorInFunction << "C14 face q destination exists / unsafe"
            << exit(FatalError);
    }
    std::fputs("time_s,region,patch,nFaces,area_m2,q_out_W,gross_abs_face_power_W\n",sums);
    std::fputs(
        "time_s,region,patch,face_local,center_x_m,center_y_m,center_z_m,"
        "area_m2,normal_x,normal_y,normal_z,q_out_W_m2,q_out_face_W\n",
        faces
    );

    forAll(dirs,i)
    {
        runTime.setTime(dirs[i],i);
        if (metal.readUpdate()!=fvMesh::UNCHANGED
         || mold.readUpdate()!=fvMesh::UNCHANGED)
        {
            FatalErrorInFunction << "Original mesh changed during native analysis"
                << exit(FatalError);
        }

        // Register BOTH original regional thermos at the same physical time
        // before evaluating either coupled mappedWall T/snGrad.
        autoPtr<fluidThermo> tm=fluidThermo::New(metal);
        autoPtr<solidThermo> td=solidThermo::New(mold);
        volScalarField rho
        (
            IOobject("rhoC14Postrun",runTime.name(),metal,
                     IOobject::NO_READ,IOobject::NO_WRITE),
            tm->rho()
        );
        volVectorField U
        (
            IOobject("U",runTime.name(),metal,
                     IOobject::MUST_READ,IOobject::NO_WRITE),
            metal
        );
        surfaceScalarField phi
        (
            IOobject("phiC14Postrun",runTime.name(),metal,
                     IOobject::NO_READ,IOobject::NO_WRITE),
            linearInterpolate(rho*U)&metal.Sf()
        );
        autoPtr<compressible::momentumTransportModel> momentum=
            compressible::momentumTransportModel::New(rho,U,phi,tm());
        autoPtr<fluidThermoThermophysicalTransportModel> fluidTransport=
            fluidThermoThermophysicalTransportModel::New(momentum(),tm());
        autoPtr<solidThermophysicalTransportModel> solidTransport=
            solidThermophysicalTransportModel::New(td());

        const tmp<surfaceScalarField> qFluid=fluidTransport->q();
        const tmp<surfaceScalarField> qSolid=solidTransport->q();
        const bool finalState=i==dirs.size()-1;
        writeFlux(sums,faces,runTime.value(),metal,mp,qFluid(),finalState);
        writeFlux(sums,faces,runTime.value(),metal,mt,qFluid(),finalState);
        writeFlux(sums,faces,runTime.value(),mold,dp,qSolid(),finalState);
        writeFlux(sums,faces,runTime.value(),mold,de,qSolid(),finalState);

        Info<< "C3D05_B_C14_FLUID_SOLID_NATIVE_Q_READONLY "
            << (i+1) << "/" << dirs.size()
            << " Time=" << runTime.value()
            << " metal_mold_faces_each=12636"
            << " q=model_transport_only, NOT_energy_closure" << endl;
    }
    if (std::fclose(sums)!=0 || std::fclose(faces)!=0)
    {
        FatalErrorInFunction << "C14 native q outputs failed to flush"
            << exit(FatalError);
    }
    Info<< "C3D05_B_C14_TRUE_FLUID_SOLID_Q_EXTRACTED_NOT_PHYSICALLY_VALIDATED"
        << endl;
    return 0;
}
