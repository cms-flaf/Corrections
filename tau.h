#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class TauCorrProvider {
public:
    enum class GenLeptonMatch : int {
        Electron = 1,
        Muon = 2,
        TauElectron = 3,
        TauMuon = 4,
        Tau = 5,
        NoMatch = 6
    };

    enum class UncSource : int {
        Central = -1,
        TauES_DM0 = 0,
        TauES_DM1 = 1,
        TauES_3prong = 2,
        EleFakingTauES_DM0 = 3,
        EleFakingTauES_DM1 = 4,
        MuFakingTauES = 5
    };

    static void Initialize(const std::string& fileName, const std::string& deepTauVersion)
    {
        _getGlobal() = std::make_unique<TauCorrProvider>(fileName, deepTauVersion);
    }

    static const TauCorrProvider& getGlobal()
    {
        const auto& corr = _getGlobal();
        if(!corr)
            throw std::runtime_error("TauCorrProvider: not initialized.");
        return *corr;
    }

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
        } else if(genMatch == GenLeptonMatch::Electron || genMatch == GenLeptonMatch::TauElectron) {
            if(source == UncSource::EleFakingTauES_DM0 && decayMode == 0) return true;
            if(source == UncSource::EleFakingTauES_DM1 && ( decayMode == 1 || decayMode == 2 )) return true;
        } else if(genMatch == GenLeptonMatch::Muon || genMatch == GenLeptonMatch::TauMuon) {
            if(source == UncSource::MuFakingTauES) return true;
        }
        return false;
    }

    TauCorrProvider(const std::string& fileName, const std::string& deepTauVersion) :
        corrections_(CorrectionSet::from_file(fileName)),
        tau_es_(corrections_->at("tau_energy_scale")),
        tau_vs_e_(corrections_->at(deepTauVersion + "VSe")),
        tau_vs_mu_(corrections_->at(deepTauVersion + "VSmu")),
        tau_vs_jet_(corrections_->at(deepTauVersion + "VSjet")),
        deepTauVersion_(deepTauVersion)
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

private:
    static std::unique_ptr<TauCorrProvider>& _getGlobal()
    {
        static std::unique_ptr<TauCorrProvider> corr;
        return corr;
    }

    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref tau_es_, tau_vs_e_, tau_vs_mu_, tau_vs_jet_;
    std::string deepTauVersion_;
};

} // namespace correction