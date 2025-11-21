import os
import itertools

from .CorrectionsCore import *
from FLAF.RunKit.run_tools import ps_call


def getBranches(syst_name, all_branches):
    final_branches = []
    for branches in all_branches:
        name = syst_name if syst_name in branches else central
        final_branches.extend(branches[name])
    return final_branches


class Corrections:
    _global_instance = None

    @staticmethod
    def initializeGlobal(load_corr_lib=False, **kwargs):
        if Corrections._global_instance is not None:
            raise RuntimeError("Global instance is already initialized")

        if load_corr_lib:
            returncode, output, err = ps_call(
                ["correction", "config", "--cflags", "--ldflags"],
                catch_stdout=True,
                decode=True,
                verbose=0,
            )
            params = output.split(" ")
            for param in params:
                if param.startswith("-I"):
                    # ROOT.gInterpreter.AddIncludePath(os.environ['FLAF_ENVIRONMENT_PATH']+"/include")#param[2:].strip())
                    ROOT.gInterpreter.AddIncludePath(param[2:].strip())
                elif param.startswith("-L"):
                    lib_path = param[2:].strip()
                elif param.startswith("-l"):
                    lib_name = param[2:].strip()
            # lib_path = os.environ['FLAF_ENVIRONMENT_PATH']+"/lib/python3.11/site-packages" #
            corr_lib = f"{lib_path}/lib{lib_name}.so"

            if not os.path.exists(corr_lib):
                raise RuntimeError("Correction library is not found.")
            ROOT.gSystem.Load(corr_lib)

        Corrections._global_instance = Corrections(**kwargs)

    @staticmethod
    def getGlobal():
        if Corrections._global_instance is None:
            raise RuntimeError("Global instance is not initialized")
        return Corrections._global_instance

    def __init__(
        self,
        *,
        global_params,
        dataset_name,
        dataset_cfg,
        process_name,
        process_cfg,
        processors,
        isData,
        trigger_class,
    ):
        self.global_params = global_params
        self.dataset_name = dataset_name
        self.dataset_cfg = dataset_cfg
        self.process_name = process_name
        self.process_cfg = process_cfg
        self.processors = processors
        self.isData = isData
        self.trigger_dict = trigger_class.trigger_dict if trigger_class else {}

        self.period = global_params["era"]

        self.to_apply = {}
        correction_origins = {}
        for cfg_name, cfg in [
            ("dataset", dataset_cfg),
            ("process", process_cfg),
            ("global", global_params),
        ]:
            if not cfg:
                continue
            for corr_entry in cfg.get("corrections", []):
                if type(corr_entry) == str:
                    name = corr_entry
                    value = {}
                elif type(corr_entry) == dict:
                    name = corr_entry["name"]
                    value = {k: v for k, v in corr_entry.items() if k != "name"}
                else:
                    raise RuntimeError(
                        f"Unknown correction entry type={type(corr_entry)}. {corr_entry}"
                    )
                if name not in self.to_apply:
                    self.to_apply[name] = value
                    correction_origins[name] = cfg_name
                else:
                    print(
                        f"Warning: correction {name} is already defined in {correction_origins[name]}. Skipping definition from {cfg_name}",
                        file=sys.stderr,
                    )
        if len(self.to_apply) > 0:
            print(
                f'Corrections to apply: {", ".join(self.to_apply.keys())}',
                file=sys.stderr,
            )

        self.xs_db_ = None
        self.tau_ = None
        self.met_ = None
        self.trg_ = None
        self.btag_ = None
        self.pu_ = None
        self.mu_ = None
        self.muScaRe_ = None
        self.ele_ = None
        self.puJetID_ = None
        self.jet_ = None
        self.fatjet_ = None
        self.Vpt_ = None
        self.JetVetoMap_ = None

    @property
    def xs_db(self):
        if self.xs_db_ is None:
            from FLAF.Common.CrossSectionDB import CrossSectionDB

            self.xs_db_ = CrossSectionDB.Load(
                os.environ["ANALYSIS_PATH"],
                self.global_params["crossSectionsFile"],
            )
        return self.xs_db_

    @property
    def pu(self):
        if self.pu_ is None:
            from .pu import puWeightProducer

            self.pu_ = puWeightProducer(period=period_names[self.period])
        return self.pu_

    @property
    def Vpt(self):
        if self.Vpt_ is None:
            from .Vpt import VptCorrProducer

            self.Vpt_ = VptCorrProducer(self.to_apply["Vpt"]["type"], self.period)
        return self.Vpt_

    @property
    def JetVetoMap(self):
        if self.JetVetoMap_ is None:
            from .JetVetoMap import JetVetoMapProvider

            self.JetVetoMap_ = JetVetoMapProvider(self.period)
        return self.JetVetoMap_

    @property
    def tau(self):
        if self.tau_ is None:
            from .tau import TauCorrProducer

            self.tau_ = TauCorrProducer(self.period, self.global_params)
        return self.tau_

    @property
    def jet(self):
        if self.jet_ is None:
            from .jet import JetCorrProducer

            self.jet_ = JetCorrProducer(
                period_names[self.period], self.isData, self.dataset_name
            )
        return self.jet_

    @property
    def fatjet(self):
        if self.fatjet_ is None:
            from .fatjet import FatJetCorrProducer

            self.fatjet_ = FatJetCorrProducer(period_names[self.period], self.isData)
        return self.fatjet_

    @property
    def btag(self):
        if self.btag_ is None:
            from .btag import bTagCorrProducer

            self.btag_ = bTagCorrProducer(
                period_names[self.period],
                self.global_params["bjet_preselection_branch"],
                tagger_name=self.global_params["tagger_name"],
                loadEfficiency=False,
                use_split_jes=False,
            )
        return self.btag_

    @property
    def met(self):
        if self.met_ is None:
            from .met import METCorrProducer

            self.met_ = METCorrProducer()
        return self.met_

    @property
    def mu(self):
        if self.mu_ is None:
            from .mu import MuCorrProducer

            # self.mu_ = MuCorrProducer(period_names[self.period])
            self.mu_ = MuCorrProducer(self.period)
        return self.mu_

    @property
    def muScaRe(self):
        if self.muScaRe_ is None:
            from .MuonScaRe_corr import MuonScaReCorrProducer

            # self.muScaRe_ = MuonScaReCorrProducer(period_names[self.period])
            self.muScaRe_ = MuonScaReCorrProducer(
                period_names[self.period], self.isData
            )
        return self.muScaRe_

    @property
    def ele(self):
        if self.ele_ is None:
            from .electron import EleCorrProducer

            self.ele_ = EleCorrProducer(period_names[self.period])
        return self.ele_

    @property
    def puJetID(self):
        if self.puJetID_ is None:
            from .puJetID import puJetIDCorrProducer

            self.puJetID_ = puJetIDCorrProducer(period_names[self.period])
        return self.puJetID_

    @property
    def trg(self):
        if self.trg_ is None:
            if self.period.split("_")[0].startswith("Run3"):
                from .triggersRun3 import TrigCorrProducer
            else:
                from .triggers import TrigCorrProducer
            self.trg_ = TrigCorrProducer(
                period_names[self.period], self.global_params, self.trigger_dict
            )
        return self.trg_

    def applyScaleUncertainties(self, df, ana_reco_objects):
        source_dict = {central: []}
        if "tauES" in self.to_apply and not self.isData:
            df, source_dict = self.tau.getES(df, source_dict)
        if "eleES" in self.to_apply:
            df, source_dict = self.ele.getES(df, source_dict)
        if "JEC" in self.to_apply or "JER" in self.to_apply:
            apply_jes = "JEC" in self.to_apply and not self.isData
            apply_jer = "JER" in self.to_apply and not self.isData
            apply_jet_horns_fix_ = (
                "JER" in self.to_apply
                and "Jet_horns_fix" in self.to_apply
                and not self.isData
            )
            df, source_dict = self.jet.getP4Variations(
                df, source_dict, apply_jer, apply_jes, apply_jet_horns_fix_
            )
        if "muScaRe" in self.to_apply:
            df, source_dict = self.muScaRe.getP4Variations(df, source_dict)
            # df, source_dict = self.fatjet.getP4Variations(df, source_dict, 'JER' in self.to_apply, 'JEC' in self.to_apply)
        if (
            "tauES" in self.to_apply
            or "JEC" in self.to_apply
            or "JER" in self.to_apply
            or "eleES" in self.to_apply
            or "muScaRe" in self.to_apply
        ):
            df, source_dict = self.met.getMET(df, source_dict, self.MET_type)
        syst_dict = {}
        for source, source_objs in source_dict.items():
            for scale in getScales(source):
                syst_name = getSystName(source, scale)
                syst_dict[syst_name] = source
                for obj in ana_reco_objects:
                    if obj not in source_objs:
                        suffix = (
                            "Central"
                            if f"{obj}_p4_Central" in df.GetColumnNames()
                            else "nano"
                        )
                        # suffix = 'nano'
                        if (
                            obj == "boostedTau"
                            and "{obj}_p4_{suffix}" not in df.GetColumnNames()
                        ):
                            continue
                        if f"{obj}_p4_{syst_name}" not in df.GetColumnNames():
                            print(
                                f"Defining nominal {obj}_p4_{syst_name} as {obj}_p4_{suffix}"
                            )
                            df = df.Define(
                                f"{obj}_p4_{syst_name}", f"{obj}_p4_{suffix}"
                            )
        return df, syst_dict

    def defineCrossSection(self, df, crossSectionBranch):
        xs_processor_names = []
        for p_name, proc in self.processors.items():
            if hasattr(proc, "onAnaTuple_defineCrossSection"):
                xs_processor_names.append(p_name)
        if len(xs_processor_names) == 0:
            raise RuntimeError(
                "No processor implements onAnaTuple_defineCrossSection method"
            )
        if len(xs_processor_names) > 1:
            raise RuntimeError(
                "Multiple processors implement onAnaTuple_defineCrossSection method. Not supported."
            )
        p_name = xs_processor_names[0]
        print(
            f'Using processor "{p_name}" to define cross section for dataset "{self.dataset_name}"'
        )
        xs_processor = self.processors[p_name]
        return xs_processor.onAnaTuple_defineCrossSection(
            df, crossSectionBranch, self.xs_db, self.dataset_name, self.dataset_cfg
        )

    def defineDenominator(self, df, denomBranch, syst_name, scale_name, ana_caches):
        denom_processor_names = []
        for p_name, proc in self.processors.items():
            if hasattr(proc, "onAnaTuple_defineDenominator"):
                denom_processor_names.append(p_name)
        if len(denom_processor_names) == 0:
            raise RuntimeError(
                "No processor implements onAnaTuple_defineDenominator method"
            )
        if len(denom_processor_names) > 1:
            raise RuntimeError(
                "Multiple processors implement onAnaTuple_defineDenominator method. Not supported."
            )
        p_name = denom_processor_names[0]
        print(
            f'Using processor "{p_name}" to define denominator for dataset "{self.dataset_name}"'
        )
        if len(ana_caches) > 1:
            print(
                f"Available ana_caches for denominator calculation: {list(ana_caches.keys())}"
            )
        denom_processor = self.processors[p_name]
        return denom_processor.onAnaTuple_defineDenominator(
            df,
            denomBranch,
            p_name,
            self.dataset_name,
            syst_name,
            scale_name,
            ana_caches,
        )

    def getNormalisationCorrections(
        self,
        df,
        *,
        lepton_legs,
        offline_legs,
        trigger_names,
        syst_name,
        source_name,
        ana_caches,
        return_variations=True,
        isCentral=True,
        use_genWeight_sign_only=True,
    ):
        lumi = self.global_params["luminosity"]

        # syst name is only needed to determine scale (only it contains up/down/cetnral)
        if "Up" in syst_name:
            scale_name = up
        elif "Down" in syst_name:
            scale_name = down
        elif "Central" in syst_name:
            scale_name = central
        else:
            raise RuntimeError("Obtained scale not Central, Up or Down")

        # source_name is needed to determine source and it doesn't contain up/down/cetnral
        # in case if source_name contains underscores we want to keep everything after the first occurence of the underscore
        start = source_name.find("_")
        src_name = source_name[start + 1 :]

        genWeight_def = (
            "std::copysign<double>(1., genWeight)"
            if use_genWeight_sign_only
            else "double(genWeight)"
        )
        df = df.Define("genWeightD", genWeight_def)

        crossSectionBranch = "crossSection"
        df = self.defineCrossSection(df, crossSectionBranch)

        all_branches = []
        if "pu" in self.to_apply:
            df, pu_SF_branches = self.pu.getWeight(df)
            all_branches.append(pu_SF_branches)

        all_sources = set(itertools.chain.from_iterable(all_branches))
        if central in all_sources:
            all_sources.remove(central)
        all_weights = []
        for syst_name in [central] + list(all_sources):
            denomBranch = f"__denom_{syst_name}"
            syst_unc, syst_scale = splitSystName(syst_name)
            df = self.defineDenominator(
                df, denomBranch, syst_unc, syst_scale, ana_caches
            )
            branches = getBranches(syst_name, all_branches)
            sf_product = " * ".join(branches) if len(branches) > 0 else "1.0"
            weight_name = (
                f"weight_{syst_name}" if syst_name != central else "weight_MC_Lumi_pu"
            )
            weight_rel_name = f"weight_MC_Lumi_{syst_name}_rel"
            weight_out_name = weight_name if syst_name == central else weight_rel_name
            weight_formula = f"genWeightD * {lumi} * {crossSectionBranch} * {sf_product} / {denomBranch}"
            df = df.Define(weight_name, f"static_cast<float>({weight_formula})")

            if syst_name == central:
                all_weights.append(weight_out_name)
            else:
                df = df.Define(
                    weight_out_name,
                    f"static_cast<float>(weight_{syst_name}/weight_MC_Lumi_pu)",
                )
                for scale in ["Up", "Down"]:
                    if syst_name == f"pu{scale}" and return_variations:
                        all_weights.append(weight_out_name)

        if "Vpt" in self.to_apply:
            df, Vpt_SF_branches = self.Vpt.getSF(df, isCentral, return_variations)
            all_weights.extend(Vpt_SF_branches)
            df, Vpt_DYw_branches = self.Vpt.getDYSF(df, isCentral, return_variations)
            all_weights.extend(Vpt_DYw_branches)
        if "tauID" in self.to_apply:
            df, tau_SF_branches = self.tau.getSF(
                df, lepton_legs, isCentral, return_variations
            )
            all_weights.extend(tau_SF_branches)
        if "btagShape" in self.to_apply:
            # scale_name for getBTagShapeSF is contained in syst_name
            df, bTagShape_SF_branches = self.btag.getBTagShapeSF(
                df, src_name, scale_name, isCentral, return_variations
            )
            all_weights.extend(bTagShape_SF_branches)
        if "mu" in self.to_apply:
            if self.mu.low_available:
                df, lowPtmuID_SF_branches = self.mu.getLowPtMuonIDSF(
                    df, lepton_legs, isCentral, return_variations
                )
                all_weights.extend(lowPtmuID_SF_branches)
            if self.mu.med_available:
                df, muID_SF_branches = self.mu.getMuonIDSF(
                    df, lepton_legs, isCentral, return_variations
                )
                all_weights.extend(muID_SF_branches)
            if self.mu.high_available:
                df, highPtmuID_SF_branches = self.mu.getHighPtMuonIDSF(
                    df, lepton_legs, isCentral, return_variations
                )
                all_weights.extend(highPtmuID_SF_branches)
        if "ele" in self.to_apply:
            df, eleID_SF_branches = self.ele.getIDSF(
                df, lepton_legs, isCentral, return_variations
            )
            all_weights.extend(eleID_SF_branches)
        if "puJetID" in self.to_apply:
            df, puJetID_SF_branches = self.puJetID.getPUJetIDEff(
                df, isCentral, return_variations
            )
            all_weights.extend(puJetID_SF_branches)
        if "btagWP" in self.to_apply:
            df, bTagWP_SF_branches = self.btag.getBTagWPSF(
                df, isCentral and return_variations, isCentral
            )
            all_weights.extend(bTagWP_SF_branches)
        if "trgSF" in self.to_apply:
            df, trg_SF_branches = self.trg.getSF(
                df,
                trigger_names,
                lepton_legs,
                isCentral and return_variations,
                isCentral,
            )
            all_weights.extend(trg_SF_branches)
        if "trgEff" in self.to_apply:
            df, trg_SF_branches = self.trg.getEff(
                df, trigger_names, offline_legs, self.trigger_dict
            )
            all_weights.extend(trg_SF_branches)
        return df, all_weights


# amcatnlo problem
# https://cms-talk.web.cern.ch/t/correct-way-to-stitch-lo-w-jet-inclusive-and-jet-binned-samples/17651/3
# https://cms-talk.web.cern.ch/t/stitching-fxfx-merged-njet-binned-samples/16751/7
