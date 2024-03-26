import os
import ROOT
from .CorrectionsCore import *
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendationForRun2
# https://indico.cern.ch/event/1062355/contributions/4466122/attachments/2287465/3888179/Update2016ULsf.pdf
# https://github.com/cms-tau-pog/TauTriggerSFs/tree/master/data
# https://github.com/cms-tau-pog/TauTriggerSFs/tree/run2_SFs

deepTauVersions = {"2p1":"2017", "2p5":"2018"}

class TauCorrProducer:
    jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
    initialized = False
    deepTauVersion = 'DeepTau2017v2p1'

    energyScaleSources_tau = ["TauES_DM0", "TauES_DM1", "TauES_3prong"]
    energyScaleSources_lep = ["EleFakingTauES_DM0", "EleFakingTauES_DM1", "MuFakingTauES"]
    SFSources_tau = ["stat1_dm0", "stat2_dm0", "stat1_dm1", "stat2_dm1", "stat1_dm10", "stat2_dm10", "stat1_dm11", "stat2_dm11", "syst_alleras", "syst_year", "syst_year_dm0", "syst_year_dm1", "syst_year_dm10", "syst_year_dm11", "total","stat_highpT_bin1", "stat_highpT_bin2", "syst_highpT", "syst_highpT_extrap", "syst_highpT_bin1", "syst_highpT_bin2"]
    SFSources_genuineLep=["genuineElectron_barrel", "genuineElectron_endcaps", "genuineMuon_etaLt0p4",
        "genuineMuon_eta0p4to0p8", "genuineMuon_eta0p8to1p2", "genuineMuon_eta1p2to1p7", "genuineMuon_etaGt1p7" ]


    def __init__(self, period, config):
        jsonFile = TauCorrProducer.jsonPath.format(period)
        self.deepTauVersion = f"""DeepTau{deepTauVersions[config["deepTauVersion"]]}v{config["deepTauVersion"]}"""
        if self.deepTauVersion=='DeepTau2018v2p5':
            jsonFile_rel = f"Corrections/data/TAU/{period}/tau_DeepTau2018v2p5_{period}.json"
            jsonFile = os.path.join(os.environ['ANALYSIS_PATH'],jsonFile_rel)
        if not TauCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "tau.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            wp_map_cpp = createWPChannelMap(config["deepTauWPs"])
            tauType_map = createTauSFTypeMap(config["genuineTau_SFtype"])
            #print(jsonFile)
            #print(self.deepTauVersion)
            ROOT.gInterpreter.ProcessLine(f'::correction::TauCorrProvider::Initialize("{jsonFile}", "{self.deepTauVersion}", {wp_map_cpp}, {tauType_map} , "{period.split("_")[0]}")')
            TauCorrProducer.initialized = True
            #deepTauVersion = f"""DeepTau{deepTauVersions[config["deepTauVersion"]]}{config["deepTauVersion"]}"""

    def getES(self, df, source_dict):
        for source in [ central ] + TauCorrProducer.energyScaleSources_tau + TauCorrProducer.energyScaleSources_lep:
            updateSourceDict(source_dict, source, 'Tau')
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                df = df.Define(f'Tau_p4_{syst_name}', f'''::correction::TauCorrProvider::getGlobal().getES(
                               Tau_p4_{nano}, Tau_decayMode, Tau_genMatch,
                               ::correction::TauCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})''')
                df = df.Define(f'Tau_p4_{syst_name}_delta', f'Tau_p4_{syst_name} - Tau_p4_{nano}')

        return df, source_dict

    def getSF(self, df, nLegs, isCentral, return_variations):
        sf_sources =TauCorrProducer.SFSources_tau+TauCorrProducer.SFSources_genuineLep
        sf_scales = [up, down] if return_variations else []
        SF_branches = []
        for source in [ central ] + sf_sources:
            #for scale in getScales(source):
            for scale in [ central ] + sf_scales:
                if source == central and scale != central: continue
                if not isCentral and scale!= central: continue
                syst_name = source+scale# if source != central else 'Central'
                #SF_branches[syst_name]= []
                for leg_idx in range(nLegs):
                    branch_name = f"weight_tau{leg_idx+1}_TauID_SF_{syst_name}"
                    #print(branch_name)
                    branch_central = f"""weight_tau{leg_idx+1}_TauID_SF_{source+central}"""
                    #print(branch_central)
                    df = df.Define(f"{branch_name}_double",
                                f'''HttCandidate.leg_type[{leg_idx}] == Leg::tau ? ::correction::TauCorrProvider::getGlobal().getSF(
                               HttCandidate.leg_p4[{leg_idx}], Tau_decayMode.at(HttCandidate.leg_index[{leg_idx}]),
                               Tau_genMatch.at(HttCandidate.leg_index[{leg_idx}]), HttCandidate.channel(),
                               ::correction::TauCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) : 1.;''')
                    if scale != central:
                        branch_name_final = branch_name + '_rel'
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double/{branch_central})")
                    else:
                        if source == central:
                            branch_name_final = f"""weight_tau{leg_idx+1}_TauID_SF_{central}"""
                        else:
                            branch_name_final = branch_name
                        df = df.Define(branch_name_final, f"static_cast<float>({branch_name}_double)")
                    SF_branches.append(branch_name_final)
                    #SF_branches[syst_name].append(f"weight_tau{leg_idx+1}_TauID_SF_{syst_name}")

        return df,SF_branches

