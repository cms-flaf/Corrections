#pragma once

#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>

#include "ROOT/RVec.hxx"

namespace correction {

// Member k of the NanoAOD LHEScaleWeight vector, taken as stored (w_var / originalXWGTUP).
//
// The nine entries are the (muR, muF) grid with muR outermost:
//   [0] (0.5, 0.5)  [1] (0.5, 1)  [2] (0.5, 2)
//   [3] (1, 0.5)    [4] (1, 1)    [5] (1, 2)
//   [6] (2, 0.5)    [7] (2, 1)    [8] (2, 2)
// with [4] the nominal and [2], [6] the unphysical corners.
//
// Exactly nine is required, and doubly so for the normalised accessor, which reads [4]
// directly. Samples that store eight drop the nominal from the middle, so every index
// above 3 would silently name a different (muR, muF) pair. A non-finite weight throws too.
//
// [4] is not always 1. The branch title claims w_var / w_nominal, but the denominator is
// really originalXWGTUP, so where the generator's nominal is not originalXWGTUP the
// leftover factor stays in every entry: on single top t-channel [4] runs 0.14-1.58
// (TbarBQ) and -1.45-2.51 (TBbarQ), and equals LHEPdfWeight[0] in every event. The pdf
// producer already applies that factor as its Central weight, so qcdScaleNormalisedWeight
// divides it back out and the two are counted once between them. Where [4] is already 1
// -- TT, DY, signal -- the division is a no-op.
inline float qcdScaleWeight(const ROOT::VecOps::RVec<float>& w, std::size_t k) {
  if (w.size() != 9) {
    throw std::runtime_error("qcdScaleWeight: expected 9 scale weights, got " +
                             std::to_string(w.size()));
  }
  const float weight = w[k];
  if (!std::isfinite(weight)) {
    throw std::runtime_error("qcdScaleWeight: non-finite scale weight at index " +
                             std::to_string(k) + ": " + std::to_string(weight));
  }
  return weight;
}

// Member k divided by the nominal [4]: the w_var / w_nominal the branch title promises.
// Used when another producer already applies the [4] factor, so it must not be applied
// twice. [4] == 0 throws rather than returning an infinity.
inline float qcdScaleNormalisedWeight(const ROOT::VecOps::RVec<float>& w, std::size_t k) {
  const float weight = qcdScaleWeight(w, k);
  const float nominal = qcdScaleWeight(w, 4);
  if (nominal == 0.f) {
    throw std::runtime_error("qcdScaleNormalisedWeight: nominal scale weight [4] is zero");
  }
  return weight / nominal;
}

}  // namespace correction
