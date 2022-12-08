import os
import ROOT
import yaml
from RunKit.sh_tools import sh_call

from .tau import TauCorrProducer
from .met import METCorrProducer
from .pu import puWeightProducer
from .CorrectionsCore import *


initialized = False
tau = None
met = None
pu = None

period_names = {
    'Run2_2016_HIPM': '2016preVFP_UL',
    'Run2_2016': '2016postVFP_UL',
    'Run2_2017': '2017_UL',
    'Run2_2018': '2018_UL',
}

def Initialize(period):
    global initialized
    global tau
    global pu
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
    pu = puWeightProducer(period=period_names[period])
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
    return df, syst_dict



def getWeights(df, config=None, sample=None):
    if not initialized:
        raise RuntimeError('Corrections are not initialized')
    lumi = config['GLOBAL']['luminosity']
    sampleType = config[sample]['sampleType']
    with open('config/crossSections.yaml', 'r') as xs_file:
        xs_dict = yaml.safe_load(xs_file)
    xs_name = config[sample]['crossSection']
    xs = xs_dict[xs_name]['crossSec']
    xs_stitching = 1
    xs_stitching_incl = 1
    xs_inclusive = 1
    stitching_weight = 1
    if sampleType == 'DY' or sampleType=='W':
        xs_stitching_name = config[sample]['crossSectionStitch']
        inclusive_sample_name = 'DYJetsToLL_M-50' if sampleType=='DY' else 'WJetsToLNu'
        xs_stitching = xs_dict[xs_stitching_name]['crossSec']
        xs_stitching_incl = xs_dict[config[inclusive_sample_name]['crossSectionStitch']]['crossSec']
        xs_inclusive = xs_dict[config[inclusive_sample_name]['crossSection']]['crossSec']

    stitching_weight_string = f' {xs_stitching} * {stitching_weight} * ({xs_inclusive}/{xs_stitching_incl})'
    df = pu.getWeight(df)
    df = df.Define('genWeightD', 'std::copysign<double>(1., genWeight)')
    scale = 'Central'
    df = df.Define('weight', f'genWeightD * {lumi} * {xs} * {stitching_weight_string} * puWeight_{scale}')
    return df, [ scale ]