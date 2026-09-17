#pragma once

#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>

#include "ROOT/RVec.hxx"

namespace correction {

// PDF member k of the NanoAOD LHEPdfWeight vector.
//
// The branch already holds w_var / w_nominal -- its title reads "LHE pdf variation
// weights (w_var / w_nominal) for LHA IDs ..." -- so the members are relative as they
// stand, and member 0 is 1. Nothing is renormalised here.
//
// A member past the end of the vector is 1: the configured count covers the longest
// vector (103 members), and a sample carrying 101 has nothing to vary at 101 or 102.
// A non-finite weight, on the other hand, is a corrupt input and is thrown, not
// quietly rewritten to 1 -- the same choice psWeight makes.
inline float pdfMemberWeight(const ROOT::VecOps::RVec<float>& w, std::size_t k) {
  if (k >= w.size()) return 1.f;
  const float weight = w[k];
  if (!std::isfinite(weight)) {
    throw std::runtime_error("pdfMemberWeight: non-finite PDF weight at index " +
                             std::to_string(k) + ": " + std::to_string(weight));
  }
  return weight;
}

}  // namespace correction
