import os
import urllib.request
import ROOT
from .CorrectionsCore import *
from FLAF.Common.Utilities import DeclareHeader


class MuonScaReCorrProducer:
    initialized = False
    # jsonPath = "Corrections/data/MUO/MuonScaRe/{}.json.gz"
    jsonPath = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/{}/latest/muon_scalesmearing.json.gz"
    initialized = False
    uncSources = ["ScaRe"]

    period = None

    def __init__(self, period, isData, pt_for_ScaRe, return_variations=False):
        self.period = period
        self.pt_for_ScaRe = pt_for_ScaRe
        jsonFile_path = MuonScaReCorrProducer.jsonPath.format(
            pog_folder_names["MUO"][period]
        )
        self.isData = isData
        self.return_variations = return_variations
        jsonFile = os.path.join(os.environ["ANALYSIS_PATH"], jsonFile_path)
        if not MuonScaReCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            DeclareHeader(os.environ["ANALYSIS_PATH"] + "/FLAF/include/Utilities.h")
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
                    syst_name = f"ScaRe{scale}" if scale != central else f"ScaRe"
                    df = df.Define(
                        f"mu{leg_idx}_p4_{syst_name}",
                        f"""::correction::MuonScaReCorrProvider::getGlobal().getES({mu_pt}, mu{leg_idx}_eta, mu{leg_idx}_phi, mu{leg_idx}_mass, mu{leg_idx}_charge, mu{leg_idx}_nTrackerLayers, isData, event, luminosityBlock, ::correction::MuonScaReCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})""",
                    )
        return df

    def getP4Variations(self, df, source_dict):
        # print(f"return variations? {self.return_variations}")
        sf_scales = [central, up, down]
        for source in ["ScaRe"]:
            updateSourceDict(source_dict, source, "Muon")
            p4 = f"Muon_p4_{self.pt_for_ScaRe}"
            for scale in sf_scales:
                syst_name = f"ScaRe{scale}" if scale != central else f"ScaRe"
                # print(
                #     f"computing ScaRe on {p4} and defining the scare varied p4 as Muon_p4_{syst_name}"
                # )
                df = df.Define(
                    f"Muon_p4_{syst_name}",
                    f"""::correction::MuonScaReCorrProvider::getGlobal().getES(v_ops::pt({p4}), v_ops::eta({p4}), v_ops::phi({p4}), v_ops::mass({p4}), Muon_charge, Muon_nTrackerLayers, isData, event, luminosityBlock, ::correction::MuonScaReCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})""",
                )
        return df, source_dict
