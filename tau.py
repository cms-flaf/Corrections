import os
import ROOT
from .CorrectionsCore import *

class TauCorrProducer:
  jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/TAU/{}/tau.json.gz"
  initialized = False

  energyScaleSources = [
    "TauES_DM0", "TauES_DM1", "TauES_3prong", "EleFakingTauES_DM0", "EleFakingTauES_DM1", "MuFakingTauES"
  ]

  def __init__(self, period):
    jsonFile = TauCorrProducer.jsonPath.format(period)
    if not TauCorrProducer.initialized:
      headers_dir = os.path.dirname(os.path.abspath(__file__))
      header_path = os.path.join(headers_dir, "tau.h")
      ROOT.gInterpreter.Declare(f'#include "{header_path}"')
      ROOT.gInterpreter.ProcessLine(f'::correction::TauCorrProvider::Initialize("{jsonFile}", "DeepTau2017v2p1")')
      TauCorrProducer.initialized = True

  def getES(self, df, source_dict):
    for source in [ central ] + TauCorrProducer.energyScaleSources:
      updateSourceDict(source_dict, source, 'Tau')
      for scale in getScales(source):
        syst_name = getSystName(source, scale)
        df = df.Define(f'Tau_p4_{syst_name}', f'''::correction::TauCorrProvider::getGlobal().getES(
            Tau_p4_{nano}, Tau_decayMode, Tau_genMatch,
            ::correction::TauCorrProvider::UncSource::{source}, ::correction::UncScale::{scale})''')
        df = df.Define(f'Tau_p4_{syst_name}_delta', f'Tau_p4_{syst_name} - Tau_p4_{nano}')

    return df, source_dict
