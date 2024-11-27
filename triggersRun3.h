#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class TrigCorrProvider : public CorrectionsBase<TrigCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        IsoMu24 = 0,
    };
    static const std::string& getMuScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> mu_names = {
            { UncScale::Down, "systdown" },
            { UncScale::Central, "nominal" },
            { UncScale::Up, "systup" },
        };
        return mu_names.at(scale);
    }
    

    TrigCorrProvider(const std::string& fileName, const std::string& era) :
        corrections_(CorrectionSet::from_file(fileName))
    {
        if (era == "2022_Summer22" || era == "2022_Summer22EE" || era == "2023_Summer23" || era == "2023_Summer23BPix"){
            muTrgCorrections["Central"]=corrections_->at("NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight");
            //muTrgCorrections["SourceName"]=corrections_->at("SourceName");
        } else {
           throw std::runtime_error("Era not supported");
        }
    }



    float getSF(const LorentzVectorM & muon_p4, UncSource source, UncScale scale) const {
        const std::string& scale_str = getMuScaleStr(scale);
        float corr_SF = muTrgCorrections.at(getUncSourceName(source))->evaluate({ abs(muon_p4.Eta()), muon_p4.Pt(), scale_str});
        return corr_SF ;
    }

private:
    static std::string& getUncSourceName(UncSource source) {
        static std::string sourcename = "Central";
        if (source==UncSource::IsoMu24) sourcename = "Central"; //Still get from the central Key, maybe rename later
        //(if source==SourceName) sourcename = SourceName
        return sourcename;
    }

private:
    std::unique_ptr<CorrectionSet> corrections_;
    std::map<std::string, Correction::Ref> muTrgCorrections;
    const std::string period_;
} ;



} // namespace correction