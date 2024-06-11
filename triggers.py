import os
import ROOT
from .CorrectionsCore import *
from Common.Utilities import *
import yaml
# Tau JSON POG integration for tau legs in eTau, muTau, diTau:
# # https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/TAU?ref_type=heads

# singleEle + e/mu legs for xTriggers eTau, muTau:
# https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTScaleFactorMeasurements

# singleMu : files taken from https://gitlab.cern.ch/cms-muonPOG/muonefficiencies/-/tree/master/Run2/UL and saved locally

# singleTau: https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauTrigger#Run_II_Trigger_Scale_Factors
# singleTau: Legacy bc there are no UL as mentioned herehttps://cms-pub-talk.web.cern.ch/t/tau-pog-review/8404/4
# singleTau: 2016 - (HLT_VLooseIsoPFTau120_Trk50_eta2p1_v OR HLT_VLooseIsoPFTau140_Trk50_eta2p1_v) - 0.88 +/- 0.08
# singleTau: 2017 - HLT_MediumChargedIsoPFTau180HighPtRelaxedIso_Trk50_eta2p1_v - 1.08 +/- 0.10
# singleTau: 2018 - (HLT_MediumChargedIsoPFTau180HighPtRelaxedIso_Trk50_eta2p1_v) - 	0.87 +/- 0.11

year_singleElefile = {
    "2018_UL":"sf_el_2018_HLTEle32.root",
    "2017_UL":"sf_el_2017_HLTEle32.root",
    "2016preVFP_UL":"sf_el_2016pre_HLTEle25.root",
    "2016postVFP_UL":"sf_el_2016post_HLTEle25.root"
}

year_singleMufile = {
    "2018_UL":"Efficiencies_muon_generalTracks_Z_Run2018_UL_SingleMuonTriggers.root",
    "2017_UL":"Efficiencies_muon_generalTracks_Z_Run2017_UL_SingleMuonTriggers.root",
    "2016preVFP_UL":"Efficiencies_muon_generalTracks_Z_Run2016_UL_HIPM_SingleMuonTriggers.root",
    "2016postVFP_UL":"Efficiencies_muon_generalTracks_Z_Run2016_UL_SingleMuonTriggers.root"
}

year_xTrg_eTaufile = {
    "2018_UL":"sf_el_2018_HLTEle24Tau30.root",
    "2017_UL":"sf_el_2017_HLTEle24Tau30.root",
    "2016preVFP_UL":"sf_mu_2016pre_HLTMu20Tau27.root",
    "2016postVFP_UL":"sf_mu_2016post_HLTMu20Tau27.root"
}

year_xTrg_muTaufile = {
    "2018_UL":"sf_mu_2018_HLTMu20Tau27.root",
    "2017_UL":"sf_mu_2017_HLTMu20Tau27.root",
    "2016preVFP_UL":"sf_mu_2016pre_HLTMu20Tau27.root",
    "2016postVFP_UL":"sf_mu_2016post_HLTMu20Tau27.root"
}

class TrigCorrProducer:
    TauTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
    MuTRG_jsonPath = "Corrections/data/TRG/{0}/{1}"
    eTRG_jsonPath = "Corrections/data/TRG/{0}/{1}"
    mu_XTrg_jsonPath = "Corrections/data/TRG/{0}/{1}"
    e_XTrg_jsonPath = "Corrections/data/TRG/{0}/{1}"
    initialized = False
    deepTauVersion = 'DeepTau2017v2p1'
    SFSources = { 'ditau': [ "ditau_DM0","ditau_DM1", "ditau_3Prong"], 'singleMu':['singleMu24'], 'singleMu50':['singleMu50or24','singleMu50'],'singleTau':['singleTau'], 'singleEle':['singleEle'],'etau':['etau_ele',"etau_DM0","etau_DM1", "etau_3Prong",],'mutau':['mutau_mu',"mutau_DM0","mutau_DM1", "mutau_3Prong"]}

    muon_trg_dict = {
        "2018_UL": ROOT.std.vector('std::string')({"NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight","NUM_IsoMu24_or_Mu50_DEN_CutBasedIdTight_and_PFIsoTight", "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"}),

        "2017_UL": ROOT.std.vector('std::string')({"NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight","NUM_IsoMu27_or_Mu50_DEN_CutBasedIdTight_and_PFIsoTight", "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"}),

        "2016preVFP_UL":ROOT.std.vector('std::string')({"NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight","NUM_IsoMu24_or_IsoTkMu24_or_Mu50_or_TkMu50_DEN_CutBasedIdTight_and_PFIsoTight", "NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"}),

        "2016postVFP_UL":ROOT.std.vector('std::string')({"NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight","NUM_IsoMu24_or_IsoTkMu24_or_Mu50_or_TkMu50_DEN_CutBasedIdTight_and_PFIsoTight", "NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose"})

    }

    muon_trgHistNames_dict = {
        "2018_UL": ["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst","NUM_IsoMu24_or_Mu50_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst", "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose_eta_pt_syst"],

        "2017_UL": ["NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst","NUM_IsoMu27_or_Mu50_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst", "NUM_Mu50_or_OldMu100_or_TkMu100_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose_eta_pt_syst"],

        "2016preVFP_UL":["NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst","NUM_IsoMu24_or_IsoTkMu24_or_Mu50_or_TkMu50_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst", "NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose_eta_pt_syst"],

        "2016postVFP_UL":["NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst","NUM_IsoMu24_or_IsoTkMu24_or_Mu50_or_TkMu50_DEN_CutBasedIdTight_and_PFIsoTight_eta_pt_syst", "NUM_Mu50_or_TkMu50_DEN_CutBasedIdGlobalHighPt_and_TkIsoLoose_eta_pt_syst"],

    }

    singleTau_SF_dict = {
        "2018_UL": {'Central': 0.87 , 'Up': 0.98 , 'Down': 0.76,},
        "2017_UL" :  {'Central': 1.08, 'Up': 1.18, 'Down': 0.98,},
        "2016preVFP_UL" :  {'Central':0.88, 'Up':0.8, 'Down':0.96,},
        "2016postVFP_UL" :   {'Central':0.88, 'Up':0.8, 'Down':0.96,},
    }

    def __init__(self, period, config):
        jsonFile_Tau = TrigCorrProducer.TauTRG_jsonPath.format(period)
        #print(jsonFile_Tau)
        #jsonFile_Mu = TrigCorrProducer.MuTRG_jsonPath.format(period)
        self.deepTauVersion = f"""DeepTau{deepTauVersions[config["deepTauVersion"]]}v{config["deepTauVersion"]}"""
        #print(self.deepTauVersion)
        jsonFile_e = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.eTRG_jsonPath.format(period, year_singleElefile[period]))
        #print(jsonFile_e)
        jsonFile_Mu = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.MuTRG_jsonPath.format(period, year_singleMufile[period]))
        #print(jsonFile_Mu)
        jsonFile_mu_XTrg = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.mu_XTrg_jsonPath.format(period,year_xTrg_muTaufile[period]))
        #print(jsonFile_mu_XTrg)
        jsonFile_e_XTrg = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.e_XTrg_jsonPath.format(period,year_xTrg_eTaufile[period]))
        self.period = period
        #self.trg_config = trg_config
        #print(jsonFile_e_XTrg)
        if self.deepTauVersion=='DeepTau2018v2p5':
            jsonFile_Tau_rel = f"Corrections/data/TAU/{period}/tau_DeepTau2018v2p5_{period}_101123.json"
            jsonFile_Tau = os.path.join(os.environ['ANALYSIS_PATH'],jsonFile_Tau_rel)
        if not TrigCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "triggers.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            wp_map_cpp = createWPChannelMap(config["deepTauWPs"])
            #print(wp_map_cpp)
            # "{self.muon_trg_dict[period]}",
            year = period.split('_')[0]
            trigNames_mu_vec = """std::vector<std::string>{\""""
            trigNames_mu_vec += """\", \"""".join(path for path in self.muon_trgHistNames_dict[period])
            trigNames_mu_vec += """\" } """
            #print(trigNames_mu_vec)
            ROOT.gInterpreter.ProcessLine(f"""::correction::TrigCorrProvider::Initialize("{jsonFile_Tau}", "{self.deepTauVersion}", {wp_map_cpp}, "{jsonFile_Mu}", "{year}", {trigNames_mu_vec},"{jsonFile_e}","{jsonFile_e_XTrg}","{jsonFile_mu_XTrg}")""")
            TrigCorrProducer.initialized = True

    def getTrgSF(self, df, trigger_names, lepton_legs, return_variations, isCentral):
        SF_branches = []
        trg_name = 'ditau'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_tau{leg_idx+1}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::tau && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getTauSF_fromCorrLib(
                                 HttCandidate.leg_p4[{leg_idx}], Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]), "{trg_name}", HttCandidate.channel(),
                                ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'singleMu'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::mu && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_fromRootFile(
                                 HttCandidate.leg_p4[{leg_idx}],::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'singleMu50'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::mu && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_fromRootFile(
                                 HttCandidate.leg_p4[{leg_idx}],::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")
        trg_name = 'singleEle'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::e && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_fromRootFile(
                                 HttCandidate.leg_p4[{leg_idx}],::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'mutau'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        if leg_idx == 0:
                            df = df.Define(f"{branch_name}_double",
                                    f'''
                                    if({applyTrgBranch_name} && HttCandidate.leg_type[{leg_idx}] == Leg::mu)
                                    {{
                                        return ::correction::TrigCorrProvider::getGlobal().getSF_fromRootFile(HttCandidate.leg_p4[{leg_idx}], ::correction::TrigCorrProvider::UncSource::{source},::correction::UncScale::{scale}, true);
                                    }}
                                    return 1.f;''')
                        elif leg_idx ==1:
                            df = df.Define(f"{branch_name}_double",
                                f'''
                                if({applyTrgBranch_name} && HttCandidate.leg_type[{leg_idx}] == Leg::tau)
                                {{
                                    return ::correction::TrigCorrProvider::getGlobal().getTauSF_fromCorrLib(
                                    HttCandidate.leg_p4[{leg_idx}], Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]), "{trg_name}", HttCandidate.channel(), ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} );
                                }}
                                return 1.f;''')
                        else:
                            print("not known leg")
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'etau'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        if leg_idx == 0:
                            df = df.Define(f"{branch_name}_double",
                                    f'''
                                    if({applyTrgBranch_name} && HttCandidate.leg_type[{leg_idx}] == Leg::e)
                                    {{
                                        return ::correction::TrigCorrProvider::getGlobal().getSF_fromRootFile(HttCandidate.leg_p4[{leg_idx}], ::correction::TrigCorrProvider::UncSource::{source},::correction::UncScale::{scale}, true);
                                    }}
                                    return 1.f;''')
                        elif leg_idx ==1:
                            df = df.Define(f"{branch_name}_double",
                                f'''
                                if({applyTrgBranch_name} && HttCandidate.leg_type[{leg_idx}] == Leg::tau)
                                {{
                                    return ::correction::TrigCorrProvider::getGlobal().getTauSF_fromCorrLib(
                                    HttCandidate.leg_p4[{leg_idx}], Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]), "{trg_name}", HttCandidate.channel(), ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} );
                                }}
                                return 1.f;''')
                        else:
                            print("not known leg")
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'singleTau'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        value_shifted = self.singleTau_SF_dict[self.period][scale]
                        df = df.Define(f"{branch_name}_double",
                                f"""
                                if({applyTrgBranch_name} && HttCandidate.leg_type[{leg_idx}] == Leg::tau)
                                {{
                                    return {value_shifted};
                                }}
                                return 1.;""")
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")
        return df,SF_branches