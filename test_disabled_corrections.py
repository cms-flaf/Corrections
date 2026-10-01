"""A dataset can switch corrections off with `disabled_corrections`, per NanoAOD source.

A shape weight stays registered with every member 1 (its branches and denominators have to
exist for every dataset of a process); any other correction is not applied. Needs ROOT and an
importable FLAF (run inside an analysis environment, source env.sh).
"""

import copy
import os
import sys
import types
import unittest

# Import the package from the directory above, as the analyses do: run from here, the script's own
# directory would make `Corrections` resolve to Corrections.py.
repo = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != repo]
sys.path.insert(0, os.path.dirname(repo))

import ROOT

from Corrections.Corrections import Corrections

STAGED = {"AnaTuple": True, "AnaTupleMerge": False}
GLOBAL_PARAMS = {
    "era": "Run3_2022",
    "nanoAODVersions": {"data": "22Sep23", "mc": "v12"},
    "corrections": {
        "JEC": {"stage": "AnaTuple"},
        "pdf": {
            "stages": ["AnaTuple", "AnaTupleMerge"],
            "branch": "LHEPdfWeight",
            "n_members": 103,
            "enabled": STAGED,
        },
        "parton_shower": {
            "stages": ["AnaTuple", "AnaTupleMerge"],
            "branch": "PSWeight",
            "enabled": STAGED,
        },
    },
}


def make_corrections(dataset_cfg, stage="AnaTuple", global_params=GLOBAL_PARAMS):
    setup = types.SimpleNamespace(global_params=global_params, law_run_version="test")
    return Corrections(
        setup=setup,
        stage=stage,
        dataset_name="ZZZ",
        dataset_cfg=dataset_cfg,
        process_name="VVV",
        process_cfg={},
        processors={},
        isData=False,
        trigger_class=None,
    )


def shape_weights(corrections, respect_enabled=True):
    df = (
        ROOT.RDataFrame(3)
        .Define("LHEPdfWeight", "ROOT::RVecF(103, 0.5f + 0.25f * rdfentry_)")
        .Define("PSWeight", "ROOT::RVecF{0.9f, 1.1f, 0.8f, 1.2f}")
    )
    df, branches = corrections.defineShapeWeights(df, respect_enabled=respect_enabled)
    return {b: list(df.Take["float"](b).GetValue()) for b in branches}


class TestDisabledCorrections(unittest.TestCase):
    def test_disabled_shape_weights_have_unit_members(self):
        corrections = make_corrections(
            {"disabled_corrections": {"v12": ["pdf", "parton_shower", "JEC"]}}
        )
        self.assertIn("pdf", corrections.to_apply)
        self.assertIn("parton_shower", corrections.to_apply)
        self.assertNotIn("JEC", corrections.to_apply)
        weights = shape_weights(corrections)
        self.assertEqual(len(weights), (1 + 103) + (1 + 4))
        for branch, values in weights.items():
            self.assertEqual(values, [1.0, 1.0, 1.0], branch)

    def test_enabled_dataset_reads_the_weights(self):
        corrections = make_corrections({})
        self.assertIn("JEC", corrections.to_apply)
        weights = shape_weights(corrections)
        self.assertEqual(weights["weight_pdf_37"], [0.5, 0.75, 1.0])
        self.assertNotEqual(weights["weight_ps_isrUp"], [1.0, 1.0, 1.0])

    def test_other_source_is_not_disabled(self):
        # The dataset is read from DAS v12 here: the HLepRare entry does not apply.
        corrections = make_corrections({"disabled_corrections": {"HLepRare": ["pdf"]}})
        self.assertEqual(shape_weights(corrections)["weight_pdf_37"], [0.5, 0.75, 1.0])
        params = copy.deepcopy(GLOBAL_PARAMS)
        del params["nanoAODVersions"]
        corrections = make_corrections(
            {"disabled_corrections": {"HLepRare": ["pdf"]}}, global_params=params
        )
        self.assertEqual(shape_weights(corrections)["weight_pdf_37"], [1.0, 1.0, 1.0])

    def test_merge_stage_defines_nothing_unless_asked(self):
        cfg = {"disabled_corrections": {"v12": ["pdf", "parton_shower"]}}
        corrections = make_corrections(cfg, stage="AnaTupleMerge")
        self.assertEqual(shape_weights(corrections), {})
        weights = shape_weights(corrections, respect_enabled=False)
        self.assertEqual(len(weights), (1 + 103) + (1 + 4))
        self.assertTrue(all(v == [1.0, 1.0, 1.0] for v in weights.values()))

    def test_unconfigured_shape_weight_is_a_no_op(self):
        params = copy.deepcopy(GLOBAL_PARAMS)
        del params["corrections"]["parton_shower"]
        corrections = make_corrections(
            {"disabled_corrections": {"v12": ["parton_shower"]}}, global_params=params
        )
        self.assertNotIn("parton_shower", corrections.to_apply)
        self.assertEqual(shape_weights(corrections)["weight_pdf_37"], [0.5, 0.75, 1.0])

    def test_unknown_name_is_refused(self):
        with self.assertRaisesRegex(RuntimeError, r"unknown corrections: \['pfd'\]"):
            make_corrections({"disabled_corrections": {"v12": ["pfd"]}})


if __name__ == "__main__":
    unittest.main()
