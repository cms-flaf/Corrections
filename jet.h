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
        BBEC1_ = 7,
        Absolute_ = 8,
        EC2_ = 9,
        HF_ = 10,
        RelativeSample_ = 11,
        JER = 12
    };
    /*
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
    }*/
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
    static const int GetJesIdx(UncSource source, UncScale scale){
        return(static_cast<int>(source)*2+GetScaleIdx(scale));
    }

    JetCorrProvider(const std::string& ptResolution,const std::string& ptResolutionSF, const std::string& JesTxtFile, const std::string& year)
    {
        jvc_JER.setSmearing(ptResolution, ptResolutionSF, false, true, 0.2, 3);
        std::vector<std::string> JesNames = {"FlavorQCD","RelativeBal","HF","BBEC1","EC2","Absolute","Total","BBEC1_"+year,"Absolute_"+year,"EC2_"+year,"HF_"+year,"RelativeSample_"+year};
        for (auto& jes : JesNames){
            jvc_JES.addJESUncertainty(jes,JetCorrectorParameters{JesTxtFile,jes});
        }
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
        auto result = jvc_JER.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
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
        return jvc_JER.getResolution(Jet_pt, Jet_eta, rho);
    }

    RVecLV getJesJet(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi,
                    const RVecF& Jet_mass, const RVecF& Jet_rawFactor, const RVecF& Jet_area,
                    const RVecI& Jet_jetId, const float rho, const RVecI& Jet_partonFlavour,
                    std::uint32_t seed, const RVecF& GenJet_pt, const RVecF& GenJet_eta,
                    const RVecF& GenJet_phi, const RVecF& GenJet_mass, int event,
                    UncSource source, UncScale scale) const {
        auto result = jvc_JES.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
                                    Jet_area, Jet_jetId, rho, Jet_partonFlavour, seed,
                                    GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, event);
        RVecLV shifted_p4(Jet_pt.size());
        for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
            int scale_idx = GetJesIdx(source, scale);
            shifted_p4[jet_idx] = LorentzVectorM(result.pt(scale_idx)[jet_idx], Jet_eta[jet_idx],
            Jet_phi[jet_idx], result.mass(scale_idx)[jet_idx]);
        }
        return shifted_p4;
    }

private:

    JetVariationsCalculator jvc_JER ;
    JetVariationsCalculator jvc_JES ;
};
} // namespace correction