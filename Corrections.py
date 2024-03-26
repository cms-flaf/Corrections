import os
import ROOT
import yaml
import itertools
from RunKit.sh_tools import sh_call

from .CorrectionsCore import *

initialized = False
tau = None
met = None
trg = None
btag = None
pu = None
mu = None
ele = None
puJetID = None
jet = None
fatjet = None
sf_to_apply = None

period_names = {
    'Run2_2016_HIPM': '2016preVFP_UL',
    'Run2_2016': '2016postVFP_UL',
    'Run2_2017': '2017_UL',
    'Run2_2018': '2018_UL',
}

def Initialize(config, isData, load_corr_lib=True, load_pu=True, load_tau=True, load_trg=True, load_btag=True,
               loadBTagEff=True, load_met=True, load_mu = True, load_ele=True, load_puJetID=True, load_jet=True,load_fatjet=True):
    global initialized
    global tau
    global pu
    global met
    global trg
    global btag
    global sf_to_apply
    global mu
    global ele
    global puJetID
    global jet
    global fatjet
    if initialized:
        raise RuntimeError('Corrections are already initialized')
    if load_corr_lib:
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
    period = config['era']
    sf_to_apply = config['corrections']
    if load_pu:
        from .pu import puWeightProducer
        pu = puWeightProducer(period=period_names[period])
    if load_tau:
        from .tau import TauCorrProducer
        tau = TauCorrProducer(period_names[period], config)
    if load_jet:
        from .jet import JetCorrProducer
        jet = JetCorrProducer(period_names[period],isData)
    if load_fatjet:
        from .fatjet import FatJetCorrProducer
        fatjet = FatJetCorrProducer(period_names[period],isData)
    if load_btag:
        from .btag import bTagCorrProducer
        btag = bTagCorrProducer(period_names[period], loadBTagEff)
    if load_met:
        from .met import METCorrProducer
        met = METCorrProducer()
    if load_mu:
        from .mu import MuCorrProducer
        mu = MuCorrProducer(period_names[period])
    if load_ele:
        from .electron import EleCorrProducer
        ele = EleCorrProducer(period_names[period])
    if load_puJetID:
        from .puJetID import puJetIDCorrProducer
        puJetID = puJetIDCorrProducer(period_names[period])
    if load_trg:
        from .triggers import TrigCorrProducer
        trg = TrigCorrProducer(period_names[period], config)
    initialized = True

def applyScaleUncertainties(df):
    if not initialized:
        raise RuntimeError('Corrections are not initialized')
    source_dict = {}
    if 'tauES' in sf_to_apply:
        df, source_dict = tau.getES(df, source_dict)
    if 'JEC_JER' in sf_to_apply:
        df, source_dict = jet.getP4Variations(df, source_dict)
        df, source_dict = fatjet.getP4Variations(df, source_dict)
    if met!=None and ('tauES' in sf_to_apply or 'JEC_JER' in sf_to_apply):
        df, source_dict = met.getPFMET(df, source_dict)
    syst_dict = { }
    for source, source_objs in source_dict.items():
        for scale in getScales(source):
            syst_name = getSystName(source, scale)
            syst_dict[syst_name] = source
            #print(source, source_objs, syst_name)
            for obj in [ "Electron", "Muon", "Tau", "Jet", "FatJet",  "MET", "PuppiMET", "boostedTau",
                         "DeepMETResponseTune", "DeepMETResolutionTune", "SubJet"]:
                if obj not in source_objs:
                    #suffix = 'Central' if f"{obj}_p4_Central" in df.GetColumnNames() else 'nano'
                    suffix = 'nano'
                    if obj=='boostedTau' and '{obj}_p4_{suffix}' not in df.GetColumnNames(): continue
                    #print(f"{obj}_p4_{syst_name}, {obj}_p4_{suffix}")
                    #print(df.Count().GetValue())
                    df = df.Define(f'{obj}_p4_{syst_name}', f'{obj}_p4_{suffix}')
    return df,syst_dict


def findRefSample(config, sample_type):
    refSample = []
    for sample, sampleDef in config.items():
        if sampleDef.get('sampleType', None) == sample_type and sampleDef.get('isReference', False):
            refSample.append(sample)
    if len(refSample) != 1:
        raise RuntimeError(f'multiple refSamples for {sample_type}: {refSample}')
    return refSample[0]

def getBranches(syst_name, all_branches):
    final_branches = []
    for branches in all_branches:
        name = syst_name if syst_name in branches else central
        final_branches.extend(branches[name])
    return final_branches

def getNormalisationCorrections(df, config, sample, nLegs, ana_cache=None, return_variations=True, isCentral=True):
    if not initialized:
        raise RuntimeError('Corrections are not initialized')
    lumi = config['GLOBAL']['luminosity']
    sampleType = config[sample]['sampleType']
    xsFile = config['GLOBAL']['crossSectionsFile']
    xsFilePath = os.path.join(os.environ['ANALYSIS_PATH'], xsFile)
    with open(xsFilePath, 'r') as xs_file:
        xs_dict = yaml.safe_load(xs_file)
    xs_stitching = 1.
    xs_stitching_incl = 1.
    xs_inclusive = 1.
    stitch_str = '1.f'

    #print(sample)
    #print(sampleType)
    if sampleType in [ 'DY', 'W']:
        xs_stitching_name = config[sample]['crossSectionStitch']
        inclusive_sample_name = findRefSample(config, sampleType)
        xs_name = config[inclusive_sample_name]['crossSection']
        xs_stitching = xs_dict[xs_stitching_name]['crossSec']
        xs_stitching_incl = xs_dict[config[inclusive_sample_name]['crossSectionStitch']]['crossSec']
        if sampleType == 'DY':
            stitch_str = 'if(LHE_Vpt==0.) return 1/2.f; return 1/3.f;'
        elif sampleType == 'W':
            stitch_str= "if(LHE_Njets==0.) return 1.f; return 1/2.f;"
    else:
        xs_name = config[sample]['crossSection']
    df = df.Define("stitching_weight", stitch_str)
    xs_inclusive = xs_dict[xs_name]['crossSec']

    stitching_weight_string = f' {xs_stitching} * stitching_weight * ({xs_inclusive}/{xs_stitching_incl})'
    df, pu_SF_branches = pu.getWeight(df)
    df = df.Define('genWeightD', 'std::copysign<double>(1., genWeight)')
    all_branches = [ pu_SF_branches ]
    #print(all_branches)
    all_sources = set(itertools.chain.from_iterable(all_branches))
    all_sources.remove(central)
    all_weights = []
    #print(f"all_sources = {list(all_sources)}")
    for syst_name in [central] + list(all_sources):
        #print(syst_name)
        denom = f'/{ana_cache["denominator"][central][central]}' if ana_cache is not None else ''
        for scale in ['Up', 'Down']:
            if syst_name == f'pu{scale}':
                #print(f"using anacache[denom][pu][{scale}]")
                denom = f"""/{ana_cache["denominator"]["pu"][scale]}""" if ana_cache is not None else ''
        #if not isCentral : continue
        branches = getBranches(syst_name, all_branches)
        #print(syst_name)
        product = ' * '.join(branches)
        #print(f"product is {product}")
        weight_name = f'weight_{syst_name}' if syst_name!=central else 'weight_MC_Lumi_pu'
        weight_rel_name = f'weight_MC_Lumi_{syst_name}_rel'
        weight_out_name = weight_name if syst_name == central else weight_rel_name
        weight_formula = f'genWeightD * {lumi} * {stitching_weight_string} * {product}{denom}'
        df = df.Define(weight_name, f'static_cast<float>({weight_formula})')
        #print(f"weight_formula is {weight_formula}")
        #print(f"weight_name is {weight_name}")
        #print(f"weight_rel_name is {weight_rel_name}")
        #print(f"weight_out_name is {weight_out_name}")

        if syst_name==central:
            all_weights.append(weight_out_name)
        else:
            df = df.Define(weight_out_name, f'static_cast<float>(weight_{syst_name}/weight_MC_Lumi_pu)')
            for scale in ['Up','Down']:
                if syst_name == f'pu{scale}' and return_variations:
                    all_weights.append(weight_out_name)
    '''
    if 'tauID' in sf_to_apply:
        df, tau_SF_branches = tau.getSF(df, nLegs, isCentral, return_variations)
        tau_branches = [ tau_SF_branches ]
        tau_sources = set(itertools.chain.from_iterable(tau_branches))
        tau_sources.remove(central)
        for syst_name in [central] + list(tau_sources):
            print(f"syst name is {syst_name}")
            branches = getBranches(syst_name, tau_branches)
            print(f"branches are {branches}")

            product = ' * '.join(branches)
            print(f"product is {product}")
            weight_name = f'weight_TauID_{syst_name}'
            if(syst_name == central):
                weight_name = f'weight_TauID_{central}'
            print(f"weight_name is {weight_name}")
            weight_rel_name = weight_name + '_rel'
            print(f"weight_rel_name is {weight_rel_name}")

            weight_out_name = weight_name if syst_name == central else weight_rel_name
            #print(f"weight_out_name is {weight_out_name}")

            weight_formula = f'{product}'
            print(weight_formula)
            df = df.Define(weight_name, f'static_cast<float>({weight_formula})')
            df = df.Define(weight_rel_name, f'static_cast<float>({weight_name}/weight_TauID_{central})')
            all_weights.append(weight_out_name)
    '''
    if tau!=None:
        df,tau_SF_branches = tau.getSF(df, nLegs, isCentral, return_variations)
        all_weights.extend(tau_SF_branches)
    if mu!= None:
        df, muID_SF_branches = mu.getMuonIDSF(df, nLegs, isCentral, return_variations)
        all_weights.extend(muID_SF_branches)
        df, highPtmuID_SF_branches = mu.getHighPtMuonIDSF(df, nLegs, isCentral, return_variations)
        all_weights.extend(highPtmuID_SF_branches)
    if ele!= None:
        df, eleID_SF_branches = ele.getIDSF(df, nLegs, isCentral, return_variations)
        all_weights.extend(eleID_SF_branches)
    if puJetID!=None and nLegs == 2:
        df, puJetID_SF_branches = puJetID.getPUJetIDEff(df,isCentral,return_variations)
        all_weights.extend(puJetID_SF_branches)
    if btag != None:
         df, bTag_SF_branches = btag.getSF(df,isCentral and return_variations, isCentral)
         all_weights.extend(bTag_SF_branches)
    return df, all_weights

def getDenominator(df, sources):
    if not initialized:
        raise RuntimeError('Corrections are not initialized')
    df, pu_SF_branches = pu.getWeight(df)
    df = df.Define('genWeightD', 'std::copysign<double>(1., genWeight)')
    syst_names =[]
    for source in sources:
        for scale in getScales(source):
            syst_name = getSystName(source, scale)
            df = df.Define(f'weight_denom_{syst_name}', f'genWeightD * puWeight_{scale}')
            syst_names.append(syst_name)
    return df,syst_names