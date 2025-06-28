import os
import ROOT
from .CorrectionsCore import *

# https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonSelection
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/MUO
# note: at the beginning of february 2024, the names have been changed to muon_Z.json.gz and muon_HighPt.json.gz for high pT muons
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2018
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016



class JetVetoMapProvider:
    JME_vetoMap_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/{}/jetvetomaps.json.gz"
    initialized = False
    period = None

    # jetvetomap_names = { "2022_Summer22": ["Summer22_23Sep2023","Summer22_23Sep2023_RunCD_v1"], #period: [filename, entryname]
    #                 "2022_Summer22EE": ["Summer22EE_23Sep2023","Summer22EE_23Sep2023_RunEFG_v1"],
    #                 "2023_Summer23BPix": ["Summer23BPixPrompt23","Summer23BPixPrompt23_RunD_v1"],
    #                 "2023_Summer23": ["Summer23Prompt23","Summer23Prompt23_RunC_v1"]}
    jetvetomap_names = { "2022_Summer22": "Summer22_23Sep2023_RunCD_v1", #period: , entryname
                    "2022_Summer22EE": "Summer22EE_23Sep2023_RunEFG_v1",
                    "2023_Summer23BPix": "Summer23BPixPrompt23_RunD_v1",
                    "2023_Summer23": "Summer23Prompt23_RunC_v1"}

    def __init__(self, era):
        period = period_names[era]
        entry_name = jetvetomap_names[period]
        JME_vetoMap_JsonFile = os.path.join(os.environ['ANALYSIS_PATH'],JetVetoMapProvider.JME_vetoMap_JsonPath.format(period))
        if not JetVetoMapProvider.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "mu.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::JetVetoMapProvider::Initialize("{JME_vetoMap_JsonFile}", "{entry_name}")')
            JetVetoMapProvider.period = period
            JetVetoMapProvider.initialized = True


    def GetJetVetoMap(self, df):
        SF_branches = []
        uncSource = "jetvetomap"
        df = df.Define(f"vetoMapLooseRegion", "Jet_pt > 15 && ( Jet_jetId & 2 ) && SelectedJet_chHEF + SelectedJet_neHEF < 0.9 ") #  (Jet_puId > 0 || Jet_pt >50) &&  for CHS jets
        df = df.Define(f"vetoMapLooseRegionNonOverlapping", " RemoveOverlaps(Jet_p4, vetoMapLooseRegion, Muon_p4, Muon_p4.size(), 0.2)")
        # jet pT > 15 GeV, tight jet ID, PU jet ID for CHS jets with pT < 50 GeV,  jet EM fraction (charged + neutral) < 0.9
        # jets that don’t overlap with PF muon (dR < 0.2) RemoveOverlaps(Jet_p4, vetoMapLooseRegion, Muon_p4, Muon_p4.size(), 0.2)
        df = df.Define(f"weight_jetVetoMap_double",f'''vetoMapLooseRegionNonOverlapping? ::correction::JetVetoMapProvider::getGlobal().GetJetVetoMapValue(Jet_p4):1''')
        # jet eta, jet phi, type = "jetvetomap"
        df = df.Define("weight_jetVetoMap", f"static_cast<float>(weight_jetVetoMap_double)")
        SF_branches.append("weight_jetVetoMap")
        return df,SF_branches

