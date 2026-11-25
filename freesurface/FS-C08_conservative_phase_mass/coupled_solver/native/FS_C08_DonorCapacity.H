/* FS-C08: donor capacity arithmetic independent of OpenFOAM.
 * No mass threshold, no clipping of a conserved inventory.
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#ifndef FS_C08_DONOR_CAPACITY_H
#define FS_C08_DONOR_CAPACITY_H
namespace Foam { namespace fsC08 {

// Compare in extended precision BEFORE narrowing. In particular an
// outgoing subnormal rate times dt can round to zero in scalar arithmetic.
// An exactly empty donor may NEVER export a nonzero rate.
inline long double donorCapacityScale
(
    long double massDensity, long double cellVolume,
    long double dt, long double outgoingRate,
    long double margin, long double damping
)
{
    if (outgoingRate<=0) return 1;
    if (massDensity==0) return 0;
    const long double capRate=margin*massDensity*cellVolume/dt;
    if (outgoingRate<=capRate) return 1;
    return damping*(capRate/outgoingRate);
}

}} // namespace Foam::fsC08
#endif
