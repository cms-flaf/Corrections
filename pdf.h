#pragma once

#include <cmath>
#include <cstddef>

#include "ROOT/RVec.hxx"

namespace correction {

// PDF member k of the NanoAOD LHEPdfWeight vector, relative to the nominal member 0.
//
// Returns 1 when the member is absent or the nominal is unusable. A member that is
// always 1 gets the Central denominator, so its relative weight is 1 and it is a no-op
// -- which is what the members past the end of a shorter vector should be.
inline float pdfMemberWeight(const ROOT::VecOps::RVec<float>& w, std::size_t k) {
  if (w.empty() || k >= w.size()) return 1.f;
  const double w0 = static_cast<double>(w[0]);
  if (!std::isfinite(w0) || w0 == 0.) return 1.f;
  const double r = static_cast<double>(w[k]) / w0;
  return std::isfinite(r) ? static_cast<float>(r) : 1.f;
}

}  // namespace correction
