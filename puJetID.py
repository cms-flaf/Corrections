import os
import ROOT
from .CorrectionsCore import *
import yaml

class puJetIDCorrProducer:
    PUJetID_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/{}/muon_Z.json.gz"
    initialized = False
    puJetID_SF_Sources = ["PUJetID_eff"]
    period = None
    puJetID = "Loose"

    def __init__(self, period):
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],puJetIDCorrProducer.PUJetID_JsonPath.format(period))
        if not puJetIDCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "puJetID.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::PUJetIDCorProvider::Initialize("{jsonFile_eff}")')
            puJetIDCorrProducer.period = period
            puJetIDCorrProducer.initialized = True

    def getPUJetIDEff(self, df):
        puJetID_SF_branches = []
        for source in [ central ] + puJetIDCorrProducer.puJetID_SF_Sources:
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                for leg_idx in [0,1]:
                    df = df.Define(f"weight_tau{leg_idx+1}_{syst_name}",
                                    f'''httCand.leg_type[{leg_idx}] == Leg::tau ? ::correction::PUJetIDCorProvider::getGlobal().getPUJetID_eff(
                                        httCand.leg_p4[{leg_idx}], "{puJetIDCorrProducer.puJetID}",
                                        ::correction::PUJetIDCorProvider::UncSource::{source}, ::correction::UncScale::{scale}, "{puJetIDCorrProducer.period}") : 1.''')
                    puJetID_SF_branches.append(f"weight_tau{leg_idx+1}_{syst_name}")
        return df,puJetID_SF_branches
