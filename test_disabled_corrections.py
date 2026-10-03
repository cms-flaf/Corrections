"""Disabled corrections and the stage rule of the shape weights.

A dataset switches corrections off with `disabled_corrections`, per NanoAOD source: none of them
is in to_apply. A disabled shape weight keeps its branches with every member 1 (its branches and
denominators have to exist for every dataset of a process). A shape weight is computed at
AnaTuple and read back at its later stages. Needs ROOT and an importable FLAF (run inside an
analysis environment, source env.sh).
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

GLOBAL_PARAMS = {
    "era": "Run3_2022",
    "nanoAODVersions": {"data": "22Sep23", "mc": "v12"},
    "corrections": {
        "JEC": {"stage": "AnaTuple"},
        "pdf": {
            "stages": ["AnaTuple", "AnaTupleMerge"],
            "branch": "LHEPdfWeight",
            "n_members": 103,
        },
        "parton_shower": {
            "stages": ["AnaTuple", "AnaTupleMerge"],
            "branch": "PSWeight",
        },
        "qcd_scale": {
            "stages": ["AnaTuple", "AnaTupleMerge"],
            "branch": "LHEScaleWeight",
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


def shape_weights(corrections):
    df = (
        ROOT.RDataFrame(3)
        .Define("LHEPdfWeight", "ROOT::RVecF(103, 0.5f + 0.25f * rdfentry_)")
        .Define("PSWeight", "ROOT::RVecF{0.9f, 1.1f, 0.8f, 1.2f}")
        .Define(
            "LHEScaleWeight",
            "ROOT::RVecF{1.1f, 1.2f, 1.3f, 0.9f, 0.5f, 1.1f, 0.8f, 0.9f, 1.f}",
        )
    )
    df, branches = corrections.defineShapeWeights(df)
    return {b: list(df.Take["float"](b).GetValue()) for b in branches}


def registered(corrections):
    from Corrections.CorrectionsCore import ShapeWeightRegistry

    return set(corrections.registerShapeWeights(ShapeWeightRegistry()).asDict())


class TestDisabledCorrections(unittest.TestCase):
    def test_disabled_corrections_are_not_applied(self):
        corrections = make_corrections(
            {"disabled_corrections": {"v12": ["pdf", "parton_shower", "JEC"]}}
        )
        self.assertEqual(set(corrections.to_apply), {"qcd_scale"})
        self.assertEqual(
            {name: mode for name, (mode, _) in corrections.shape_weights.items()},
            {"pdf": "unit", "parton_shower": "unit", "qcd_scale": "compute"},
        )
        weights = shape_weights(corrections)
        self.assertEqual(
            len([b for b in weights if "qcd_scale" not in b]), (1 + 103) + (1 + 4)
        )
        for branch, values in weights.items():
            if "qcd_scale" not in branch:
                self.assertEqual(values, [1.0, 1.0, 1.0], branch)

    def test_enabled_dataset_computes_the_weights(self):
        corrections = make_corrections({})
        self.assertEqual(
            set(corrections.to_apply), {"JEC", "pdf", "parton_shower", "qcd_scale"}
        )
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

    def test_merge_stage_reads_back(self):
        # Computed at AnaTuple only; later stages register the branches to read them back,
        # for a dataset that disables the weights as for one that does not.
        for cfg in [{}, {"disabled_corrections": {"v12": ["pdf", "parton_shower"]}}]:
            with self.subTest(cfg=cfg):
                corrections = make_corrections(cfg, stage="AnaTupleMerge")
                self.assertEqual(shape_weights(corrections), {})
                self.assertIn(("pdf", "37"), registered(corrections))
                self.assertIn(("isr", "Up"), registered(corrections))

    def test_unconfigured_shape_weight_is_a_no_op(self):
        params = copy.deepcopy(GLOBAL_PARAMS)
        del params["corrections"]["parton_shower"]
        corrections = make_corrections(
            {"disabled_corrections": {"v12": ["parton_shower"]}}, global_params=params
        )
        self.assertNotIn("parton_shower", corrections.shape_weights)
        self.assertEqual(shape_weights(corrections)["weight_pdf_37"], [0.5, 0.75, 1.0])

    def test_qcd_scale_carries_the_nominal_without_pdf(self):
        # The nominal scale weight (entry 4) enters weight_base once: through pdf's Central
        # when pdf is computed, through qcd_scale's Central when the dataset disables pdf.
        weights = shape_weights(make_corrections({}))
        self.assertEqual(weights["weight_qcd_scale_Central"], [1.0, 1.0, 1.0])
        weights = shape_weights(
            make_corrections({"disabled_corrections": {"v12": ["pdf"]}})
        )
        self.assertEqual(weights["weight_qcd_scale_Central"], [0.5, 0.5, 0.5])

    def test_unknown_name_is_refused(self):
        with self.assertRaisesRegex(RuntimeError, r"unknown corrections: \['pfd'\]"):
            make_corrections({"disabled_corrections": {"v12": ["pfd"]}})

    def test_enabled_option_is_refused(self):
        params = copy.deepcopy(GLOBAL_PARAMS)
        params["corrections"]["pdf"]["enabled"] = {
            "AnaTuple": True,
            "AnaTupleMerge": False,
        }
        with self.assertRaisesRegex(RuntimeError, "'enabled' is no longer an option"):
            make_corrections({}, global_params=params)

    def test_shape_weight_needs_the_anatuple_stage(self):
        params = copy.deepcopy(GLOBAL_PARAMS)
        params["corrections"]["pdf"]["stages"] = ["AnaTupleMerge"]
        with self.assertRaisesRegex(RuntimeError, "stages must include AnaTuple"):
            make_corrections({}, global_params=params)


if __name__ == "__main__":
    unittest.main()
