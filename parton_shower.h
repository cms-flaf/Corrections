#pragma once

#include <cmath>
#include "ROOT/RVec.hxx"

namespace correction {

// NanoAOD PSWeight is already w_var / w_nominal. The index ordering is fixed by the
// CMSSW producer that writes the branch, PhysicsTools/NanoAOD/plugins/
// GenWeightsTableProducer.cc, whose documentation string reads verbatim:
//
//   "PS weights (w_var / w_nominal); [0] is ISR=2 FSR=1; [1] is ISR=1 FSR=2;
//    [2] is ISR=0.5 FSR=1; [3] is ISR=1 FSR=0.5;"
//
// That string is written into the NanoAOD branch title, but the Define-rename in
// AnaProd/anaTupleDef.py drops it, so it cannot be read back from the anaTuple. The
// size check below is what makes relying on the convention safe: the same producer
// writes a single dummy weight of 1.0 when the sample does not carry the expected 14
// or 46 underlying weights, and writes the full set for Sherpa. Only a length of
// exactly 4 is the standard four-variation set.
//
// A sample that lands in one of those other cases yields 1 here, which makes the
// nuisance a no-op for it -- silently. The inclusive denominator ratio is the
// diagnostic: it comes out exactly 1.000000 for such a sample.
inline float psWeight(const ROOT::VecOps::RVec<float>& ps, size_t idx) {
  if (ps.size() != 4) return 1.f;
  const float w = ps[idx];
  // Guard non-finite only. A zero or negative PS weight is a generator problem worth
  // seeing downstream, not something to quietly rewrite to 1.
  return std::isfinite(w) ? w : 1.f;
}

}  // namespace correction
