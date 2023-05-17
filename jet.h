#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class JetCorrProvider : public CorrectionsBase<JetCorrProvider> {
public:
     enum class UncSource : int {
        Central = -1,
        Total = 0,
        RelativeBal = 1,
        HF = 2,
        BBEC1 = 3,
        EC2 = 4,
        Absolute = 5,
        FlavorQCD = 6,
        BBEC1_2018 = 7,
        Absolute_2018 = 8,
        EC2_2018 = 9,
        HF_2018 = 10,
        RelativeSample_2018 = 11,
        BBEC1_2017 = 12,
        Absolute_2017 = 13,
        EC2_2017 = 14,
        HF_2017 = 15,
        RelativeSample_2017 = 16,
        BBEC1_2016 = 17,
        Absolute_2016 = 18,
        EC2_2016 = 19,
        HF_2016 = 20,
        RelativeSample_2016 = 21
    };

    static const std::string getJesName(UncSource source ){
        static const std::map<UncSource, std::string> JesNames{
        {UncSource::FlavorQCD,"FlavorQCD"},
        {UncSource::RelativeBal,"RelativeBal"},
        {UncSource::HF,"HF"},
        {UncSource::BBEC1,"BBEC1"},
        {UncSource::EC2,"EC2"},
        {UncSource::Absolute,"Absolute"},
        {UncSource::Total,"Total"},
        {UncSource::BBEC1_2018,"BBEC1_2018"},
        {UncSource::Absolute_2018,"Absolute_2018"},
        {UncSource::EC2_2018,"EC2_2018"},
        {UncSource::HF_2018,"HF_2018"},
        {UncSource::RelativeSample_2018,"RelativeSample_2018"},
        {UncSource::BBEC1_2017,"BBEC1_2017"},
        {UncSource::Absolute_2017,"Absolute_2017"},
        {UncSource::EC2_2017,"EC2_2017"},
        {UncSource::HF_2017,"HF_2017"},
        {UncSource::RelativeSample_2017,"RelativeSample_2017"},
        {UncSource::BBEC1_2016,"BBEC1_2016"},
        {UncSource::Absolute_2016,"Absolute_2016"},
        {UncSource::EC2_2016,"EC2_2016"},
        {UncSource::HF_2016,"HF_2016"},
        {UncSource::RelativeSample_2016,"RelativeSample_2016"}
    };
        return JesNames.at(source);
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
    static const int GetScaleIdx(UncScale scale){
        static const std::map<UncScale, int> scale_indexes = {
            {UncScale::Up, 1},
            {UncScale::Down,2},
            {UncScale::Central,0},
        };
        return scale_indexes.at(scale);
    }

    JetCorrProvider(const std::string& ptResolution,const std::string& ptResolutionSF, const std::string& JesTxtFile)
    {
        jetVarCalc.setSmearing(ptResolution, ptResolutionSF, false, true, 0.2, 3);
        JesTxtFile_= JesTxtFile;
    }

    RVecLV getSmearing(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi,
                    const RVecF& Jet_mass, const RVecF& Jet_rawFactor, const RVecF& Jet_area,
                    const RVecI& Jet_jetId, const float rho, const RVecI& Jet_partonFlavour,
                    std::uint32_t seed, const RVecF& GenJet_pt, const RVecF& GenJet_eta,
                    const RVecF& GenJet_phi, const RVecF& GenJet_mass, int event,
                    UncSource source, UncScale scale) const
    {
        const UncScale jet_scale = source == UncSource::Central ? UncScale::Central : scale;
        const std::string& scale_str = getScaleStr(jet_scale);
        auto result = jetVarCalc.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
                                    Jet_area, Jet_jetId, rho, Jet_partonFlavour, seed,
                                    GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, event);
        RVecLV shifted_p4(Jet_pt.size());
        for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
            int scale_idx = GetScaleIdx(scale);
            shifted_p4[jet_idx] = LorentzVectorM(result.pt(scale_idx)[jet_idx], Jet_eta[jet_idx],
            Jet_phi[jet_idx], result.mass(scale_idx)[jet_idx]);
        }
        return shifted_p4;
    }
    RVecF getResolution(const RVecF& Jet_pt, const RVecF& Jet_eta, const float rho) const {
        return jetVarCalc.getResolution(Jet_pt, Jet_eta, rho);
    }

    RVecLV getJesJet(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi,
                    const RVecF& Jet_mass, const RVecF& Jet_rawFactor, const RVecF& Jet_area,
                    const RVecI& Jet_jetId, const float rho, const RVecI& Jet_partonFlavour,
                    std::uint32_t seed, const RVecF& GenJet_pt, const RVecF& GenJet_eta,
                    const RVecF& GenJet_phi, const RVecF& GenJet_mass, int event,
                    UncSource source, UncScale scale) const {
        JetVariationsCalculator jvc ;
        JetCorrectorParameters jetParams(JesTxtFile_,getJesName(source));
        jvc.addJESUncertainty(getJesName(source),JetCorrectorParameters{JesTxtFile_,getJesName(source)});
        auto result = jvc.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
                                    Jet_area, Jet_jetId, rho, Jet_partonFlavour, seed,
                                    GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, event);
        RVecLV shifted_p4(Jet_pt.size());
        for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
            int scale_idx = GetScaleIdx(scale);
            shifted_p4[jet_idx] = LorentzVectorM(result.pt(scale_idx)[jet_idx], Jet_eta[jet_idx],
            Jet_phi[jet_idx], result.mass(scale_idx)[jet_idx]);
        }
        return shifted_p4;
    }

private:

    JetVariationsCalculator jetVarCalc ;
    std::string JesTxtFile_;
};
} // namespace correction