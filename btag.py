import os
import ROOT
from .CorrectionsCore import *
from Common.Utilities import WorkingPointsbTag
import yaml



class bTagCorrProducer:
    jsonPath = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/{}/btagging.json.gz"
    bTagEff_JsonPath = "Corrections/data/BTV/{}/btagEff_TT.root"
    initialized = False
    SFSources = ["btagSFbc", "btagSFlight"]
    correlation = ["nocorr","correlated", "uncorrelated"]

    def __init__(self, period, loadEfficiency=True):
        jsonFile = bTagCorrProducer.jsonPath.format(period)
        jsonFile_eff = os.path.join(os.environ['ANALYSIS_PATH'],bTagCorrProducer.bTagEff_JsonPath.format(period))
        if not loadEfficiency:
            jsonFile_eff = ""
        if not bTagCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "btag.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            ROOT.gInterpreter.ProcessLine(f'::correction::bTagCorrProvider::Initialize("{jsonFile}", "{jsonFile_eff}")')
            bTagCorrProducer.initialized = True

    def getWPValues(self):
        wp_values = {}
        for wp in WorkingPointsbTag:
            root_wp = getattr(ROOT.WorkingPointsbTag, wp.name)
            wp_values[wp] = ROOT.correction.bTagCorrProvider.getGlobal().getWPvalue(root_wp)
        return wp_values

    def getSF(self, df, return_variations=True):
        sf_sources = bTagCorrProducer.SFSources if return_variations else []
        SF_branches = []
        for source in [ central ] + sf_sources:
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                for corr in self.correlation:
                    if source==central and corr!="nocorr" or source!=central and corr=="nocorr":
                        continue
                    syst_name2 = f"{syst_name}_{corr}" if corr!="nocorr" else syst_name
                    for wp in WorkingPointsbTag:
                        df = df.Define(f"bTagSF_{wp.name}_{syst_name2}",
                                    f''' ::correction::bTagCorrProvider::getGlobal().getSF(
                                    Jet_p4, Jet_bCand, Jet_hadronFlavour, Jet_btagDeepFlavB,WorkingPointsbTag::{wp.name},
                                ::correction::bTagCorrProvider::UncSource::{source}, ::correction::UncScale::{scale},
                                ::correction::bTagCorrProvider::Correlation::{corr}) ''')
                        SF_branches.append(f"bTagSF_{wp.name}_{syst_name2}")
                        #print(SF_branches)
        return df,SF_branches



