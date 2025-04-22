import os
import ROOT
from .CorrectionsCore import *

# EWK_corr_sample = {
#     "DY":"ZJetsCorr_collection_wek.root",
#     "W":"WJetsCorr_collection_ewk.root",
# }
# hist_names = {
#     "DY":"eej_pTV_kappa_EW",
#     "W":"evj_pTV_kappa_EW",
# }

class VptCorrProducer:
    EWK_corr_filePath = "Corrections/data/ZPT/{0}"
    initialized = False
    SFSources = ["Vpt", "ewcorr"]

    def __init__(self, sampleType):
        rootFile_EWKcorr_name = "ZJetsCorr_collection_wek.root" if sampleType == "DY" else "WJetsCorr_collection_ewk.root"

        rootFile_EWKcorr = os.path.join(os.environ['ANALYSIS_PATH'],VptCorrProducer.EWK_corr_filePath.format(rootFile_EWKcorr_name))
        hist_name = "eej_pTV_kappa_EW" if sampleType == "DY" else "evj_pTV_kappa_EW"
        hist_nominal_weight = "ewcorr"
        self.sampleType = sampleType
        if not VptCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "Vpt.h")
            ROOT.gInterpreter.Declare(f"""#include "{header_path}" """)
            ROOT.gInterpreter.ProcessLine(f"""::correction::VptCorrProvider::Initialize("{rootFile_EWKcorr}", "{hist_name}", "{hist_nominal_weight}")""")
            VptCorrProducer.initialized = True

    def getSF(self, df, isCentral, return_variations):
        sf_sources =VptCorrProducer.SFSources
        sf_scales = [up, down] if return_variations else []
        SF_branches = []
        for source in sf_sources:
            for scale in [ central ] + sf_scales:
                if source == central and scale != central: continue
                if not isCentral and scale!= central: continue
                syst_name = source+scale# if source != central else 'Central'
                branch_SF_name = f"weight_EWKCorr_{syst_name}"
                branch_name_central = f"weight_EWKCorr_{source}Central"
                if self.sampleType == "W" or self.sampleType == "DY":
                    df = df.Define(f"{branch_SF_name}_double",
                                    f'''::correction::VptCorrProvider::getGlobal().getSF_fromRootFile(
                                        LHE_Vpt, ::correction::VptCorrProvider::UncSource::{source}, ::correction::UncScale::{scale} )''')
                else:
                    df = df.Define(f"{branch_SF_name}_double","1.f")

                if scale != central:
                    branch_name_final = branch_SF_name + '_rel'
                    df = df.Define(branch_name_final, f"static_cast<float>({branch_SF_name}_double/{branch_name_central})")
                else:
                    if source == central:
                        branch_name_final = branch_name_central
                    else:
                        branch_name_final = branch_SF_name
                    df = df.Define(branch_name_final, f"static_cast<float>({branch_SF_name}_double)")
                SF_branches.append(branch_name_final)
        return df,SF_branches
