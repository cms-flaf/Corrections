import os
import ROOT
from .CorrectionsCore import *
import yaml

class JetCorrProducer:
    JEC_SF_txtPath = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_SF_AK4PFchs.txt"
    JEC_PtRes_txtPath = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_PtResolution_AK4PFchs.txt"
    JEC_PhiRes_txtPath = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_PhiResolution_AK4PFchs.txt"
    JEC_EtaRes_txtPath = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Summer19UL18_JRV2_MC_EtaResolution_AK4PFchs.txt"
    JES_Regouped_txtPath = "Corrections/data/JME/{}/Summer19UL18_JRV2_MC/Regrouped_Summer19UL18_V5_MC_UncertaintySources_AK4PFchs.txt"
    initialized = False
    #Sources = []
    period = None
    def __init__(self, period):
        ptResolution = os.path.join(os.environ['ANALYSIS_PATH'],JetCorrProducer.JEC_PtRes_txtPath.format(period))
        ptResolutionSF = os.path.join(os.environ['ANALYSIS_PATH'],JetCorrProducer.JEC_SF_txtPath.format(period))
        JEC_Regrouped = os.path.join(os.environ['ANALYSIS_PATH'], JetCorrProducer.JES_Regouped_txtPath.format(period))
        if not JetCorrProducer.initialized:
            ROOT.gSystem.Load("libJetMETCorrectionsModules.so")
            ROOT.gSystem.Load("libCondFormatsJetMETObjects.so")
            ROOT.gSystem.Load("libCommonToolsUtils.so")
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "jet.h")
            JME_calc_path = os.path.join(headers_dir, "JMESystematicsCalculators.cc")
            ROOT.gInterpreter.Declare(f'#include "{JME_calc_path}"')
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::JetCorrProvider::Initialize("{ptResolution}", "{ptResolutionSF}","{JEC_Regrouped}")')
            JetCorrProducer.period = period
            JetCorrProducer.initialized = True
    def getP4Smearing(self, df, source_dict):
        for source in [ central ] :
            updateSourceDict(source_dict, source, 'Jet')
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                df = df.Define(f'Jet_p4_{syst_name}', f'''::correction::JetCorrProvider::getGlobal().getSmearing(
                                Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor, Jet_area,
                                Jet_jetId, Rho_fixedGridRhoFastjetAll, Jet_partonFlavour, 0, GenJet_pt, GenJet_eta,
                                GenJet_phi, GenJet_mass, event,
                               ::correction::JetCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})''')
                df = df.Define(f'Jet_p4_{syst_name}_delta', f'Jet_p4_{syst_name} - Jet_p4_{nano}')
        return df, source_dict

    def getJes(self, df, source_dict):
        for source in ["FlavorQCD","RelativeBal" "HF" "BBEC1" "EC2" "Absolute" "Total" "BBEC1_2018" "Absolute_2018" "EC2_2018" "HF_2018" "RelativeSample_2018"] :
            updateSourceDict(source_dict, source, 'Jet')
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                print(f"Jet_p4_{syst_name}")
                df = df.Define(f'Jet_p4_{syst_name}', f'''::correction::JetCorrProvider::getGlobal().getJesJet(
                                Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor, Jet_area,
                                Jet_jetId, Rho_fixedGridRhoFastjetAll, Jet_partonFlavour, 0, GenJet_pt, GenJet_eta,
                                GenJet_phi, GenJet_mass, event,
                               ::correction::JetCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})''')
                df = df.Define(f'Jet_p4_{syst_name}_delta', f'Jet_p4_{syst_name} - Jet_p4_{nano}')
        return df, source_dict

    def getEnergyResolution(self, df):
        df= df.Define(f"Jet_ptRes", f""" ::correction::JetCorrProvider::getGlobal().getResolution(
            Jet_pt, Jet_eta, Rho_fixedGridRhoFastjetAll ) """)
        return df