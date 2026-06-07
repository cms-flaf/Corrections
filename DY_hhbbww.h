#pragma once

#include <cmath>
#include <iostream>

#include "correction.h"
#include "corrections.h"

namespace correction {

    class DYbbwwCorrProvider : public CorrectionsBase<DYbbwwCorrProvider> {
      public:
        explicit DYbbwwCorrProvider(const std::string& fileName)
            : corrections_(CorrectionSet::from_file(fileName)), dy_hhbbww_Weight_(corrections_->at("dy_correction_weight")) {}

        // template <typename LV1, typename LV2>
        double getWeight(const std::string& era,
                         int njets,
                         float pt_ll,
                         const std::string& syst) const {
            static constexpr int kMinNJets = 2;
            static constexpr int MaxJets = 10;

            double weight = 1.0;

            if (njets < kMinNJets) {
                weight = 1.0;
            } else {
                weight = safeEvaluate(dy_hhbbww_Weight_, era, std::min(njets, MaxJets), pt_ll, syst);
            }
            return weight;
        }

      private:
        std::unique_ptr<CorrectionSet> corrections_;
        Correction::Ref dy_hhbbww_Weight_;
    };

}  // namespace correction