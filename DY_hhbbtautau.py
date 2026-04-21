import os
import ROOT
from .CorrectionsCore import *
from FLAF.Common.Utilities import *


class DYbbtautauCorrProducer:
    JsonPath = "/afs/cern.ch/work/m/mrieger/public/hbt/external_files/custom_dy_files/hbt_corrections.json.gz"
    initialized = False

    era_map = {
        "Run3_2022": "2022preEE",
        "Run3_2022EE": "2022postEE",
        "Run3_2023": "2023preBPix",
        "Run3_2023BPix": "2023postBPix",
    }

    def __init__(self, era):
        if not DYbbtautauCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "DYbbtautau.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::DYbbtautauCorrProvider::Initialize("{self.JsonPath}")'
            )
            DYbbtautauCorrProducer.initialized = True

    def getWeight(
        self,
        df,
        return_variations=True,
        return_list_of_branches=False,
        enabled=True,
    ):
        branches = []

        systs = ["nominal"]
        if return_variations:
            systs += ["stat_up", "stat_down"]#, "syst_up", "syst_down"] # stat_btag0_down, stat_btag0_up, stat_btag1_down, stat_btag1_up, stat_btag2_down, stat_btag2_up, syst_gauss_down, syst_gauss_up, syst_linear_down, syst_linear_up]
            
        for syst in systs:
            if syst == "nominal":
                branch_name = f"weight_dy_central"
            else:
                branch_name = f"weight_dy_{syst}"
            if enabled:
                df = df.Define(f"pt_ll", "(tau1_gen_vis_pt+tau2_gen_vis_pt)")
                df = df.Define(
                    branch_name,
                    f'''::correction::DYbbtautauCorrProvider::getGlobal().getWeight(
                            "{self.era_map[self.era]}",
                            nJet,
                            nBJets,
                            ptll,
                            "{syst}"
                        )'''
                )
            branches.append(branch_name)

        if return_list_of_branches:
            return df, branches
        return df