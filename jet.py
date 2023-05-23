import os
import ROOT
from .CorrectionsCore import *
import yaml

class JetCorrProducer:
    JEC_SF_txtPath_MC = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_SF_AK4PFchs.txt"
    JEC_PtRes_txtPath_MC = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_PtResolution_AK4PFchs.txt"
    JEC_PhiRes_txtPath_MC = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_PhiResolution_AK4PFchs.txt"
    JEC_EtaRes_txtPath_MC = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_EtaResolution_AK4PFchs.txt"
    JES_Regouped_txtPath_MC = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/RegroupedV2_Summer19UL18_V5_MC_UncertaintySources_AK4PFchs.txt"
    JEC_SF_txtPath_data = "Corrections/data/JME/{}/Summer19UL18_JRV2_DATA/Summer19UL18_JRV2_DATA_SF_AK4PFchs.txt"
    JEC_PtRes_txtPath_data = "Corrections/data/JME/{}/Summer19UL18_JRV2_DATA/Summer19UL18_JRV2_DATA_PtResolution_AK4PFchs.txt"
    JEC_PhiRes_txtPath_data = "Corrections/data/JME/{}/Summer19UL18_JRV2_DATA/Summer19UL18_JRV2_DATA_PhiResolution_AK4PFchs.txt"
    JEC_EtaRes_txtPath_data = "Corrections/data/JME/{}/Summer19UL18_JRV2_DATA/Summer19UL18_JRV2_DATA_EtaResolution_AK4PFchs.txt"
    initialized = False
    #Sources = []
    period = None
    def __init__(self, period,isData):
        JetCorrProducer.isData = isData
        ptResolution = os.path.join(os.environ['ANALYSIS_PATH'],JetCorrProducer.JEC_PtRes_txtPath_MC.format(period))
        ptResolutionSF = os.path.join(os.environ['ANALYSIS_PATH'],JetCorrProducer.JEC_SF_txtPath_MC.format(period))
        JEC_Regrouped = os.path.join(os.environ['ANALYSIS_PATH'], JetCorrProducer.JES_Regouped_txtPath_MC.format(period))
        if JetCorrProducer.isData:
            ptResolution = os.path.join(os.environ['ANALYSIS_PATH'],JetCorrProducer.JEC_PtRes_txtPath_data.format(period))
            ptResolutionSF = os.path.join(os.environ['ANALYSIS_PATH'],JetCorrProducer.JEC_SF_txtPath_data.format(period))
        if not JetCorrProducer.initialized:
            ROOT.gSystem.Load("libJetMETCorrectionsModules.so")
            ROOT.gSystem.Load("libCondFormatsJetMETObjects.so")
            ROOT.gSystem.Load("libCommonToolsUtils.so")
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "jet.h")
            JME_calc_path = os.path.join(headers_dir, "JMESystematicsCalculators.cc")
            ROOT.gInterpreter.Declare(f'#include "{JME_calc_path}"')
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f"""::correction::JetCorrProvider::Initialize("{ptResolution}", "{ptResolutionSF}","{JEC_Regrouped}", "{period.split("_")[0]}")""")
            JetCorrProducer.period = period
            JetCorrProducer.initialized = True

    def getP4Variations(self, df, source_dict):
        df = df.Define(f'Jet_p4_shifted_map', f'''::correction::JetCorrProvider::getGlobal().getShiftedP4(
                                Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor, Jet_area,
                                Jet_jetId, Rho_fixedGridRhoFastjetAll, Jet_partonFlavour, 0, GenJet_pt, GenJet_eta,
                                GenJet_phi, GenJet_mass, event)''')
        for source in [ central] + ["JER", "FlavorQCD","RelativeBal", "HF", "BBEC1", "EC2", "Absolute", "Total", "BBEC1_", "Absolute_", "EC2_", "HF_", "RelativeSample_" ]:
            source_eff = source
            if source.endswith("_") :
                source_eff = source+ JetCorrProducer.period.split("_")[0]
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