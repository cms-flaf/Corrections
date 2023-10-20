import os
import ROOT
from .CorrectionsCore import *
from Common.Utilities import *
import yaml


class TrigCorrProducer:
    TauTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
    MuTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_Z.json.gz"
    eTRG_jsonPath = "Corrections/data/EGM/{}/trig.root"
    initialized = False
    deepTauVersion = 'DeepTau2017v2p1'
    SFSources = { 'ditau': [ "ditau_DM0","ditau_DM1", "ditau_3Prong"], 'singleMu':['singleMu'], 'singleEle':['singleEle']}

    muon_trg_dict = {
        "2018_UL": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight",
        "2017_UL": "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight",
        "2016preVFP_UL":"NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight",
        "2016postVFP_UL":"NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"
    }

    def __init__(self, period, config):
        jsonFile_Tau = TrigCorrProducer.TauTRG_jsonPath.format(period)
        jsonFile_Mu = TrigCorrProducer.MuTRG_jsonPath.format(period)
        self.deepTauVersion = f"""DeepTau{deepTauVersions[config["deepTauVersion"]]}v{config["deepTauVersion"]}"""
        jsonFile_e = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.eTRG_jsonPath.format(period))
        if self.deepTauVersion=='DeepTau2018v2p5':
            jsonFile_Tau = f"Corrections/data/TAU/{period}/tau_DeepTau2018v2p5_UL2018.json"
        if not TrigCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "triggers.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            wp_map_cpp = createWPChannelMap(config["deepTauWPs"])
            ROOT.gInterpreter.ProcessLine(f"""::correction::TrigCorrProvider::Initialize("{jsonFile_Tau}", "{self.deepTauVersion}", {wp_map_cpp}, "{jsonFile_Mu}", "{period}",
                                          "{self.muon_trg_dict[period]}","{jsonFile_e}")""")
            TrigCorrProducer.initialized = True

    def getTrgSF(self, df, trigger_names, nLegs, return_variations, isCentral):
        SF_branches = []
        trg_name = 'ditau'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx in range(nLegs):
                applyTrgBranch_name = f"{trg_name}_tau{leg_idx+1}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::tau && HLT_{trg_name} && tau{leg_idx+1}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_tau{leg_idx+1}_TrgSF_{suffix}"
                        branch_central = f"weight_tau{leg_idx+1}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getTauSF_fromCorrLib(
                                 HttCandidate.leg_p4[{leg_idx}], Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]), "{trg_name}", HttCandidate.channel(),
                                ::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'singleMu'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx in [0,1]:
                applyTrgBranch_name = f"{trg_name}_tau{leg_idx+1}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::mu && HLT_{trg_name} && tau{leg_idx+1}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_tau{leg_idx+1}_TrgSF_{suffix}"
                        branch_central = f"weight_tau{leg_idx+1}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getMuSF_fromCorrLib(
                                 HttCandidate.leg_p4[{leg_idx}],::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")

        trg_name = 'singleEle'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx in [0,1]:
                applyTrgBranch_name = f"{trg_name}_tau{leg_idx+1}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""HttCandidate.leg_type[{leg_idx}] == Leg::e && HLT_{trg_name} && tau{leg_idx+1}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_tau{leg_idx+1}_TrgSF_{suffix}"
                        branch_central = f"weight_tau{leg_idx+1}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getEleSF_fromRootFile(
                                 HttCandidate.leg_p4[{leg_idx}],::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")
        return df,SF_branches