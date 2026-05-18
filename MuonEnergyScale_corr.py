import os
import urllib.request
import ROOT
from .CorrectionsCore import *
from FLAF.Common.Utilities import DeclareHeader


class MuonEnergyScaleProducer:
    initialized = False
    # jsonPath = "Corrections/data/MUO/MuonScaRe/{}.json.gz"
    # jsonPath = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/{}/latest/muon_scalesmearing.json.gz"
    jsonPath = "Corrections/data/MUO/MuonScaRe/{}/muon_scalesmearing.json.gz"  # tmp patch because currently VXBS ScaRe are copied from /afs/cern.ch/user/f/ferrico/cmsonly/MUON_JSON_VXBS/
    initialized = False
    uncSources = ["ScaRe"]

    period = None

    def __init__(
        self,
        period,
        isData,
        pt_for_ScaRe,
        return_variations=True,
        apply_scare=True,
        apply_fsr_recovery=True,
    ):
        self.period = period
        self.pt_for_ScaRe = pt_for_ScaRe
        self.apply_scare = apply_scare
        self.apply_fsr_recovery = apply_fsr_recovery
        jsonFile_path = MuonEnergyScaleProducer.jsonPath.format(
            pog_folder_names["MUO"][period]
        )
        self.isData = isData
        self.return_variations = return_variations
        jsonFile = os.path.join(os.environ["ANALYSIS_PATH"], jsonFile_path)
        if not MuonEnergyScaleProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            DeclareHeader(os.environ["ANALYSIS_PATH"] + "/FLAF/include/Utilities.h")
            header_path = os.path.join(headers_dir, "MuonScaReProvider.h")
            ROOT.gROOT.ProcessLine(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(
                f'::correction::MuonScaReCorrProvider::Initialize("{jsonFile}")'
            )
            header_path = os.path.join(headers_dir, "MuonFsrRecoveryProvider.h")
            ROOT.gROOT.ProcessLine(f'#include "{header_path}"')
            MuonEnergyScaleProducer.initialized = True

    def getP4Variations(self, df, source_dict):
        sources = [central]
        if not self.isData:
            sources += MuonEnergyScaleProducer.uncSources
        for source in sources:
            updateSourceDict(source_dict, source, "Muon")
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                for suffix in ["nano", "bsConstrainedPt"]:
                    p4 = f"Muon_p4_{suffix}"
                    scare_branch = f"Muon_p4_{syst_name}_{suffix}"
                    scare_FSR_branch = f"Muon_p4_FSR_{syst_name}_{suffix}"
                    if suffix == self.pt_for_ScaRe:
                        scare_branch = f"Muon_p4_{syst_name}"
                        scare_FSR_branch = f"Muon_p4_FSR_{syst_name}"
                    print(
                        f"computing ScaRe on {p4} and defining the scare varied p4 as Muon_p4_{syst_name}"
                    )
                    if self.apply_scare:
                        df = df.Define(
                            scare_branch,
                            f"""::correction::MuonScaReCorrProvider::getGlobal().getES(v_ops::pt({p4}), v_ops::eta({p4}), v_ops::phi({p4}), v_ops::mass({p4}), Muon_charge, Muon_nTrackerLayers, isData, event, luminosityBlock, ::correction::MuonScaReCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})""",
                        )
                        p4 = scare_branch
                    if self.apply_fsr_recovery:
                        df = df.Define(
                            scare_FSR_branch,
                            f"""::correction::MuonFsrRecoveryProvider::fsr_corrected_p4(v_ops::pt({p4}), v_ops::eta({p4}), v_ops::phi({p4}), v_ops::mass({p4}), Muon_fsrPhotonIdx, FsrPhoton_pt, FsrPhoton_eta, FsrPhoton_phi, FsrPhoton_dROverEt2, FsrPhoton_relIso03, FsrPhoton_electronIdx)""",
                        )
                        df = df.Define(
                            f"{scare_FSR_branch}_delta",
                            f"{scare_FSR_branch} - Muon_p4_{nano}",
                        )
                    df = df.Define(
                        f"{scare_branch}_delta",
                        f"{scare_branch} - Muon_p4_{nano}",
                    )

        return df, source_dict

    def getP4VariationsForLegs(self, df):
        sources = [central]
        if not self.isData:
            sources += MuonEnergyScaleProducer.uncSources
        for source in sources:
            updateSourceDict(source_dict, source, "Muon")
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                for suffix in ["nano", "bsConstrainedPt"]:
                    for leg_idx in [1, 2]:
                        p4 = f"mu{leg_idx}_p4_{suffix}"
                        scare_branch = f"mu{leg_idx}_p4_{syst_name}_{suffix}"
                        FSR_branch = f"mu{leg_idx}_p4_FSR_{syst_name}_{suffix}"
                        if suffix == self.pt_for_ScaRe:
                            scare_branch = f"mu{leg_idx}_p4_{syst_name}"
                            FSR_branch = f"mu{leg_idx}_p4_FSR_{syst_name}"
                        if self.apply_scare:
                            print(
                                f"computing ScaRe on leg {leg_idx} on {p4} and defining the scare varied p4 as {scare_branch}"
                            )
                            df = df.Define(
                                scare_branch,
                                f"""::correction::MuonScaReCorrProvider::getGlobal().getES({p4}.Pt(), {p4}.Eta(), {p4}.Phi(), {p4}.M(), mu{leg_idx}_charge, mu{leg_idx}_nTrackerLayers, isData, event, luminosityBlock, ::correction::MuonScaReCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})""",
                            )
                            p4 = scare_branch
                        if self.apply_fsr_recovery:
                            print(
                                f"applying FSR recovery on leg {leg_idx} on {p4} and defining the scare varied p4 as {FSR_branch}"
                            )
                            df = df.Define(
                                FSR_branch,
                                f"""::correction::MuonFsrRecoveryProvider::fsr_corrected_p4({p4}.Pt(), {p4}.Eta(), {p4}.Phi(), {p4}.M(), mu{leg_idx}_fsrPhotonIdx, FsrPhoton_pt, FsrPhoton_eta, FsrPhoton_phi, FsrPhoton_dROverEt2, FsrPhoton_relIso03, FsrPhoton_electronIdx)""",
                            )
                            df = df.Define(
                                f"{FSR_branch}_delta",
                                f"{FSR_branch} - mu{leg_idx}_p4_{nano}",
                            )
                        df = df.Define(
                            f"{scare_branch}_delta",
                            f"{scare_branch} - mu{leg_idx}_p4_{nano}",
                        )
        return df, source_dict