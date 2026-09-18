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
// generated with the central PDF of the stored set -- for TT it is exactly 1. Single top
// t-channel (4FS, LHA 325500) reweights onto a Hessian conversion of its generation PDF,
// so there member 0 is a real per-event weight: measured over 20k events, 0.14-1.58 for
// TbarBQ and -1.45-2.51 for TBbarQ, and equal to LHEScaleWeight[4] in every event.
//
// Nothing is renormalised here. The accessor returns the stored value and
// pdfWeightProducer takes member 0 as its Central weight, which puts w[0] in weight_base
// and in the Central denominator: the nominal moves onto the set's central PDF with the
// sample's total normalisation preserved, and a variation carries w[k]/w[0] without a
// division here. Under FLAF's sign-only genWeight that is exact wherever |genWeight| is
// constant, which holds for the samples member 0 actually moves: 135.293 for TBbarQ and
// 81.976 for TbarBQ (81.104 for TTto2L2Nu, 26780 for DY). sign(genWeight) * w[0] is then
// the reweighted ME weight up to that constant, which cancels against the denominator.
// The LO signals do vary, by 1.5% at MX-300, but their member 0 is exactly 1.
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
