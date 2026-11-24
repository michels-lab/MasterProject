/*---------------------------------------------------------------------------*\
  FS-C08 OpenFOAM Foundation14 native read-only bridge (experimental).

  This deliberately DOES NOT solve a shrinkage/free-surface problem:
  - loads actual saved FS-C07 fluid alpha.metal, alpha.metal.solid from fvMesh;
  - audits all internal volume fractions without clipping;
  - optionally maps cell fractions to constant-density mass ledgers and
    calls the independently tested ConservativePhaseExchange C++17 kernel
    at zero Gamma and zero flux, to check native mesh/cell interoperability.
  - NEVER calls mesh.write(), field.write(), runTime.write(), foamMultiRun.
  - material densities are optional and NEVER labelled as JMatPro unless
    external provenance is explicitly supplied; still only constant-T
    proxies, not real temperature-dependent density.

  To run on a preserved experiment, only choose true saved field times, e.g.
  -time '0.2,0.4,1' or -latestTime. No automatic scan of thousands of
  functionObject-only time directories.
\*---------------------------------------------------------------------------*/

#include "argList.H"
#include "timeSelector.H"
#include "fvMesh.H"
#include "volFields.H"
#include "../native_cpp/ConservativePhaseExchange.H"

#include <cmath>
#include <algorithm>

using namespace Foam;

int main(int argc, char *argv[])
{
    argList::addNote
    (
        "FS-C08 READ-ONLY native bridge for saved FS-C07 fluid phases. "
        "NOT a CFD solver, NO physical shrinkage accepted."
    );

    timeSelector::addOptions();
    #include "addRegionOption.H"

    argList::addOption
    (
        "rhoLiquid",
        "kg/m3",
        "Optional positive constant-density liquid mass PROXY, not JMatPro"
    );
    argList::addOption
    (
        "rhoSolid",
        "kg/m3",
        "Optional positive constant-density solid mass PROXY, not JMatPro"
    );
    argList::addOption
    (
        "provenance",
        "identifier",
        "Required description tag if both density proxies are provided"
    );

    #include "setRootCaseNoFunctionObjects.H"
    #include "createTimeNoFunctionObjects.H"

    if (!args.optionFound("time") && !args.optionFound("latestTime"))
    {
        FatalErrorInFunction
            << "Specify -time '0.2,0.4,1' or -latestTime; "
            << "do NOT scan thousands of function-object time dirs."
            << exit(FatalError);
    }

    scalar rhoL = 0;
    scalar rhoS = 0;
    word provenance = "UNSPECIFIED";
    const bool gotL = args.optionReadIfPresent("rhoLiquid", rhoL);
    const bool gotS = args.optionReadIfPresent("rhoSolid", rhoS);
    const bool gotProvenance =
        args.optionReadIfPresent("provenance", provenance);

    if (gotL != gotS || (gotL && !gotProvenance))
    {
        FatalErrorInFunction
            << "If densities are supplied, BOTH -rhoLiquid and -rhoSolid "
            << "and an explicit -provenance identifier are required."
            << exit(FatalError);
    }

    if
    (
        gotL
     && (!std::isfinite(rhoL) || rhoL <= 0
      || !std::isfinite(rhoS) || rhoS <= 0)
    )
    {
        FatalErrorInFunction
            << "Density proxies must be finite, positive and SI kg/m3."
            << exit(FatalError);
    }

    const instantList timeDirs = timeSelector::select0(runTime, args);

    if (timeDirs.empty())
    {
        FatalErrorInFunction
            << "No time directories selected."
            << exit(FatalError);
    }

    word regionName = "fluid";
    args.optionReadIfPresent("region", regionName);

    Info<< "FS_C08_NATIVE_READ_ONLY_BRIDGE region=" << regionName
        << " selected_times=" << timeDirs.size()
        << " density_proxies=" << gotL
        << " provenance=" << provenance << nl
        << "WARNING: Original FS-C07 fields remain unmodified. "
        << "Gamma, CHT, pressure coupling and feeding NOT solved." << nl;

    fvMesh mesh
    (
        IOobject
        (
            regionName,
            runTime.name(),
            runTime,
            IOobject::MUST_READ
        )
    );

    Info.precision(16);

    forAll(timeDirs, timei)
    {
        runTime.setTime(timeDirs[timei], timei);

        if (mesh.readUpdate() != fvMesh::UNCHANGED)
        {
            FatalErrorInFunction
                << "Mesh changed between selected snapshots; this audit "
                << "requires the same natively saved fluid mesh."
                << exit(FatalError);
        }

        volScalarField metal
        (
            IOobject
            (
                "alpha.metal",
                runTime.name(),
                mesh,
                IOobject::MUST_READ,
                IOobject::NO_WRITE
            ),
            mesh
        );

        volScalarField solid
        (
            IOobject
            (
                "alpha.metal.solid",
                runTime.name(),
                mesh,
                IOobject::MUST_READ,
                IOobject::NO_WRITE
            ),
            mesh
        );

        const scalarField& V = mesh.V();
        const scalarField& a = metal.primitiveField();
        const scalarField& s = solid.primitiveField();

        if (V.size() != a.size() || V.size() != s.size())
        {
            FatalErrorInFunction
                << "Native mesh field sizes are not identical."
                << exit(FatalError);
        }

        scalar metalVolume = 0;
        scalar solidVolume = 0;
        scalar liquidDifferenceVolume = 0;
        scalar excessVolume = 0;
        scalar maxExcess = 0;
        label significantCells = 0;
        label significantCoreCells = 0;
        label validatedCxxCellExchanges = 0;
        scalar liquidMassProxy = 0;
        scalar solidMassProxy = 0;
        scalar massLedgerResidualProxy = 0;

        forAll(V, celli)
        {
            const scalar ai = a[celli];
            const scalar si = s[celli];
            const scalar volume = V[celli];

            if
            (
                !std::isfinite(ai) || !std::isfinite(si)
             || !std::isfinite(volume) || volume <= 0
            )
            {
                FatalErrorInFunction
                    << "Nonfinite native VOF/solid or invalid cell volume "
                    << "at cell " << celli << " time " << runTime.value()
                    << exit(FatalError);
            }

            metalVolume += volume*ai;
            solidVolume += volume*si;
            liquidDifferenceVolume += volume*(ai-si);
            const scalar over = max(scalar(0), si-ai);
            excessVolume += volume*over;
            maxExcess = max(maxExcess, over);
            if (over > 1e-8)
            {
                ++significantCells;
                if (ai >= 0.5) ++significantCoreCells;
            }

            // Optional constant-density mapping. Only apply the tested
            // C++17 mass ledger to strictly valid native core cells.
            // Any invalid low-VOF fields are never silently clipped.
            if (gotL && ai >= 0.5 && ai <= 1 && si >= 0 && si <= ai)
            {
                const scalar liquidMass=(ai-si)*volume*rhoL;
                const scalar solidMass=si*volume*rhoS;
                const MichelMasterProject::FS_C08::CellProps props
                {
                    volume, rhoL, rhoS
                };
                const MichelMasterProject::FS_C08::Masses masses
                {
                    liquidMass, solidMass, 0
                };

                const auto result =
                    MichelMasterProject::FS_C08::exchange
                    (
                        masses,
                        props,
                        1e-7,  // exchange test at zero Gamma, NOT a timestep
                        0.0,
                        MichelMasterProject::FS_C08::OutwardMassFlux{}
                    );

                ++validatedCxxCellExchanges;
                liquidMassProxy += liquidMass;
                solidMassProxy += solidMass;
                massLedgerResidualProxy += result.metalMassResidual_kg;
            }
        }

        Info
            << "FS_C08_NATIVE_VOLUME_AUDIT"
            << " time_s=" << runTime.value()
            << " cells=" << V.size()
            << " V_metal_raw_m3=" << metalVolume
            << " V_solid_raw_m3=" << solidVolume
            << " V_liquid_difference_raw_m3=" << liquidDifferenceVolume
            << " V_solid_excess_m3=" << excessVolume
            << " max_fraction_excess=" << maxExcess
            << " n_significant_excess_gt_1e8=" << significantCells
            << " n_core_excess_gt_1e8=" << significantCoreCells
            << nl;

        if (gotL)
        {
            Info
                << "FS_C08_NATIVE_CPP17_CORE_LEDGER"
                << " time_s=" << runTime.value()
                << " core_cells_checked=" << validatedCxxCellExchanges
                << " core_liquid_mass_proxy_kg=" << liquidMassProxy
                << " core_solid_mass_proxy_kg=" << solidMassProxy
                << " exchange_mass_residual_kg="
                << massLedgerResidualProxy
                << " density_provenance=" << provenance
                << " NOT_GLOBAL_METAL_MASS_BALANCE=1"
                << nl;
        }
    }

    Info<< "FS_C08_NATIVE_BRIDGE_END"
        << " read_only=1"
        << " solver_reexecuted=0"
        << " phase_fields_written=0"
        << " physical_shrinkage_validated=0"
        << nl;

    return 0;
}
// ************************************************************************* //
