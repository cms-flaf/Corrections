"""Correction providers of several eras in one process.

Every provider is an ordinary C++ object created and owned from Python (CppProvider); the C++
classes are compiled once per process, and a JIT string reaches its object through `ref`. Needs
the analysis environment (ROOT, correctionlib, FLAF_PATH) and /cvmfs.
"""

import gc
import os
import sys
import tempfile
import unittest
import weakref

# Import the package from the directory above, as the analyses do: run from here, the script's own
# directory would make `Corrections` resolve to Corrections.py. The path is restored afterwards so
# that test modules loaded after this one in the same run still import.
repo = os.path.dirname(os.path.abspath(__file__))
_sys_path = list(sys.path)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != repo]
sys.path.insert(0, os.path.dirname(repo))

import correctionlib
import ROOT

from Corrections.CorrectionsCore import (
    CppProvider,
    campaign_names,
    createTauSFTypeMap,
    createWPChannelMap,
    declareHeader,
    declareProviderHeader,
    pog_folder_names,
)
from Corrections.pu import puWeightProducer
from Corrections.tau import TauCorrProducer

sys.path = _sys_path

PU_ERAS = {
    "2022_Summer22": "Collisions2022_355100_357900_eraBCD_GoldenJson",
    "2023_Summer23": "Collisions2023_366403_369802_eraBC_GoldenJson",
}
TAU_YEARS = {"Run3_2022": "2022_preEE", "Run3_2023": "2023_preBPix"}
TAU_CONFIG = {
    "deepTauVersion": "2p5",
    "deepTauWPs": {"tauTau": {"VSe": "VVLoose", "VSmu": "Tight", "VSjet": "Medium"}},
    "genuineTau_SFtype": {"tauTau": "dm"},
}


def declare_flaf_tools():
    """LorentzVectorM, Channel and GenLeptonMatch, which tau.h uses."""
    declareHeader(os.path.join(os.environ["FLAF_PATH"], "include", "AnalysisTools.h"))


def pu_file(campaign):
    return puWeightProducer.JsonPath.format(
        folder=pog_folder_names["LUM"][campaign], suffix=""
    )


def pu_reference(campaign, n_true_int):
    cset = correctionlib.CorrectionSet.from_file(pu_file(campaign))
    return cset[PU_ERAS[campaign]].evaluate(n_true_int, "nominal")


def pu_provider(campaign):
    """The provider of a puWeightProducer, built as Corrections builds it."""
    return puWeightProducer(campaign=campaign).provider


def tau_reference(era, syst):
    """DeepTau VSjet SF of a genuine 50 GeV tau in decay mode 0, from correctionlib."""
    file = TauCorrProducer.jsonPath.format(pog_folder_names["TAU"][campaign_names[era]])
    vs_jet = correctionlib.CorrectionSet.from_file(file)["DeepTau2018v2p5VSjet"]
    return vs_jet.evaluate(50.0, 0, 5, "Medium", "VVLoose", syst, "dm")


def pu_column(df, name, provider):
    return df.Define(
        name,
        f"{provider.ref}->getWeight(::correction::UncScale::Central, Pileup_nTrueInt)",
    )


def run_pu(providers, n_true_int=30.0):
    """{name: weight} from one RDataFrame with one column per provider."""
    df = ROOT.RDataFrame(100).Define("Pileup_nTrueInt", f"{n_true_int}f")
    results = {}
    for name, provider in providers.items():
        df = pu_column(df, name, provider)
        results[name] = df.Max(name)
    return {name: result.GetValue() for name, result in results.items()}


class TwoErasInOneDataFrame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ROOT.EnableImplicitMT(4)

    @classmethod
    def tearDownClass(cls):
        ROOT.DisableImplicitMT()

    def test_each_era_gives_its_own_weight(self):
        providers = {
            "w22": pu_provider("2022_Summer22"),
            "w23": pu_provider("2023_Summer23"),
        }
        self.assertNotEqual(providers["w22"].ref, providers["w23"].ref)
        values = run_pu(providers)
        self.assertAlmostEqual(
            values["w22"], pu_reference("2022_Summer22", 30.0), places=5
        )
        self.assertAlmostEqual(
            values["w23"], pu_reference("2023_Summer23", 30.0), places=5
        )
        self.assertNotAlmostEqual(values["w22"], values["w23"], places=3)

    def test_a_later_era_leaves_an_earlier_one_alone(self):
        first = pu_provider("2022_Summer22")
        before = run_pu({"w": first})["w"]
        pu_provider("2023_Summer23")
        again = pu_provider("2022_Summer22")
        self.assertNotEqual(first.ref, again.ref)
        after = run_pu({"w": first, "w_again": again})
        self.assertEqual(after["w"], before)
        self.assertEqual(after["w_again"], before)

    def test_each_tau_producer_gives_its_own_sf(self):
        # the tau provider is constructed from a C++ argument list (CppProvider cpp_args)
        declare_flaf_tools()
        producers = {
            era: TauCorrProducer(era=era, config=TAU_CONFIG, columns={})
            for era in TAU_YEARS
        }
        self.assertNotEqual(
            producers["Run3_2022"].provider.ref, producers["Run3_2023"].provider.ref
        )
        df = ROOT.RDataFrame(100).Define("tau_p4", "LorentzVectorM(50., 0.5, 0., 1.)")
        results = {}
        for era, producer in producers.items():
            for scale, syst in (("Central", "nom"), ("Up", f"syst_{TAU_YEARS[era]}_up")):
                column = f"sf_{era}_{scale}"
                df = df.Define(
                    column,
                    f"""{producer.provider.ref}->getSF(tau_p4, 0,
                            static_cast<int>(GenLeptonMatch::Tau), "Medium", Channel::tauTau,
                            ::correction::TauCorrProvider::UncSource::syst_year,
                            ::correction::UncScale::{scale})""",
                )
                results[era, syst] = df.Max(column)
        self.assertNotAlmostEqual(
            tau_reference("Run3_2022", "nom"), tau_reference("Run3_2023", "nom"), places=3
        )
        for (era, syst), result in results.items():
            with self.subTest(era=era, syst=syst):
                self.assertAlmostEqual(
                    result.GetValue(), tau_reference(era, syst), places=5
                )


class ConstAccess(unittest.TestCase):
    HEADER = """
#pragma once
namespace correction {
    struct ConstAccessProbe {
        explicit ConstAccessProbe(float value) : value_(value) {}
        float get() const { return value_; }
        float bump() { return ++value_; }
        float value_;
    };
}
"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = os.path.join(cls.tmp.name, "const_access_probe.h")
        with open(path, "w") as f:
            f.write(cls.HEADER)
        declareHeader(path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_a_const_method_is_reachable(self):
        probe = CppProvider("correction::ConstAccessProbe", 2.5)
        df = ROOT.RDataFrame(1).Define("x", f"{probe.ref}->get()")
        self.assertEqual(df.Max("x").GetValue(), 2.5)

    def test_a_non_const_method_is_refused_when_compiled(self):
        probe = CppProvider("correction::ConstAccessProbe", 2.5)
        with self.assertRaises(Exception):
            ROOT.RDataFrame(1).Define("x", f"{probe.ref}->bump()")
        self.assertEqual(probe.obj.get(), 2.5)


class TauYearPerObject(unittest.TestCase):
    """The tau scale names carry the year of their own object, in either creation order."""

    @classmethod
    def setUpClass(cls):
        declare_flaf_tools()
        declareProviderHeader("tau.h")
        cls.wps = createWPChannelMap(
            {"tauTau": {"VSe": "VVLoose", "VSmu": "Tight", "VSjet": "Medium"}}
        )
        cls.types = createTauSFTypeMap({"tauTau": "dm"})
        cls.file = TauCorrProducer.jsonPath.format(
            pog_folder_names["TAU"]["2022_Summer22"]
        )

    def tau(self, year):
        return CppProvider(
            "correction::TauCorrProvider",
            cpp_args=f'"{self.file}", "DeepTau2018v2p5", {self.wps}, {self.types}, "{year}"',
        )

    def scale_name(self, provider):
        source = ROOT.correction.TauCorrProvider.UncSource.syst_year
        return provider.obj.getScaleStr(source, ROOT.correction.UncScale.Up)

    def test_both_orders(self):
        for years in (("2022_preEE", "2023_preBPix"), ("2023_preBPix", "2022_preEE")):
            with self.subTest(years=years):
                providers = [self.tau(year) for year in years]
                for year, provider in zip(years, providers):
                    self.assertEqual(self.scale_name(provider), f"syst_{year}_up")


class Construction(unittest.TestCase):
    def test_a_failing_constructor_names_the_class_and_the_arguments(self):
        declareProviderHeader("pu.h")
        with self.assertRaises(RuntimeError) as caught:
            CppProvider("correction::puCorrProvider", "/nonexistent/pu.json", "x")
        message = str(caught.exception)
        self.assertIn("correction::puCorrProvider", message)
        self.assertIn("/nonexistent/pu.json", message)

    def test_the_object_is_owned_by_python(self):
        self.assertTrue(pu_provider("2022_Summer22").obj.__python_owns__)

    def test_a_header_is_declared_once(self):
        declareProviderHeader("pu.h")
        hits = declareHeader.cache_info().hits
        declareProviderHeader("pu.h")
        self.assertEqual(declareHeader.cache_info().hits, hits + 1)

    def test_a_header_that_does_not_compile_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "broken.h")
            with open(path, "w") as f:
                f.write("this is not C++;\n")
            with self.assertRaises(RuntimeError):
                declareHeader(path)


class Lifetime(unittest.TestCase):
    """A provider kept only by the object that holds the dataframe stays valid through the event
    loop (Corrections instances are kept on the DataFrameWrapper for that reason)."""

    def test_the_holder_keeps_the_provider(self):
        class Holder:
            pass

        holder = Holder()
        holder.provider = pu_provider("2023_Summer23")
        alive = weakref.ref(holder.provider)
        df = ROOT.RDataFrame(10).Define("Pileup_nTrueInt", "30.f")
        df = pu_column(df, "w", holder.provider)
        result = df.Max("w")
        gc.collect()
        self.assertIsNotNone(alive())
        self.assertAlmostEqual(
            result.GetValue(), pu_reference("2023_Summer23", 30.0), places=5
        )
        del holder
        gc.collect()
        self.assertIsNone(alive())


if __name__ == "__main__":
    unittest.main()
