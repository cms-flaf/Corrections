#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>

#include "correction.h"

namespace correction {

    using LorentzVectorXYZ = ROOT::Math::LorentzVector<ROOT::Math::PxPyPzE4D<double>>;
    using LorentzVectorM = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>;
    using LorentzVectorE = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiE4D<double>>;
    using RVecI = ROOT::VecOps::RVec<int>;
    using RVecS = ROOT::VecOps::RVec<size_t>;
    using RVecShort = ROOT::VecOps::RVec<short>;
    using RVecUC = ROOT::VecOps::RVec<UChar_t>;
    using RVecF = ROOT::VecOps::RVec<float>;
    using RVecB = ROOT::VecOps::RVec<bool>;
    using RVecVecI = ROOT::VecOps::RVec<RVecI>;
    using RVecLV = ROOT::VecOps::RVec<LorentzVectorM>;

    enum class UncScale : int {
        Down = -1,
        Central = 0,
        Up = +1,
    };

    template <typename... Args>
    void print_args(Args&&... args) noexcept {
        ((std::cerr << "\t" << std::forward<Args>(args) << "\n"), ...);
    }

    template <typename... Args>
    double safeEvaluate(const correction::Correction::Ref& corrRef, Args&&... args) {
        try {
            std::vector<correction::Variable::Type> values{std::forward<Args>(args)...};
            return corrRef->evaluate(values);
        } catch (const std::exception& e) {
            std::cerr << "ERROR while evaluating correction ......... " << corrRef->name() << "  .........\n";
            print_args(std::forward<Args>(args)...);
            std::cerr << "exception message: " << e.what() << "\n";
            throw;  // rilancia dopo aver loggato
        } catch (...) {
            std::cerr << "UNKNOWN ERROR in correction .........  " << corrRef->name() << "  .........\n";
            print_args(std::forward<Args>(args)...);
            throw;
        }
    }

    // Snap a value just outside the binning [lo, hi) into it, and throw if it is further out.
    // Shifted anaTuple trees store float deltas with an 8-bit mantissa, so a value that
    // passed a cut at a bin edge can be read back fractionally beyond it. The upper edge is
    // exclusive in correctionlib, so the clamp stops one ulp below it.
    inline double clampToRange(double value, double lo, double hi, double rel_tol = 0.01) {
        if (value < lo - rel_tol * std::abs(lo) || value > hi + rel_tol * std::abs(hi))
            throw std::runtime_error("clampToRange: " + std::to_string(value) + " is outside [" + std::to_string(lo) +
                                     ", " + std::to_string(hi) + ") beyond tolerance");
        return std::clamp(value, lo, std::nextafter(hi, lo));
    }

    template <typename CorrectionClass>
    class CorrectionsBase {
      public:
        template <typename... Args>
        static void Initialize(Args&&... args) {
            try {
                if (_getGlobal()) {
                    std::cerr << typeid(CorrectionClass).name() << " already initialized." << std::endl;
                    throw std::runtime_error("Class already initialized.");
                }
                _getGlobal() = std::make_unique<CorrectionClass>(args...);
            } catch (std::exception& e) {
                std::cerr << "Error while initializing " << typeid(CorrectionClass).name()
                          << " with arguments:" << "\n";
                print_args(std::forward<Args>(args)...);
                std::cerr << "exception message: " << e.what() << "\n";
                throw;
            } catch (...) {
                std::cerr << "Error while initializing " << typeid(CorrectionClass).name()
                          << " with arguments:" << "\n";
                print_args(std::forward<Args>(args)...);
                std::cerr << "exception category: unknown\n";
                throw;
            }
        }

        static const CorrectionClass& getGlobal() {
            const auto& corr = _getGlobal();
            if (!corr) {
                std::cerr << typeid(CorrectionClass).name() << " used before initialization";
                throw std::runtime_error("Class not initialized.");
            }
            return *corr;
        }

      private:
        static std::unique_ptr<CorrectionClass>& _getGlobal() {
            static std::unique_ptr<CorrectionClass> corr;
            return corr;
        }
    };
}  // end of namespace correction
