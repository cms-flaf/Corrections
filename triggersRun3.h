#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class TrigCorrProvider : public CorrectionsBase<TrigCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        IsoMu24 = 0,
        singleEle = 1,
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
    static const std::string& getEleScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> ele_names = {
            { UncScale::Down, "sfdown" },
            { UncScale::Central, "sf" },
            { UncScale::Up, "sfup" },
        };
        return ele_names.at(scale);
    }

    TrigCorrProvider(const std::string& muon_trg_file, const std::string& ele_trg_file, const std::string& muon_trg_key, const std::string& ele_trg_key,  const std::string& era) :
        mutrgcorrections_(CorrectionSet::from_file(muon_trg_file)),
        etrgcorrections_(CorrectionSet::from_file(ele_trg_file))
    {
        if (era == "2022_Summer22" || era == "2022_Summer22EE" || era == "2023_Summer23" || era == "2023_Summer23BPix"){
            muTrgCorrections["Central"]=mutrgcorrections_->at(muon_trg_key);
            eleTrgCorrections["Central"]=etrgcorrections_->at(ele_trg_key);
        } else {
           throw std::runtime_error("Era not supported");
        }
    }

    float getSF_singleEleWpTight(const LorentzVectorM & part_p4, std::string year, UncSource source, UncScale scale) const {
        float corr_SF = 1;
        const std::string& scale_str = getEleScaleStr(scale);
        std::string Working_Point = "HLT_SF_Ele30_MVAiso80ID";
        corr_SF = eleTrgCorrections.at(getUncSourceName(source))->evaluate({year, scale_str, Working_Point, part_p4.Eta(), part_p4.Pt()});
        return corr_SF ;
    }
    float getSF_singleIsoMu(const LorentzVectorM & part_p4, std::string year, UncSource source, UncScale scale) const {
        float corr_SF = 1;
        const std::string& scale_str = getMuScaleStr(scale);
        corr_SF = muTrgCorrections.at(getUncSourceName(source))->evaluate({ abs(part_p4.Eta()), part_p4.Pt(), scale_str});
        return corr_SF ;
    }
private:
    static std::string& getUncSourceName(UncSource source) {
        static std::string sourcename = "Central";
        if (source==UncSource::IsoMu24) sourcename = "Central"; //Still get from the central Key, maybe rename later
        if (source==UncSource::singleEle) sourcename = "Central"; //Still get from the central Key, maybe rename later
        //(if source==SourceName) sourcename = SourceName
        return sourcename;
    }

private:
    std::unique_ptr<CorrectionSet> mutrgcorrections_, etrgcorrections_ ;
    std::map<std::string, Correction::Ref> muTrgCorrections, eleTrgCorrections;
    const std::string period_;
} ;



} // namespace correction