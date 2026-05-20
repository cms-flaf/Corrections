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

        self.cset = correctionlib.CorrectionSet.from_file(
            os.path.join(
                config["analysis_path"],
                "Corrections/data/hleprare/recoil",
                self.json_map[period],
            )
        )
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
        if ref_pt < 1e-12:
            return 0.0, 0.0  # avoid division by zero

        ux, uy = ref_x / ref_pt, ref_y / ref_pt
        vx, vy = -uy, ux
        parallel = x * ux + y * uy
        perpendicular = x * vx + y * vy
        return parallel, perpendicular

    @staticmethod
    def _reconstruct_from_para_perp(para, perp, ref_x, ref_y):
        ref_pt = math.sqrt(ref_x**2 + ref_y**2)
        if ref_pt < 1e-12:
            return 0.0, 0.0  # avoid division by zero

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

    @classmethod
    def compute_h(cls, gen_pt, gen_phi, vis_pt, vis_phi, met_pt, met_phi):
        vx, vy = cls._xy_from_pt_phi(gen_pt, gen_phi)
        v_vis_x, v_vis_y = cls._xy_from_pt_phi(vis_pt, vis_phi)
        metx, mety = cls._xy_from_pt_phi(met_pt, met_phi)

        # H = -V_vis - MET
        hx = -v_vis_x - metx
        hy = -v_vis_y - mety
        return cls._project_along_reference(hx, hy, vx, vy)

    @classmethod
    def met_from_u(cls, gen_pt, gen_phi, vis_pt, vis_phi, upara, uperp):
        vx, vy = cls._xy_from_pt_phi(gen_pt, gen_phi)
        v_vis_x, v_vis_y = cls._xy_from_pt_phi(vis_pt, vis_phi)
        ucx, ucy = cls._build_from_para_perp(upara, uperp, vx, vy)

        # U = MET + V_vis - V --> MET = U - V_vis + V
        metx = ucx - v_vis_x + vx
        mety = ucy - v_vis_y + vy
        return cls._pt_phi_from_xy(metx, mety)

    @classmethod
    def met_from_h(cls, gen_pt, gen_phi, vis_pt, vis_phi, hpara, hperp):
        vx, vy = cls._xy_from_pt_phi(vis_pt, vis_phi)
        v_vis_x, v_vis_y = cls._xy_from_pt_phi(vis_pt, vis_phi)
        hcx, hcy = cls._build_from_para_perp(hpara, hperp, vx, vy)

        # H = -V_vis - MET --> MET = -H - V_vis
        metx = -hcx - v_vis_x
        mety = -hcy - v_vis_y
        return cls._pt_phi_from_xy(metx, mety)

    def apply_correction(self, order, njet, ptll, var, val, method="QuantileMapHist"):
        if method == "Rescaling":
            return self.rescaling.evaluate(order, float(njet), ptll, var, val)

        if method == "QuantileMapHist":
            return self.qmphist.evaluate(order, float(njet), ptll, var, val)

        if method == "QuantileMapFit":
            if abs(val) > 150.0:
                return self.rescaling.evaluate(order, float(njet), ptll, var, val)
            raise NotImplementedError(
                "QuantileMapFit method requires root input for Data CDF; use QuantileMapHist or Rescaling methods; or implement the root files from HLEpRare to use this method"
            )

        raise ValueError(f"Unknown method {method} for recoil corrections")

    def corrected_met(
        self,
        order,
        njet,
        gen_pt,
        gen_phi,
        vis_pt,
        vis_phi,
        met_pt,
        met_phi,
        method="QuantileMapHist",
    ):
        ptll = gen_pt  # for bosonic recoil corrections, the relevant variable is the gen-level boson pt

        upara, uperp = self.compute_u(gen_pt, gen_phi, vis_pt, vis_phi, met_pt, met_phi)
        upara_corr = self.apply_correction(order, njet, ptll, "Upara", upara, method)
        uperp_corr = self.apply_correction(order, njet, ptll, "Uperp", uperp, method)

        met_pt_corr, met_phi_corr = self.met_from_u(
            gen_pt, gen_phi, vis_pt, vis_phi, upara_corr, uperp_corr
        )

        return {
            "upara": upara,
            "uperp": uperp,
            "upara_corr": upara_corr,
            "uperp_corr": uperp_corr,
            "met_pt_corr": met_pt_corr,
            "met_phi_corr": met_phi_corr,
        }

    def apply_uncertainty(
        self,
        order,
        njet,
        gen_pt,
        gen_phi,
        vis_pt,
        vis_phi,
        met_pt_nominal,
        met_phi_nominal,
        syst,
    ):
        if syst not in ("RespUp", "RespDown", "ResoUp", "ResoDown"):
            raise ValueError(
                f"Unknown systematic variation {syst} for recoil uncertainty"
            )

        ptll = gen_pt
        hpara, hperp = self.compute_h(
            gen_pt, gen_phi, vis_pt, vis_phi, met_pt_nominal, met_phi_nominal
        )

        hpara_variation = self.unc.evaluate(order, float(njet), ptll, "Hpara", syst)
        hperp_variation = self.unc.evaluate(order, float(njet), ptll, "Hperp", syst)

        met_pt_variation, met_phi_variation = self.met_from_h(
            gen_pt, gen_phi, vis_pt, vis_phi, hpara_variation, hperp_variation
        )

        return {
            "hpara": hpara,
            "hperp": hperp,
            "hpara_variation": hpara_variation,
            "hperp_variation": hperp_variation,
            "met_pt_variation": met_pt_variation,
            "met_phi_variation": met_phi_variation,
        }
