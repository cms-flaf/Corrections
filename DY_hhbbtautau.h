// #pragma once
// #include "correction.h"
// #include "corrections.h"

// namespace correction {

//     class DYbbtautauCorrProducer : public CorrectionsBase<DYbbtautauCorrProducer> {
//       public:
//         static const std::string& getScaleStr(UncScale scale) {
//             static const std::map<UncScale, std::string> names = {
//                 {UncScale::Down, "down"},
//                 {UncScale::Central, "nominal"},
//                 {UncScale::Up, "up"},
//             };
//             return names.at(scale);
//         }
//         DYbbtautauCorrProducer()
//             : corrections_(CorrectionSet::from_file(fileName)), puweight(corrections_->at(jsonName)) {}

//         float getWeight(UncScale scale, float Pileup_nTrueInt) const {
//             const std::string& scale_str = getScaleStr(scale);
//             return puweight->evaluate({Pileup_nTrueInt, scale_str});
//         }

//       private:
//         std::unique_ptr<CorrectionSet> corrections_;
//         Correction::Ref DY_corr_weight;
//     };

// }  // namespace correction



#pragma once

#include <algorithm>
#include <map>
#include <memory>
#include <string>

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

        //const int njets_eval = njets; //std::min(njets, 6);
        //const int ntags_eval = ntags; //std::min(ntags, 2);

        return dyWeight_->evaluate({era, njets, ntags, ptll, syst});
    }

  private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref dyWeight_;
};

}  // namespace correction