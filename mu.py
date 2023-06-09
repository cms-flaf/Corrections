import os
import ROOT
from .CorrectionsCore import *
import yaml

class MuCorrProducer:
    muIDEff_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/MUO/{}/muon_Z.json.gz"
    initialized = False
    #muID_SF_Sources = ["NUM_TightID_DEN_genTracks","NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight","NUM_TightRelIso_DEN_TightIDandIPCut"]
    muID_SF_Sources = ["NUM_TightID_DEN_genTracks","NUM_TightRelIso_DEN_TightIDandIPCut"]
    muID_SF_Sources_dict = {"NUM_TightID_DEN_genTracks":"TightID", #num-den
                       "NUM_TightRelIso_DEN_TightIDandIPCut":"TightRelIso"}
    #muID_SF_Sources = []
    period = None

    def __init__(self, period):
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],MuCorrProducer.muIDEff_JsonPath.format(period))
        if not MuCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "mu.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::MuCorrProvider::Initialize("{jsonFile_eff}")')
            MuCorrProducer.period = period
            MuCorrProducer.initialized = True

    def getMuonIDSF(self, df, isCentral=True):
        muID_SF_branches = []
        for source in [ central ] + MuCorrProducer.muID_SF_Sources:
            for scale in getScales(source):
                if not isCentral and scale!= central: continue
                syst_name = getSystName(source, scale)
                if(scale!=central):
                    syst_name=getSystName(MuCorrProducer.muID_SF_Sources_dict[source],scale)
                for leg_idx in [0,1]:
                    branch_name = f"weight_tau{leg_idx+1}_MuidSF_{syst_name}"
                    branch_central = f"""weight_tau{leg_idx+1}_MuidSF_{getSystName(central, central)}"""
                    df = df.Define(f"{branch_name}_double",
                                    f'''httCand.leg_type[{leg_idx}] == Leg::mu ? ::correction::MuCorrProvider::getGlobal().getMuonIDSF(
                                        httCand.leg_p4[{leg_idx}], Muon_pfRelIso04_all.at(httCand.leg_index[{leg_idx}]), Muon_tightId.at(httCand.leg_index[{leg_idx}]),
                                        ::correction::MuCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}, "{MuCorrProducer.period}") : 1.''')
                    if scale != central:
                        df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                        branch_name += '_rel'
                    else:
                        df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                    muID_SF_branches.append(f"{branch_name}")
        return df,muID_SF_branches
