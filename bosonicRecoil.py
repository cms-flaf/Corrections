import os
import ROOT
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
            "Corrections/data/hleprare/bosonicRecoil",
            self.json_map[period],
        )

        if not BosonicRecoilCorrection.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "bosonicRecoil.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::BosonicRecoilProvider::Initialize("{json_file}")'
            )
            BosonicRecoilCorrection.initialized = True

    def applyBosonicRecoilCorrections(self, df, process_cfg, to_apply):
        if self.isData:
            return df

        if "bosonicRecoil" not in to_apply:
            return df

        recoil_cfg = process_cfg.get("corrections", {}).get("bosonicRecoil", {})
        if not recoil_cfg.get("enabled", False):
            return df

        recoil_order = recoil_cfg.get("order", "None")
        if recoil_order not in ["LO", "NLO", "NNLO"]:
            raise RuntimeError(
                f"Process order {recoil_order} not recognized for Bosonic Recoil Corrections. Supported values are 'LO', 'NLO', 'NNLO'."
            )

        print(f"Applying bosonic recoil corrections with order {recoil_order}.")
        recoil_method = to_apply["bosonicRecoil"].get("method", "QuantileMapHist")
        apply_systematics = to_apply["bosonicRecoil"].get("apply_systematics", True)

        column_names = [str(c) for c in df.GetColumnNames()]
        has_gen_recoil_inputs = all(
            c in column_names
            for c in [
                "recoil_GenBoson_pt",
                "recoil_GenBoson_phi",
                "recoil_GenBoson_vis_pt",
                "recoil_GenBoson_vis_phi",
            ]
        )

        df = df.Define("recoil_ptll", "static_cast<double>(LHE_Vpt)")
        df = df.Define(
            "recoil_njet",
            "::correction::BosonicRecoilProvider::GetRecoilNJetFromReco("
            "static_cast<float>(b1_pt), "
            "static_cast<float>(b1_eta), "
            "static_cast<float>(b2_pt), "
            "static_cast<float>(b2_eta), "
            "VBFJet_pt, "
            "VBFJet_eta)",
        )

        if has_gen_recoil_inputs:  # this is following hleprare recommendation
            df = df.Define("recoil_boson_pt", "static_cast<double>(recoil_GenBoson_pt)")
            df = df.Define(
                "recoil_boson_phi", "static_cast<double>(recoil_GenBoson_phi)"
            )
            df = df.Define(
                "recoil_boson_vis_pt", "static_cast<double>(recoil_GenBoson_vis_pt)"
            )
            df = df.Define(
                "recoil_boson_vis_phi", "static_cast<double>(recoil_GenBoson_vis_phi)"
            )
            df = df.Define(
                "recoil_nom_result",
                f"::correction::BosonicRecoilProvider::getGlobal().correctMET("
                f'"{recoil_order}", '
                f"static_cast<double>(recoil_njet), "
                f"static_cast<double>(recoil_ptll), "
                f"static_cast<double>(recoil_boson_pt), "
                f"static_cast<double>(recoil_boson_phi), "
                f"static_cast<double>(recoil_boson_vis_pt), "
                f"static_cast<double>(recoil_boson_vis_phi), "
                f"static_cast<double>(PuppiMET_pt), "
                f"static_cast<double>(PuppiMET_phi), "
                f'"{recoil_method}")',
            )
        else:  # workaround for when Gen-level recoil inputs are not available
            df = df.Define(
                "recoil_lhe_boson_p4",
                "::correction::BosonicRecoilProvider::GetLHEBosonP4("
                "LHEPart_pt, LHEPart_eta, LHEPart_phi, LHEPart_mass, "
                "LHEPart_pdgId, LHEPart_status)",
            )
            df = df.Define(
                "recoil_lep_vis_boson_p4",
                "::correction::BosonicRecoilProvider::GetVisibleBosonP4FromLepGenVis("
                "static_cast<float>(tau1_gen_vis_pt), "
                "static_cast<float>(tau1_gen_vis_eta), "
                "static_cast<float>(tau1_gen_vis_phi), "
                "static_cast<float>(tau1_gen_vis_mass), "
                "static_cast<float>(tau2_gen_vis_pt), "
                "static_cast<float>(tau2_gen_vis_eta), "
                "static_cast<float>(tau2_gen_vis_phi), "
                "static_cast<float>(tau2_gen_vis_mass))",
            )
            df = df.Define(
                "recoil_boson_pt", "static_cast<double>(recoil_lhe_boson_p4.pt())"
            )
            df = df.Define(
                "recoil_boson_phi", "static_cast<double>(recoil_lhe_boson_p4.phi())"
            )
            df = df.Define(
                "recoil_boson_vis_pt",
                "static_cast<double>(recoil_lep_vis_boson_p4.pt())",
            )
            df = df.Define(
                "recoil_boson_vis_phi",
                "static_cast<double>(recoil_lep_vis_boson_p4.phi())",
            )

            df = df.Define(
                "recoil_valid_lep_vis",
                "::correction::BosonicRecoilProvider::HasValidLepVisGenMatch("
                "static_cast<int>(tau1_gen_kind), "
                "static_cast<int>(tau2_gen_kind))",
            )

            df = df.Define(
                "recoil_nom_result",
                f"""
                if (!recoil_valid_lep_vis) {{
                    return ::correction::BosonicRecoilProvider::GetIdentityRecoilResult(
                        static_cast<double>(recoil_boson_pt),
                        static_cast<double>(recoil_boson_phi),
                        static_cast<double>(recoil_boson_vis_pt),
                        static_cast<double>(recoil_boson_vis_phi),
                        static_cast<double>(PuppiMET_pt),
                        static_cast<double>(PuppiMET_phi)
                    );
                }}
                return ::correction::BosonicRecoilProvider::getGlobal().correctMET(
                    "{recoil_order}",
                    static_cast<double>(recoil_njet),
                    static_cast<double>(recoil_ptll),
                    static_cast<double>(recoil_boson_pt),
                    static_cast<double>(recoil_boson_phi),
                    static_cast<double>(recoil_boson_vis_pt),
                    static_cast<double>(recoil_boson_vis_phi),
                    static_cast<double>(PuppiMET_pt),
                    static_cast<double>(PuppiMET_phi),
                    "{recoil_method}"
                );
                """,
            )
            print(
                "Warning: Gen-level recoil inputs not available. Using workaround with LHE boson and gen visible tau pair. This is a temporary solution for bosonic recoil. Make sure that necessary GenPart related inputs are saved in AnaTuple stage"
            )

        df = df.Define(
            "PuppiMET_pt_recoil", "static_cast<float>(recoil_nom_result.met_pt_corr)"
        )

        df = df.Define(
            "PuppiMET_phi_recoil", "static_cast<float>(recoil_nom_result.met_phi_corr)"
        )

        df = df.Define("recoil_upara", "static_cast<float>(recoil_nom_result.upara)")

        df = df.Define("recoil_uperp", "static_cast<float>(recoil_nom_result.uperp)")

        df = df.Define(
            "recoil_upara_corr", "static_cast<float>(recoil_nom_result.upara_corr)"
        )

        df = df.Define(
            "recoil_uperp_corr", "static_cast<float>(recoil_nom_result.uperp_corr)"
        )

        if apply_systematics:
            for syst in ["RespUp", "RespDown", "ResolUp", "ResolDown"]:
                result_name = f"recoil_{syst}"
                if has_gen_recoil_inputs:
                    df = df.Define(
                        result_name,
                        f"::correction::BosonicRecoilProvider::getGlobal().applyUncertainty("
                        f'"{recoil_order}", '
                        f"static_cast<double>(recoil_njet), "
                        f"static_cast<double>(recoil_ptll), "
                        f"static_cast<double>(recoil_boson_pt), "
                        f"static_cast<double>(recoil_boson_phi), "
                        f"static_cast<double>(recoil_boson_vis_pt), "
                        f"static_cast<double>(recoil_boson_vis_phi), "
                        f"static_cast<double>(PuppiMET_pt_recoil), "
                        f"static_cast<double>(PuppiMET_phi_recoil), "
                        f'"{syst}")',
                    )
                else:
                    df = df.Define(
                        result_name,
                        f"""
                        if (!recoil_valid_lep_vis) {{
                            return ::correction::BosonicRecoilProvider::GetIdentityRecoilSystematics(
                                static_cast<double>(recoil_boson_pt),
                                static_cast<double>(recoil_boson_phi),
                                static_cast<double>(recoil_boson_vis_pt),
                                static_cast<double>(recoil_boson_vis_phi),
                                static_cast<double>(PuppiMET_pt_recoil),
                                static_cast<double>(PuppiMET_phi_recoil)
                            );
                        }}
                        return ::correction::BosonicRecoilProvider::getGlobal().applyUncertainty(
                            "{recoil_order}",
                            static_cast<double>(recoil_njet),
                            static_cast<double>(recoil_ptll),
                            static_cast<double>(recoil_boson_pt),
                            static_cast<double>(recoil_boson_phi),
                            static_cast<double>(recoil_boson_vis_pt),
                            static_cast<double>(recoil_boson_vis_phi),
                            static_cast<double>(PuppiMET_pt_recoil),
                            static_cast<double>(PuppiMET_phi_recoil),
                            "{syst}"
                        );
                        """,
                    )

                df = df.Define(
                    f"PuppiMET_pt_recoil_{syst}",
                    f"static_cast<float>({result_name}.met_pt)",
                )

                df = df.Define(
                    f"PuppiMET_phi_recoil_{syst}",
                    f"static_cast<float>({result_name}.met_phi)",
                )

        return df

    @property
    def method(self):
        return self.config.get("method", "QuantileMapHist")

    @property
    def apply_systematics(self):
        return self.config.get("apply_systematics", True)
