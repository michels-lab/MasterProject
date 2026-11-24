#include "ConservativePhaseNetwork.H"
#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

using namespace MichelMasterProject::FS_C08;

bool near(double a,double b,double atol=1.e-10)
{
    return std::abs(a-b)<=atol;
}
template<typename F>
void mustFail(F fn)
{
    try {fn();} catch(const std::domain_error&) {return;}
    throw std::runtime_error("Expected network invariant refusal");
}
int main()
{
    // SYNTHETIC values, NOT cast-iron thermokinetics / lab JMatPro.
    const EnthalpyProperties thermo{800,700,1000,200000,1400};
    const CellProps geom{1.e-5,7000,7300};
    const FVCell a{geom,{0.028,0.0073,0.000001},1500};
    const FVCell b{geom,{0.021,0.0073,0.000001},1460};
    const std::vector<FVCell> cells{a,b};
    const NetworkStep step{
        0.1,{80,-20},{{0,1,{0.0007,0.00002,0.000001}}},{}
    };
    const auto r=advanceNetwork(cells,thermo,step);
    assert(r.next.size()==2);
    assert(near(r.totalGammaTransfer_kg,0.00006,1.e-15));
    assert(near(r.metalMassResidual_kg,0,1.e-14));
    assert(near(r.gasMassResidual_kg,0,1.e-14));
    assert(near(r.enthalpyResidual_J,0,1.e-8));
    assert(near(r.next[0].mass.liquid_kg,
                a.mass.liquid_kg-0.00007-0.00008,1.e-14));
    assert(near(r.next[0].mass.solid_kg,
                a.mass.solid_kg-0.000002+0.00008,1.e-14));
    assert(near(r.next[1].mass.liquid_kg,
                b.mass.liquid_kg+0.00007+0.00002,1.e-14));
    assert(near(r.next[1].mass.solid_kg,
                b.mass.solid_kg+0.000002-0.00002,1.e-14));
    assert(r.next[0].T_K>1500); // latent release at owner
    const auto reverse=advanceNetwork(
        cells,thermo,{0.1,{-20,80},{{0,1,{-0.0002,0,0}}},{}}
    );
    assert(std::abs(reverse.metalMassResidual_kg)<1.e-14);
    assert(std::abs(reverse.enthalpyResidual_J)<1.e-8);
    const auto heat=advanceNetwork(cells,thermo,{0.1,{0,0},{},{100,-25}});
    assert(near(heat.enthalpyResidual_J,0,1.e-8));
    assert(near(heat.externalHeat_J,7.5,1.e-14));
    assert(near(heat.finalMetalMass_kg,heat.initialMetalMass_kg,1.e-14));
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{1e12,0},{},{}});});
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{-1e12,0},{},{}});});
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{0,0},{{0,1,{1,0,0}}},{}});});
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{0,0},{{0,0,{1e-6,0,0}}},{}});});
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{0},{},{}});});
    mustFail([&]{advanceNetwork(cells,thermo,{-0.1,{0,0},{},{}});});
    mustFail([&]{advanceNetwork(cells,{0,700,1000,200000,1400},step);});
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{0,0},{{0,1,{0,0,1e20}}},{}});});
    mustFail([&]{advanceNetwork(cells,thermo,{0.1,{0,0},{{0,1,{0,0,0},1e40}}, {}});});
    std::cout << "FS-C08 native-mesh compatible FV network: PASS "
              << "(nonzero Gamma + liquid/solid/gas face flows + enthalpy, synthetic only)\n";
}
