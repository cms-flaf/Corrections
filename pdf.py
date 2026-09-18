import os
import sys

import ROOT

from .CorrectionsCore import *


class pdfWeightProducer:
    """PDF members as an indexed shape-weight source.

    PDF4LHC15 (arXiv:1510.03865) takes the spread across members of each bin of the
    fitted distribution, so the members cannot be reduced per event. Each one is a scale
    of the `pdf` source and therefore gets its own anaCache denominator and its own
    weight_base_pdf<k>_rel, the same way pileup gets one per Up/Down.

    The members are taken as stored, with no renormalisation -- see pdf.h for what that
    means for a sample whose member 0 is not 1.

    A vector shorter than the 101 base members throws, as does a non-finite weight. The
    two optional alphaS members are 0 where a sample does not carry them (the
    four-flavour-scheme samples stop at 101), which makes weight_base_pdf101/102_rel come
    out NaN for those samples rather than passing as a weight of 1.

    Rows that FuseAnaTuples padded are excluded from that check. AnaTupleMerge is the one
    stage that does not filter on `valid`, and a padded row carries an empty vector for
    every array column, so reading one would throw on data the histograms never see.

    The branch is the NanoAOD name at AnaTuple, where the denominators are summed, and
    the renamed anaTuple copy at AnaTupleMerge -- the same trap as PSWeight/PS_Weight.
    """

    initialized = False

    uncSource = ["pdf"]

    warned_missing = False

    @classmethod
    def scales(cls, cfg):
        return [str(member) for member in range(int(cfg.get("n_members", 103)))]

    @staticmethod
    def branchName(source, scale):
        if source == central:
            return "weight_pdf_Central"
        return f"weight_pdf_{scale}"

    def __init__(self, branch="LHEPdfWeight", n_members=103):
        self.branch = branch
        self.n_members = int(n_members)
        if self.n_members < 1:
            raise RuntimeError(
                f"pdfWeightProducer: n_members = {self.n_members} is not a member count."
            )
        registerSourceScales("pdf", self.scales({"n_members": self.n_members}))
        if not pdfWeightProducer.initialized:
            header = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf.h")
            ROOT.gInterpreter.Declare(f'#include "{header}"')
            pdfWeightProducer.initialized = True

    def getWeight(
        self,
        df,
        return_variations=True,
        return_list_of_branches=False,
        enabled=True,
    ):
        sf_sources = pdfWeightProducer.uncSource if return_variations else []
        branches = []

        has_input = False
        has_valid = False
        if enabled:
            columns = {str(c) for c in df.GetColumnNames()}
            if any(c.startswith("weight_pdf_") for c in columns):
                raise RuntimeError(
                    "pdfWeightProducer: weight_pdf_* columns already exist. Defining "
                    "them again would shadow the persisted values. Set enabled: false "
                    "for pdf at this stage."
                )
            has_input = self.branch in columns
            has_valid = "valid" in columns
            if not has_input and not pdfWeightProducer.warned_missing:
                pdfWeightProducer.warned_missing = True
                print(
                    f"WARNING: '{self.branch}' not found; the pdf members are all 1 for "
                    "this dataset.",
                    file=sys.stderr,
                )

        for source in [central] + sf_sources:
            for scale in getScales(source):
                branch_name = pdfWeightProducer.branchName(source, scale)
                if enabled:
                    if source == central or not has_input:
                        expr = "1.f"
                    else:
                        expr = f"::correction::pdfMemberWeight({self.branch}, {scale})"
                        if has_valid:
                            expr = f"valid ? {expr} : 0.f"
                    df = df.Define(branch_name, expr)
                    branches.append(branch_name)

        if return_list_of_branches:
            return df, branches
        return df
