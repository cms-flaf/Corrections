#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class TauCorrProvider : public CorrectionsBase<TauCorrProvider> {
public:

    enum class UncSource : int {
        Central = -1,
        TauES_DM0 = 0,
        TauES_DM1 = 1,
        TauES_3prong = 2,
        EleFakingTauES_DM0 = 3,
        EleFakingTauES_DM1 = 4,
        MuFakingTauES = 5,
        TauID_genuineTau_DM0 = 6,
        TauID_genuineTau_DM1 = 7,
        TauID_genuineTau_3Prong = 8,
        TauID_genuineTau_Pt20_25 = 9,
        TauID_genuineTau_Pt25_30 = 10,
        TauID_genuineTau_Pt30_35 = 11,
        TauID_genuineTau_Pt35_40 = 12,
        TauID_genuineTau_Ptgt40 = 13,
        TauID_genuineElectron_barrel = 14,
        TauID_genuineElectron_endcaps = 15,
        TauID_genuineMuon_etaLt0p4 = 16,
        TauID_genuineMuon_eta0p4to0p8 = 17,
        TauID_genuineMuon_eta0p8to1p2 = 18,
        TauID_genuineMuon_eta1p2to1p7 = 19,
        TauID_genuineMuon_etaGt1p7 = 20,
    };

    using wpsMapType = std::map<Channel, std::vector<std::pair<std::string, int> > >;


    static bool isTwoProngDM(int dm)
    {
        static const std::set<int> twoProngDMs = { 5, 6 };
        return twoProngDMs.count(dm);
    }

    static const std::string& getScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> names = {
            { UncScale::Down, "down" },
            { UncScale::Central, "nom" },
            { UncScale::Up, "up" },
        };
        return names.at(scale);
    }

    static bool sourceApplies(UncSource source, const LorentzVectorM& p4, int decayMode, GenLeptonMatch genMatch)
    {
        if(genMatch == GenLeptonMatch::Tau) {
            if(source == UncSource::TauES_DM0 && decayMode == 0) return true;
            if(source == UncSource::TauES_DM1 && ( decayMode == 1 || decayMode == 2 )) return true;
            if(source == UncSource::TauES_3prong && ( decayMode == 10 || decayMode == 11 )) return true;
            if(source == UncSource::TauID_genuineTau_DM0 && decayMode==0 && p4.pt()>40) return true;
            if(source == UncSource::TauID_genuineTau_DM1 && ( decayMode == 1 || decayMode == 2 ) && p4.pt()>40) return true;
            if(source == UncSource::TauID_genuineTau_3Prong && ( decayMode == 10 || decayMode == 11 ) && p4.pt()>40) return true;
            if(source == UncSource::TauID_genuineTau_Pt20_25 && p4.pt()>20 && p4.pt()<=25 ) return true;
            if(source == UncSource::TauID_genuineTau_Pt25_30 && p4.pt()>25 && p4.pt()<=30 ) return true;
            if(source == UncSource::TauID_genuineTau_Pt30_35 && p4.pt()>30 && p4.pt()<=35 ) return true;
            if(source == UncSource::TauID_genuineTau_Pt35_40 && p4.pt()>35 && p4.pt()<=40 ) return true;
            if(source == UncSource::TauID_genuineTau_Ptgt40 && p4.pt()>40 ) return true;
        } else if(genMatch == GenLeptonMatch::Electron || genMatch == GenLeptonMatch::TauElectron) {
            if(source == UncSource::EleFakingTauES_DM0 && decayMode == 0) return true;
            if(source == UncSource::EleFakingTauES_DM1 && ( decayMode == 1 || decayMode == 2 )) return true;
            if(source == UncSource::TauID_genuineElectron_barrel && std::abs(p4.eta())<1.46) return true;
            if(source == UncSource::TauID_genuineElectron_endcaps && std::abs(p4.eta())>1.558) return true;
        } else if(genMatch == GenLeptonMatch::Muon || genMatch == GenLeptonMatch::TauMuon) {
            if(source == UncSource::MuFakingTauES) return true;
            if(source == UncSource::TauID_genuineMuon_etaLt0p4 && std::abs(p4.eta())>0 && std::abs(p4.eta())<=0.4) return true;
            if(source == UncSource::TauID_genuineMuon_eta0p4to0p8 && std::abs(p4.eta())>0.4 && std::abs(p4.eta())<=0.8) return true;
            if(source == UncSource::TauID_genuineMuon_eta0p8to1p2 && std::abs(p4.eta())>0.8 && std::abs(p4.eta())<=1.2) return true;
            if(source == UncSource::TauID_genuineMuon_eta1p2to1p7 && std::abs(p4.eta())>1.2 && std::abs(p4.eta())<=1.7) return true;
            if(source == UncSource::TauID_genuineMuon_etaGt1p7 && std::abs(p4.eta())>1.7 ) return true;
        }
        return false;
    }

    TauCorrProvider(const std::string& fileName, const std::string& deepTauVersion, const wpsMapType& wps_map, const std::map<Channel, std::string>& tauType_map) :
        corrections_(CorrectionSet::from_file(fileName)),
        tau_es_(corrections_->at("tau_energy_scale")),
        tau_vs_e_(corrections_->at(deepTauVersion + "VSe")),
        tau_vs_mu_(corrections_->at(deepTauVersion + "VSmu")),
        tau_vs_jet_(corrections_->at(deepTauVersion + "VSjet")),
        deepTauVersion_(deepTauVersion),
        wps_map_(wps_map),
        tauType_map_(tauType_map)
    {
    }

    RVecLV getES(const RVecLV& Tau_p4, const RVecI& Tau_decayMode, const RVecI& Tau_genMatch,
                 UncSource source, UncScale scale) const
    {
        RVecLV final_p4 = Tau_p4;
        for(size_t n = 0; n < Tau_p4.size(); ++n) {
            if(!isTwoProngDM(Tau_decayMode.at(n))) {
                const GenLeptonMatch genMatch = static_cast<GenLeptonMatch>(Tau_genMatch.at(n));
                const UncScale tau_scale = sourceApplies(source, Tau_p4[n], Tau_decayMode.at(n), genMatch)
                                           ? scale : UncScale::Central;
                const std::string& scale_str = getScaleStr(tau_scale);
                const double sf = tau_es_->evaluate({Tau_p4[n].pt(), Tau_p4[n].eta(), Tau_decayMode.at(n),
                static_cast<int>(genMatch), deepTauVersion_, scale_str});
                final_p4[n] *= sf;
            }
        }
        return final_p4;
    }

    float getSF(const LorentzVectorM& Tau_p4, int Tau_decayMode, int Tau_genMatch, Channel ch, UncSource source, UncScale scale) const
    {
        if(isTwoProngDM(Tau_decayMode)) throw std::runtime_error("no SF for two prong tau decay modes");
        const auto & wpVSe = wps_map_.at(ch).at(0);
        const auto & wpVSmu = wps_map_.at(ch).at(1);
        const auto & wpVSjet = wps_map_.at(ch).at(2);
        const auto & genuineTau_SFtype = tauType_map_.at(ch);
        const GenLeptonMatch genMatch = static_cast<GenLeptonMatch>(Tau_genMatch);
        if(genMatch == GenLeptonMatch::Tau) {
            const UncScale tau_had_scale = sourceApplies(source, Tau_p4, Tau_decayMode, genMatch)
                                           ? scale : UncScale::Central;
            const std::string& scale_str = scale != UncScale::Central  ? getScaleStr(tau_had_scale) : "default" ;
            const auto sf = tau_vs_jet_->evaluate({Tau_p4.pt(),Tau_decayMode, Tau_genMatch, wpVSjet.first, wpVSe.first, scale_str, genuineTau_SFtype});
            if(tau_had_scale != UncScale::Central && (wpVSe.second < static_cast<int>(WorkingPointsTauVSe::VLoose) || wpVSmu.second < static_cast<int>(WorkingPointsTauVSmu::Tight))){
                //const auto sf_central = tau_vs_jet_->evaluate({Tau_p4.pt(), Tau_decayMode, Tau_genMatch,  wpVSjet.first, wpVSe.first, "default", genuineTau_SFtype});
                //const float additional_unc = Tau_p4.pt() > 100 ? 0.15 : 0.05;
                //return sf_central * ( sf / sf_central + std::copysign(additional_unc, sf - sf_central));
                throw std::runtime_error("working points not supported");
            }


            return sf;
        }
        if(genMatch==GenLeptonMatch::Electron || genMatch == GenLeptonMatch::TauElectron){
            const UncScale tau_ele_scale = sourceApplies(source, Tau_p4, Tau_decayMode, genMatch)
                                           ? scale : UncScale::Central;
            const std::string& scale_str = getScaleStr(tau_ele_scale);
            return tau_vs_e_->evaluate({Tau_p4.eta(), Tau_genMatch, wpVSe.first, scale_str});
        }
         if(genMatch == GenLeptonMatch::Muon || genMatch == GenLeptonMatch::TauMuon){
            const UncScale tau_mu_scale = sourceApplies(source, Tau_p4, Tau_decayMode, genMatch)
                                           ? scale : UncScale::Central;
            const std::string& scale_str = getScaleStr(tau_mu_scale);
            return tau_vs_mu_->evaluate({Tau_p4.eta(), Tau_genMatch, wpVSmu.first, scale_str});
        }
        return 1.;
    }
private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref tau_es_, tau_vs_e_, tau_vs_mu_, tau_vs_jet_;
    std::string deepTauVersion_;
    const wpsMapType wps_map_;
    const std::map<Channel, std::string> tauType_map_;

};

} // namespace correction