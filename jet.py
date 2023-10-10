import os
import ROOT
from .CorrectionsCore import *

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

    jsonPath_btag = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/{}/btagging.json.gz"

    initialized = False
    uncSources_core = ["FlavorQCD","RelativeBal", "HF", "BBEC1", "EC2", "Absolute", "BBEC1_", "Absolute_", "EC2_", "HF_", "RelativeSample_" ]
    uncSources_extended = uncSources_core+["JER", "Total"]

    #Sources = []
    period = None
    def __init__(self, period,isData):
        JetCorrProducer.isData = isData
        jsonFile_btag = JetCorrProducer.jsonPath_btag.format(period)
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
            headershape_path = os.path.join(headers_dir, "btagShape.h")
            JME_calc_path = os.path.join(headers_dir, "JMESystematicsCalculators.cc")
            ROOT.gInterpreter.Declare(f'#include "{JME_calc_path}"')
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.Declare(f'#include "{headershape_path}"')
            ROOT.gInterpreter.ProcessLine(f"""::correction::JetCorrProvider::Initialize("{ptResolution}", "{ptResolutionSF}","{JEC_Regrouped}", "{period.split("_")[0]}")""")
            ROOT.gInterpreter.ProcessLine(f"""::correction::bTagShapeCorrProvider::Initialize("{jsonFile_btag}", "{period.split("_")[0]}")""")
            JetCorrProducer.period = period
            JetCorrProducer.initialized = True

    def addtbTagShapeSFInDf(df, bTagShapeSource, SF_branches, source, scale, syst_name, want_rel = True):
        bTagShape_branch_name = f"weight_bTagShapeSF_{syst_name}"
        bTagShape_branch_central = f"""weight_bTagShapeSF_{getSystName(central, central)}"""
        df = df.Define(f"{bTagShape_branch_name}_double",
                    f''' ::correction::bTagShapeCorrProvider::getGlobal().getBTagShapeSF(
                    Jet_p4, Jet_bCand, Jet_hadronFlavour, Jet_btagDeepFlavB,
                    ::correction::bTagShapeCorrProvider::UncSource::{bTagShapeSource},
                    ::correction::UncScale::{scale},
                    ::correction::JetCorrProvider::UncSource::{source}) ''')
        if want_rel:
            df = df.Define(f"{bTagShape_branch_name}_rel", f"static_cast<float>({bTagShape_branch_name}_double/{bTagShape_branch_central})")
            bTagShape_branch_name += '_rel'
        else:
            df = df.Define(f"{bTagShape_branch_name}", f"static_cast<float>({bTagShape_branch_name}_double)")
        SF_branches.append(bTagShape_branch_name)
        return df, SF_branches


    def getP4Variations(self, df, source_dict):
        df = df.Define(f'Jet_p4_shifted_map', f'''::correction::JetCorrProvider::getGlobal().getShiftedP4(
                                Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor, Jet_area,
                                Jet_jetId, Rho_fixedGridRhoFastjetAll, Jet_partonFlavour, 0, GenJet_pt, GenJet_eta,
                                GenJet_phi, GenJet_mass, event)''')
        for source in [ central] + JetCorrProducer.uncSources_extended:
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

    def getBtagShapeSFs(self, df, jes_syst_name, isCentral):
        SF_branches_core = []
        SF_branches_jes = []
        bTagShapeSource_jesCentral_syst_name = getSystName(central, central)
        df, SF_branches_core= JetCorrProducer.addtbTagShapeSFInDf(df, central,SF_branches_core, central, central, bTagShapeSource_jesCentral_syst_name, False)
        if isCentral:
            for bTagShapeSource_jesCentral in ["lf", "hf", "lfstats1", "lfstats2", "hfstats1", "hfstats2", "cferr1", "cferr2"]:
                for scale in getScales(bTagShapeSource_jesCentral):
                    bTagShapeSource_jesCentral_syst_name = getSystName(bTagShapeSource_jesCentral, scale)
                    df, SF_branches_core= JetCorrProducer.addtbTagShapeSFInDf(df, bTagShapeSource_jesCentral,SF_branches_core, central, scale, bTagShapeSource_jesCentral_syst_name, True)
        else:
            for jes_source in JetCorrProducer.uncSources_core:
                jes_source_eff= "JES_" + jes_source
                bTagShapeSource = 'jes'+jes_source if jes_source != central else central
                if jes_source.endswith("_") :
                    jes_source_eff = jes_source_eff+ JetCorrProducer.period.split("_")[0]
                    jes_source+="year"
                    bTagShapeSource+="year"
                for scale in getScales(jes_source):
                    if jes_syst_name != getSystName(jes_source_eff, scale): continue
                    df, SF_branches_jes= JetCorrProducer.addtbTagShapeSFInDf(df, bTagShapeSource, SF_branches_jes,jes_source, scale,jes_syst_name, False)
                if len(SF_branches_jes)>1:
                    print(f"len di SF_branches_jes = {len(SF_branches_jes)}")
        final_sf_jes = SF_branches_jes[0] if len(SF_branches_jes)==1 else ""
        return df,SF_branches_core, final_sf_jes

    def getEnergyResolution(self, df):
        df= df.Define(f"Jet_ptRes", f""" ::correction::JetCorrProvider::getGlobal().getResolution(
            Jet_pt, Jet_eta, Rho_fixedGridRhoFastjetAll ) """)
        return df
