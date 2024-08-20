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
        NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight = 29,
        NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight = 30,

    };
    static const std::map<WorkingPointsMuonID, std::string>& getWPID()
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



    static const std::string& getScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> names = {
            { UncScale::Down, "systdown" },
            { UncScale::Central, "nominal" },
            { UncScale::Up, "systup" },
        };
        return names.at(scale);
    }

     static bool sourceApplies(UncSource source, const float Muon_pfRelIso04_all, const bool Muon_TightId, const float muon_Pt, const float Muon_tkRelIso, const bool Muon_highPtId)
    {
        // RECO
        if(source == UncSource::NUM_TrackerMuons_DEN_genTracks) return true;

        // ID
        bool tightID_condition = (Muon_TightId && Muon_pfRelIso04_all<0.15);
        bool highPtID_condition = (Muon_highPtId && Muon_tkRelIso < 0.15);
        if(source == UncSource::NUM_TightID_DEN_TrackerMuons && tightID_condition ) return true;
        if(source == UncSource::NUM_TightID_DEN_genTracks && tightID_condition ) return true;

        if(source == UncSource::NUM_HighPtID_DEN_TrackerMuons && highPtID_condition ) return true;
        if(source == UncSource::NUM_HighPtID_DEN_genTracks && highPtID_condition ) return true;

        // ISO
        if(source == UncSource::NUM_TightRelIso_DEN_TightIDandIPCut && tightID_condition ) return true;
        if(source == UncSource::NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut && highPtID_condition ) return true;

        // TRG
        if(source == UncSource::NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight&& muon_Pt > 26) return true;
        if(source == UncSource::NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight&& muon_Pt > 29) return true;
        if(source == UncSource::NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight&& muon_Pt > 26) return true;
        return false;
    }

    MuCorrProvider(const std::string& fileName, const int& year) :
    corrections_(CorrectionSet::from_file(fileName))
    {
        muIDCorrections["NUM_TrackerMuons_DEN_genTracks"]=corrections_->at("NUM_TrackerMuons_DEN_genTracks");
        muIDCorrections["NUM_TightID_DEN_TrackerMuons"]=corrections_->at("NUM_TightID_DEN_TrackerMuons");
        muIDCorrections["NUM_TightID_DEN_genTracks"]=corrections_->at("NUM_TightID_DEN_genTracks");
        muIDCorrections["NUM_HighPtID_DEN_TrackerMuons"]=corrections_->at("NUM_HighPtID_DEN_TrackerMuons");
        muIDCorrections["NUM_HighPtID_DEN_genTracks"]=corrections_->at("NUM_HighPtID_DEN_genTracks");
        muIDCorrections["NUM_TightRelIso_DEN_TightIDandIPCut"]=corrections_->at("NUM_TightRelIso_DEN_TightIDandIPCut");
        muIDCorrections["NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut"]=corrections_->at("NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut");

        if (year==2018){
            muIDCorrections["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"] = corrections_->at("NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight");
        }
        if(year==2017){
            muIDCorrections["NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight"] = corrections_->at("NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight");
        }
        if (year == 2016 ){
            muIDCorrections["NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"] = corrections_->at("NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight");
        }
    }

    float getMuonSF(const LorentzVectorM & muon_p4, const float Muon_pfRelIso04_all, const bool Muon_TightId, const float Muon_tkRelIso, const bool Muon_highPtId, UncSource source, UncScale scale, std::string year) const {
        const UncScale muID_scale = sourceApplies(source, Muon_pfRelIso04_all, Muon_TightId, muon_p4.Pt(), Muon_tkRelIso, Muon_highPtId)
                                           ? scale : UncScale::Central;
        const std::string& scale_str = getScaleStr(muID_scale);
        if (source == UncSource::NUM_TrackerMuons_DEN_genTracks) {
            //const std::string& reco_scale_str = scale==UncScale::Central ? "nominal" : scale_str;
            return (muon_p4.Pt() >= 40)? muIDCorrections.at(getUncSourceName(source))->evaluate({abs(muon_p4.Eta()), muon_p4.Pt(), scale_str}) : 1.;
        }
        return source == UncSource::Central ? 1. : muIDCorrections.at(getUncSourceName(source))->evaluate({ abs(muon_p4.Eta()), muon_p4.Pt(), scale_str}) ;
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
    static std::string& getUncSourceName(UncSource source) {
        static std::string k = "Central";
        if (source == UncSource::NUM_GlobalMuons_DEN_genTracks) k = "NUM_GlobalMuons_DEN_genTracks";
        if (source == UncSource::NUM_HighPtID_DEN_genTracks) k = "NUM_HighPtID_DEN_genTracks";
        if (source == UncSource::NUM_HighPtID_DEN_TrackerMuons) k = "NUM_HighPtID_DEN_TrackerMuons";
        if (source == UncSource::NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight) k = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight";
        if (source == UncSource::NUM_LooseID_DEN_genTracks) k = "NUM_LooseID_DEN_genTracks";
        if (source == UncSource::NUM_LooseID_DEN_TrackerMuons) k = "NUM_LooseID_DEN_TrackerMuons";
        if (source == UncSource::NUM_LooseRelIso_DEN_LooseID) k = "NUM_LooseRelIso_DEN_LooseID";
        if (source == UncSource::NUM_LooseRelIso_DEN_MediumID) k = "NUM_LooseRelIso_DEN_MediumID";
        if (source == UncSource::NUM_LooseRelIso_DEN_MediumPromptID) k = "NUM_LooseRelIso_DEN_MediumPromptID";
        if (source == UncSource::NUM_LooseRelIso_DEN_TightIDandIPCut) k = "NUM_LooseRelIso_DEN_TightIDandIPCut";
        if (source == UncSource::NUM_LooseRelTkIso_DEN_HighPtIDandIPCut) k = "NUM_LooseRelTkIso_DEN_HighPtIDandIPCut";
        if (source == UncSource::NUM_LooseRelTkIso_DEN_TrkHighPtIDandIPCut) k = "NUM_LooseRelTkIso_DEN_TrkHighPtIDandIPCut";
        if (source == UncSource::NUM_MediumID_DEN_genTracks) k = "NUM_MediumID_DEN_genTracks";
        if (source == UncSource::NUM_MediumID_DEN_TrackerMuons) k = "NUM_MediumID_DEN_TrackerMuons";
        if (source == UncSource::NUM_MediumPromptID_DEN_genTracks) k = "NUM_MediumPromptID_DEN_genTracks";
        if (source == UncSource::NUM_MediumPromptID_DEN_TrackerMuons) k = "NUM_MediumPromptID_DEN_TrackerMuons";
        if (source == UncSource::NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose) k = "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose";
        if (source == UncSource::NUM_SoftID_DEN_genTracks) k = "NUM_SoftID_DEN_genTracks";
        if (source == UncSource::NUM_SoftID_DEN_TrackerMuons) k = "NUM_SoftID_DEN_TrackerMuons";
        if (source == UncSource::NUM_TightID_DEN_genTracks) k = "NUM_TightID_DEN_genTracks";
        if (source == UncSource::NUM_TightID_DEN_TrackerMuons) k = "NUM_TightID_DEN_TrackerMuons";
        if (source == UncSource::NUM_TightRelIso_DEN_MediumID) k = "NUM_TightRelIso_DEN_MediumID";
        if (source == UncSource::NUM_TightRelIso_DEN_MediumPromptID) k = "NUM_TightRelIso_DEN_MediumPromptID";
        if (source == UncSource::NUM_TightRelIso_DEN_TightIDandIPCut) k = "NUM_TightRelIso_DEN_TightIDandIPCut";
        if (source == UncSource::NUM_TightRelTkIso_DEN_HighPtIDandIPCut) k = "NUM_TightRelTkIso_DEN_HighPtIDandIPCut";
        if (source == UncSource::NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut) k = "NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut";
        if (source == UncSource::NUM_TrackerMuons_DEN_genTracks) k = "NUM_TrackerMuons_DEN_genTracks";
        if (source == UncSource::NUM_TrkHighPtID_DEN_genTracks) k = "NUM_TrkHighPtID_DEN_genTracks";
        if (source == UncSource::NUM_TrkHighPtID_DEN_TrackerMuons) k = "NUM_TrkHighPtID_DEN_TrackerMuons";
        return k;
    }
private:
    std::unique_ptr<CorrectionSet> corrections_;
    std::map<std::string, Correction::Ref> muIDCorrections;

};



class HighPtMuCorrProvider : public CorrectionsBase<HighPtMuCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        NUM_GlobalMuons_DEN_TrackerMuonProbes = 0,
        NUM_HighPtID_DEN_GlobalMuonProbes = 1,
        NUM_TrkHighPtID_DEN_GlobalMuonProbes = 2,
        NUM_probe_LooseRelTkIso_DEN_HighPtProbes = 3,
        NUM_probe_TightRelTkIso_DEN_HighPtProbes = 4,
        NUM_probe_LooseRelTkIso_DEN_TrkHighPtProbes = 5,
        NUM_probe_TightRelTkIso_DEN_TrkHighPtProbes = 6,
        NUM_TightID_DEN_GlobalMuonProbes = 7,
        NUM_MediumID_DEN_GlobalMuonProbes = 8,
        NUM_probe_LooseRelTkIso_DEN_MediumIDProbes = 9,
        NUM_probe_TightRelTkIso_DEN_MediumIDProbes = 10,
        NUM_HLT_DEN_TrkHighPtTightRelIsoProbes = 11,
        NUM_HLT_DEN_TrkHighPtLooseRelIsoProbes = 12,
        NUM_HLT_DEN_HighPtTightRelIsoProbes = 13,
        NUM_HLT_DEN_HighPtLooseRelIsoProbes = 14,
        NUM_HLT_DEN_MediumIDTightRelIsoProbes = 15,
        NUM_HLT_DEN_MediumIDLooseRelIsoProbes = 16,
    };

    static const std::string& getScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> names = {
            { UncScale::Down, "systdown" },
            { UncScale::Central, "nominal" },
            { UncScale::Up, "systup" },
        };
        return names.at(scale);
    }


     static bool sourceApplies(UncSource source, const float Muon_pfRelIso04_all, const bool Muon_TightId, const float muon_Pt, const float Muon_tkRelIso, const bool Muon_highPtId)
    {
        // RECO
        if (source == UncSource::NUM_GlobalMuons_DEN_TrackerMuonProbes) return true;
        // ID
        bool tightID_condition = (Muon_TightId && Muon_pfRelIso04_all<0.15);
        bool highPtID_condition = (Muon_highPtId && Muon_tkRelIso < 0.15);
        if(source == UncSource::NUM_TightID_DEN_GlobalMuonProbes && tightID_condition ) return true;
        if(source == UncSource::NUM_HighPtID_DEN_GlobalMuonProbes && highPtID_condition ) return true;
        // ISO
        if (source == UncSource::NUM_probe_TightRelTkIso_DEN_HighPtProbes && highPtID_condition ) return true;
        return false;
    }

    HighPtMuCorrProvider(const std::string& fileName) :
    corrections_(CorrectionSet::from_file(fileName))
    {
        highPtmuCorrections["NUM_GlobalMuons_DEN_TrackerMuonProbes"]=corrections_->at("NUM_GlobalMuons_DEN_TrackerMuonProbes");
        highPtmuCorrections["NUM_TightID_DEN_GlobalMuonProbes"]=corrections_->at("NUM_TightID_DEN_GlobalMuonProbes");
        highPtmuCorrections["NUM_HighPtID_DEN_GlobalMuonProbes"]=corrections_->at("NUM_HighPtID_DEN_GlobalMuonProbes");
        highPtmuCorrections["NUM_probe_TightRelTkIso_DEN_HighPtProbes"]=corrections_->at("NUM_probe_TightRelTkIso_DEN_HighPtProbes");

    }

    float getHighPtMuonSF(const LorentzVectorM & muon_p4, const float Muon_pfRelIso04_all, const bool Muon_TightId, const float Muon_tkRelIso, const bool Muon_highPtId, UncSource source, UncScale scale) const {
        const UncScale muID_scale = sourceApplies(source, Muon_pfRelIso04_all, Muon_TightId, muon_p4.Pt(), Muon_tkRelIso, Muon_highPtId) ? scale : UncScale::Central;
        const std::string& scale_str = getScaleStr(muID_scale);
        const auto mu_p = std::sqrt(muon_p4.Pt()*muon_p4.Pt()+muon_p4.Eta()*muon_p4.Eta()+muon_p4.Phi()*muon_p4.Phi()+muon_p4.M()*muon_p4.M());
        if (source == UncSource::NUM_GlobalMuons_DEN_TrackerMuonProbes) {
            //std::cout << mu_p <<std::endl;
            //std::cout << abs(muon_p4.Eta()) <<std::endl;
            //std::cout << scale_str << std::endl;
            //const std::string& reco_scale_str = scale==UncScale::Central? "nominal" : scale_str;
            //std::cout << reco_scale_str << std::endl;
            return highPtmuCorrections.at(getUncSourceName(source))->evaluate({abs(muon_p4.Eta()), mu_p, scale_str}) ;
        }
        return source == UncSource::Central ? 1. : highPtmuCorrections.at(getUncSourceName(source))->evaluate({abs(muon_p4.Eta()),muon_p4.Pt(), scale_str}) ;
    }

private:

    static std::string& getUncSourceName(UncSource source) {
        static std::string sourcename = "Central";
        if (source == UncSource::NUM_GlobalMuons_DEN_TrackerMuonProbes) sourcename =  "NUM_GlobalMuons_DEN_TrackerMuonProbes";
        if (source == UncSource::NUM_HighPtID_DEN_GlobalMuonProbes) sourcename =  "NUM_HighPtID_DEN_GlobalMuonProbes";
        if (source == UncSource::NUM_TrkHighPtID_DEN_GlobalMuonProbes) sourcename =  "NUM_TrkHighPtID_DEN_GlobalMuonProbes";
        if (source == UncSource::NUM_probe_LooseRelTkIso_DEN_HighPtProbes) sourcename =  "NUM_probe_LooseRelTkIso_DEN_HighPtProbes";
        if (source == UncSource::NUM_probe_TightRelTkIso_DEN_HighPtProbes) sourcename =  "NUM_probe_TightRelTkIso_DEN_HighPtProbes";
        if (source == UncSource::NUM_probe_LooseRelTkIso_DEN_TrkHighPtProbes) sourcename =  "NUM_probe_LooseRelTkIso_DEN_TrkHighPtProbes";
        if (source == UncSource::NUM_probe_TightRelTkIso_DEN_TrkHighPtProbes) sourcename =  "NUM_probe_TightRelTkIso_DEN_TrkHighPtProbes";
        if (source == UncSource::NUM_TightID_DEN_GlobalMuonProbes) sourcename =  "NUM_TightID_DEN_GlobalMuonProbes";
        if (source == UncSource::NUM_MediumID_DEN_GlobalMuonProbes) sourcename =  "NUM_MediumID_DEN_GlobalMuonProbes";
        if (source == UncSource::NUM_probe_LooseRelTkIso_DEN_MediumIDProbes) sourcename =  "NUM_probe_LooseRelTkIso_DEN_MediumIDProbes";
        if (source == UncSource::NUM_probe_TightRelTkIso_DEN_MediumIDProbes) sourcename =  "NUM_probe_TightRelTkIso_DEN_MediumIDProbes";
        if (source == UncSource::NUM_HLT_DEN_TrkHighPtTightRelIsoProbes) sourcename =  "NUM_HLT_DEN_TrkHighPtTightRelIsoProbes";
        if (source == UncSource::NUM_HLT_DEN_TrkHighPtLooseRelIsoProbes) sourcename =  "NUM_HLT_DEN_TrkHighPtLooseRelIsoProbes";
        if (source == UncSource::NUM_HLT_DEN_HighPtTightRelIsoProbes) sourcename =  "NUM_HLT_DEN_HighPtTightRelIsoProbes";
        if (source == UncSource::NUM_HLT_DEN_HighPtLooseRelIsoProbes) sourcename =  "NUM_HLT_DEN_HighPtLooseRelIsoProbes";
        if (source == UncSource::NUM_HLT_DEN_MediumIDTightRelIsoProbes) sourcename =  "NUM_HLT_DEN_MediumIDTightRelIsoProbes";
        if (source == UncSource::NUM_HLT_DEN_MediumIDLooseRelIsoProbes) sourcename =  "NUM_HLT_DEN_MediumIDLooseRelIsoProbes";
        return sourcename;
    }
private:
    std::unique_ptr<CorrectionSet> corrections_;
    std::map<std::string, Correction::Ref> highPtmuCorrections;

};


} // namespace correction