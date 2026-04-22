#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class DYbbtautauCorrProvider : public CorrectionsBase<DYbbtautauCorrProvider> {
  public:
    explicit DYbbtautauCorrProvider(const std::string& fileName)
        : corrections_(CorrectionSet::from_file(fileName)),
          dyWeight_(corrections_->at("dy_weight")) {}

    float getWeight(const std::string& era,
                    int njets,
                    int ntags,
                    float ptll,
                    const std::string& syst) const {
        if (njets < 2) {
            return 1.f;
        }

        return dyWeight_->evaluate({era, njets, ntags, ptll, syst});
    }

  private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref dyWeight_;
};

}  // namespace correction