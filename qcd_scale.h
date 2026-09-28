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
// Two layouts reach this accessor, and k is always the index in the nine-entry grid above.
//
// Nine entries: k is the stored position. [4] is read as stored, which is not always 1
// (see below), so it must not be replaced by a constant.
//
// Eight entries: NanoAOD omitted (muR, muF) = (1, 1) and CMSSW sorted what remained, so
// the stored order is [0] (0.5, 0.5), [1] (0.5, 1), [2] (0.5, 2), [3] (1, 0.5),
// [4] (1, 2), [5] (2, 0.5), [6] (2, 1), [7] (2, 2). Nine-scheme indices 0..3 are
// unchanged and 5..8 shift down by one. The missing nominal is 1: the branch is
// w_var / w_nominal and that point was the divisor. Checked on
// TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX (Run3Summer22EE NanoAODv12), whose branch
// title lists exactly those eight pairs and whose LHEPdfWeight[0] is 1.
// Treating the eight entries as the first eight of the nine-entry grid would name
// [4] as the nominal when it is (1, 2). Any other length still throws, as does a
// non-finite weight.
//
// [4] is not always 1. The branch title claims w_var / w_nominal, but the denominator is
// really originalXWGTUP, so where the generator's nominal is not originalXWGTUP the
// leftover factor stays in every entry: on single top t-channel [4] runs 0.14-1.58
// (TbarBQ) and -1.45-2.51 (TBbarQ), and equals LHEPdfWeight[0] in every event. The pdf
// producer already applies that factor as its Central weight, so qcdScaleNormalisedWeight
// divides it back out and the two are counted once between them. Where [4] is already 1
// -- TT, DY, signal -- the division is a no-op.
inline float qcdScaleWeight(const ROOT::VecOps::RVec<float>& w, std::size_t k) {
  if (k > 8) {
    throw std::runtime_error("qcdScaleWeight: scale index out of range: " +
                             std::to_string(k));
  }
  // k is a nine-scheme index. Eight stored entries omit the nominal at index 4.
  std::size_t stored = k;
  if (w.size() == 8) {
    if (k == 4) return 1.f;
    stored = k < 4 ? k : k - 1;
  } else if (w.size() != 9) {
    throw std::runtime_error(
        "qcdScaleWeight: expected 9 scale weights, or 8 with the nominal omitted, got " +
        std::to_string(w.size()));
  }
  const float weight = w[stored];
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
