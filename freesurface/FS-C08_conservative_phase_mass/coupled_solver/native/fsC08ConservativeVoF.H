/* FS-C08 | Extension of real Foundation14 compressibleVoF fluid module.
 * Explicitly separates phase-mass continuity from old VoFSolidificationMelting.
 * No calibration inferred, no shadow or post-processing time step.
 * Copyright 2026 Michel's Lab, GPL-3.0-or-later.
 */
#ifndef fsC08ConservativeVoF_H
#define fsC08ConservativeVoF_H

#include "compressibleVoF.H"
#include "FS_C08_PhaseMassTransport.H"

namespace Foam
{
namespace solvers
{

class fsC08ConservativeVoF : public compressibleVoF
{
    autoPtr<fsC08::PhaseMassTransport> phaseMass_;

    // Restore mixture mass from actual liquid+solid inventories, not
    // alpha.metal * rho_liquid alone. Gas remains native compressibleVoF.
    void reconcileMixtureDensity();

protected:
    virtual void prePredictor() override;
    virtual void pressureCorrector() override;

public:
    TypeName("fsC08ConservativeVoF");

    explicit fsC08ConservativeVoF(fvMesh& mesh);
    virtual ~fsC08ConservativeVoF();

    // Publicly exposes no synthetic trigger; invoked by foamMultiRun PIMPLE.
};

} // namespace solvers
} // namespace Foam

#endif
