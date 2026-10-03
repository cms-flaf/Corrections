"""EleCorrProvider scale and smearing against the EGM recipe, evaluated with correctionlib.

Needs the analysis environment (ROOT, correctionlib, FLAF_PATH) and /cvmfs/cms-griddata.cern.ch.
"""

import os
import subprocess
import unittest

import correctionlib
import numpy as np
import ROOT

_HERE = os.path.dirname(os.path.abspath(__file__))
_EGM = "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/latest"
_ID_FILE = f"{_EGM}/electron.json.gz"
_SS_FILE = f"{_EGM}/electronSS_EtDependent.json.gz"
_RUN = 380001


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
    # electron.h relies on the FLAF types (LorentzVectorM, GenLeptonMatch) declared before it.
    ROOT.gInterpreter.Declare(
        f'#include "{os.environ["FLAF_PATH"]}/include/AnalysisTools.h"'
    )
    ROOT.gInterpreter.Declare(f'#include "{os.path.join(_HERE, "electron.h")}"')
    ROOT.gInterpreter.ProcessLine(
        f'::correction::EleCorrProvider::Initialize("{_ID_FILE}", "{_SS_FILE}", "Electron-ID-SF", "SmearAndSyst")'
    )


def _p4s(electrons):
    out = ROOT.ROOT.VecOps.RVec(
        "ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double> >"
    )()
    for pt, eta, phi in electrons:
        out.push_back(
            ROOT.Math.LorentzVector("ROOT::Math::PtEtaPhiM4D<double>")(
                pt, eta, phi, 0.000511
            )
        )
    return out


def _vec(kind, values):
    out = ROOT.ROOT.VecOps.RVec(kind)()
    for value in values:
        out.push_back(value)
    return out


class TestElectronScaleAndSmearing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _setup_root()
        cls.provider = ROOT.correction.EleCorrProvider.getGlobal()
        cset = correctionlib.CorrectionSet.from_file(_SS_FILE)
        cls.scale = cset.compound["Scale"]
        cls.smear = cset["SmearAndSyst"]
        cls.Source = ROOT.correction.EleCorrProvider.UncSource
        cls.Scale = ROOT.correction.UncScale
        # pt, eta, phi; r9 at 0.98 falls in the high-r9 bin only if it is read as a float.
        cls.electrons = [(40.0, 0.5, 0.1), (25.0, -1.2, 2.0), (12.0, 0.3, -1.0)]
        # NanoAOD stores both as float32, so the reference is evaluated at the float32 values;
        # none of them sits on a bin edge.
        cls.sc_eta = [float(np.float32(x)) for x in [0.52, -1.21, 0.31]]
        cls.r9 = [float(np.float32(x)) for x in [0.98, 0.93, 0.95]]
        cls.gain = [12, 12, 6]
        cls.event = (1, 7, 123456789)

    def _random(self, index):
        run, lumi, event = self.event
        return ROOT.TRandom3(
            ROOT.correction.electronSmearingSeed(run, lumi, event, index)
        ).Gaus(0.0, 1.0)

    def _mc(self, source, scale, event=None):
        run, lumi, evt = event or self.event
        return self.provider.getESEtDep_MC(
            _p4s(self.electrons),
            _vec("float", self.sc_eta),
            run,
            lumi,
            evt,
            _vec("float", self.r9),
            source,
            scale,
        )

    def test_data_gets_the_scale(self):
        out = self.provider.getESEtDep_data(
            _p4s(self.electrons),
            _vec("unsigned char", self.gain),
            _vec("float", self.sc_eta),
            _RUN,
            _vec("float", self.r9),
        )
        for n, (pt, eta, phi) in enumerate(self.electrons):
            expected = pt
            if pt >= 15:
                expected *= self.scale.evaluate(
                    "scale",
                    float(_RUN),
                    self.sc_eta[n],
                    self.r9[n],
                    pt,
                    float(self.gain[n]),
                )
            self.assertAlmostEqual(out[n].pt(), expected, places=9)
            self.assertAlmostEqual(out[n].eta(), eta, places=12)
            self.assertAlmostEqual(out[n].phi(), phi, places=12)

    def test_r9_is_read_as_a_float(self):
        # Through RDataFrame, as electron.py calls it: a float r9 column bound to an integer RVec
        # parameter would compile and truncate 0.98 to 0, i.e. the low-r9 width.
        pt, eta, phi = self.electrons[0]
        high = self.smear.evaluate("smear", pt, self.r9[0], self.sc_eta[0])
        low = self.smear.evaluate("smear", pt, 0.0, self.sc_eta[0])
        self.assertNotAlmostEqual(high, low, places=6)
        run, lumi, event = self.event
        df = (
            ROOT.RDataFrame(1)
            .Define(
                "Electron_p4_nano",
                f"RVecLV{{LorentzVectorM({pt}, {eta}, {phi}, 0.000511)}}",
            )
            .Define("Electron_superclusterEta", f"RVecF{{{self.sc_eta[0]}f}}")
            .Define("Electron_r9", f"RVecF{{{self.r9[0]}f}}")
            .Define("run", f"static_cast<UInt_t>({run})")
            .Define("luminosityBlock", f"static_cast<UInt_t>({lumi})")
            .Define("event", f"static_cast<ULong64_t>({event})")
            .Define(
                "pt_out",
                "::correction::EleCorrProvider::getGlobal().getESEtDep_MC(Electron_p4_nano, Electron_superclusterEta,"
                " run, luminosityBlock, event, Electron_r9, ::correction::EleCorrProvider::UncSource::Central,"
                " ::correction::UncScale::Central)[0].pt()",
            )
        )
        out = df.Take["double"]("pt_out").GetValue()[0]
        self.assertAlmostEqual(out, pt * (1 + high * self._random(0)), places=9)

    def test_mc_nominal_is_smeared(self):
        out = self._mc(self.Source.Central, self.Scale.Central)
        for n, (pt, _, _) in enumerate(self.electrons):
            expected = pt
            if pt >= 15:
                width = self.smear.evaluate("smear", pt, self.r9[n], self.sc_eta[n])
                expected = pt * (1 + width * self._random(n))
            self.assertAlmostEqual(out[n].pt(), expected, places=9)

    def test_mc_variations_share_the_random_number(self):
        central = self._mc(self.Source.Central, self.Scale.Central)
        for scale, smear_key, scale_key in [
            (self.Scale.Up, "smear_up", "scale_up"),
            (self.Scale.Down, "smear_down", "scale_down"),
        ]:
            smeared = self._mc(self.Source.EleSmear, scale)
            scaled = self._mc(self.Source.EleES, scale)
            for n, (pt, _, _) in enumerate(self.electrons):
                if pt < 15:
                    self.assertAlmostEqual(smeared[n].pt(), pt, places=12)
                    self.assertAlmostEqual(scaled[n].pt(), pt, places=12)
                    continue
                width = self.smear.evaluate(smear_key, pt, self.r9[n], self.sc_eta[n])
                self.assertAlmostEqual(
                    smeared[n].pt(), pt * (1 + width * self._random(n)), places=9
                )
                factor = self.smear.evaluate(scale_key, pt, self.r9[n], self.sc_eta[n])
                self.assertAlmostEqual(
                    scaled[n].pt(), factor * central[n].pt(), places=9
                )

    def test_smearing_is_deterministic_per_event(self):
        first = self._mc(self.Source.Central, self.Scale.Central)
        second = self._mc(self.Source.Central, self.Scale.Central)
        other = self._mc(
            self.Source.Central, self.Scale.Central, event=(1, 7, 123456790)
        )
        for n in range(2):
            self.assertEqual(first[n].pt(), second[n].pt())
            self.assertNotEqual(first[n].pt(), other[n].pt())


if __name__ == "__main__":
    unittest.main()
