#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class bTagCorrProvider : public CorrectionsBase<bTagCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
    };

    static const std::string& getWPStr(WorkingPointsbTag wp)
    {
        static const std::map<WorkingPointsbTag, std::string> names = {
            { WorkingPointsbTag::Tight, "T" },
            { WorkingPointsbTag::Medium, "M" },
            { WorkingPointsbTag::Loose, "L" },
        };
        return names.at(wp);
    }
    static WorkingPointsbTag getWPFromString(const std::string wp_string)
    {
        static const std::map< std::string,WorkingPointsbTag> wps = {
            { "Tight", WorkingPointsbTag::Tight },
            { "Medium", WorkingPointsbTag::Medium },
            { "Loose", WorkingPointsbTag::Loose },
        };
        return wps.at(wp_string);
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
            const std::vector<std::string> WpNames = {"Loose", "Medium", "Tight"};
            const std::vector<int> Flavours = {0, 4, 5};
            for(const auto & flav : Flavours){
                auto denum = root_ext::ReadCloneObject<TH2>(*efficiencyFile, "jet_pt_eta_"+std::to_string(flav), "", true);
                for (const auto & WPName : WpNames){
                    auto num = root_ext::ReadCloneObject<TH2>(*efficiencyFile,  "jet_pt_eta_"+std::to_string(flav)+"_"+WPName,"", true);
                    num->Divide(denum);
                    histMapEfficiency[std::make_pair(getWPFromString(WPName),flav)] = std::shared_ptr<TH2>(num);
                }
            }
        }
    }

    float getWPvalue(WorkingPointsbTag wp) const {
        return deepJet_wp_values_->evaluate({getWPStr(wp)});
    }

    float getSF(const RVecLV& Jet_p4, const RVecB& pre_sel, const RVecI& Jet_Flavour,const RVecF& Jet_bTag_score, WorkingPointsbTag btag_wp, UncSource source, UncScale scale) const
    {
        float eff_MC_tot = 1.;
        float eff_data_tot = 1.;
        for(size_t jet_idx = 0; jet_idx < Jet_p4.size(); jet_idx++){
            if(!pre_sel[jet_idx]) continue;

            float eff_MC = GetNormalisedEfficiency(GetBtagEfficiency(Jet_p4[jet_idx].pt(), std::abs(Jet_p4[jet_idx].eta()), Jet_Flavour[jet_idx], btag_wp));
            auto sf_source = Jet_Flavour[jet_idx] == 0 ? &deepJet_incl_ : &deepJet_comb_;
            float SF = (*sf_source)->evaluate({"central",getWPStr(btag_wp),  Jet_Flavour[jet_idx], std::abs(Jet_p4[jet_idx].eta()),Jet_p4[jet_idx].pt() });
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
            % flavour % getWPStr(wp);
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


};

} //namespace correction