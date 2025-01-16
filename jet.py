import os
import ROOT
from .CorrectionsCore import *
# https://docs.google.com/spreadsheets/d/1JZfk78_9SD225bcUuTWVo4i02vwI5FfeVKH-dwzUdhM/edit#gid=1345121349

# MET corrections
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETRun2Corrections
# https://lathomas.web.cern.ch/lathomas/METStuff/XYCorrections/XYMETCorrection_withUL17andUL18andUL16.h
# https://indico.cern.ch/event/1033432/contributions/4339934/attachments/2235168/3788215/metxycorrections_UL2016.pdf
# JEC uncertainty sources took from recommendation here:
# https://twiki.cern.ch/twiki/bin/view/CMS/JECDataMC
# https://github.com/cms-jet/JECDatabase/tree/master
# https://twiki.cern.ch/twiki/bin/view/CMS/JECUncertaintySources
# JER uncertainty source took from:
# https://twiki.cern.ch/twiki/bin/view/CMS/JetResolution
# https://github.com/cms-jet/JRDatabase
# smearing procedure
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetResolution#Smearing_procedures

# according to recommendation, SummerUL19 should be used but also SummerUL20 are available for JER.
'''BBEC1_2016postVFP

IMPORTANT
From: https://twiki.cern.ch/twiki/bin/view/CMS/PdmVRun2LegacyAnalysis

Note: The RunIISummer19UL16(APV) samples have a bug in the beamspot position affecting only (most of the) 2016 samples HN, HN, talk. The RunIISummer19UL16 samples will be invalidated at the end of August. Please migrate to Summer20UL now. All Summer19UL samples are based on an older version of pythia. The difference of Summer19UL and Summer20UL due to the difference in the pythia version was studied and found negligible 1 2 3. Invalidation and deletion of all RunIISummer19 samples, for all years, is scheduled for the end of September 2021

'''


directories_JER = {
    "2018_UL":"Summer19UL18_JRV2",
    "2017_UL": "Summer19UL17_JRV2",
    "2016preVFP_UL":"Summer20UL16APV_JRV3",
    "2016postVFP_UL":"Summer20UL16_JRV3",
    }
directories_JEC = {
    "2018_UL":"Summer19UL18_V5_MC",
    "2017_UL": "Summer19UL17_V5_MC",
    "2016preVFP_UL":"Summer19UL16APV_V7_MC",
    "2016postVFP_UL":"Summer19UL16_V7_MC",
    }

regrouped_files_names = {
    "2018_UL":"RegroupedV2_Summer19UL18_V5_MC_UncertaintySources_AK4PFchs.txt",
    "2017_UL": "RegroupedV2_Summer19UL17_V5_MC_UncertaintySources_AK4PFchs.txt",
    "2016preVFP_UL":"RegroupedV2_Summer19UL16APV_V7_MC_UncertaintySources_AK4PFchs.txt",
    "2016postVFP_UL":"RegroupedV2_Summer19UL16_V7_MC_UncertaintySources_AK4PFchs.txt"
    }

class JetCorrProducer:
    JEC_SF_path = 'Corrections/data/JME/{}'
    jsonPath_btag = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/{}/btagging.json.gz"

    initialized = False

    jet_algorithm = "AK4PFPuppi"
    
    uncSources_regrouped = [ "FlavorQCD",
                             "RelativeBal",
                             "HF",
                             "BBEC1",
                             "EC2",
                             "Absolute",
                             "BBEC1_",
                             "Absolute_",
                             "EC2_",
                             "HF_",
                             "RelativeSample_" ]

    uncSources_minimal = ["Total"]

    jet_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/{}/jet_jerc.json.gz"
    # fatjet_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/{}/fatJet_jerc.json.gz"
    jersmear_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/jer_smear.json.gz"

    # format: key = period, value = (JEC tag, JER tag)
    run3_period_map_mc = { "2022_Summer22": ("Summer22_22Sep2023_V2_MC", "Summer22_22Sep2023_JRV1_MC"),
                           "2022_Prompt": ("Winter22Run3_V2_MC", "JR_Winter22Run3_V1_MC"),
                           "2022_Summer22EE": ("Summer22EE_22Sep2023_V2_MC", "Summer22EE_22Sep2023_JRV1_MC"),
                           "2023_Summer23BPix": ("Summer23BPixPrompt23_V1_MC", "Summer23BPixPrompt23_RunD_JRV1_MC"),
                           "2024_Winter24": ("Winter24Prompt24_V2_MC", "Summer23BPixPrompt23_RunD_JRV1_MC") }

    run3_period_map_data = { "2022_Summer22": ("Summer22_22Sep2023_RunCD_V2_DATA", "Summer22_22Sep2023_JRV1_MC"),
                             "2023_Summer23BPix": ("Summer23BPixPrompt23_RunD_V1_DATA", "Summer23BPixPrompt23_RunD_JRV1_MC") }

    #Sources = []
    period = None
    def __init__(self, period, isData, use_corrlib = True, use_regrouped = False):
        self.isData = isData
        self.use_regrouped = use_regrouped
        self.use_corrlib = use_corrlib
        self.uncSources_toUse = []
        if self.use_regrouped:
            self.uncSources_toUse = JetCorrProducer.uncSources_regrouped
        else:
            self.uncSources_toUse = JetCorrProducer.uncSources_minimal
        self.year = int(period[:4])
        print(f"period: {period}")
        print(f"year: {self.year}")
        if not self.use_corrlib:
            print("Initializing old JetCorrProducer")
            JEC_SF_path_period = JetCorrProducer.JEC_SF_path.format(period)
            JEC_dir = directories_JEC[period]
            JEC_SF_db = "Corrections/data/JECDatabase/textFiles/"

            JER_dir = directories_JER[period]
            JER_SF_db = "Corrections/data/JRDatabase/textFiles/"

            JER_SF_txtPath_MC = f"{JER_SF_db}/{JER_dir}_MC/{JER_dir}_MC_SF_AK4PFchs.txt"
            JER_PtRes_txtPath_MC = f"{JER_SF_db}/{JER_dir}_MC/{JER_dir}_MC_PtResolution_AK4PFchs.txt"
            JER_PhiRes_txtPath_MC = f"{JER_SF_db}/{JER_dir}_MC/{JER_dir}_MC_PhiResolution_AK4PFchs.txt"
            JER_EtaRes_txtPath_MC = f"{JER_SF_db}/{JER_dir}_MC/{JER_dir}_MC_EtaResolution_AK4PFchs.txt"

            JER_SF_txtPath_data = f"{JER_SF_db}/{JER_dir}_DATA/{JER_dir}_DATA_SF_AK4PFchs.txt"
            JER_PtRes_txtPath_data = f"{JER_SF_db}/{JER_dir}_DATA/{JER_dir}_DATA_PtResolution_AK4PFchs.txt"
            JER_PhiRes_txtPath_data = f"{JER_SF_db}/{JER_dir}_DATA/{JER_dir}_DATA_PhiResolution_AK4PFchs.txt"
            JER_EtaRes_txtPath_data = f"{JER_SF_db}/{JER_dir}_DATA/{JER_dir}_DATA_EtaResolution_AK4PFchs.txt"

            JEC_Regouped_txtPath_MC = f"{JEC_SF_db}/{JEC_dir}/{regrouped_files_names[period]}"

            ptResolution = os.path.join(os.environ['ANALYSIS_PATH'],JER_PtRes_txtPath_MC.format(period))
            ptResolutionSF = os.path.join(os.environ['ANALYSIS_PATH'],JER_SF_txtPath_MC.format(period))
            JEC_Regrouped = os.path.join(os.environ['ANALYSIS_PATH'], JEC_Regouped_txtPath_MC.format(period))
            if self.isData:
                ptResolution = os.path.join(os.environ['ANALYSIS_PATH'],JER_PtRes_txtPath_data.format(period))
                ptResolutionSF = os.path.join(os.environ['ANALYSIS_PATH'],JER_SF_txtPath_data.format(period))
            if not JetCorrProducer.initialized:
                ROOT.gSystem.Load("libJetMETCorrectionsModules.so")
                ROOT.gSystem.Load("libCondFormatsJetMETObjects.so")
                ROOT.gSystem.Load("libCommonToolsUtils.so")
                headers_dir = os.path.dirname(os.path.abspath(__file__))
                header_path = os.path.join(headers_dir, "jet.h")
                JME_calc_base = os.path.join(headers_dir, "JMECalculatorBase.cc")
                JME_calc_path = os.path.join(headers_dir, "JMESystematicsCalculators.cc")
                ROOT.gInterpreter.Declare(f'#include "{JME_calc_base}"')
                ROOT.gInterpreter.Declare(f'#include "{JME_calc_path}"')
                ROOT.gInterpreter.Declare(f'#include "{header_path}"')
                ROOT.gInterpreter.ProcessLine(f"""::correction::JetCorrProvider::Initialize("{ptResolution}", "{ptResolutionSF}","{JEC_Regrouped}", "{periods[period]}")""")
                JetCorrProducer.period = period
                JetCorrProducer.initialized = True
        else:
            print("Initializing new JetCorrProducer")
            jet_path = JetCorrProducer.jet_jsonPath.format(period)
            jet_jsonFile = os.path.join(os.environ['ANALYSIS_PATH'], jet_path)
            jersmear_path = JetCorrProducer.jersmear_jsonPath
            jetsmear_jsonFile = os.path.join(os.environ['ANALYSIS_PATH'], jersmear_path)
            run3_period_map = JetCorrProducer.run3_period_map_data if self.isData else JetCorrProducer.run3_period_map_mc
            jec_tag, jer_tag = run3_period_map[period]
            year = period.split('_')[0]
            algo = JetCorrProducer.jet_algorithm
            if not JetCorrProducer.initialized:
                headers_dir = os.path.dirname(os.path.abspath(__file__))
                header_path = os.path.join(headers_dir, "jet.h")
                ROOT.gInterpreter.Declare(f'#include "{header_path}"')
                ROOT.gInterpreter.ProcessLine(f'::correction::JetCorrectionProvider::Initialize("{jet_jsonFile}", "{jetsmear_jsonFile}", "{jec_tag}", "{jer_tag}", "{algo}", "{year}, {self.use_regrouped}")')
                JetCorrProducer.initialized = True


    def getP4Variations(self, df, source_dict, apply_JER, apply_JES):
        class_name = ""
        if self.use_corrlib:
            df = df.Define("Jet_p4_shifted_map", '''::correction::JetCorrectionProvider::getGlobal().getShiftedP4(Jet_pt, Jet_eta, Jet_phi, Jet_mass,
                                                                                                                  Jet_rawFactor, Jet_area, Rho_fixedGridRhoFastjetAll,
                                                                                                                  GenJet_pt, Jet_genJetIdx, event)''')
            class_name = "JetCorrectionProvider"
        else:
            df = df.Define('Jet_p4_shifted_map', f'''::correction::JetCorrProvider::getGlobal().getShiftedP4(
                            Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor, Jet_area,
                            Jet_jetId, Rho_fixedGridRhoFastjetAll, Jet_partonFlavour, 0, GenJet_pt, GenJet_eta,
                            GenJet_phi, GenJet_mass, event)''')       
            class_name = "JetCorrProvider"     

        apply_jer_list = []
        if apply_JER:
            apply_jer_list.append("JER")
        apply_jes_list = self.uncSources_toUse if apply_JES else []
        # central variable is imported from CorrectionsCore.p, where it is defined
        for source in [ central ] + apply_jes_list + apply_jer_list:
            source_eff = source
            if source in apply_jes_list: # source!=central and source != "JER":
                source_eff = "JES_" + source_eff
            if source.endswith("_") :
                source_eff = source_eff + JetCorrProducer.period.split("_")[0]
                source += "year"
            updateSourceDict(source_dict, source_eff, 'Jet')
            for scale in getScales(source):
                syst_name = getSystName(source_eff, scale)
                df = df.Define(f"Jet_p4_{syst_name}", f"Jet_p4_shifted_map.at({{::correction::{class_name}::UncSource::{source}, ::correction::UncScale::{scale}}})")
                df = df.Define(f"Jet_p4_{syst_name}_delta", f"Jet_p4_{syst_name} - Jet_p4_{nano}")

        return df, source_dict


    def getEnergyResolution(self, df):
        if self.use_corrlib:
            df = df.Define("Jet_ptRes", "::correction::JetCorrectionProvider::getGlobal().GetResolutions(Jet_pt, Jet_mass, Jet_rawFactor, Jet_eta, Rho_fixedGridRhoFastjetAll)")
        else:
            df = df.Define("Jet_ptRes", "::correction::JetCorrProvider::getGlobal().getResolution(Jet_pt, Jet_eta, Rho_fixedGridRhoFastjetAll)")
        return df

    #def getVetoMap(self, df):
    #    df = df.Define(f"vetoMapLooseRegion", "Jet_pt > 15 && ( Jet_jetId & 2 ) && (Jet_puId > 0 || Jet_pt >50) ")

    # jet pT > 15 GeV
    # tight jet ID
    # PU jet ID for CHS jets with pT < 50 GeV
    # jet EM fraction (charged + neutral) < 0.9
    # jets that don’t overlap with PF muon (dR < 0.2) RemoveOverlaps(Jet_p4, vetoMapLooseRegion, Muon_p4, Muon_p4.size(), 0.2)