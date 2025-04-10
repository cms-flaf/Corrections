import os
import ROOT
from .CorrectionsCore import *
from FLAF.Common.Utilities import *
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

# singleTau;diTau run3: https://gitlab.cern.ch/cms-tau-pog/jsonpog-integration/-/tree/TauPOG_v2_deepTauV2p5/POG/TAU?ref_type=heads
# crossTrigger run3 : https://gitlab.cern.ch/cms-higgs-leprare/hleprare/-/tree/master/TriggerScaleFactors?ref_type=heads
# singleEle : /cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/EGM/{period}/electronHlt.json.gz
# singleMu : /cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{period}/muon_Z.json.gz
# missing efficiencies for singleMu --> run2 eff are https://gitlab.cern.ch/cms-muonPOG/muonefficiencies/-/tree/master (but run3 is missing also on this folder) 


# SFSources_bbtautau = { 'ditau': [ "ditau_DM0","ditau_DM1", "ditau_3Prong"], 'singleMu':['singleMu'],'singleTau':['singleTau'], 'singleEle':['singleEle'],'etau':['etau_ele',"etau_DM0","etau_DM1", "etau_3Prong",],'mutau':['mutau_mu',"mutau_DM0","mutau_DM1", "mutau_3Prong"]}


class TrigCorrProducer:
    MuTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_Z.json.gz"
    eTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/EGM/{}/electronHlt.json.gz"
    # TauTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
    TauTRG_jsonPath = os.path.join(os.environ['ANALYSIS_PATH'], "Corrections/data/TRG/{}/tau_DeepTau2018v2p5_{}.json")
    muTauTRG_jsonPath = os.path.join(os.environ['ANALYSIS_PATH'], "Corrections/data/TRG/{}/CrossMuTauHlt_MuLeg_v1.json")
    eTauTRG_jsonPath = os.path.join(os.environ['ANALYSIS_PATH'], "Corrections/data/TRG/{}/CrossEleTauHlt_EleLeg_v1.json")
    TaujetTRG_jsonPath = os.path.join(os.environ['ANALYSIS_PATH'], "Corrections/data/TRG/{}/DiTauJetHlt_JetLeg_v1.json")
    #"/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
    initialized = False
    SFSources = { 'singleIsoMu':['IsoMu24'],'singleEleWpTight':['singleEle'],
                'singleMu':['IsoMu24'], 'singleEle':['singleEle'], 'ditau':['ditau_DM0', 'ditau_DM1', 'ditau_3Prong']}
    muon_trg_dict = {"2022_Summer22":"NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight","2022_Summer22EE":"NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"}
    ele_trg_dict = {
        "SF" :{"2022_Summer22":"Electron-HLT-SF",
                "2022_Summer22EE":"Electron-HLT-SF"},
        "DataEff" :{"2022_Summer22":"Electron-HLT-DataEff",
                "2022_Summer22EE":"Electron-HLT-DataEff"},
        "McEff" :{"2022_Summer22":"Electron-HLT-McEff",
                "2022_Summer22EE":"Electron-HLT-McEff"}} # same as CrossTrigger_etau_eleLeg
    tau_trg_dict = {
        '2022_Summer22': 'tau_trigger',
        '2022_Summer22EE': 'tau_trigger',}
    
    year = ""
    def __init__(self, period, config):
        jsonFile_Mu = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.MuTRG_jsonPath.format(period))
        jsonFile_e = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.eTRG_jsonPath.format(period))
        tau_filename_dict = {'2022_Summer22': '2022_preEE',
                            '2022_Summer22EE': '2022_postEE',
                            '2023_Summer23': '2023_preBPix',
                            '2023_Summer23BPix': '2023_postBPix'}
        jsonFile_Tau = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.TauTRG_jsonPath.format(tau_filename_dict[period],tau_filename_dict[period]))  
        #jsonFile_Tau = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.TauTRG_jsonPath.format(period))  #uncomment this line when central path is available
        jsonFile_TauJet = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.TaujetTRG_jsonPath.format(tau_filename_dict[period]))  
        jsonFile_muTau = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.muTauTRG_jsonPath.format(tau_filename_dict[period]))  
        jsonFile_eTau = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.eTauTRG_jsonPath.format(tau_filename_dict[period]))  
        self.period = period
        print(f"jsonFile_Mu: {jsonFile_Mu}")
        print(f"jsonFile_e: {jsonFile_e}")
        print(f"jsonFile_Tau: {jsonFile_Tau}")
        print(f"jsonFile_TauJet: {jsonFile_TauJet}")
        print(f"jsonFile_muTau: {jsonFile_muTau}")
        print(f"jsonFile_eTau: {jsonFile_eTau}")

        # jsonFile_Tau = os.path.join(os.environ['ANALYSIS_PATH'],f"Corrections/data/TAU/{tau_filename_dict[period]}/tau_DeepTau2018v2p5_{tau_filename_dict[period]}.json")


        if not TrigCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "triggersRun3.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            TrigCorrProducer.year = period.split("_")[0]
            self.year = period.split('_')[0]
            if (period.endswith('Summer22')):  TrigCorrProducer.year = period.split("_")[0]+"Re-recoBCD"
            if (period.endswith('Summer22EE')):  TrigCorrProducer.year = period.split("_")[0]+"Re-recoE+PromptFG"
            if (period.endswith('Summer23')):  TrigCorrProducer.year = period.split("_")[0]+"PromptC"
            if (period.endswith('Summer23BPix')):  TrigCorrProducer.year = period.split("_")[0]+"2023PromptD"
            
            print(f"{self.muon_trg_dict[period]}")
            print(f"{self.ele_trg_dict['McEff'][period]}")
            print(f"{self.tau_trg_dict[period]}")
            print(f"TrigCorrProducer.year: {TrigCorrProducer.year}")
            print(f"period: {period}")
            
            # ROOT.gInterpreter.ProcessLine(f"""::correction::TrigCorrProvider::Initialize("{jsonFile_Mu}","{jsonFile_e}", "{jsonFile_Tau}", "{self.muon_trg_dict[period]}","{self.ele_trg_dict['McEff'][period]}", "{self.tau_trg_dict[period]}", "{period}")""")
            ROOT.gInterpreter.ProcessLine(f"""::correction::TrigCorrProvider::Initialize("{jsonFile_Mu}","{jsonFile_e}", "{jsonFile_Tau}", "{jsonFile_TauJet}", "{jsonFile_eTau}", "{jsonFile_muTau}", "{self.muon_trg_dict[period]}","{self.ele_trg_dict['McEff'][period]}", "{self.tau_trg_dict[period]}","{period}")""")
            print("TriggCorrProducer initialized")
            TrigCorrProducer.initialized = True

    def getSF(self, df, trigger_names, lepton_legs, return_variations, isCentral):
        SF_branches = []
        legs_to_be ={
        'singleIsoMu' : ['mu','mu'],
        'singleEleWpTight' : ['e','e'],
        'ditau' : ['tau','tau'],
        'singleMu' : ['mu','mu'],
        'singleEle' : ['e','e']
        }
        for trg_name in ['singleEleWpTight','singleIsoMu','singleEle', 'singleMu', 'ditau']:
            if trg_name not in trigger_names: continue
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                leg_to_be = legs_to_be[trg_name][leg_idx]
                df = df.Define(applyTrgBranch_name, f"""{leg_name}_type == static_cast<int>(Leg::{leg_to_be}) && {leg_name}_index >= 0 && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if source == central and scale != central: continue
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        #the trigCorr dictionary below is due to different analysis having different trigger names for muon and electron.
                        trigCorr_dict = {'singleIsoMu' : 'singleIsoMu',
                                        'singleEleWpTight' : 'singleEleWpTight',
                                        'ditau' : 'ditau',
                                        'singleMu' : 'singleIsoMu',
                                        'singleEle' : 'singleEleWpTight'}
                        #for tau trigger sf, selecting SF for the time being as a corrtype, rather than eff_data/eff_mc
                        if trg_name == 'ditau':
                            df = df.Define(f"{branch_name}_double",
                                        f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_{trigCorr_dict[trg_name]}(
                                        {leg_name}_p4,"{TrigCorrProducer.year}",Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]), "{trigCorr_dict[trg_name]}", "Medium", "sf", ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        else:
                            df = df.Define(f"{branch_name}_double",
                                        f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_{trigCorr_dict[trg_name]}(
                                        {leg_name}_p4,"{TrigCorrProducer.year}", ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")
        return df,SF_branches
    
    def getEff(self, df, trigger_names, offline_legs, return_variations, isCentral):
        offline_legs =["tau1","tau2"]
        SF_branches = []
        trg_name = "singleEle"
        leg_to_be = 'e'
        trg_path = "HLT_Ele30_WPTight_Gsf"
        # sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
        for leg_idx, leg_name in enumerate(offline_legs):
            applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
            query = f"""{leg_name}_type == static_cast<int>(Leg::{leg_to_be}) && {leg_name}_index >= 0 && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}"""
            print(f"query: {query}") 
            df = df.Define(applyTrgBranch_name, f"""{query}""")
            # df.Display(f"HLT_{trg_name}").Print()
            # df.Display(f"{leg_name}_HasMatching_{trg_name}").Print()
            # df.Display(f"{applyTrgBranch_name}").Print()
            df = df.Define(f"eff_MC_{leg_name}_{trg_name}", f"""{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getEff_singleEle({leg_name}_p4, "{TrigCorrProducer.year}", ::correction::TrigCorrProvider::UncSource::{central}, ::correction::UncScale::{central})  : 1.f """)
            df.Display([f"eff_MC_{leg_name}_{trg_name}", "tau1_pt", "tau2_pt"],10).Print()
            # SF_branches.append(f"eff_MC_{leg_name}_{trg_name}")


        # for leg_idx, leg_name in enumerate(offline_legs):
        #     branch_name = f"{trg_name}_{leg_name}_MCEff_"
        #     branch_central = f"weight_{leg_name}_MCEff_{trg_name}_{getSystName(central,central)}"
        #     #the trigCorr dictionary below is due to different analysis having different trigger names for muon and electron.
        #     df = df.Define(f"{branch_name}_double",
        #                                 f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_{trigCorr_dict[trg_name]}(
        #                                 {leg_name}_p4,"{TrigCorrProducer.year}", ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
            


        # for trg_name in ['singleEleWpTight','singleIsoMu','singleEle', 'singleMu', 'ditau']:
        #     if trg_name not in trigger_names: continue
        #     sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
        #     for leg_idx, leg_name in enumerate(lepton_legs):
        #         applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
        #         leg_to_be = legs_to_be[trg_name][leg_idx]
        #         df = df.Define(applyTrgBranch_name, f"""{leg_name}_type == static_cast<int>(Leg::{leg_to_be}) && {leg_name}_index >= 0 && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
        #         for source in [ central ] + sf_sources:
        #             for scale in getScales(source):
        #                 if source == central and scale != central: continue
        #                 if not isCentral and scale!= central: continue
        #                 syst_name = getSystName(source, scale)
        #                 suffix = f"{trg_name}_{syst_name}"
        #                 branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
        #                 branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
        #                 #the trigCorr dictionary below is due to different analysis having different trigger names for muon and electron.
        #                 trigCorr_dict = {'singleIsoMu' : 'singleIsoMu',
        #                                 'singleEleWpTight' : 'singleEleWpTight',
        #                                 'ditau' : 'ditau',
        #                                 'singleMu' : 'singleIsoMu',
        #                                 'singleEle' : 'singleEleWpTight'}
        #                 #for tau trigger sf, selecting SF for the time being as a corrtype, rather than eff_data/eff_mc
        #                 if trg_name == 'ditau':
        #                     df = df.Define(f"{branch_name}_double",
        #                                 f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_{trigCorr_dict[trg_name]}(
        #                                 {leg_name}_p4,"{TrigCorrProducer.year}",Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]), "{trigCorr_dict[trg_name]}", "Medium", "sf", ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
        #                 else:
        #                     df = df.Define(f"{branch_name}_double",
        #                                 f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF_{trigCorr_dict[trg_name]}(
        #                                 {leg_name}_p4,"{TrigCorrProducer.year}", ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
        #                 if scale != central:
        #                     df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
        #                     branch_name += '_rel'
        #                 else:
        #                     df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
        #                 SF_branches.append(f"{branch_name}")
        return df,SF_branches
