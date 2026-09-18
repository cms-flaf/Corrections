#pragma once

#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>

#include "ROOT/RVec.hxx"

namespace correction {

// PDF member k of the NanoAOD LHEPdfWeight vector, taken as stored.
//
// The branch holds w_var / originalXWGTUP, so member 0 is 1 only where the sample was
// generated with the central PDF of the stored set -- TT, DY, signal, ST s-channel and
// tW are. Single top t-channel (4FS, LHA 325500) is not: its set's central is a Hessian
// conversion of the generation PDF, so there member 0 varies 0.82-1.03 per event and is
// equal to LHEScaleWeight[4], the scale family's nominal slot. Nothing is renormalised
// here, so for such a sample the members stay relative to originalXWGTUP rather than to
// the set's central. Reweighting the nominal onto that central would change the central
// prediction and is a separate decision; genWeight (== originalXWGTUP) enters the
// analysis by sign only.
//
// The base set is 101 members, the nominal plus 100 eigenvectors; the two alphaS members
// that follow in a "_pdfas" set are optional, so the four-flavour-scheme samples carry
// 101 and the rest 103. Fewer than 101 is a sample this configuration does not describe,
// not a missing extra, and is thrown -- as is a non-finite weight, the same choice
// psWeight makes. An absent optional member is 0, so it cannot be read as a weight of 1.
inline float pdfMemberWeight(const ROOT::VecOps::RVec<float>& w, std::size_t k) {
  if (w.size() < 101) {
    throw std::runtime_error("pdfMemberWeight: expected at least 101 PDF weights, got " +
                             std::to_string(w.size()));
  }
  if (k >= w.size()) return 0.f;
  const float weight = w[k];
  if (!std::isfinite(weight)) {
    throw std::runtime_error("pdfMemberWeight: non-finite PDF weight at index " +
                             std::to_string(k) + ": " + std::to_string(weight));
  }
  return weight;
}

}  // namespace correction
