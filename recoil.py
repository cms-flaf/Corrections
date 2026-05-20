import os
import math
import correctionlib
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
        if not BosonicRecoilCorrection.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "recoil.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            BosonicRecoilCorrection.initialized = True

        self.cset = correctionlib.CorrectionSet.from_file(os.path.join(config["corrections_path"], self.json_map[period]))
        self.rescaling = self.cset["Recoil_correction_Rescaling"]
        self.qmphist = self.cset["Recoil_correction_QuantileMapHist"]
        self.qmpfit = self.cset["Recoil_correction_QuantileMapFit"]
        self.unc = self.cset["Recoil_correction_Uncertainty"]
    
    @staticmethod
    def _xy_from_pt_phi(pt, phi):
        return pt * math.cos(phi), pt * math.sin(phi)
    
    @staticmethod
    def _pt_phi_from_xy(px, py):
        return math.sqrt(px**2, py**2), math.atan2(py, px)
    
    @staticmethod
    def _project_along_reference(x, y, ref_x, ref_y):
        ref_pt = math.sqrt(ref_x**2 + ref_y**2)
        if ref_pt < 1e-12: return 0.0, 0.0 # avoid division by zero

        ux, uy = ref_x / ref_pt, ref_y / ref_pt
        vx, vy = -uy, ux
        parallel = x * ux + y * uy
        perpendicular = x * vx + y * vy
        return parallel, perpendicular
    
    @staticmethod
    def _reconstruct_from_para_perp(para, perp, ref_x, ref_y):
        ref_pt = math.sqrt(ref_x**2 + ref_y**2)
        if ref_pt < 1e-12: return 0.0, 0.0 # avoid division by zero

        ux, uy = ref_x / ref_pt, ref_y / ref_pt
        vx, vy = -uy, ux
        x = para * ux + perp * vx
        y = para * uy + perp * vy
        return x, y
    
    @classmethod
    def compute_u(cls, gen_pt, gen_phi, vis_pt, vis_phi, met_pt, met_phi):
        vx, vy = cls._xy_from_pt_phi(gen_pt, gen_phi)
        v_vis_x, v_vis_y = cls._xy_from_pt_phi(vis_pt, vis_phi)
        metx, mety = cls._xy_from_pt_phi(met_pt, met_phi)

        # U = MET + V_vis - V
        ux = metx + v_vis_x - vx
        uy = mety + v_vis_y - vy
        return cls._project_along_reference(ux, uy, vx, vy)
    
    