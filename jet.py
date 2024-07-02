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
    uncSources_core = ["FlavorQCD","RelativeBal", "HF", "BBEC1", "EC2", "Absolute", "BBEC1_", "Absolute_", "EC2_", "HF_", "RelativeSample_" ]

    #Sources = []
    period = None
    def __init__(self, period,isData):
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

        JetCorrProducer.isData = isData

        ptResolution = os.path.join(os.environ['ANALYSIS_PATH'],JER_PtRes_txtPath_MC.format(period))
        ptResolutionSF = os.path.join(os.environ['ANALYSIS_PATH'],JER_SF_txtPath_MC.format(period))
        JEC_Regrouped = os.path.join(os.environ['ANALYSIS_PATH'], JEC_Regouped_txtPath_MC.format(period))
        if JetCorrProducer.isData:
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

    def getP4Variations(self, df, source_dict, apply_JER=True):
        df = df.Define(f'Jet_p4_shifted_map', f'''::correction::JetCorrProvider::getGlobal().getShiftedP4(
                                Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor, Jet_area,
                                Jet_jetId, Rho_fixedGridRhoFastjetAll, Jet_partonFlavour, 0, GenJet_pt, GenJet_eta,
                                GenJet_phi, GenJet_mass, event)''')
        apply_jer_list = []
        if apply_JER:
            apply_jer_list.append("JER")
        for source in [ central] + JetCorrProducer.uncSources_core + apply_jer_list:
            source_eff = source
            if source!=central and source != "JER":
                source_eff= "JES_" + source_eff
            if source.endswith("_") :
                source_eff = source_eff+ JetCorrProducer.period.split("_")[0]
                source+="year"
            updateSourceDict(source_dict, source_eff, 'Jet')
            for scale in getScales(source):
                syst_name = getSystName(source_eff, scale)
                df = df.Define(f'Jet_p4_{syst_name}', f'''Jet_p4_shifted_map.at({{::correction::JetCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}}})''')
                df = df.Define(f'Jet_p4_{syst_name}_delta', f'Jet_p4_{syst_name} - Jet_p4_{nano}')
        return df,source_dict


    def getEnergyResolution(self, df):
        df= df.Define(f"Jet_ptRes", f""" ::correction::JetCorrProvider::getGlobal().getResolution(
            Jet_pt, Jet_eta, Rho_fixedGridRhoFastjetAll ) """)
        return df
