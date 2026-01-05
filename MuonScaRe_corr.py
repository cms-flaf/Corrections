import os
import urllib.request
import ROOT
from .CorrectionsCore import *


class MuonScaReCorrProducer:
    initialized = False
    jsonPath = "Corrections/data/MUO/MuonScaRe/{}.json"
    initialized = False
    uncSources = ["ScaRe"]

    period = None

    def __init__(self, period, isData, pt_for_ScaRe, return_variations=False):
        self.period = period
        self.pt_for_ScaRe = pt_for_ScaRe
        print(period)
        jsonFile_path = MuonScaReCorrProducer.jsonPath.format(period)
        self.isData = isData
        self.return_variations = return_variations
        jsonFile = os.path.join(os.environ["ANALYSIS_PATH"], jsonFile_path)
        if not MuonScaReCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "MuonScaReProvider.h")
            ROOT.gROOT.ProcessLine(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::MuonScaReCorrProvider::Initialize("{jsonFile}")'
            )
            MuonScaReCorrProducer.initialized = True

    def getP4VariationsForLegs(self, df):
        sf_scales = [central, up, down] if self.return_variations else [central]
        for source in ["ScaRe"]:
            for scale in sf_scales:
                for leg_idx in [1, 2]:
                    mu_pt = f"mu{leg_idx}_{self.pt_for_ScaRe}"
                    print("mu_pt:", mu_pt)
                    df = df.Define(
                        f"mu{leg_idx}_p4_corr",
                        f"""::correction::MuonScaReCorrProvider::getGlobal().getES({mu_pt}, mu{leg_idx}_eta, mu{leg_idx}_phi, mu{leg_idx}_mass, mu{leg_idx}_charge, mu{leg_idx}_nTrackerLayers, isData, event, luminosityBlock, ::correction::MuonScaReCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})""",
                    )
        return df

    # def getP4Variations(self, df, source_dict):
    #     # Data apply scale correction
    #     for source in [central] + ["ScaRe"]:
    #         source_eff = source
    #         updateSourceDict(source_dict, source_eff, "Muon")
    #         p4 = f'{leg_name}_{self.columns["p4"]}'
    #         for scale in getScales(source):
    #             syst_name = getSystName(source_eff, scale)
    #             df = df.Define(
    #                 f"Muon_p4_{syst_name}",
    #                 f"""::correction::MuonScaReCorrProvider::getGlobal().getES(Muon_pt, Muon_eta, Muon_phi, Muon_mass, Muon_charge, Muon_nTrackerLayers, isData, ::correction::MuonScaReCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})""",
    #             )
    #             df = df.Define(
    #                 f"Muon_p4_{syst_name}_delta",
    #                 f"Muon_p4_{syst_name} - Muon_p4_{nano}",
    #             )
    #     return df, source_dict
