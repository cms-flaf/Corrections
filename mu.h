#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class MuCorrProvider : public CorrectionsBase<MuCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        NUM_GlobalMuons_DEN_genTracks = 0,
        NUM_HighPtID_DEN_genTracks = 1,
        NUM_HighPtID_DEN_TrackerMuons = 2,
        NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight = 3,
        NUM_LooseID_DEN_genTracks = 4,
        NUM_LooseID_DEN_TrackerMuons = 5,
        NUM_LooseRelIso_DEN_LooseID = 6,
        NUM_LooseRelIso_DEN_MediumID = 7,
        NUM_LooseRelIso_DEN_MediumPromptID = 8,
        NUM_LooseRelIso_DEN_TightIDandIPCut = 9,
        NUM_LooseRelTkIso_DEN_HighPtIDandIPCut = 10,
        NUM_LooseRelTkIso_DEN_TrkHighPtIDandIPCut = 11,
        NUM_MediumID_DEN_genTracks = 12,
        NUM_MediumID_DEN_TrackerMuons = 13,
        NUM_MediumPromptID_DEN_genTracks = 14,
        NUM_MediumPromptID_DEN_TrackerMuons = 15,
        NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose = 16,
        NUM_SoftID_DEN_genTracks = 17,
        NUM_SoftID_DEN_TrackerMuons = 18,
        NUM_TightID_DEN_genTracks = 19,
        NUM_TightID_DEN_TrackerMuons = 20,
        NUM_TightRelIso_DEN_MediumID = 21,
        NUM_TightRelIso_DEN_MediumPromptID = 22,
        NUM_TightRelIso_DEN_TightIDandIPCut = 23,
        NUM_TightRelTkIso_DEN_HighPtIDandIPCut = 24,
        NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut = 25,
        NUM_TrackerMuons_DEN_genTracks = 26,
        NUM_TrkHighPtID_DEN_genTracks = 27,
        NUM_TrkHighPtID_DEN_TrackerMuons = 28,
    };


    /*
    static const std::map<WorkingPointsMuonID, std::string>& getWPNames()
    {
        static const std::map<WorkingPointsMuonID, std::string> names = {
            { WorkingPointsMuonID::HighPtID, "HighPtID"},
            { WorkingPointsMuonID::LooseID, "LooseID"},
            { WorkingPointsMuonID::MediumID, "MediumID"},
            { WorkingPointsMuonID::MediumPromptID, "MediumPromptID"},
            { WorkingPointsMuonID::SoftID, "SoftID"},
            { WorkingPointsMuonID::TightID, "TightID"},
            { WorkingPointsMuonID::TrkHighPtID, "TrkHighPtID"},
        };
        return names;
    };
    */

    static const std::string& getScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> names = {
            { UncScale::Down, "systdown" },
            { UncScale::Central, "sf" },
            { UncScale::Up, "systup" },
        };
        return names.at(scale);
    }

     static bool sourceApplies(UncSource source, const float Muon_pfRelIso04_all, const bool Muon_TightId)
                                // const bool Muon_mediumId, const float tkRelIso, const bool highPtID, const bool Muon_TightId )
    {
        //if(UncSource == NUM_MediumPromptID_DEN_genTracks && Muon_mediumId) return true;
        if(source == UncSource::NUM_TightID_DEN_genTracks && Muon_TightId) return true;
        if(source == UncSource::NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight && (Muon_TightId && Muon_pfRelIso04_all<0.15)) return true;
        if(source == UncSource::NUM_TightRelIso_DEN_MediumPromptID &&  Muon_pfRelIso04_all < 0.15) return true;
        return false;
    }

    MuCorrProvider(const std::string& fileName) :
    corrections_(CorrectionSet::from_file(fileName))
    {
        muIDCorrections["NUM_TightID_DEN_genTracks"]= corrections_->at("NUM_TightID_DEN_genTracks");
        muIDCorrections["NUM_TightRelIso_DEN_TightIDandIPCut"] = corrections_->at("NUM_TightRelIso_DEN_TightIDandIPCut");
        muIDCorrections["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"] = corrections_->at("NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight");
    }

    float getRecoSF(const LorentzVectorM& muon_p4) const {
        for (const auto & map_element : getRecoSFMap()){
                if(muon_p4.mag() > map_element.first) continue;
                for (const auto & set_element : map_element.second){
                    if(abs(muon_p4.Eta()) > set_element.first) continue;
                    return set_element.second;
                }
            }
            return 1.;
        }
    float getMuonIDSF(const LorentzVectorM & muon_p4, const float Muon_pfRelIso04_all, const bool Muon_TightId, UncSource source, UncScale scale, std::string year) const {
        const UncScale muID_scale = sourceApplies(source, Muon_pfRelIso04_all, Muon_TightId)
                                           ? scale : UncScale::Central;
        const std::string& scale_str = getScaleStr(muID_scale);
        if(!sourceApplies(source, Muon_pfRelIso04_all, Muon_TightId)) return 1.;
        return muIDCorrections.at(getUncSourceName(source))->evaluate({year, muon_p4.Eta(), muon_p4.Pt(), scale_str});
    }

private:
    static const std::map<float, std::set<std::pair<float, float>>>& getRecoSFMap()
        {
            static const std::map<float, std::set<std::pair<float, float>>> RecoSFMap = {
                {50., { std::pair<float,float>(1.6, 0.9943),std::pair<float,float>(2.4, 1.0)} },
                {100., { std::pair<float,float>(1.6, 0.9948), std::pair<float,float>(2.4, 0.993)} },
                {150., { std::pair<float,float>(1.6, 0.9950), std::pair<float,float>(2.4, 0.990)} },
                {200., { std::pair<float,float>(1.6, 0.994), std::pair<float,float>(2.4, 0.988)} },
                {300., { std::pair<float,float>(1.6, 0.9914), std::pair<float,float>(2.4, 0.981)} },
                {400., { std::pair<float,float>(1.6, 0.993), std::pair<float,float>(2.4, 0.983)} },
                {600., { std::pair<float,float>(1.6, 0.991), std::pair<float,float>(2.4, 0.978)} },
                {1500., { std::pair<float,float>(1.6, 1.0), std::pair<float,float>(2.4, 0.98)} },
            };
            return RecoSFMap;
        }
        std::string getUncSourceName(UncSource source) const {
        static const std::map<UncSource,std::string> uncSourceNames = {
            {UncSource::NUM_GlobalMuons_DEN_genTracks, "NUM_GlobalMuons_DEN_genTracks"},
            {UncSource::NUM_HighPtID_DEN_genTracks, "NUM_HighPtID_DEN_genTracks"},
            {UncSource::NUM_HighPtID_DEN_TrackerMuons, "NUM_HighPtID_DEN_TrackerMuons"},
            {UncSource::NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight, "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"},
            {UncSource::NUM_LooseID_DEN_genTracks, "NUM_LooseID_DEN_genTracks"},
            {UncSource::NUM_LooseID_DEN_TrackerMuons, "NUM_LooseID_DEN_TrackerMuons"},
            {UncSource::NUM_LooseRelIso_DEN_LooseID, "NUM_LooseRelIso_DEN_LooseID"},
            {UncSource::NUM_LooseRelIso_DEN_MediumID, "NUM_LooseRelIso_DEN_MediumID"},
            {UncSource::NUM_LooseRelIso_DEN_MediumPromptID, "NUM_LooseRelIso_DEN_MediumPromptID"},
            {UncSource::NUM_LooseRelIso_DEN_TightIDandIPCut, "NUM_LooseRelIso_DEN_TightIDandIPCut"},
            {UncSource::NUM_LooseRelTkIso_DEN_HighPtIDandIPCut, "NUM_LooseRelTkIso_DEN_HighPtIDandIPCut"},
            {UncSource::NUM_LooseRelTkIso_DEN_TrkHighPtIDandIPCut, "NUM_LooseRelTkIso_DEN_TrkHighPtIDandIPCut"},
            {UncSource::NUM_MediumID_DEN_genTracks, "NUM_MediumID_DEN_genTracks"},
            {UncSource::NUM_MediumID_DEN_TrackerMuons, "NUM_MediumID_DEN_TrackerMuons"},
            {UncSource::NUM_MediumPromptID_DEN_genTracks, "NUM_MediumPromptID_DEN_genTracks"},
            {UncSource::NUM_MediumPromptID_DEN_TrackerMuons, "NUM_MediumPromptID_DEN_TrackerMuons"},
            {UncSource::NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose, "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"},
            {UncSource::NUM_SoftID_DEN_genTracks, "NUM_SoftID_DEN_genTracks"},
            {UncSource::NUM_SoftID_DEN_TrackerMuons, "NUM_SoftID_DEN_TrackerMuons"},
            {UncSource::NUM_TightID_DEN_genTracks, "NUM_TightID_DEN_genTracks"},
            {UncSource::NUM_TightID_DEN_TrackerMuons, "NUM_TightID_DEN_TrackerMuons"},
            {UncSource::NUM_TightRelIso_DEN_MediumID, "NUM_TightRelIso_DEN_MediumID"},
            {UncSource::NUM_TightRelIso_DEN_MediumPromptID, "NUM_TightRelIso_DEN_MediumPromptID"},
            {UncSource::NUM_TightRelIso_DEN_TightIDandIPCut, "NUM_TightRelIso_DEN_TightIDandIPCut"},
            {UncSource::NUM_TightRelTkIso_DEN_HighPtIDandIPCut, "NUM_TightRelTkIso_DEN_HighPtIDandIPCut"},
            {UncSource::NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut, "NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut"},
            {UncSource::NUM_TrackerMuons_DEN_genTracks, "NUM_TrackerMuons_DEN_genTracks"},
            {UncSource::NUM_TrkHighPtID_DEN_genTracks, "NUM_TrkHighPtID_DEN_genTracks"},
            {UncSource::NUM_TrkHighPtID_DEN_TrackerMuons, "NUM_TrkHighPtID_DEN_TrackerMuons"},
        };
        return uncSourceNames.at(source);
    }
private:
    std::unique_ptr<CorrectionSet> corrections_;
    std::map<std::string, Correction::Ref> muIDCorrections;

};

} // namespace correction