import os
import ROOT
from .CorrectionsCore import *
import yaml

deepTauVersions = {"2p1":"2017", "2p5":"2018"}

class TauCorrProducer:
    jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
    initialized = False
    deepTauVersion = 'DeepTau2017v2p1'

    energyScaleSources_tau = ["TauES_DM0", "TauES_DM1", "TauES_3prong"]
    energyScaleSources_lep = ["EleFakingTauES_DM0", "EleFakingTauES_DM1", "MuFakingTauES"]
    SFSources_genuineTau_dm = [ "TauID_genuineTau_DM0","TauID_genuineTau_DM1", "TauID_genuineTau_3Prong"]
    SFSources_genuineTau_pt = ["TauID_genuineTau_Pt20_25", "TauID_genuineTau_Pt25_30", "TauID_genuineTau_Pt30_35",
        "TauID_genuineTau_Pt35_40", "TauID_genuineTau_Ptgt40"]
    SFSources_genuineLep=["TauID_genuineElectron_barrel", "TauID_genuineElectron_endcaps", "TauID_genuineMuon_etaLt0p4",
        "TauID_genuineMuon_eta0p4to0p8", "TauID_genuineMuon_eta0p8to1p2", "TauID_genuineMuon_eta1p2to1p7", "TauID_genuineMuon_etaGt1p7" ]

    def __init__(self, period, config):
        jsonFile = TauCorrProducer.jsonPath.format(period)
        if not TauCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "tau.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            wp_map_cpp = createWPChannelMap(config["deepTauWPs"])
            tauType_map = createTauSFTypeMap(config["genuineTau_SFtype"])
            ROOT.gInterpreter.ProcessLine(f'::correction::TauCorrProvider::Initialize("{jsonFile}", "{self.deepTauVersion}", {wp_map_cpp}, {tauType_map})')
            TauCorrProducer.initialized = True
            deepTauVersion = f"""DeepTau{deepTauVersions[config["deepTauVersion"]]}{config["deepTauVersion"]}"""

    def getES(self, df, source_dict):
        for source in [ central ] + TauCorrProducer.energyScaleSources_tau + TauCorrProducer.energyScaleSources_lep:
            updateSourceDict(source_dict, source, 'Tau')
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                df = df.Define(f'Tau_p4_{syst_name}', f'''::correction::TauCorrProvider::getGlobal().getES(
                               Tau_p4_{nano}, Tau_decayMode, Tau_genMatch,
                               ::correction::TauCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})''')
                df = df.Define(f'Tau_p4_{syst_name}_delta', f'Tau_p4_{syst_name} - Tau_p4_{nano}')

        return df, source_dict

    def getSF(self, df, return_variations=True, isCentral=True):
        sf_sources =TauCorrProducer.SFSources_genuineTau_dm+ TauCorrProducer.SFSources_genuineTau_pt+ TauCorrProducer.SFSources_genuineLep if return_variations else []
        SF_branches = {}
        for source in [ central ] + sf_sources:
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                if not isCentral and scale!= central: continue
                SF_branches[syst_name]= []
                for leg_idx in [0,1]:
                    df = df.Define(f"weight_tau{leg_idx+1}_idSF_{syst_name}",
                                f'''httCand.leg_type[{leg_idx}] == Leg::tau ? ::correction::TauCorrProvider::getGlobal().getSF(
                               httCand.leg_p4[{leg_idx}], Tau_decayMode.at(httCand.leg_index[{leg_idx}]),
                               Tau_genMatch.at(httCand.leg_index[{leg_idx}]), httCand.channel(),
                               ::correction::TauCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) : 1.;''')
                    SF_branches[syst_name].append(f"weight_tau{leg_idx+1}_idSF_{syst_name}")
        return df,SF_branches

