import os
import ROOT
from .CorrectionsCore import *


class FatJetCorrProducer:
    initialized = False

    period = None

    base_file_path = "/afs/cern.ch/user/a/aguzel/public/AK8SF/jsons"
    fatjet_corr_dict = {
        "particleNetWithMass_HbbvsQCD": {
            "file_name": {
                "2022_Summer22": f"{base_file_path}/ak8_sf_corrections_bbww_combined_2022_preEE.json",
                "2022_Summer22EE": f"{base_file_path}/ak8_sf_corrections_bbww_combined_2022_postEE.json",
                "2023_Summer23": f"{base_file_path}/ak8_sf_msdtest_Pt-combined_2023_preBPix.json",
                "2023_Summer23BPix": f"{base_file_path}/ak8_sf_msdtest_Pt-combined_2023_postBPix.json",
            },
            "keys_bb": {
                "2022_Summer22": "HHbbww_2022_preEE_SF_bb",
                "2022_Summer22EE": "HHbbww_2022_postEE_SF_bb",
                "2023_Summer23": "HHbbww_2023_preBPix_SF_bb",
                "2023_Summer23BPix": "HHbbww_2023_postBPix_SF_bb",
            },
            "keys_cc": {
                "2022_Summer22": "HHbbww_2022_preEE_SF_cc",
                "2022_Summer22EE": "HHbbww_2022_postEE_SF_cc",
                "2023_Summer23": "HHbbww_2023_preBPix_SF_cc",
                "2023_Summer23BPix": "HHbbww_2023_postBPix_SF_cc",
            },
        }
    }

    fatjet_Sources = ["Hbb", "Hcc", "tau21"]

    def __init__(self, period, ana, tagger, fatjetName, isData=False):
        # ana input for future, if other analyses will use separate corrections
        self.isData = isData
        self.fatjetName = fatjetName

        this_dict = self.fatjet_corr_dict[tagger]
        file_nameID = this_dict["file_name"][period]
        bb_key = this_dict["keys_bb"][period]
        cc_key = this_dict["keys_cc"][period]

        if not FatJetCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "fatjet.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::FatJetCorrProvider::Initialize("{file_nameID}","{bb_key}","{cc_key}")'
            )
            FatJetCorrProducer.initialized = True

        self.period = period
        self.columns = {}

    def getSF(self, df, isCentral, return_variations):
        sf_sources = FatJetCorrProducer.fatjet_Sources
        SF_branches = []
        sf_scales = [up, down] if return_variations else []
        for source in sf_sources:
            for scale in [central] + sf_scales:
                if not isCentral and scale != central:
                    continue
                branch_name = f"weight_{self.fatjetName}_FatJetSF_{source+scale}"
                branch_central = (
                    f"""weight_{self.fatjetName}_FatJetSF_{source+central}"""
                )

                df = df.Define(
                    f"{branch_name}_double",
                    f"""{self.fatjetName}_isValid ? ::correction::FatJetCorrProvider::getGlobal().get_SF(
                            {self.fatjetName}_pt, {self.fatjetName}_hadronFlavour,
                            ::correction::FatJetCorrProvider::UncSource::{source},
                            ::correction::UncScale::{scale})
                        : 1.""",
                )

                if scale != central:
                    branch_name_final = branch_name + "_rel"
                    df = df.Define(
                        branch_name_final,
                        f"static_cast<float>({branch_name}_double/{branch_central})",
                    )
                else:
                    if source == central:
                        branch_name_final = (
                            f"""weight_{self.fatjetName}_FatJetSF_{central}"""
                        )
                    else:
                        branch_name_final = branch_name
                    df = df.Define(
                        branch_name_final,
                        f"static_cast<float>({branch_name}_double)",
                    )

                SF_branches.append(branch_name_final)
        return df, SF_branches
