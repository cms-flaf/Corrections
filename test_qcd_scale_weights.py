import math
import os
import unittest

import ROOT

_HEADER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qcd_scale.h")
ROOT.gInterpreter.Declare(f'#include "{_HEADER}"')


def _vec(values):
    out = ROOT.ROOT.VecOps.RVec("float")()
    for value in values:
        out.push_back(float(value))
    return out


class TestQcdScaleWeights(unittest.TestCase):
    def test_nine_entries_are_read_at_their_own_index(self):
        # [4] is deliberately not 1: the nine-entry nominal must be taken as stored.
        stored = [0.5, 0.6, 0.7, 0.8, 0.2, 1.1, 1.2, 1.3, 1.4]
        weights = _vec(stored)
        for index, value in enumerate(stored):
            self.assertAlmostEqual(
                ROOT.correction.qcdScaleWeight(weights, index), value
            )
        self.assertAlmostEqual(
            ROOT.correction.qcdScaleNormalisedWeight(weights, 5), 1.1 / 0.2
        )

    def test_eight_entries_omit_the_nominal_and_shift_the_rest(self):
        # Stored order after dropping (muR, muF) = (1, 1): nine-scheme 0,1,2,3,5,6,7,8.
        stored = [10.0, 11.0, 12.0, 13.0, 15.0, 16.0, 17.0, 18.0]
        weights = _vec(stored)
        expected = {
            0: 10.0,
            1: 11.0,
            2: 12.0,
            3: 13.0,
            5: 15.0,
            6: 16.0,
            7: 17.0,
            8: 18.0,
        }
        for index, value in expected.items():
            self.assertAlmostEqual(
                ROOT.correction.qcdScaleWeight(weights, index), value
            )
        self.assertEqual(ROOT.correction.qcdScaleWeight(weights, 4), 1.0)
        # pdf already applies the nominal, so the normalised member is the stored one.
        self.assertAlmostEqual(
            ROOT.correction.qcdScaleNormalisedWeight(weights, 5), 15.0
        )

    def test_other_lengths_and_bad_values_throw(self):
        def fails(call):
            with self.assertRaises(Exception):
                call()

        fails(lambda: ROOT.correction.qcdScaleWeight(_vec([1, 2, 3, 4, 5, 6, 7]), 0))
        fails(lambda: ROOT.correction.qcdScaleWeight(_vec([]), 0))
        fails(lambda: ROOT.correction.qcdScaleWeight(_vec([1] * 9), 9))
        fails(
            lambda: ROOT.correction.qcdScaleWeight(
                _vec([1, 1, 1, 1, math.nan, 1, 1, 1, 1]), 4
            )
        )
        fails(
            lambda: ROOT.correction.qcdScaleNormalisedWeight(
                _vec([1, 1, 1, 1, 0, 1, 1, 1, 1]), 0
            )
        )
        # The shifted slot of an eight-entry vector is still checked, and the
        # synthetic nominal is not.
        shifted = _vec([1, 1, 1, 1, math.nan, 1, 1, 1])
        fails(lambda: ROOT.correction.qcdScaleWeight(shifted, 5))
        self.assertEqual(ROOT.correction.qcdScaleWeight(shifted, 4), 1.0)


if __name__ == "__main__":
    unittest.main()
