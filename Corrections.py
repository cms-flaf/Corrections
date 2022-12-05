import os
import ROOT
from RunKit.sh_tools import sh_call

from .tau import TauCorrProducer
from .met import METCorrProducer
from .CorrectionsCore import *


initialized = False
tau = None
met = None

period_names = {
    'Run2_2016_HIPM': '2016preVFP_UL',
    'Run2_2016': '2016postVFP_UL',
    'Run2_2017': '2017_UL',
    'Run2_2018': '2018_UL',
}

def Initialize(period):
    global initialized
    global tau
    global met
    if initialized:
        raise RuntimeError('Corrections are already initialized')
    returncode, output, err= sh_call(['correction', 'config', '--cflags', '--ldflags'],
                                     catch_stdout=True, decode=True, verbose=0)
    params = output.split(' ')
    for param in params:
        if param.startswith('-I'):
            ROOT.gInterpreter.AddIncludePath(param[2:].strip())
        elif param.startswith('-L'):
            lib_path = param[2:].strip()
        elif param.startswith('-l'):
            lib_name = param[2:].strip()
    corr_lib = f"{lib_path}/lib{lib_name}.so"
    if not os.path.exists(corr_lib):
        print(f'correction config output: {output}')
        raise RuntimeError("Correction library is not found.")
    ROOT.gSystem.Load(corr_lib)
    tau = TauCorrProducer(period=period_names[period])
    met = METCorrProducer()
    initialized = True

def applyScaleUncertainties(df):
    if not initialized:
        raise RuntimeError('Corrections are not initialized')
    source_dict = {}
    df, source_dict = tau.getES(df, source_dict)
    df, source_dict = met.getPFMET(df, source_dict)
    syst_dict = { }
    for source, source_objs in source_dict.items():
        for scale in getScales(source):
            syst_name = getSystName(source, scale)
            syst_dict[syst_name] = source
            for obj in [ "Electron", "Muon", "Tau", "Jet", "FatJet", "boostedTau", "MET", "PuppiMET",
                         "DeepMETResponseTune", "DeepMETResolutionTune" ]:
                if obj not in source_objs:
                    suffix = 'Central' if obj in [ "Tau", "MET" ] else 'nano'
                    df = df.Define(f'{obj}_p4_{syst_name}', f'{obj}_p4_{suffix}')
    print(syst_dict)
    return df, syst_dict


def getWeights(df):
    if not initialized:
        raise RuntimeError('Corrections are not initialized')
    weight_dict = {}
    df, weight_dict = tau.getESWeight(df, weight_dict)
    df = df.Define('w_genWeightD', 'std::copysign<double>(1., genWeight)')
    weight_dict.append('genWeightD')
    print(weight_dict)
    return df,weight_dict