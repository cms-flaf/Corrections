#pragma once

#include <cmath>
#include <cstddef>
#include <memory>
#include <mutex>
#include <vector>

#include "ROOT/RVec.hxx"

namespace correction {

// Per-member PDF weights from the NanoAOD LHEPdfWeight vector.
//
// PDF4LHC15 (arXiv:1510.03865) takes the spread across members of each bin of the fitted
// distribution, so the members are kept per event and combined per bin later. Dividing
// each member by its own inclusive sum of weights is what makes that spread shape-only.
// Member 0 is the nominal, so its sum must reproduce the plain anaCache denominator.

// Inclusive sums of weight * w[k]/w[0] over every generated event.
class PdfDenominator {
public:
  PdfDenominator()
      : sums_(std::make_shared<std::vector<double>>()),
        n_bad_(std::make_shared<std::size_t>(0)),
        n_mismatch_(std::make_shared<std::size_t>(0)),
        mutex_(std::make_shared<std::mutex>()) {}

  float operator()(const ROOT::VecOps::RVec<float>& w, double weight) {
    const std::lock_guard<std::mutex> lock(*mutex_);
    if (w.empty()) {
      ++(*n_mismatch_);
      return 0.f;
    }
    if (sums_->empty()) sums_->assign(w.size(), 0.);
    if (w.size() != sums_->size()) {
      ++(*n_mismatch_);
      return 0.f;
    }
    const double w0 = static_cast<double>(w[0]);
    const bool usable = std::isfinite(w0) && w0 != 0.;
    if (!usable) ++(*n_bad_);
    for (std::size_t k = 0; k < w.size(); ++k) {
      double r = 1.;
      if (usable) {
        r = static_cast<double>(w[k]) / w0;
        if (!std::isfinite(r)) r = 1.;
      }
      (*sums_)[k] += weight * r;
    }
    return 0.f;
  }

  std::vector<double> sums() const {
    const std::lock_guard<std::mutex> lock(*mutex_);
    return *sums_;
  }
  std::size_t nBadNominal() const {
    const std::lock_guard<std::mutex> lock(*mutex_);
    return *n_bad_;
  }
  std::size_t nSizeMismatch() const {
    const std::lock_guard<std::mutex> lock(*mutex_);
    return *n_mismatch_;
  }

private:
  std::shared_ptr<std::vector<double>> sums_;
  std::shared_ptr<std::size_t> n_bad_, n_mismatch_;
  std::shared_ptr<std::mutex> mutex_;
};

// Shape-only per-member weight (w[k]/w[0]) * norm[k], with norm[k] = D_0 / D_k.
// Element 0 is 1 by construction.
class PdfRelWeights {
public:
  explicit PdfRelWeights(const std::vector<double>& norm) : norm_(norm) {}

  ROOT::VecOps::RVec<float> operator()(const ROOT::VecOps::RVec<float>& w) const {
    ROOT::VecOps::RVec<float> out(norm_.size(), 1.f);
    if (w.size() != norm_.size() || w.empty()) return out;
    const double w0 = static_cast<double>(w[0]);
    if (!std::isfinite(w0) || w0 == 0.) return out;
    for (std::size_t k = 0; k < w.size(); ++k) {
      const double v = static_cast<double>(w[k]) / w0 * norm_[k];
      out[k] = std::isfinite(v) ? static_cast<float>(v) : 1.f;
    }
    return out;
  }

private:
  std::vector<double> norm_;
};

}  // namespace correction
