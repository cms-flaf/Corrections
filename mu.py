import os
import ROOT
from .CorrectionsCore import *
import yaml


class MuCorrProducer:
    muIDEff_JsonPath = "Corrections/data/MUO/{}/Efficiencies_muon_generalTracks_Z_Run2018_UL_ID.root"
    initialized = False
    SFSources = ["HighPtID"]


    def __init__(self, period):
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],MuCorrProducer.muIDEff_JsonPath.format(period))
        if not MuCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "mu.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::MuCorrProvider::Initialize()')
            MuCorrProducer.initialized = True

    def getRecoSF(self, df):
        recoMu_SF_branches = []
        for leg_idx in [0,1]:
            df = df.Define(f"weight_tau{leg_idx+1}_RecoMuSF",
                            f'''httCand.leg_type[{leg_idx}] == Leg::mu ? ::correction::MuCorrProvider::getGlobal().getRecoSF(httCand.leg_p4[{leg_idx}]) : 1.;''')
            recoMu_SF_branches.append(f"weight_tau{leg_idx+1}_RecoMuSF")
        return df,recoMu_SF_branches