import os
import ROOT
from .CorrectionsCore import *


class DYbbwwCorrProducer:
    JsonPath = "Corrections/data/DY_corr_hhbbww/dy_correction_weight.json.gz"
    initialized = False

    era_map = {
        "Run3_2022": "2022_2022EE_2023_2023BPix",
        "Run3_2022EE": "2022_2022EE_2023_2023BPix",
        "Run3_2023": "2022_2022EE_2023_2023BPix",
        "Run3_2023BPix": "2022_2022EE_2023_2023BPix",
        "Run3_2024": "2022_2022EE_2023_2023BPix",  # Different file for 2024, not implemented yet
    }

    default_variations = []

    def __init__(
        self,
        era,
        *,
        njets_branch="nJet",
        pt_ll="pt_lep1_lep2",
        valid="valid",
        variations=None,
    ):
        self.era = era
        self.valid = valid

        if self.era not in self.era_map:
            raise RuntimeError(
                f"DYbbwwCorrProducer: unsupported era '{self.era}'. "
                f"Supported eras: {list(self.era_map.keys())}"
            )

        analysis_path = os.environ.get("ANALYSIS_PATH")
        if analysis_path is None:
            raise RuntimeError(
                "DYbbwwCorrProducer: ANALYSIS_PATH is not set. "
                "Cannot resolve DY correction JSON path."
            )

        if os.path.isabs(self.JsonPath):
            self.json_path = self.JsonPath
        else:
            self.json_path = os.path.join(analysis_path, self.JsonPath)

        if not os.path.exists(self.json_path):
            raise FileNotFoundError(
                f"DYbbwwCorrProducer: DY correction JSON not found: {self.json_path}"
            )

        self.njets_branch = njets_branch
        self.pt_ll = pt_ll
        self.variations = list(
            self.default_variations if variations is None else variations
        )

        if not DYbbwwCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "DY_hhbbww.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::DYbbwwCorrProvider::Initialize("{self.json_path}")'
            )
            DYbbwwCorrProducer.initialized = True

    def _valid_expr(self):
        if isinstance(self.valid, bool):
            return "true" if self.valid else "false"
        return f"static_cast<bool>({self.valid})"

    def getWeight(
        self,
        df,
        return_variations=True,
        return_list_of_branches=False,
        enabled=True,
    ):
        if not enabled:
            if return_list_of_branches:
                return df, []
            return df

        systs = ["nominal"]
        if return_variations:
            systs += self.variations

        branches = []
        valid_expr = self._valid_expr()

        for syst in systs:
            branch_name = (
                "weight_dy_hhbbww_central"
                if syst == "nominal"
                else f"weight_dy_hhbbww_{syst}"
            )
            df = df.Define(
                branch_name,
                f"""static_cast<float>(
                    ::correction::DYbbwwCorrProvider::getGlobal().getWeight(
                        \"{self.era_map[self.era]}\",
                        static_cast<int>({self.njets_branch}),
                        static_cast<float>({self.pt_ll}),
                        \"{syst}\",
                        {valid_expr}
                    )
                )""",
            )

            branches.append(branch_name)

        if return_list_of_branches:
            return df, branches
        return df
