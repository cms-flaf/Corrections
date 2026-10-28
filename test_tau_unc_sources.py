"""The uncertainty sources of TauCorrProvider, for the producer of every era of tau.py:

- every UncSource enumerator has a value of its own (two enumerators with one value are one source in
  C++: `stat1_dm1` once had the value of `stat2_dm0`, so its variation evaluated `stat2_dm0`,
  cms-flaf/FLAF#349);
- every key getScaleStr builds for the sources an era uses is a `syst` key of that era's DeepTau VSjet
  JSON, except the KNOWN_MISSING ones, which are checked to be still absent;
- getSF of each stat{1,2}_dm* source on a genuine tau equals the JSON with that source's key for the
  decay mode the source covers, and the nominal SF for the other decay modes.

Needs the analysis environment (ROOT, correctionlib, FLAF_PATH) and /cvmfs.
"""

import collections
import gzip
import json
import os
import sys
import unittest

# Import the package from the directory above, as test_multi_era.py does.
repo = os.path.dirname(os.path.abspath(__file__))
_sys_path = list(sys.path)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != repo]
sys.path.insert(0, os.path.dirname(repo))

import correctionlib
import ROOT

from Corrections.CorrectionsCore import (
    campaign_names,
    central,
    declareHeader,
    pog_folder_names,
)
from Corrections.tau import TauCorrProducer, era_in_tau_json

sys.path = _sys_path

CONFIG = {
    "deepTauVersion": "2p5",
    "deepTauWPs": {"tauTau": {"VSe": "VVLoose", "VSmu": "Tight", "VSjet": "Medium"}},
    "genuineTau_SFtype": {"tauTau": "dm"},
}
VS_JET = "DeepTau2018v2p5VSjet"
GENUINE_TAU = 5
PT = 40.0  # below 140 GeV, so the SF comes from the DM-binned part of the JSON

# (era, source) pairs whose getScaleStr keys the era's VSjet JSON does not have. The `syst` category
# default then gives the nominal SF, so these sources do not vary: a known latent defect outside
# cms-flaf/FLAF#349, reported separately. The JSONs name the DM-split systematics
# syst_TES_<year>_dm<N>_*, have no total_*, the 2016 year strings of era_in_tau_json are swapped with
# respect to the files read, and the 2024 JSON has a single high-pT bin.
DM_BINNED_ERAS = (
    "Run2_2016_HIPM",
    "Run2_2016",
    "Run2_2017",
    "Run2_2018",
    "Run3_2022",
    "Run3_2022EE",
    "Run3_2023",
    "Run3_2023BPix",
)
KNOWN_MISSING = (
    {
        (era, source)
        for era in DM_BINNED_ERAS
        for source in (
            "syst_year_dm0",
            "syst_year_dm1",
            "syst_year_dm10",
            "syst_year_dm11",
            "total",
        )
    }
    | {("Run2_2016_HIPM", "syst_year"), ("Run2_2016", "syst_year")}
    | {("Run3_2024", "stat_highpT_bin2")}
)

# The decay modes of a genuine tau that each stat source shifts (DM 2 is SF-binned with DM 1).
STAT_SOURCE_DMS = {
    f"stat{i}_dm{dm}": dms
    for i in (1, 2)
    for dm, dms in ((0, (0,)), (1, (1, 2)), (10, (10,)), (11, (11,)))
}
DECAY_MODES = (0, 1, 2, 10, 11)


def tau_json(era):
    return TauCorrProducer.jsonPath.format(pog_folder_names["TAU"][campaign_names[era]])


def vs_jet_syst_keys(file):
    """Every key of the `syst` categories of the VSjet correction, read from the JSON itself."""
    with gzip.open(file, "rt") as f:
        corrections = json.load(f)["corrections"]
    (vs_jet,) = [c for c in corrections if c["name"] == VS_JET]
    keys = set()
    nodes = [vs_jet["data"]]
    while nodes:
        node = nodes.pop()
        if isinstance(node, dict):
            if node.get("nodetype") == "category" and node.get("input") == "syst":
                keys.update(item["key"] for item in node["content"])
            nodes.extend(node.values())
        elif isinstance(node, list):
            nodes.extend(node)
    return keys


def vs_jet_reference(vs_jet, dm, syst):
    """The SF of a genuine tau of PT and decay mode `dm`, from correctionlib."""
    wp_vs_e = CONFIG["deepTauWPs"]["tauTau"]["VSe"]
    return vs_jet.evaluate(PT, dm, GENUINE_TAU, "Medium", wp_vs_e, syst, "dm")


class TauUncSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declareHeader(
            os.path.join(os.environ["FLAF_PATH"], "include", "AnalysisTools.h")
        )
        cls.producers = {
            era: TauCorrProducer(era=era, config=CONFIG, columns={})
            for era in era_in_tau_json
        }
        cls.Source = ROOT.correction.TauCorrProvider.UncSource
        cls.Scale = ROOT.correction.UncScale

    def test_every_source_has_its_own_value(self):
        constants = ROOT.TEnum.GetEnum(
            "correction::TauCorrProvider::UncSource"
        ).GetConstants()
        values = {c.GetName(): c.GetValue() for c in constants}
        used = (
            [central]
            + TauCorrProducer.energyScaleSources_tau
            + TauCorrProducer.energyScaleSources_lep
            + TauCorrProducer.SFSources_tau
            + TauCorrProducer.SFSources_genuineLep
        )
        self.assertLessEqual(set(used), set(values))
        names_by_value = collections.defaultdict(list)
        for name, value in values.items():
            names_by_value[value].append(name)
        shared = {v: names for v, names in names_by_value.items() if len(names) > 1}
        self.assertEqual(shared, {})

    def test_scale_names_are_json_keys(self):
        used = set()
        for era, producer in self.producers.items():
            json_keys = vs_jet_syst_keys(tau_json(era))
            self.assertTrue(json_keys)
            for source in producer.sf_sources_tau:
                used.add((era, source))
                for scale in ("Up", "Down"):
                    key = str(
                        producer.provider.obj.getScaleStr(
                            getattr(self.Source, source), getattr(self.Scale, scale)
                        )
                    )
                    with self.subTest(era=era, source=source, scale=scale, key=key):
                        if (era, source) in KNOWN_MISSING:
                            self.assertNotIn(key, json_keys)
                        else:
                            self.assertIn(key, json_keys)
        # a known-missing source that an era no longer uses has to leave KNOWN_MISSING as well
        self.assertEqual(KNOWN_MISSING - used, set())

    def test_stat_sources_shift_their_own_decay_mode(self):
        p4 = ROOT.LorentzVectorM(PT, 0.5, 0.0, 1.0)
        checked = set()
        for era, producer in self.producers.items():
            sources = [s for s in producer.sf_sources_tau if s in STAT_SOURCE_DMS]
            vs_jet = correctionlib.CorrectionSet.from_file(tau_json(era))[VS_JET]
            for source in sources:
                for dm in DECAY_MODES:
                    nominal = vs_jet_reference(vs_jet, dm, "nom")
                    for scale in ("Up", "Down"):
                        with self.subTest(era=era, source=source, dm=dm, scale=scale):
                            sf = producer.provider.obj.getSF(
                                p4,
                                dm,
                                GENUINE_TAU,
                                "Medium",
                                ROOT.Channel.tauTau,
                                getattr(self.Source, source),
                                getattr(self.Scale, scale),
                            )
                            if dm in STAT_SOURCE_DMS[source]:
                                expected = vs_jet_reference(
                                    vs_jet, dm, f"{source}_{scale.lower()}"
                                )
                                # a key that does not shift this DM would make the check vacuous
                                self.assertNotAlmostEqual(expected, nominal, places=5)
                            else:
                                expected = nominal
                            self.assertAlmostEqual(sf, expected, places=5)
                checked.add(source)
        self.assertEqual(checked, set(STAT_SOURCE_DMS))


if __name__ == "__main__":
    unittest.main()
