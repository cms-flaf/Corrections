import os
import sys

import ROOT

_initialized = False


def _declare():
    global _initialized
    if not _initialized:
        header = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf.h")
        ROOT.gInterpreter.Declare(f'#include "{header}"')
        _initialized = True


class PdfDenominatorAccumulator:
    """Inclusive sums of weight * LHEPdfWeight[k]/LHEPdfWeight[0], one per member.

    Summed over every generated event in the anaTuple denominator loop, where only the
    NanoAOD name LHEPdfWeight exists: anaTupleDef defines the renamed copy later. One
    instance may be applied to several frames; the sums accumulate across them.
    """

    def __init__(self, branch="LHEPdfWeight"):
        _declare()
        self.branch = branch
        self.accumulator = ROOT.correction.PdfDenominator()

    def available(self, df):
        return self.branch in {str(c) for c in df.GetColumnNames()}

    def apply(self, df, weight_expr, tag):
        weight_column = f"__pdf_denom_weight_{tag}"
        out_column = f"__pdf_denom_{tag}"
        df = df.Define(weight_column, f"static_cast<double>({weight_expr})")
        df = df.Define(out_column, self.accumulator, [self.branch, weight_column])
        return df, df.Sum(out_column)

    def report(self):
        sums = [float(x) for x in self.accumulator.sums()]
        if len(sums) == 0:
            return None
        return {
            "branch": self.branch,
            "n_members": len(sums),
            "sums": sums,
            "n_bad_nominal": int(self.accumulator.nBadNominal()),
            "n_size_mismatch": int(self.accumulator.nSizeMismatch()),
        }


def definePdfRelWeights(df, cfg, ana_cache):
    """Define the per-member shape-only weights at AnaTupleMerge.

    weight_pdf_rel[k] = (w[k]/w[0]) * (D_0/D_k), so summing it with weight_base over all
    events gives the nominal yield for every member and only the acceptance survives.
    """
    entry = (ana_cache or {}).get("pdf_denominator")
    if not entry:
        return df, []
    branch = cfg.get("merged_branch", "LHEPdf_Weight")
    if branch not in {str(c) for c in df.GetColumnNames()}:
        print(
            f"WARNING: '{branch}' not found; the per-member PDF weights are not stored.",
            file=sys.stderr,
        )
        return df, []

    sums = entry["sums"]
    norm = ROOT.std.vector("double")()
    n_empty = 0
    for value in sums:
        if value == 0:
            n_empty += 1
            norm.push_back(1.0)
        else:
            norm.push_back(sums[0] / value)
    if n_empty:
        print(
            f"WARNING: {n_empty} PDF members have a zero denominator; "
            "their weights are left at 1.",
            file=sys.stderr,
        )

    _declare()
    out_branch = cfg.get("output_branch", "weight_pdf_rel")
    df = df.Define(out_branch, ROOT.correction.PdfRelWeights(norm), [branch])
    return df, [out_branch]
