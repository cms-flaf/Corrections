import os
import ROOT
from .CorrectionsCore import *
from FLAF.Common.Utilities import WorkingPointsbTag
import yaml
import json

# https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagShapeCalibration
# https://twiki.cern.ch/twiki/bin/view/CMS/BTagCalibration
# https://twiki.cern.ch/twiki/bin/view/CMS/BTagSFMethods
# https://github.com/cms-btv-pog
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/BTV
# https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation
# https://cms-talk.web.cern.ch/t/ul-b-tagging-sf-update/20209/2
# https://gitlab.cern.ch/cms-btv/btv-json-sf/-/tree/master/data/UL2016preVFP
# https://github.com/hh-italian-group/h-tautau/blob/master/McCorrections/src/BTagWeight.cpp
# https://btv-wiki.docs.cern.ch/PerformanceCalibration/SFUncertaintiesAndCorrelations/working-point-based-sfs-fixedwp-sfs
# https://btv-wiki.docs.cern.ch/PerformanceCalibration/fixedWPSFRecommendations/


# shouldcorrectly process source name containing two underscores (e.g. JES_Absolute_2022)
# will correctly cut out second word and check if its in the list
def IsInJESList(src_name, jes_list):
    split_src_name = src_name.split("_")
    if len(split_src_name) == 1:
        return src_name in jes_list
    elif len(split_src_name) > 1:
        to_check = split_src_name[1] + "_"
        return to_check in jes_list
    else:
        raise RuntimeError(f"Cannot parse source name: {src_name}")


class bTagCorrProducer:
    jsonPath = "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/{}/latest/btagging.json.gz"
    bTagEff_JsonPath = "Corrections/data/BTV/{}/btagEff.root"
    initialized = False
    uncSource_bTagWP = [
        "btagSFbc_uncorrelated",
        "btagSFlight_uncorrelated",
        "btagSFbc_correlated",
        "btagSFlight_correlated",
    ]
    uncSources_bTagShape_jes = [
        "Total",
        "FlavorQCD",
        "RelativeBal",
        "HF",
        "BBEC1",
        "EC2",
        "Absolute",
        "BBEC1_",
        "Absolute_",
        "EC2_",
        "HF_",
        "RelativeSample_",
    ]
    uncSources_bTagShape_norm = [
        "lf",
        "hf",
        "lfstats1",
        "lfstats2",
        "hfstats1",
        "hfstats2",
        "cferr1",
        "cferr2",
    ]

    tagger_to_brag_branch = {
        "particleNet": "PNetB",
        "deepJet": "DeepFlavB",
        "UParTAK4": "UParTAK4B",
    }

    # important note: From the 2024 campaign onwards, only the UParTAK4 tagger is supported, and only json files are provided.
    def __init__(
        self,
        *,
        period,
        jetCollection,
        loadEfficiency=False,
        tagger="particleNet",
        useSplitJes=False,
        wantShape=False,
    ):
        print(f"tagger={tagger}")
        self.tagger = tagger
        self.btag_branch = bTagCorrProducer.tagger_to_brag_branch[tagger]
        self.jetCollection = jetCollection
        self.useSplitJes = useSplitJes
        jsonFile = bTagCorrProducer.jsonPath.format(pog_folder_names["BTV"][period])
        jsonFile_eff = os.path.join(
            os.environ["ANALYSIS_PATH"],
            bTagCorrProducer.bTagEff_JsonPath.format(period),
        )
        if not loadEfficiency:
            jsonFile_eff = ""
        if not bTagCorrProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "btag.h")
            headershape_path = os.path.join(headers_dir, "btagShape.h")
            ROOT.gInterpreter.Declare(f'#include "{headershape_path}"')
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')

            ROOT.gInterpreter.ProcessLineSynch(
                f'::correction::bTagCorrProvider::Initialize("{jsonFile}", "{jsonFile_eff}", "{self.tagger}")'
            )
            # ROOT.correction.bTagCorrProvider.Initialize(
            #     jsonFile, jsonFile_eff, self.tagger
            # )
            ROOT.correction.bTagCorrProvider.getGlobal()
            wantShape_str = "false"
            if wantShape:
                wantShape_str = "true"
            ROOT.gInterpreter.ProcessLineSynch(
                f"""::correction::bTagShapeCorrProvider::Initialize("{jsonFile}", "{periods[period]}", "{self.tagger}", {wantShape_str})"""
            )
            # ROOT.correction.bTagShapeCorrProvider.Initialize(
            #     jsonFile, periods[period], self.tagger
            # )
            ROOT.correction.bTagShapeCorrProvider.getGlobal()

            bTagCorrProducer.initialized = True

    def getWPValues(self):
        wp_values = {}
        for wp in WorkingPointsbTag:
            root_wp = getattr(ROOT.WorkingPointsbTag, wp.name)
            wp_values[wp] = ROOT.correction.bTagCorrProvider.getGlobal().getWPvalue(
                root_wp
            )
        return wp_values

    def getWPid(self, df, jetCollection=None):
        jetCollection = jetCollection or self.jetCollection
        df = df.Define(
            f"{jetCollection}_idbtag{self.btag_branch}",
            f"::correction::bTagCorrProvider::getGlobal().getWPBranch({jetCollection}_btag{self.btag_branch})",
        )
        return df

    def getBTagWPSF(self, df, return_variations=True, isCentral=True):
        sf_sources = bTagCorrProducer.uncSource_bTagWP
        SF_branches = []
        sf_scales = [up, down] if return_variations else []
        for source in [central] + sf_sources:
            for scale in [central] + sf_scales:
                if source == central and scale != central:
                    continue
                if not isCentral and scale != central:
                    continue
                # syst_name = source+scale if source != central else 'Central'
                syst_name = source + scale
                for wp in WorkingPointsbTag:
                    branch_name = f"weight_bTagSF_{wp.name}_{syst_name}"
                    # print(branch_name)
                    branch_central = f"""weight_bTagSF_{wp.name}_{source+central}"""
                    # branch_central = f"""weight_bTagSF_{wp.name}_{getSystName(central, central)}"""
                    p4 = f"{self.jetCollection}_p4"
                    hadronFlavour = f"{self.jetCollection}_hadronFlavour"
                    btagScore = f"{self.jetCollection}_btag{self.btag_branch}"
                    df = df.Define(
                        f"{branch_name}_double",
                        f""" ::correction::bTagCorrProvider::getGlobal().getSF(
                                {p4}, {hadronFlavour}, {btagScore}, WorkingPointsbTag::{wp.name},
                                ::correction::bTagCorrProvider::UncSource::{source}, ::correction::UncScale::{scale}) """,
                    )
                    if scale != central:
                        branch_name_final = branch_name + "_rel"
                        df = df.Define(
                            branch_name_final,
                            f"static_cast<float>({branch_name}_double/{branch_central})",
                        )
                    else:
                        if source == central:
                            branch_name_final = f"""weight_bTagSF_{wp.name}_{central}"""
                        else:
                            branch_name_final = branch_name
                        df = df.Define(
                            branch_name_final,
                            f"static_cast<float>({branch_name}_double)",
                        )
                    SF_branches.append(branch_name_final)
        return df, SF_branches

    def getBTagShapeSF(self, df, src_name, scale_name, isCentral, return_variations):
        sf_sources_norm = bTagCorrProducer.uncSources_bTagShape_norm
        sf_scales = [up, down] if return_variations else []
        SF_branches = []
        src_list = []
        scale_list = []
        force_name_as_central = False
        # here list must be corrected
        if isCentral and return_variations:
            src_list = [central] + bTagCorrProducer.uncSources_bTagShape_norm
            scale_list = [central] + sf_scales

        if not isCentral:
            if IsInJESList(src_name, bTagCorrProducer.uncSources_bTagShape_jes):
                src_list = [
                    f"jes{src_name}"
                ]  # Right now, src name was 'Total', but should be 'jesTotal'
                scale_list = [scale_name]
                force_name_as_central = True
            else:
                src_list = [central]
                scale_list = [central]

        print(f"src_name={src_name}, scale_name={scale_name}")
        print(f"\tsrc_list={src_list}")
        print(f"\tscale_list={scale_list}")

        for source in src_list:
            for scale in scale_list:
                if (source == central and scale != central) or (
                    source != central and scale == central
                ):
                    continue
                syst_name = getSystName(
                    source, scale
                )  # if source != central else 'Central'
                branch_name = f"weight_bTagShape_{syst_name}"
                branch_central = f"weight_bTagShape_{central}"

                p4 = f"{self.jetCollection}_p4"
                hadronFlavour = f"{self.jetCollection}_hadronFlavour"
                btagScore = f"{self.jetCollection}_btag{self.btag_branch}"

                df = df.Define(
                    f"{branch_name}_double",
                    f"""::correction::bTagShapeCorrProvider::getGlobal().getBTagShapeSF(
                    {p4}, {hadronFlavour}, {btagScore},
                    ::correction::bTagShapeCorrProvider::UncSource::{source},
                    ::correction::UncScale::{scale}
                    ) """,
                )

                if (
                    scale != central and not force_name_as_central
                ):  # If jes unc we do not want relative
                    branch_name_final = branch_name + "_rel"
                    df = df.Define(
                        branch_name_final,
                        f"static_cast<float>({branch_name}_double/{branch_central})",
                    )
                else:
                    if (
                        source == central or force_name_as_central
                    ):  # If jes unc, we want to give the fake name 'weight_btagShape_Central' but this is not actually central, it uses the up/down_jes keys in btagShape
                        branch_name_final = f"""weight_bTagShape_{central}"""
                    else:
                        branch_name_final = branch_name
                    df = df.Define(
                        branch_name_final, f"static_cast<float>({branch_name}_double)"
                    )
                SF_branches.append(branch_name_final)
        return df, SF_branches


class btagShapeWeightCorrector:
    cat_to_channelId = {"e": 1, "mu": 2, "eE": 11, "eMu": 12, "muMu": 22}

    def __init__(
        self,
        *,
        norm_file_path
    ): 
        with open(norm_file_path, "r") as norm_file:
            self.shape_weight_corr_dict = json.load(norm_file)

        self.initialized = []
        for key in self.shape_weight_corr_dict.keys():
            if key not in self.initialized:
                self._InitCppMap(key)
                self.initialized.append(key)

    def _InitCppMap(self, unc_src_scale):
        correction_factors = self.shape_weight_corr_dict[unc_src_scale]

        ROOT.gInterpreter.Declare("#include <map>")

        # init c++ map
        cpp_map_entries = []
        for cat, multipl_dict in correction_factors.items():
            channelId = btagShapeWeightCorrector.cat_to_channelId[cat]
            for key, ratio in multipl_dict.items():
                # key has structure f"ratio_ncetnralJet_{number}""
                num_jet = int(key.split("_")[-1])
                cpp_map_entries.append(f"{{{{{channelId}, {num_jet}}}, {ratio}}}")
        cpp_init = ", ".join(cpp_map_entries)

        ROOT.gInterpreter.Declare(
            f"""
            static const std::map<std::pair<int, int>, float> ratios_{unc_src_scale} = {{
                {cpp_init}
            }};

            float integral_correction_ratio_{unc_src_scale}(int ncentralJet, int channelId) {{
                std::pair<int, int> key{{channelId, ncentralJet}};
                try 
                {{
                    float ratio = ratios_{unc_src_scale}.at(key);
                    return ratio;
                }}
                catch (...)
                {{
                    return 1.0f;
                }}
            }}"""
        )

    def UpdateBtagWeight(
            self,
            *, 
            df, 
            unc_src, 
            unc_scale,
        ):
        
        if unc_src != unc_scale:
            unc_src_scale = f"{unc_src}_{unc_scale}"
        else:
            unc_src_scale = unc_src

        if unc_src_scale not in self.shape_weight_corr_dict.keys():
            raise RuntimeError(
                f"`BtagShapeWeightCorrection.json` does not contain key `{unc_src_scale}`."
            )

        df = df.Redefine(
            "weight_bTagShape_Central",
            f"""if (ncentralJet >= 2 && ncentralJet <= 8) 
                    return integral_correction_ratio_{unc_src_scale}(ncentralJet, channelId)*weight_bTagShape_Central;
                return weight_bTagShape_Central;""",
        )

        return df