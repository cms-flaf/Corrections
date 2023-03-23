#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class PUJetIDCorrProvider : public CorrectionsBase<PUJetIDCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        PUJetID_eff = 0,
    };

    static const std::string& getScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> names = {
            { UncScale::Down, "down" },
            { UncScale::Central, "nom" },
            { UncScale::Up, "up" },
        };
        return names.at(scale);
    }

     static bool sourceApplies(UncSource source, const float jet_Pt)
    {
        if(source == UncSource::PUJetID_eff && jet_Pt < 50) return true;
        return false;
    }

    PUJetIDCorrProvider(const std::string& fileName) :
    corrections_(CorrectionSet::from_file(fileName)),
    puJetEff_(corrections_->at("PUJetID_eff"))
    {
    }
    float getPUJetID_eff(const LorentzVectorM & jet_p4, const std::string working_point, UncSource source, UncScale scale) const {
        const UncScale PUJetID_scale = sourceApplies(source,jet_p4.Pt())
                                           ? scale : UncScale::Central;
        const std::string& scale_str = getScaleStr(PUJetID_scale);
        if(PUJetID_scale == UncScale::Central){
            return 1.
        }
        return puJetEff_->evaluate({jet_p4.Eta(), jet_p4.Pt(), scale_str, working_point}) ;

    }

private:

private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref puJetEff_;

};

} // namespace correction