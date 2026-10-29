"""Trigger corrections exist for the Run 3 eras only: `Corrections.trg` refuses any other era by
name, and builds the Run 3 producer for a Run 3 era. Needs ROOT, an importable FLAF and /cvmfs (run
inside an analysis environment, source env.sh).
"""

import os
import sys
import types
import unittest

# Import the package from the directory above, as the analyses do: run from here, the script's own
# directory would make `Corrections` resolve to Corrections.py. The path is restored afterwards so
# that test modules loaded after this one in the same run still import.
repo = os.path.dirname(os.path.abspath(__file__))
_sys_path = list(sys.path)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != repo]
sys.path.insert(0, os.path.dirname(repo))

from Corrections.Corrections import Corrections
from Corrections.CorrectionsCore import declareHeader
from Corrections.triggersRun3 import TrigCorrProducer

sys.path = _sys_path


def make_corrections(era):
    setup = types.SimpleNamespace(global_params={"era": era}, law_run_version="test")
    return Corrections(
        setup=setup,
        stage="AnaTuple",
        dataset_name="ZZZ",
        dataset_cfg={},
        process_name="VVV",
        process_cfg={},
        processors={},
        isData=False,
        trigger_class=None,
    )


class TriggerEras(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Channel and LorentzVectorM, which triggersRun3.h uses.
        declareHeader(
            os.path.join(os.environ["FLAF_PATH"], "include", "AnalysisTools.h")
        )

    def test_an_era_outside_run3_is_refused_by_name(self):
        corrections = make_corrections("Run2_2018")
        with self.assertRaisesRegex(RuntimeError, "era Run2_2018"):
            corrections.trg

    def test_a_run3_era_gets_the_run3_producer(self):
        self.assertIsInstance(make_corrections("Run3_2022").trg, TrigCorrProducer)


if __name__ == "__main__":
    unittest.main()
