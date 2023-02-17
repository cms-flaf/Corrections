#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class TrigCorrProvider : public CorrectionsBase<TrigCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        tautrg_ditau_DM0 = 0,
        tautrg_ditau_DM1 = 1,
        tautrg_ditau_3Prong = 2,
        mutrg_singleMu = 3,
        eletrg_singleEle = 4,
    };
    using wpsMapType = std::map<Channel, std::vector<std::pair<std::string, int> > >;
    static bool isTwoProngDM(int dm)
    {
        static const std::set<int> twoProngDMs = { 5, 6 };
        return twoProngDMs.count(dm);
    }
    static const std::string& getTauScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> tau_names = {
            { UncScale::Down, "down" },
            { UncScale::Central, "nom" },
            { UncScale::Up, "up" },
        };
        return tau_names.at(scale);
    }
    static const std::string& getMuScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> tau_names = {
            { UncScale::Down, "systdown" },
            { UncScale::Central, "sf" },
            { UncScale::Up, "systup" },
        };
        return tau_names.at(scale);
    }
    static bool sourceApplies_tau_fromCorrLib(UncSource source, int decayMode, const std::string& trg_type)
    {
        if(trg_type=="ditau"){
            if(source == UncSource::tautrg_ditau_DM0 && decayMode == 0) return true;
            if(source == UncSource::tautrg_ditau_DM1 && ( decayMode == 1 || decayMode == 2 )) return true;
            if(source == UncSource::tautrg_ditau_3Prong && ( decayMode == 10 || decayMode == 11 )) return true;
        }
        return false;
    }

    TrigCorrProvider(const std::string& tauFileName, const std::string& deepTauVersion, const wpsMapType& wps_map,
                    const std::string& muFileName, const std::string& period, const std::string& mu_trigger,
                    const std::string& eleFileName) :
        tau_corrections_(CorrectionSet::from_file(tauFileName)),
        tau_trg_(tau_corrections_->at("tau_trigger")),
        deepTauVersion_(deepTauVersion),
        wps_map_(wps_map),
        mu_corrections_(CorrectionSet::from_file(muFileName)),
        mu_trg_(mu_corrections_->at(mu_trigger)),
        period_(period)
    {

        auto eleFile = root_ext::OpenRootFile(eleFileName);
        histo_ele_SF.reset(root_ext::ReadCloneObject<TH2>(*eleFile, "EGamma_SF2D", "EGamma_SF2D", true));

    }

    float getTauSF_fromCorrLib(const LorentzVectorM& Tau_p4, int Tau_decayMode, const std::string& trg_type, Channel ch, UncSource source, UncScale scale) const
    {
        if(isTwoProngDM(Tau_decayMode)) throw std::runtime_error("no SF for two prong tau decay modes");
        const auto & wpVSjet = wps_map_.at(ch).at(2);
        const UncScale tau_scale = sourceApplies_tau_fromCorrLib(source, Tau_decayMode, trg_type)
                                        ? scale : UncScale::Central;
        const std::string& scale_str = getTauScaleStr(tau_scale);
        return tau_trg_->evaluate({Tau_p4.pt(), Tau_decayMode, trg_type, wpVSjet.first,"sf", scale_str});
    }

    float getMuSF_fromCorrLib(const LorentzVectorM& Mu_p4, UncSource source, UncScale scale) const
    {
        const UncScale mu_scale = source== UncSource::mutrg_singleMu ? scale : UncScale::Central;
        const std::string& scale_str = getMuScaleStr(mu_scale);
        return mu_trg_->evaluate({period_, std::abs(Mu_p4.Eta()), Mu_p4.Pt(), scale_str});
    }

    float getEleSF_fromRootFile(const LorentzVectorM& Ele_p4, UncSource source, UncScale scale) const
    {
        const UncScale ele_scale = source== UncSource::eletrg_singleEle ? scale : UncScale::Central;
        const auto x_axis = histo_ele_SF->GetXaxis();
        int x_bin = x_axis->FindFixBin(Ele_p4.Eta());
        if(x_bin < 1)
            x_bin =1;
        if( x_bin > x_axis->GetNbins() )
            x_bin = x_axis->GetNbins();
        const auto y_axis = histo_ele_SF->GetYaxis();

        int y_bin = y_axis->FindFixBin(Ele_p4.Pt());
        if(y_bin < 1)
            y_bin =1;
        if( y_bin > y_axis->GetNbins() )
            y_bin = y_axis->GetNbins();

        return histo_ele_SF->GetBinContent(x_bin,y_bin) + static_cast<int>(ele_scale) * histo_ele_SF->GetBinError(x_bin,y_bin);
    }

private:
    std::unique_ptr<CorrectionSet> tau_corrections_;
    Correction::Ref tau_trg_;
    const std::string deepTauVersion_;
    const wpsMapType wps_map_;
    std::unique_ptr<CorrectionSet> mu_corrections_;
    Correction::Ref mu_trg_;
    const std::string period_;
    std::unique_ptr<TH2> histo_ele_SF;

} ;

} // namespace correction