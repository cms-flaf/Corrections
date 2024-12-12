import os
import ROOT
from .CorrectionsCore import *
from Common.Utilities import *
import yaml
# Tau JSON POG integration for tau legs in eTau, muTau, diTau:
# # https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/TAU?ref_type=heads

# singleEle + e/mu legs for xTriggers eTau, muTau:
# https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTScaleFactorMeasurements

# singleMu : files taken from https://gitlab.cern.ch/cms-muonPOG/muonefficiencies/-/tree/master/Run2/UL and saved locally

# singleTau: https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauTrigger#Run_II_Trigger_Scale_Factors
# singleTau: Legacy bc there are no UL as mentioned herehttps://cms-pub-talk.web.cern.ch/t/tau-pog-review/8404/4
# singleTau: 2016 - (HLT_VLooseIsoPFTau120_Trk50_eta2p1_v OR HLT_VLooseIsoPFTau140_Trk50_eta2p1_v) - 0.88 +/- 0.08
# singleTau: 2017 - HLT_MediumChargedIsoPFTau180HighPtRelaxedIso_Trk50_eta2p1_v - 1.08 +/- 0.10
# singleTau: 2018 - (HLT_MediumChargedIsoPFTau180HighPtRelaxedIso_Trk50_eta2p1_v) - 	0.87 +/- 0.11



class TrigCorrProducer:
    MuTRG_jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_Z.json.gz"
    initialized = False
    SFSources = { 'singleIsoMu':['IsoMu24'] }

    muon_trg_dict = {
        "2022_Summer22": ROOT.std.vector('std::string')({"NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"}),
    }


    def __init__(self, period, config):
        jsonFile_Mu = os.path.join(os.environ['ANALYSIS_PATH'],TrigCorrProducer.MuTRG_jsonPath.format(period))

        self.period = period
        self.year = period.split('_')[0]


        if not TrigCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "triggersRun3.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            #print(wp_map_cpp)
            # "{self.muon_trg_dict[period]}",
            year = period.split('_')[0]
            ROOT.gInterpreter.ProcessLine(f"""::correction::TrigCorrProvider::Initialize("{jsonFile_Mu}", "{period}")""")
            TrigCorrProducer.initialized = True

    def getSF(self, df, trigger_names, lepton_legs, return_variations, isCentral):
        SF_branches = []
        trg_name = 'singleIsoMu'
        if trg_name in trigger_names:
            sf_sources = TrigCorrProducer.SFSources[trg_name] if return_variations else []
            for leg_idx, leg_name in enumerate(lepton_legs):
                applyTrgBranch_name = f"{trg_name}_{leg_name}_ApplyTrgSF"
                df = df.Define(applyTrgBranch_name, f"""{leg_name}_type == static_cast<int>(Leg::mu) && {leg_name}_index >= 0 && HLT_{trg_name} && {leg_name}_HasMatching_{trg_name}""")
                for source in [ central ] + sf_sources:
                    for scale in getScales(source):
                        if source == central and scale != central: continue
                        if not isCentral and scale!= central: continue
                        syst_name = getSystName(source, scale)
                        suffix = syst_name
                        if scale == central:
                            suffix = f"{trg_name}_{syst_name}"
                        branch_name = f"weight_{leg_name}_TrgSF_{suffix}"
                        branch_central = f"weight_{leg_name}_TrgSF_{trg_name}_{getSystName(central,central)}"
                        df = df.Define(f"{branch_name}_double",
                                    f'''{applyTrgBranch_name} ? ::correction::TrigCorrProvider::getGlobal().getSF(
                                 {leg_name}_p4,::correction::TrigCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} ) : 1.f''')
                        if scale != central:
                            df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                            branch_name += '_rel'
                        else:
                            df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                        SF_branches.append(f"{branch_name}")
        return df,SF_branches