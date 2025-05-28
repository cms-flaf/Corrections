import os
import ROOT
from .CorrectionsCore import *

# https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonSelection
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/MUO
# note: at the beginning of february 2024, the names have been changed to muon_Z.json.gz and muon_HighPt.json.gz for high pT muons
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2018
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016



class MuCorrProducer:
    muIDEff_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_Z.json.gz"
    HighPtmuIDEff_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_HighPt.json.gz"
    LowPtmuIDEff_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_JPsi.json.gz"
    initialized = False

    ##### dictionaries containing ALL uncertainties ######

    #### low pt ID (NO MORE NEEDED) ####
    lowPtMu_SF_Sources_dict = {
        # ID SF - with tracker muons - RECOMMENDED
        "NUM_TightID_DEN_TrackerMuons": "TightID",
    }

    #### high pt ID (NO MORE NEEDED) ####
    highPtMu_SF_Sources_dict = {
        # reco SF
        "NUM_GlobalMuons_DEN_TrackerMuonProbes":"Reco", # --> This is the recommended one for RECO!!
        # ID SF - with tracker muons - RECOMMENDED
        "NUM_TightID_DEN_GlobalMuonProbes": "TightID",
        "NUM_HighPtID_DEN_GlobalMuonProbes": "HighPtID",
        # Iso SF
        "NUM_probe_TightRelTkIso_DEN_HighPtProbes": "HighPtIdRelTkIso",
    }

    ##### ID + trigger ####
    muID_SF_Sources_dict = {
        # reco SF
        "NUM_TrackerMuons_DEN_genTracks":"Reco", # --> This is the recommended one for RECO!!
        # ID SF - with genTracks - NOT RECOMMENDED --> WE DO NOT USE THIS
        "NUM_MediumPromptID_DEN_genTracks":"MediumID", # medium ID - NOT NEEDED NOW BECAUSE WE DON'T USE MEDIUM ID
        "NUM_TightID_DEN_genTracks":"TightID", # tight ID
        "NUM_HighPtID_DEN_genTracks": "HighPtID",# HighPtID

        # ID SF - with tracker muons - RECOMMENDED
        "NUM_MediumPromptID_DEN_TrackerMuons":"MediumID_Trk", # medium ID - NOT NEEDED NOW BECAUSE WE DON'T USE MEDIUM ID
        "NUM_TightID_DEN_TrackerMuons":"TightID_Trk", # tight ID
        "NUM_HighPtID_DEN_TrackerMuons": "HighPtID_Trk",# HighPtID ID

        # Iso SF
        "NUM_TightRelIso_DEN_MediumPromptID":"MediumRelIso", # medium ID, tight iso # NOT NEEDED NOW BECAUSE WE DON'T USE MEDIUM ID
        "NUM_TightRelIso_DEN_TightIDandIPCut":"TightRelIso", # tight ID, tight iso
        "NUM_TightRelTkIso_DEN_TrkHighPtIDandIPCut" :"HighPtIdRelTkIso",  # highPtID, tight tkRelIso
        "NUM_LoosePFIso_DEN_TightID":"LoosePFIso", # tight ID, tight PF Iso

        # Trigger
        "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight":"TightIso24", # trg --> FOR ALL PT RANGE!!
        "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight":"TightIso27", # trg --> FOR ALL PT RANGE!!
        "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose":"Mu50", # trg --> FOR ALL PT RANGE!!
        "NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose":"Mu50_tkMu50", # trg --> FOR ALL PT RANGE!!
        "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight": "TightIso24OrTightIsoTk24", # trg --> FOR ALL PT RANGE!!
    }

    #muID_SF_Sources = []
    ####### in these lists there are the uncertainties we will consider #######

    # for muon ID --> we consider only sources related to TightID
    #muReco_SF_sources = ["NUM_TrackerMuons_DEN_genTracks"]
    #muID_SF_Sources = ["NUM_TightID_DEN_TrackerMuons"]
    #muIso_SF_Sources = ["NUM_TightRelIso_DEN_TightIDandIPCut"]

    #Convert to dicts so we can have different names for different years, motivated by Run3 moving to PF and not having RECO efficiency
    muReco_SF_sources = {
        "2016preVFP_UL": ["NUM_TrackerMuons_DEN_genTracks"],
        "2016postVFP_UL": ["NUM_TrackerMuons_DEN_genTracks"],
        "2017_UL": ["NUM_TrackerMuons_DEN_genTracks"],
        "2018_UL": ["NUM_TrackerMuons_DEN_genTracks"],
        "2022_Summer22": [], #2022 has no genTrack to TrackerMuons key
        "2022_Summer22EE": [],
        "2023_Summer23": [],
        "2023_Summer23BPix": [],
        }
    muID_SF_Sources = {
        "2016preVFP_UL": ["NUM_TightID_DEN_TrackerMuons"],
        "2016postVFP_UL": ["NUM_TightID_DEN_TrackerMuons"],
        "2017_UL": ["NUM_TightID_DEN_TrackerMuons"],
        "2018_UL": ["NUM_TightID_DEN_TrackerMuons"],
        "2022_Summer22": ["NUM_TightID_DEN_TrackerMuons"],
        "2022_Summer22EE": ["NUM_TightID_DEN_TrackerMuons"],
        "2023_Summer23": ["NUM_TightID_DEN_TrackerMuons"],
        "2023_Summer23BPix": ["NUM_TightID_DEN_TrackerMuons"],
        }
    muIso_SF_Sources = {
        "2016preVFP_UL": ["NUM_TightRelIso_DEN_TightIDandIPCut"],
        "2016postVFP_UL": ["NUM_TightRelIso_DEN_TightIDandIPCut"],
        "2017_UL": ["NUM_TightRelIso_DEN_TightIDandIPCut"],
        "2018_UL": ["NUM_TightRelIso_DEN_TightIDandIPCut"],
        "2022_Summer22": ["NUM_LoosePFIso_DEN_TightID"],
        "2022_Summer22EE": ["NUM_LoosePFIso_DEN_TightID"],
        "2023_Summer23": ["NUM_LoosePFIso_DEN_TightID"],
        "2023_Summer23BPix": ["NUM_LoosePFIso_DEN_TightID"],
        }

    # for high pt id
    highPtmuReco_SF_sources = ["NUM_GlobalMuons_DEN_TrackerMuonProbes"]
    highPtmuID_SF_Sources = ["NUM_TightID_DEN_GlobalMuonProbes", "NUM_HighPtID_DEN_GlobalMuonProbes"]
    highPtmuIso_SF_Sources = ["NUM_probe_TightRelTkIso_DEN_HighPtProbes"] # not find the tightID with tight PF iso

    # for low pt id
    lowPtmuReco_SF_sources = []
    lowPtmuID_SF_Sources = ["NUM_TightID_DEN_TrackerMuons"]
    lowPtmuIso_SF_Sources = []


    # trigger
    year_unc_dict= {
        "2018_UL": ["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"], #,"NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"], # for HLT_mu50
        "2017_UL": ["NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight"], #, "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"], # for HLT_mu50
        "2016preVFP_UL": ["NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight" ], #,"NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"], # for HLT_mu50
        "2016postVFP_UL":["NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight" ], #,"NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"], # for HLT_mu50
        "2022_Summer22": ["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"],
        "2022_Summer22EE": ["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"],
        "2023_Summer23": ["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"],
        "2023_Summer23BPix": ["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"],
    }
    period = None


    def __init__(self, era):
        period = period_names[era]
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],MuCorrProducer.muIDEff_JsonPath.format(period))
        jsonFile_eff_highPt = os.path.join(os.environ['ANALYSIS_PATH'],MuCorrProducer.HighPtmuIDEff_JsonPath.format(period))
        jsonFile_eff_lowPt = os.path.join(os.environ['ANALYSIS_PATH'],MuCorrProducer.LowPtmuIDEff_JsonPath.format(period))
        if not MuCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "mu.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::MuCorrProvider::Initialize("{jsonFile_eff}", "{era}")')
            ROOT.gInterpreter.ProcessLine(f'::correction::HighPtMuCorrProvider::Initialize("{jsonFile_eff_highPt}")')
            ROOT.gInterpreter.ProcessLine(f'::correction::LowPtMuCorrProvider::Initialize("{jsonFile_eff_lowPt}")')
            MuCorrProducer.period = period
            MuCorrProducer.initialized = True

        self.low_available = era.startswith('Run3')
        self.med_available = True
        self.high_available = True

    def getMuonIDSF(self, df, lepton_legs, isCentral, return_variations):
        SF_branches = []
        #sf_sources = MuCorrProducer.muID_SF_Sources + MuCorrProducer.muReco_SF_sources + MuCorrProducer.muIso_SF_Sources
        sf_sources = MuCorrProducer.muID_SF_Sources[MuCorrProducer.period] + MuCorrProducer.muReco_SF_sources[MuCorrProducer.period] + MuCorrProducer.muIso_SF_Sources[MuCorrProducer.period]
        sf_scales = [central, up, down] if return_variations else [central]
        for source in sf_sources :
            for scale in sf_scales:
                if source == central and scale != central: continue
                if not isCentral and scale!= central: continue
                source_name = MuCorrProducer.muID_SF_Sources_dict[source] if source != central else central
                syst_name = source_name+scale if source != central else 'Central'
                for leg_idx, leg_name in enumerate(lepton_legs): #So legname is lep1 or lep2 for bbww, and tau1 or tau2 for bbtautau, can use this instead of a hard hh_bbww = True
                    branch_name = f"weight_{leg_name}_MuonID_SF_{syst_name}"
                    branch_central = f"""weight_{leg_name}_MuonID_SF_{source_name+central}"""
                    genMatch_bool = f"(({leg_name}_gen_kind == 2) || ({leg_name}_gen_kind == 4))"

                    df = df.Define(f"{branch_name}_double",f'''{leg_name}_legType == Leg::mu && {leg_name}_index >= 0 && ({genMatch_bool}) ? ::correction::MuCorrProvider::getGlobal().getMuonSF({leg_name}_p4, Muon_pfRelIso04_all.at({leg_name}_index), Muon_tightId.at({leg_name}_index),Muon_tkRelIso.at({leg_name}_index),Muon_highPtId.at({leg_name}_index),::correction::MuCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) : 1.''')


                    #Change to this format
                    #df = df.Define(pair_name, vector<val1,val2>)
                    #df = df.Define(SF_value, pair_name[0]) #Add these to the branch list
                    #df = df.Define(SF_validitiy, pair_name[1]) #Add these to the branch list -- Maybe -1 underflow, 0 within, +1 overflow, -2 notGenMuon

                    #print(f"{branch_name}_double")
                    #if scale==central:
                    #    df.Filter(f"{branch_name}_double!=1.").Display({f"{branch_name}_double"}).Print()
                    if scale != central:
                        branch_name_final = branch_name + '_rel'
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double/{branch_central})")
                    else:
                        if source == central:
                            branch_name_final = f"""weight_{leg_name}_MuonID_SF_{central}"""
                        else:
                            branch_name_final = branch_name
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double)")
                    SF_branches.append(branch_name_final)
        return df,SF_branches

########################################################################################################
    #### NO MORE NEEDED (but keeping just in case :D ) ####
    #Ignore this ^ comment from valeria i guess? We are now saving high and low pT SFs for development
    def getHighPtMuonIDSF(self, df, lepton_legs, isCentral, return_variations):
        highPtMuSF_branches = []
        sf_sources =  MuCorrProducer.highPtmuReco_SF_sources + MuCorrProducer.highPtmuID_SF_Sources + MuCorrProducer.highPtmuIso_SF_Sources
        sf_scales = [up, down] if return_variations else []
        for source in sf_sources :
            for scale in [ central ] + sf_scales:
                if source == central and scale != central: continue
                if not isCentral and scale!= central: continue
                source_name = MuCorrProducer.highPtMu_SF_Sources_dict[source] if source != central else central
                syst_name = source_name+scale if source != central else 'Central'
                for leg_idx, leg_name in enumerate(lepton_legs):
                    branch_name = f"weight_{leg_name}_HighPt_MuonID_SF_{syst_name}"
                    branch_central = f"""weight_{leg_name}_HighPt_MuonID_SF_{source_name+central}"""
                    genMatch_bool = f"(({leg_name}_gen_kind == 2) || ({leg_name}_gen_kind == 4))"

                    df = df.Define(f"{branch_name}_double",f'''{leg_name}_legType == Leg::mu && {leg_name}_index >= 0 && ({genMatch_bool}) ? ::correction::HighPtMuCorrProvider::getGlobal().getHighPtMuonSF({leg_name}_p4, Muon_pfRelIso04_all.at({leg_name}_index), Muon_tightId.at({leg_name}_index), Muon_highPtId.at({leg_name}_index), Muon_tkRelIso.at({leg_name}_index),::correction::HighPtMuCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) : 1.''')

                    #df.Display({f"""{branch_name}_double"""}).Print()
                    #if source in MuCorrProducer.muReco_SF_sources:
                    #    df = df.Define(f"{branch_name}_double",f'''HttCandidate.leg_type[{leg_idx}] == Leg::mu && HttCandidate.leg_p4[{leg_idx}].pt() >= 10 && HttCandidate.leg_p4[{leg_idx}].pt() < 200 ? ::correction::MuCorrProvider::getGlobal().getMuonSF( HttCandidate.leg_p4[{leg_idx}], Muon_pfRelIso04_all.at(HttCandidate.leg_index[{leg_idx}]), Muon_tightId.at(HttCandidate.leg_index[{leg_idx}]),Muon_tkRelIso.at(HttCandidate.leg_index[{leg_idx}]),Muon_highPtId.at(HttCandidate.leg_index[{leg_idx}]),::correction::MuCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}, "{MuCorrProducer.period}") : 1.''')
                    #else:
                    #    df = df.Define(f"{branch_name}_double", f'''HttCandidate.leg_type[{leg_idx}] == Leg::mu && HttCandidate.leg_p4[{leg_idx}].pt() >= 15 && HttCandidate.leg_p4[{leg_idx}].pt() < 120 ? ::correction::MuCorrProvider::getGlobal().getMuonSF(HttCandidate.leg_p4[{leg_idx}], Muon_pfRelIso04_all.at(HttCandidate.leg_index[{leg_idx}]), Muon_tightId.at(HttCandidate.leg_index[{leg_idx}]),Muon_tkRelIso.at(HttCandidate.leg_index[{leg_idx}]),Muon_highPtId.at(HttCandidate.leg_index[{leg_idx}]),::correction::MuCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}, "{MuCorrProducer.period}") : 1.''')
                    #print(f"{branch_name}_double")
                    #if scale==central:
                    #    df.Filter(f"{branch_name}_double!=1.").Display({f"{branch_name}_double"}).Print()
                    if scale != central:
                        branch_name_final = branch_name + '_rel'
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double/{branch_central})")
                    else:
                        if source == central:
                            branch_name_final = f"""weight_{leg_name}_HighPt_MuonID_SF_{central}"""
                        else:
                            branch_name_final = branch_name
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double)")
                    highPtMuSF_branches.append(branch_name_final)
        return df,highPtMuSF_branches




########################################################################################################
    def getLowPtMuonIDSF(self, df, lepton_legs, isCentral, return_variations):
        lowPtMuSF_branches = []
        sf_sources =  MuCorrProducer.lowPtmuReco_SF_sources + MuCorrProducer.lowPtmuID_SF_Sources + MuCorrProducer.lowPtmuIso_SF_Sources
        sf_scales = [up, down] if return_variations else []
        for source in sf_sources :
            for scale in [ central ] + sf_scales:
                if source == central and scale != central: continue
                if not isCentral and scale!= central: continue
                source_name = MuCorrProducer.lowPtMu_SF_Sources_dict[source] if source != central else central
                syst_name = source_name+scale if source != central else 'Central'
                for leg_idx, leg_name in enumerate(lepton_legs):
                    branch_name = f"weight_{leg_name}_LowPt_MuonID_SF_{syst_name}"
                    branch_central = f"""weight_{leg_name}_LowPt_MuonID_SF_{source_name+central}"""

                    genMatch_bool = f"(({leg_name}_gen_kind == 2) || ({leg_name}_gen_kind == 4))"

                    df = df.Define(f"{branch_name}_double",f'''{leg_name}_legType == Leg::mu && {leg_name}_index >= 0 && ({genMatch_bool}) ? ::correction::LowPtMuCorrProvider::getGlobal().getLowPtMuonSF({leg_name}_p4, Muon_pfRelIso04_all.at({leg_name}_index), Muon_tightId.at({leg_name}_index), Muon_highPtId.at({leg_name}_index), Muon_tkRelIso.at({leg_name}_index),::correction::LowPtMuCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) : 1.''')

                    if scale != central:
                        branch_name_final = branch_name + '_rel'
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double/{branch_central})")
                    else:
                        if source == central:
                            branch_name_final = f"""weight_{leg_name}_LowPt_MuonID_SF_{central}"""
                        else:
                            branch_name_final = branch_name
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double)")
                    lowPtMuSF_branches.append(branch_name_final)
        return df,lowPtMuSF_branches