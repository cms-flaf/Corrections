"""JER gen matching of JetCorrectionProvider.

A jet with a gen jet inside the match cone (R/2: 0.2 for AK4, 0.4 for AK8) and within three times its
resolution is smeared by scaling, pt' = pt_gen + sf (pt - pt_gen), which is linear in the scale
factor: pt(JERUp) + pt(JERDown) = 2 pt(Central), since sf_up + sf_down = 2 sf. Inconsistent gen-jet
inputs are refused. Needs the analysis environment (ROOT, correctionlib, FLAF_PATH) and /cvmfs.
"""

import os
import subprocess
import sys
import unittest

# Import the package from the directory above, as the analyses do: run from here, the script's own
# directory would make `Corrections` resolve to Corrections.py. The path is restored afterwards so
# that test modules loaded after this one in the same run still import.
repo = os.path.dirname(os.path.abspath(__file__))
_sys_path = list(sys.path)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != repo]
sys.path.insert(0, os.path.dirname(repo))

import ROOT

from Corrections.jet import JetCorrProducer

sys.path = _sys_path

PERIOD = "2022_Summer22"
FIRST = "{::correction::JetCorrectionProvider::UncSource::"
SCALE = "::correction::UncScale::"


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
    # jet.h relies on the FLAF types declared before it.
    ROOT.gInterpreter.Declare(
        f'#include "{os.environ["FLAF_PATH"]}/include/AnalysisTools.h"'
    )


class TestJerGenMatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _setup_root()
        # Declaring jet.h before RDataFrame is loaded leaves cling unable to materialise the
        # standard-library symbols of its static initialisers.
        ROOT.RDataFrame(1)
        JetCorrProducer(PERIOD, isData=False, sample_name="TTto2L2Nu")

    def _smear(self, kind, gen_dphi, gen_args=None):
        # One jet at pt 60 GeV, |eta| 0.5; its gen jet at pt 57 GeV, displaced in phi by gen_dphi.
        df = ROOT.RDataFrame(1)
        for name, value in [
            ("pt", "RVecF{60.f}"),
            ("eta", "RVecF{0.5f}"),
            ("phi", "RVecF{1.0f}"),
            ("mass", "RVecF{8.f}"),
            ("rawFactor", "RVecF{0.05f}"),
            ("area", "RVecF{0.5f}"),
            ("gen_pt", "RVecF{57.f}"),
            ("gen_eta", "RVecF{0.5f}"),
            ("gen_phi", f"RVecF{{{1.0 + gen_dphi}f}}"),
            ("gen_idx", "ROOT::VecOps::RVec<int>{0}"),
        ]:
            df = df.Define(f"j_{name}", value)
        gen = gen_args or "j_gen_pt, j_gen_eta, j_gen_phi, j_gen_idx"
        df = df.Define(
            "m",
            f"::correction::JetCorrectionProvider::getGlobal().getShiftedP4_{kind}(j_pt, j_eta, j_phi, j_mass,"
            " j_rawFactor, j_area, 20.f, 12345, true, true, false, 1u, false, false,"
            f" {gen})",
        )
        values = {}
        for scale in ["Central", "Up", "Down"]:
            source = "Central" if scale == "Central" else "JER"
            col = f"pt_{scale}"
            df = df.Define(
                col,
                f"m.at({FIRST}{source}, {SCALE}{scale}}}).at(0).Pt()",
            )
            values[scale] = df.Take["double"](col)
        return {k: v.GetValue()[0] for k, v in values.items()}

    def _is_scaled(self, pts):
        return abs(pts["Up"] + pts["Down"] - 2 * pts["Central"]) < 1e-4

    def test_matched_ak4_jet_is_scaled(self):
        pts = self._smear("Jet", 0.05)
        self.assertTrue(self._is_scaled(pts), pts)
        self.assertNotAlmostEqual(pts["Up"], pts["Down"], places=3)

    def test_ak4_jet_outside_its_cone_is_not_scaled(self):
        self.assertFalse(self._is_scaled(self._smear("Jet", 0.3)))

    def test_ak8_jet_matches_within_the_wider_cone(self):
        self.assertTrue(self._is_scaled(self._smear("FatJet", 0.3)))

    def test_ak8_jet_outside_its_cone_is_not_scaled(self):
        self.assertFalse(self._is_scaled(self._smear("FatJet", 0.5)))

    def test_inconsistent_gen_inputs_are_refused(self):
        # The argument layout of the past: the jet's gen index in place of gen eta, no gen phi.
        with self.assertRaises(Exception) as ctx:
            self._smear(
                "Jet", 0.05, gen_args="j_gen_pt, RVecF{0.f, 1.f}, RVecF{}, RVecI{}"
            )
        self.assertIn("inconsistent gen-jet inputs", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
