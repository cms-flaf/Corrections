#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class JetCorrProvider : public CorrectionsBase<JetCorrProvider> {
public:
     enum class UncSource : int {
        Central = -1,
        JER = 0,
        Total = 1,
        RelativeBal = 2,
        HF = 3,
        BBEC1 = 4,
        EC2 = 5,
        Absolute = 6,
        FlavorQCD = 7,
        BBEC1_ = 8,
        Absolute_ = 9,
        EC2_ = 10,
        HF_ = 11,
        RelativeSample_ = 12
    };

    static const UncSource getJesFromName(std::string sourceName ){
        static const std::map< std::string, UncSource> JesNames{
        {"FlavorQCD",UncSource::FlavorQCD},
        {"RelativeBal",UncSource::RelativeBal},
        {"HF",UncSource::HF},
        {"BBEC1",UncSource::BBEC1},
        {"EC2",UncSource::EC2},
        {"Absolute",UncSource::Absolute},
        {"Total",UncSource::Total},
        {"BBEC1_2018",UncSource::BBEC1_},
        {"Absolute_2018",UncSource::Absolute_},
        {"EC2_2018",UncSource::EC2_},
        {"HF_2018",UncSource::HF_},
        {"RelativeSample_2018",UncSource::RelativeSample_},
        {"BBEC1_2017",UncSource::BBEC1_},
        {"Absolute_2017",UncSource::Absolute_},
        {"EC2_2017",UncSource::EC2_},
        {"HF_2017",UncSource::HF_},
        {"RelativeSample_2017",UncSource::RelativeSample_},
        {"BBEC1_2016",UncSource::BBEC1_},
        {"Absolute_2016",UncSource::Absolute_},
        {"EC2_2016",UncSource::EC2_},
        {"HF_2016",UncSource::HF_},
        {"RelativeSample_2016",UncSource::RelativeSample_}
    };

        return JesNames.at(sourceName);
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
    static const int GetJesIdx(UncSource source, UncScale scale){
        if (source == UncSource::Central) return 0;
        return(static_cast<int>(source)*2+GetScaleIdx(scale));
    }

    JetCorrProvider(const std::string& ptResolution,const std::string& ptResolutionSF, const std::string& JesTxtFile, const std::string& year)
    {
        jvc_total.setSmearing(ptResolution, ptResolutionSF, false, true, 0.2, 3);
        JesNames = {"FlavorQCD","RelativeBal","HF","BBEC1","EC2","Absolute","Total","BBEC1_"+year,"Absolute_"+year,"EC2_"+year,"HF_"+year,"RelativeSample_"+year};
        for (auto& jes : JesNames){
            jvc_total.addJESUncertainty(jes,JetCorrectorParameters{JesTxtFile,jes});
        }
    }


    std::map<std::pair<UncSource,UncScale>, RVecLV> getShiftedP4(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi,
                    const RVecF& Jet_mass, const RVecF& Jet_rawFactor, const RVecF& Jet_area,
                    const RVecI& Jet_jetId, const float rho, const RVecI& Jet_partonFlavour,
                    std::uint32_t seed, const RVecF& GenJet_pt, const RVecF& GenJet_eta,
                    const RVecF& GenJet_phi, const RVecF& GenJet_mass, int event) const {
        std::map<std::pair<UncSource,UncScale>, RVecLV> all_shifted_p4;
        auto result = jvc_total.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
                                    Jet_area, Jet_jetId, rho, Jet_partonFlavour, seed,
                                    GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, event);
        size_t nVariations = 1 + 2 + 2*JesNames.size();
        std::vector<RVecLV> shifted_p4s(nVariations);
        /*
        std::vector<std::string> allVariations= {"Central","JER"};
        allVariations.insert(allVariations.end(), JesNames.begin(), JesNames.end());
        for (size_t iVar =0; iVar < nVariations ; iVar++){
            RVecLV shifted_p4(Jet_pt.size());
        }*/
        int scale_idx =  GetJesIdx(UncSource::Central, UncScale::Central);
        RVecLV shifted_p4_Central(Jet_pt.size());
        /* fill for central */
        for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
            shifted_p4_Central[jet_idx] = LorentzVectorM(result.pt(scale_idx)[jet_idx], Jet_eta[jet_idx],
            Jet_phi[jet_idx], result.mass(scale_idx)[jet_idx]);
        }
        all_shifted_p4.insert({{UncSource::Central, UncScale::Central}, shifted_p4_Central});

        std::vector<UncScale> uncScales={UncScale::Up, UncScale::Down};
        for (auto& uncScale : uncScales){
            /* fill for JER */
            RVecLV shifted_p4_JER(Jet_pt.size());
            int JER_scale_idx =  GetJesIdx(UncSource::JER, uncScale);
            for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
                shifted_p4_JER[jet_idx] = LorentzVectorM(result.pt(JER_scale_idx)[jet_idx], Jet_eta[jet_idx],
                Jet_phi[jet_idx], result.mass(JER_scale_idx)[jet_idx]);
            }
            all_shifted_p4.insert({{UncSource::JER, uncScale}, shifted_p4_JER});

            /* fill for JES */
            for (auto & jes : JesNames){
                RVecLV shifted_p4_JES(Jet_pt.size());
                int JES_scale_idx =  GetJesIdx(getJesFromName(jes), uncScale);
                for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
                    shifted_p4_JES[jet_idx] = LorentzVectorM(result.pt(JES_scale_idx)[jet_idx], Jet_eta[jet_idx],
                    Jet_phi[jet_idx], result.mass(JES_scale_idx)[jet_idx]);
                }
            all_shifted_p4.insert({{getJesFromName(jes), uncScale}, shifted_p4_JER});
            }
        }
        return all_shifted_p4;
    }
    /*
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
    }*/
    RVecF getResolution(const RVecF& Jet_pt, const RVecF& Jet_eta, const float rho) const {
        return jvc_total.getResolution(Jet_pt, Jet_eta, rho);
    }
    /*
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
    }*/

private:

    JetVariationsCalculator jvc_total ;
    std::vector<std::string> JesNames;
};
} // namespace correction