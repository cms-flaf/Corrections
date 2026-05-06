import os
import ROOT
import .CorrectionsCore import *

# Bosonic recoil corrections following recommendations from https://cms-higgs-leprare.docs.cern.ch/htt-common/V_recoil/

class BosonicRecoilCorrection:
    initialized = False

    def __init__(self):
        if not BosonicRecoilCorrection.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "recoil.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            BosonicRecoilCorrection.initialized = True
    
    def getRecoil(self):
        return
