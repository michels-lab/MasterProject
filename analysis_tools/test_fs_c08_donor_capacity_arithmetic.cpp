// Standalone numerical regression; not OpenFOAM/CFD validation.
#include "../freesurface/FS-C08_conservative_phase_mass/coupled_solver/native/FS_C08_DonorCapacity.H"
#include <cassert>
#include <limits>
#include <iostream>
int main() {
    using Foam::fsC08::donorCapacityScale;
    const double q=std::numeric_limits<double>::denorm_min();
    const double dt=1e-6,V=4e-8;
    assert(q>0 && dt*q==0);
    assert(donorCapacityScale(0,V,dt,q,0.95L,0.8L)==0);
    assert(donorCapacityScale(0,V,dt,0,0.95L,0.8L)==1);
    assert(donorCapacityScale(q,V,dt,q,0.95L,0.8L)>0);
    assert(donorCapacityScale(1,1,1,0.5L,0.95L,0.8L)==1);
    const auto f=donorCapacityScale(1,1,1,2,0.95L,0.8L);
    assert(f>0 && f*2<0.95L);
    std::cout << "FS_C08_DONOR_CAPACITY_ARITHMETIC_PASS\n";
}
