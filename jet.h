#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class JetCorrProvider : public CorrectionsBase<JetCorrProvider> {
public:
     enum class UncSource : int {
        Central = 0
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
    static bool sourceApplies(UncSource source)
    {
        return false;
    }
    JetCorrProvider(const std::string& ptResolution,const std::string& ptResolutionSF)
    {
        jetVarCalc.setSmearing(ptResolution, ptResolutionSF, false, true, 0.2, 3);
    }

    RVecLV getSmearing(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi,
                    const RVecF& Jet_mass, const RVecF& Jet_rawFactor, const RVecF& Jet_area,
                    const RVecI& Jet_jetId, const float rho, const RVecI& Jet_partonFlavour,
                    std::uint32_t seed, const RVecF& GenJet_pt, const RVecF& GenJet_eta,
                    const RVecF& GenJet_phi, const RVecF& GenJet_mass, int event,
                    UncSource source, UncScale scale) const
    {
        const UncScale jet_scale = sourceApplies(source)
                                           ? scale : UncScale::Central;
        const std::string& scale_str = getScaleStr(jet_scale);
        auto result = jetVarCalc.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
                                    Jet_area, Jet_jetId, rho, Jet_partonFlavour, seed,
                                    GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, event);
        RVecLV shifted_p4(Jet_pt.size());
        for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
            shifted_p4[jet_idx] = LorentzVectorM(result.pt(static_cast<int>(source))[jet_idx], Jet_eta[jet_idx],
            Jet_phi[jet_idx], result.mass(static_cast<int>(source))[jet_idx]);
        }
        return shifted_p4;
    }

private:
    JetVariationsCalculator jetVarCalc ;
};
} // namespace correction