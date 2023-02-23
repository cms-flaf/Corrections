#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class bTagCorrProvider : public CorrectionsBase<bTagCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        btagSFbc_uncorrelated = 0,
        btagSFlight_uncorrelated = 1,
        btagSFbc_correlated = 2,
        btagSFlight_correlated = 3,
    };


    static WorkingPointsbTag getWPFromString(const std::string wp_string)
    {
        static const std::map< std::string,WorkingPointsbTag> wps = {
            { "Tight", WorkingPointsbTag::Tight },
            { "Medium", WorkingPointsbTag::Medium },
            { "Loose", WorkingPointsbTag::Loose },
        };
        return wps.at(wp_string);
    }
    static const std::string& getScaleStr(UncScale scale, UncSource source)
    {
        static const std::map<std::pair<UncScale, UncSource>, std::string> names = {
            { {UncScale::Down, UncSource::btagSFbc_uncorrelated}, "down_uncorrelated" },
            { {UncScale::Down, UncSource::btagSFlight_uncorrelated}, "down_uncorrelated" },
            { {UncScale::Down, UncSource::btagSFbc_correlated}, "down_correlated" },
            { {UncScale::Down, UncSource::btagSFlight_correlated}, "down_correlated" },
            { {UncScale::Central, UncSource::Central}, "central"},
            { {UncScale::Up, UncSource::btagSFbc_uncorrelated}, "up_uncorrelated" },
            { {UncScale::Up, UncSource::btagSFlight_uncorrelated}, "up_uncorrelated" },
            { {UncScale::Up, UncSource::btagSFbc_correlated}, "up_correlated" },
            { {UncScale::Up, UncSource::btagSFlight_correlated}, "up_correlated" },
        };
        return names.at(std::make_pair(scale, source));
    }

    static bool sourceApplies(UncSource source, int Jet_Flavour)
    {
        if(source == UncSource::btagSFbc_uncorrelated && (Jet_Flavour == 4 || Jet_Flavour==5) ) return true;
        if(source == UncSource::btagSFlight_uncorrelated && Jet_Flavour == 0 ) return true;
        if(source == UncSource::btagSFbc_correlated && (Jet_Flavour == 4 || Jet_Flavour==5) ) return true;
        if(source == UncSource::btagSFlight_correlated && Jet_Flavour == 0 ) return true;
        return false;
    }

    using histEffmap= std::map<std::pair<WorkingPointsbTag, int>, std::shared_ptr<TH2>> ;
    bTagCorrProvider(const std::string& fileName, const std::string& efficiencyFileName) :
        corrections_(CorrectionSet::from_file(fileName)),
        deepJet_incl_(corrections_->at("deepJet_incl")),
        deepJet_comb_(corrections_->at("deepJet_comb")),
        deepJet_wp_values_(corrections_->at("deepJet_wp_values"))
    {
        if(efficiencyFileName.size()>0){
            auto efficiencyFile = root_ext::OpenRootFile(efficiencyFileName);
            static const std::vector<std::string> WpNames = {"Loose", "Medium", "Tight"};
            static const std::vector<int> Flavours = {0, 4, 5};
            for(const auto & flav : Flavours){
                auto denum = root_ext::ReadCloneObject<TH2>(*efficiencyFile, "jet_pt_eta_"+std::to_string(flav), "", true);
                for (const auto & WPName : WpNames){
                    auto num = root_ext::ReadCloneObject<TH2>(*efficiencyFile,  "jet_pt_eta_"+std::to_string(flav)+"_"+WPName,"", true);
                    num->Divide(denum);
                    histMapEfficiency[std::make_pair(getWPFromString(WPName),flav)] = std::shared_ptr<TH2>(num);
                }
            }
        }
        wp_names = {
            { WorkingPointsbTag::Tight, "T" },
            { WorkingPointsbTag::Medium, "M" },
            { WorkingPointsbTag::Loose, "L" },
        };
    }

    float getWPvalue(WorkingPointsbTag wp) const {
        return deepJet_wp_values_->evaluate({wp_names.at(wp)});
    }

    float getSF(const RVecLV& Jet_p4, const RVecB& pre_sel, const RVecI& Jet_Flavour,const RVecF& Jet_bTag_score, WorkingPointsbTag btag_wp, UncSource source, UncScale scale) const
    {
        float eff_MC_tot = 1.;
        float eff_data_tot = 1.;
        for(size_t jet_idx = 0; jet_idx < Jet_p4.size(); jet_idx++){
            if(!pre_sel[jet_idx]) continue;
            const UncScale jet_tag_scale = sourceApplies(source, Jet_Flavour[jet_idx])
                                           ? scale : UncScale::Central;
            const std::string& scale_str = getScaleStr(jet_tag_scale, source);
            float eff_MC = GetNormalisedEfficiency(GetBtagEfficiency(Jet_p4[jet_idx].pt(), std::abs(Jet_p4[jet_idx].eta()), Jet_Flavour[jet_idx], btag_wp));
            auto sf_source = Jet_Flavour[jet_idx] == 0 ? &deepJet_incl_ : &deepJet_comb_;
            float SF = (*sf_source)->evaluate({scale_str, wp_names.at(btag_wp),  Jet_Flavour[jet_idx], std::abs(Jet_p4[jet_idx].eta()),Jet_p4[jet_idx].pt() });
            float eff_data = GetNormalisedEfficiency(eff_MC*SF);
            if(Jet_bTag_score[jet_idx] > getWPvalue(btag_wp)) {
                eff_MC_tot*= eff_MC;
                eff_data_tot*= eff_data;
            } else {
                eff_MC_tot*= (1-eff_MC);
                eff_data_tot*= (1-eff_data);
            }
        }

        return eff_MC_tot!=0 ? eff_data_tot/eff_MC_tot : 0.;
    }
private:
    float GetBtagEfficiency(float pt, float eta, int flavour, WorkingPointsbTag wp) const {
        const auto key = std::make_pair(wp, flavour);
        auto iter = histMapEfficiency.find(key);
        if(iter == histMapEfficiency.end())
            throw analysis::exception("ERROR: bTagEfficiency not found in the map! Flavour= %1% VS WP = %2%")
            % flavour % wp_names.at(wp);
        const auto& hist = iter->second;
        const auto x_axis = hist->GetXaxis();
        int x_bin = x_axis->FindFixBin(pt);
        if(x_bin < 1)
            x_bin =1;
        if( x_bin > x_axis->GetNbins() )
            x_bin = x_axis->GetNbins();
        const auto y_axis = hist->GetYaxis();

        int y_bin = y_axis->FindFixBin(eta);
        if(y_bin < 1)
            y_bin =1;
        if( y_bin > y_axis->GetNbins() )
            y_bin = y_axis->GetNbins();

        return hist->GetBinContent(x_bin,y_bin) ;
    }

    static float GetNormalisedEfficiency(float eff){
        if(eff > 1. ) return 1.;
        if (eff<0. ) return 0.;
        return eff;
    }
private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref deepJet_incl_, deepJet_comb_,deepJet_wp_values_;
    histEffmap histMapEfficiency;
    std::map<WorkingPointsbTag,std::string> wp_names;

};

} //namespace correction