"""The light-jet variation clamp of bTagShapeCorrProvider (btag.py: shape_variation_min_pt_light).

In the Summer23BPix BTV shape file the light-jet pT binning starts at 30 GeV: a 20-30 GeV light jet gets
the 30-50 GeV central but, through the variations' flow, their >200 GeV content. With the clamp the
lf/hf/lf-hfstats variations of such a jet are evaluated at 30 GeV, the bin of its central; nothing else
changes: central, b and c jets, the JES-varied scale factors, jets at or above 30 GeV, and every other
campaign. Needs the analysis environment (ROOT, correctionlib, FLAF_PATH) and /cvmfs.
"""

import os
import subprocess
import sys
import unittest

# Import the package from the directory above, as the analyses do (see test_jer_gen_match.py).
repo = os.path.dirname(os.path.abspath(__file__))
_sys_path = list(sys.path)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != repo]
sys.path.insert(0, os.path.dirname(repo))

import ROOT
import correctionlib

from FLAF.Common.Utilities import WorkingPointsbTag, generate_enum_class
from Corrections.btag import bTagCorrProducer
from Corrections.CorrectionsCore import pog_folder_names

sys.path = _sys_path

SOURCES = ["lf", "hf", "lfstats1", "lfstats2", "hfstats1", "hfstats2"]
ETA, SCORE = 1.0, 0.03


def _setup_root():
    flags = subprocess.run(
        ["correction", "config", "--cflags", "--ldflags"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    lib_dir, lib_name = None, None
    for flag in flags:
        if flag.startswith("-I"):
            ROOT.gInterpreter.AddIncludePath(flag[2:])
        elif flag.startswith("-L"):
            lib_dir = flag[2:]
        elif flag.startswith("-l"):
            lib_name = flag[2:]
    ROOT.gSystem.Load(os.path.join(lib_dir, f"lib{lib_name}.so"))
    # what FLAF declares before a correction provider is built (Common/Utilities.py)
    ROOT.gInterpreter.Declare("#include <TH2.h>")
    for header in ("RootExt.h", "AnalysisTools.h", "exception.h"):
        ROOT.gInterpreter.Declare(
            f'#include "{os.environ["FLAF_PATH"]}/include/{header}"'
        )
    # btag.h uses the working-point enum FLAF declares from its Python definition
    ROOT.gInterpreter.Declare(generate_enum_class(WorkingPointsbTag))


class TestBtagShapeLightJetClamp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _setup_root()
        ROOT.RDataFrame(1)
        cls.btag = {
            c: bTagCorrProducer(campaign=c, jetCollection="centralJet", wantShape=True)
            for c in ("2023_Summer23BPix", "2023_Summer23")
        }
        cls.file = {
            c: correctionlib.CorrectionSet.from_file(
                bTagCorrProducer.jsonPath.format(pog_folder_names["BTV"][c])
            )["particleNet_shape"]
            for c in cls.btag
        }

    def _provider(self, campaign, pt, flavour, source, scale):
        """The provider's SF of one jet, as the analyses call it."""
        df = ROOT.RDataFrame(1)
        df = df.Define("p4", f"RVecLV{{LorentzVectorM({pt}, {ETA}, 0., 5.)}}")
        df = df.Define("flav", f"ROOT::VecOps::RVec<int>{{{flavour}}}")
        df = df.Define("score", f"RVecF{{{SCORE}f}}")
        df = df.Define(
            "sf",
            f"{self.btag[campaign].shape_provider.ref}->getBTagShapeSF(p4, flav, score, "
            f"::correction::bTagShapeCorrProvider::UncSource::{source}, "
            f"::correction::UncScale::{scale})",
        )
        return float(df.Take["float"]("sf").GetValue()[0])

    def _file(self, campaign, name, pt, flavour):
        return self.file[campaign].evaluate(name, flavour, ETA, pt, SCORE)

    def test_2023bpix_light_jet_variations_take_the_central_bin(self):
        for s in SOURCES:
            for scale, key in (("Up", "up"), ("Down", "down")):
                got = self._provider("2023_Summer23BPix", 25.0, 0, s, scale)
                self.assertAlmostEqual(
                    got,
                    self._file("2023_Summer23BPix", f"{key}_{s}", 30.0, 0),
                    places=5,
                    msg=s,
                )
                # without the clamp the file gives the >200 GeV value here
                self.assertNotAlmostEqual(
                    got,
                    self._file("2023_Summer23BPix", f"{key}_{s}", 25.0, 0),
                    places=3,
                    msg=s,
                )

    def test_2023bpix_light_jet_variations_bracket_central(self):
        central = self._provider("2023_Summer23BPix", 25.0, 0, "Central", "Central")
        for s in SOURCES:
            up = self._provider("2023_Summer23BPix", 25.0, 0, s, "Up") / central
            down = self._provider("2023_Summer23BPix", 25.0, 0, s, "Down") / central
            self.assertLessEqual(
                (up - 1) * (down - 1), 1e-6, msg=f"{s}: {up:.4f} / {down:.4f}"
            )

    def test_unchanged_elsewhere(self):
        cases = [
            ("2023_Summer23BPix", 25.0, 0, "Central", "Central", "central"),  # central
            (
                "2023_Summer23BPix",
                40.0,
                0,
                "lf",
                "Up",
                "up_lf",
            ),  # light jet above 30 GeV
            ("2023_Summer23BPix", 25.0, 5, "lf", "Up", "up_lf"),  # b jet
            ("2023_Summer23BPix", 25.0, 4, "cferr1", "Up", "up_cferr1"),  # c jet
            ("2023_Summer23BPix", 25.0, 0, "jesTotal", "Up", "up_jes"),  # JES-varied SF
            ("2023_Summer23", 25.0, 0, "lf", "Up", "up_lf"),  # another campaign
            ("2023_Summer23", 25.0, 0, "hfstats1", "Down", "down_hfstats1"),
        ]
        for campaign, pt, flavour, source, scale, name in cases:
            got = self._provider(campaign, pt, flavour, source, scale)
            self.assertAlmostEqual(
                got,
                self._file(campaign, name, pt, flavour),
                places=5,
                msg=(campaign, pt, flavour, name),
            )

    def test_only_2023bpix_is_clamped(self):
        self.assertEqual(
            bTagCorrProducer.shape_variation_min_pt_light, {"2023_Summer23BPix": 30.0}
        )

    def test_clamp_refused_on_a_file_with_a_light_jet_bin_below(self):
        # Summer23 has a 20-30 GeV light-jet bin: clamping there would replace it, so the provider refuses
        path = bTagCorrProducer.jsonPath.format(
            pog_folder_names["BTV"]["2023_Summer23"]
        )
        with self.assertRaises(Exception) as ctx:
            ROOT.correction.bTagShapeCorrProvider(
                path, "2023", "particleNet", True, 30.0
            )
        self.assertIn("no longer applies", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
