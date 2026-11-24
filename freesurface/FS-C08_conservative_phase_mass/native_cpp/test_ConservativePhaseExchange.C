/* Compile: c++ -std=c++17 -Wall -Wextra -Werror -pedantic ... */
#include "ConservativePhaseExchange.H"
#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>

using namespace MichelMasterProject::FS_C08;

bool approx(const double a,const double b,double tolerance=1.e-13)
{
    return std::abs(a-b)<tolerance;
}

template<class F>
void mustFail(F fn)
{
    try { fn(); } catch (const std::domain_error&) {return;}
    throw std::runtime_error("Expected negative mass / overfill / bad physics to fail");
}

int main()
{
    // Synthetic density values are NOT real cast-iron material properties.
    const CellProps p{1.e-5,7000,7300};
    const Masses a{0.042,0,0.000001};
    auto r=exchange(a,p,0.1,210,{});
    assert(approx(r.transferred_liquid_to_solid_kg,0.00021));
    assert(approx(r.next.liquid_kg+r.next.solid_kg,0.042));
    assert(std::abs(r.metalMassResidual_kg)<1.e-14);
    assert(r.metalVolumeChange_m3<0);
    assert(approx(r.metalVolumeChange_m3,r.conversionOnlyVolumeChange_m3));
    assert(r.gasVoidVolume_m3>4.e-6);

    // Melting must be the opposite source on the same metal mass.
    auto melted=exchange(r.next,p,0.1,-210,{});
    assert(approx(melted.next.liquid_kg,a.liquid_kg));
    assert(approx(melted.next.solid_kg,0));
    assert(approx(melted.next.gas_kg,a.gas_kg));

    // If graphite expansion / material density yields rho_s<rho_l,
    // an identical conversion increases geometric metal volume.
    const CellProps expansion{1.e-5,7000,6750};
    auto expands=exchange(a,expansion,0.1,210,{});
    assert(expands.metalVolumeChange_m3>0);

    // Internal flux enters cell 1 and exits cell 0: cancels globally.
    const Masses b{0.014,0.0,0.000001};
    auto left=exchange(a,p,0.1,120,{0.0008,0,0});
    auto right=exchange(b,p,0.1,80,{-0.0008,0,0});
    assert(approx(
      left.next.liquid_kg+left.next.solid_kg+
      right.next.liquid_kg+right.next.solid_kg,
      a.liquid_kg+a.solid_kg+b.liquid_kg+b.solid_kg));
    assert(approx(left.transferred_liquid_to_solid_kg+
                  right.transferred_liquid_to_solid_kg,0.0002));

    // External metal outflow reduces inventory, unlike phase exchange.
    auto out=exchange(a,p,0.1,0,{0.001,0,0});
    assert(approx(out.next.liquid_kg,0.0419));
    assert(std::abs(out.metalMassResidual_kg)<1.e-14);

    mustFail([&](){exchange(a,p,1,1e9,{});});
    mustFail([&](){exchange(a,p,1,-1e9,{});});
    mustFail([&](){exchange(a,p,1,0,{1,0,0});});
    mustFail([&](){exchange(a,p,-1,0,{});});
    mustFail([&](){exchange(a,CellProps{1e-5,0,7300},1,0,{});});
    mustFail([&](){exchange(Masses{0.07,0,0},p,0.1,0,{-1e-3,0,0});});

    std::cout << "FS-C08 C++17 native-language conservative Gamma kernel: "
              << "PASS (synthetic only, NOT OpenFOAM CFD)\n";
}
