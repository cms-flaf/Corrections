import os
import ROOT
from .CorrectionsCore import *

class puJetIDCorrProducer:
    PUJetID_JsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/{}/jmar.json.gz"
    initialized = False
    puJetID_SF_Sources = ["PUJetID_eff"]
    period = None
    puJetID = "L"

    def __init__(self, period):
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],puJetIDCorrProducer.PUJetID_JsonPath.format(period))
        if not puJetIDCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "puJetID.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::PUJetIDCorrProvider::Initialize("{jsonFile_eff}")')
            puJetIDCorrProducer.period = period
            puJetIDCorrProducer.initialized = True

    def getPUJetIDEff(self, df,isCentral=True):
        puJetID_SF_branches = []
        for source in [ central ] + puJetIDCorrProducer.puJetID_SF_Sources:
            for scale in getScales(source):
                if not isCentral and scale!= central: continue
                syst_name = getSystName(source, scale)
                if source == central :
                    syst_name = "PUJetID_Central"
                for leg_idx in [0,1]:
                    branch_name = f"weight_b{leg_idx+1}_{syst_name}"
                    branch_central = f"""weight_b{leg_idx+1}_PUJetID_Central"""
                    df = df.Define(f"{branch_name}_double",
                                    f'''::correction::PUJetIDCorrProvider::getGlobal().getPUJetID_eff(
                                        HbbCandidate.leg_p4[{leg_idx}], "{puJetIDCorrProducer.puJetID}",
                                        ::correction::PUJetIDCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})''')
                    if scale != central:
                        df = df.Define(f"{branch_name}_rel", f"static_cast<float>({branch_name}_double/{branch_central})")
                        branch_name += '_rel'
                    else:
                        df = df.Define(f"{branch_name}", f"static_cast<float>({branch_name}_double)")
                    puJetID_SF_branches.append(f"{branch_name}")
        return df,puJetID_SF_branches
