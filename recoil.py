import os
from .CorrectionsCore import *

# Bosonic recoil corrections following recommendations from https://cms-higgs-leprare.docs.cern.ch/htt-common/V_recoil/


class BosonicRecoilCorrection:
    initialized = False

    json_map = {
        "Run3_2022": "Recoil_corrections_2022preEE_v5.json.gz",
        "Run3_2022EE": "Recoil_corrections_2022postEE_v5.json.gz",
        "Run3_2023": "Recoil_corrections_2023preBPix_v5.json.gz",
        "Run3_2023BPix": "Recoil_corrections_2023postBPix_v5.json.gz",
        "Run3_2024": "Recoil_corrections_2024_v5.json.gz",
    }

    def __init__(self, period, config, isData, dataset_name, process_name, process_cfg):
        self.period = period
        self.config = config
        self.isData = isData
        self.dataset_name = dataset_name
        self.process_name = process_name
        self.process_cfg = process_cfg

        json_file = os.path.join(
            os.environ["ANALYSIS_PATH"],
            "Corrections/data/hleprare/recoil",
            self.json_map[period],
        )

        if not BosonicRecoilCorrection.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "recoil.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::BosonicRecoilCorrectionProvider::Initialize("{json_file}")'
            )
            BosonicRecoilCorrection.initialized = True

    @property
    def method(self):
        return self.config.get("method", "QuantileMapHist")

    @property
    def apply_systematics(self):
        return self.config.get("apply_systematics", True)
