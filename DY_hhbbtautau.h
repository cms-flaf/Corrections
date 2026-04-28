#pragma once

#include <cmath>
#include <iostream>

#include "correction.h"
#include "corrections.h"

namespace correction {

    class DYbbtautauCorrProvider : public CorrectionsBase<DYbbtautauCorrProvider> {
      public:
        explicit DYbbtautauCorrProvider(const std::string& fileName)
            : corrections_(CorrectionSet::from_file(fileName)), dyWeight_(corrections_->at("dy_weight")) {}

        template <typename LV1, typename LV2>
        double getWeight(const std::string& era,
                         int njets,
                         int ntags,
                         const LV1& tau1_gen_p4,
                         const LV2& tau2_gen_p4,
                         const std::string& syst,
                         bool isDY,
                         bool isValid) const {
            const float ptll = static_cast<float>((tau1_gen_p4 + tau2_gen_p4).Pt());

            double weight = 1.0;  // Declare outside the if-else
            if (!isDY || !isValid) {
                weight = 1.0;
            } else {
                weight = safeEvaluate(dyWeight_, era, njets, ntags, ptll, syst);
            }
            return weight;
        }

      private:
        std::unique_ptr<CorrectionSet> corrections_;
        Correction::Ref dyWeight_;
    };

}  // namespace correction