/*---------------------------------------------------------------------------*\
  FS-C08: native OpenFOAM Foundation14 fvMesh shadow step (SYNTHETIC ONLY).

  This is real owner/neighbour finite-volume connectivity, not a model
  prediction. It calls a conservatively balanced C++17 three-phase mass/
  enthalpy operator on ALL real native mesh cells, with nonzero +/-Gamma
  on the cells adjacent to one actual interior face, and all three phase
  face mass flows + latent enthalpy. All original FS-C07 fields remain
  untouched: no CFD pressure/velocity/free-surface solve is performed.

  Refuses any fixture not explicitly labelled SYNTHETIC_ONLY_NOT_JMATPRO.
  All thermo constants, timestep, source rates and face flows read from
  the separate versioned fixture, never from assumed material values.
\*---------------------------------------------------------------------------*/

#include "argList.H"
#include "fvMesh.H"
#include "IFstream.H"
#include "dictionary.H"
#include "IOmanip.H"
#include "../../native_cpp/ConservativePhaseNetwork.H"

#include <cmath>
#include <exception>
#include <vector>

using namespace Foam;
namespace mp = MichelMasterProject::FS_C08;

int main(int argc, char *argv[])
{
    argList::addNote
    (
        "FS-C08: one synthetic conservative Gamma!=0 three-phase FV shadow "
        "step on genuine OpenFOAM14 fvMesh owner/neighbour connectivity. "
        "READ-ONLY original case, NOT a calibrated shrinkage CFD solver."
    );
    #include "addRegionOption.H"
    argList::addOption
    (
        "fixture", "path",
        "Mandatory independent SYNTHETIC_ONLY_NOT_JMATPRO OpenFOAM dictionary"
    );
    #include "setRootCaseNoFunctionObjects.H"
    #include "createTimeNoFunctionObjects.H"

    fileName fixture;
    if (!args.optionReadIfPresent("fixture", fixture))
    {
        FatalErrorInFunction
            << "Specify -fixture with synthetic phase-mass source and "
            << "thermophysical provenance." << exit(FatalError);
    }
    IFstream input(fixture);
    if (!input.good())
    {
        FatalErrorInFunction
            << "Cannot read synthetic fixture " << fixture
            << exit(FatalError);
    }
    const dictionary cfg(input);
    const word provenance = cfg.lookup<word>("materialProvenance");
    if (provenance != "SYNTHETIC_ONLY_NOT_JMATPRO")
    {
        FatalErrorInFunction
            << "Refusing non-synthetic uncalibrated phase transport fixture: "
            << provenance << exit(FatalError);
    }

    word regionName = "fluid";
    args.optionReadIfPresent("region", regionName);
    fvMesh mesh
    (
        IOobject
        (
            regionName,
            runTime.name(),
            runTime,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        )
    );
    const label nCells = mesh.nCells();
    const label nInternal = mesh.nInternalFaces();
    if (nCells < 2 || nInternal < 1)
    {
        FatalErrorInFunction
            << "Native phase-transport shadow step needs a real mesh with "
            << "at least two cells and one internal face." << exit(FatalError);
    }

    const label facei = cfg.lookup<label>("internalFaceIndex");
    if (facei < 0 || facei >= nInternal)
    {
        FatalErrorInFunction
            << "Chosen face must be a genuine internal fvMesh face; got "
            << facei << " of " << nInternal << exit(FatalError);
    }
    const label owner=mesh.owner()[facei];
    const label neighbour=mesh.neighbour()[facei];
    if (owner < 0 || neighbour < 0 || owner >= nCells ||
        neighbour >= nCells || owner == neighbour)
    {
        FatalErrorInFunction
            << "Native owner-neighbour connectivity is inconsistent."
            << exit(FatalError);
    }

    const scalar rhoL=cfg.lookup<scalar>("rhoLiquid_kg_m3");
    const scalar rhoS=cfg.lookup<scalar>("rhoSolid_kg_m3");
    const scalar rhoG=cfg.lookup<scalar>("rhoGas_kg_m3");
    const scalar alphaL=cfg.lookup<scalar>("initialAlphaLiquid");
    const scalar alphaS=cfg.lookup<scalar>("initialAlphaSolid");
    const scalar dt=cfg.lookup<scalar>("dt_s");

    if (!std::isfinite(rhoG) || rhoG<=0 ||
        !std::isfinite(alphaL) || !std::isfinite(alphaS) ||
        alphaL<=0 || alphaS<0 || alphaL+alphaS>=1)
    {
        FatalErrorInFunction
            << "Initial positive liquid, nonnegative solid and positive "
            << "gas void required, with valid synthetic gas density."
            << exit(FatalError);
    }

    const mp::EnthalpyProperties thermo
    {
        cfg.lookup<scalar>("cpLiquid_J_kg_K"),
        cfg.lookup<scalar>("cpSolid_J_kg_K"),
        cfg.lookup<scalar>("cpGas_J_kg_K"),
        cfg.lookup<scalar>("latentHeat_J_kg"),
        cfg.lookup<scalar>("Tref_K")
    };
    const scalar temperatureBackground=
        cfg.lookup<scalar>("temperatureBackground_K");
    const scalar temperatureOwner=cfg.lookup<scalar>("temperatureOwner_K");
    const scalar temperatureNeighbour=
        cfg.lookup<scalar>("temperatureNeighbour_K");
    const scalar gammaOwner=cfg.lookup<scalar>("gammaOwner_kg_m3_s");
    const scalar gammaNeighbour=cfg.lookup<scalar>("gammaNeighbour_kg_m3_s");

    const mp::OutwardMassFlux faceRate
    {
        cfg.lookup<scalar>("liquidFaceMassFlow_kg_s"),
        cfg.lookup<scalar>("solidFaceMassFlow_kg_s"),
        cfg.lookup<scalar>("gasFaceMassFlow_kg_s")
    };
    const scalar heatRate=cfg.lookup<scalar>("faceHeatFlow_W");
    const scalarField& V=mesh.V();
    std::vector<mp::FVCell> cells;
    cells.reserve(static_cast<std::size_t>(nCells));
    forAll(V,celli)
    {
        const double volume=V[celli];
        const double T=celli==owner?temperatureOwner:
                        celli==neighbour?temperatureNeighbour:
                        temperatureBackground;
        const mp::Masses m
        {
            alphaL*volume*rhoL,
            alphaS*volume*rhoS,
            (1.0-alphaL-alphaS)*volume*rhoG
        };
        cells.push_back({{volume,rhoL,rhoS},m,T});
    }
    std::vector<double> gamma(cells.size(),0.0);
    gamma[static_cast<std::size_t>(owner)]=gammaOwner;
    gamma[static_cast<std::size_t>(neighbour)]=gammaNeighbour;

    const mp::NetworkStep step
    {
        dt, gamma,
        {{
            static_cast<std::size_t>(owner),
            static_cast<std::size_t>(neighbour),
            faceRate,heatRate
        }},
        {}
    };
    mp::NetworkResult r;
    try
    {
        r=mp::advanceNetwork(cells,thermo,step);
    }
    catch(const std::exception& error)
    {
        FatalErrorInFunction
            << "FS-C08 native mass/enthalpy step rejected: " << error.what()
            << ". No original case data were written." << exit(FatalError);
    }
    const double massScale=
        std::max(1.0,std::abs(r.initialMetalMass_kg));
    const double energyScale=
        std::max(1.0,std::abs(r.initialEnthalpy_J));
    if
    (
        std::abs(r.metalMassResidual_kg)>1e-10*massScale
     || std::abs(r.gasMassResidual_kg)>1e-10*massScale
     || std::abs(r.enthalpyResidual_J)>1e-10*energyScale
    )
    {
        FatalErrorInFunction
            << "Native FV mass/enthalpy conservation failed."
            << exit(FatalError);
    }

    Info<< setprecision(16);
    Info<< "FS_C08_NATIVE_SHADOW_STEP"
        << " cells=" << nCells
        << " internal_faces=" << nInternal
        << " face_index=" << facei
        << " owner=" << owner
        << " neighbour=" << neighbour
        << " dt_s=" << dt
        << " GammaOwner_kg_m3_s=" << gammaOwner
        << " GammaNeighbour_kg_m3_s=" << gammaNeighbour
        << " flowL_kg_s=" << faceRate.liquid_kg_s
        << " flowS_kg_s=" << faceRate.solid_kg_s
        << " flowG_kg_s=" << faceRate.gas_kg_s
        << " initial_metal_kg=" << r.initialMetalMass_kg
        << " final_metal_kg=" << r.finalMetalMass_kg
        << " initial_gas_kg=" << r.initialGasMass_kg
        << " final_gas_kg=" << r.finalGasMass_kg
        << " initial_enthalpy_J=" << r.initialEnthalpy_J
        << " final_enthalpy_J=" << r.finalEnthalpy_J
        << " gamma_transferred_kg=" << r.totalGammaTransfer_kg
        << " delta_metal_volume_m3=" << r.metalVolumeChange_m3
        << " metal_mass_residual_kg=" << r.metalMassResidual_kg
        << " gas_mass_residual_kg=" << r.gasMassResidual_kg
        << " enthalpy_residual_J=" << r.enthalpyResidual_J
        << " owner_T_final_K=" << r.next[owner].T_K
        << " neighbour_T_final_K=" << r.next[neighbour].T_K
        << nl;

    Info<< "FS_C08_NATIVE_SHADOW_END"
        << " synthetic_only=1"
        << " nonzero_gamma=" << (gammaOwner!=0 || gammaNeighbour!=0)
        << " native_fvmesh_owner_neighbour=1"
        << " three_phase_internal_flux=1"
        << " closed_domain_no_boundary_flux=1"
        << " original_fields_written=0"
        << " OpenFOAM_CFD_pressure_solved=0"
        << " OpenFOAM_CFD_velocity_solved=0"
        << " physical_3d_shrinkage_validated=0"
        << nl;
    return 0;
}
// ************************************************************************* //
