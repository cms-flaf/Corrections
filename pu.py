import os
import ROOT
from .CorrectionsCore import *

class puWeightProducer:
    jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/LUM/{}/puWeights.json.gz"
    initialized = False

    uncSource = 'pu'

    def __init__(self, period):
        jsonFile = puWeightProducer.jsonPath.format(period)
        if not puWeightProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "pu.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::puCorrProvider::Initialize("{jsonFile}")')
            puWeightProducer.initialized = True

    def getWeight(self, df):
        for scale in ['Central', 'Up', 'Down']:
            df = df.Define(f'puWeight_{scale}', f'''::correction::puCorrProvider::getGlobal().getWeight(
                            ::correction::UncScale::{scale}, Pileup_nTrueInt)''')
        return df
