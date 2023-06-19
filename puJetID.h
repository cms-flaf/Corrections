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
    RVecF getPUJetID_eff(const RVecLV & Jet_p4, const std::string working_point, UncSource source, UncScale scale) const {
        RVecF weights(Jet_p4.size(), 1);
        for(size_t jet_idx = 0 ; jet_idx < Jet_p4.size(); jet_idx++)
        {
            if(Jet_p4[jet_idx].Pt()<20 || std::abs(Jet_p4[jet_idx].Eta())>5){
                weights[jet_idx] = 0.;
                continue;
            }
            const UncScale PUJetID_scale = sourceApplies(source,Jet_p4[jet_idx].Pt())
                                           ? scale : UncScale::Central;
            const std::string& scale_str = getScaleStr(PUJetID_scale);
            if(PUJetID_scale == UncScale::Central){
                weights[jet_idx] = 1.;
            }
            weights[jet_idx] = static_cast<float>(puJetEff_->evaluate({Jet_p4[jet_idx].Eta(), Jet_p4[jet_idx].Pt(), scale_str, working_point}));
        }
        return weights;
    }

private:

private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref puJetEff_;

};

} // namespace correction