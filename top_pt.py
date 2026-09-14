import sys

from .CorrectionsCore import *


class TopPtCorrProducer:
    """Top pT reweighting for SM ttbar, as a shape weight.

    https://twiki.cern.ch/twiki/bin/view/CMS/TopPtReweighting. The event weight is the
    geometric mean of the per-top SFs, and (Down, Central, Up) = (SF, 1, SF). The top pT
    is read from `branch` (TTInfo_top_pt).
    """

    uncSource = ["top_pt"]

    # Per-top SF as a C++ expression of the RVec `{pt}`. Coefficients still to be
    # cross-checked against the TWiki.
    parameterizations = {
        # ratio of data to NLO (POWHEG+PYTHIA8)
        "data_nlo": "ROOT::VecOps::exp(0.0615f - 0.0005f * ({pt}))",
        # ratio of the NNLO QCD + NLO EW prediction to NLO
        "nnlo_nlo": (
            "0.103f * ROOT::VecOps::exp(-0.0118f * ({pt}))"
            " - 0.000134f * ({pt}) + 0.973f"
        ),
    }

    warned_missing = False

    def __init__(
        self, era, *, branch="TTInfo_top_pt", parameterization="nnlo_nlo", max_pt=None
    ):
        self.era = era
        self.branch = branch

        if parameterization not in self.parameterizations:
            raise RuntimeError(
                f"TopPtCorrProducer: unknown parameterization '{parameterization}'. "
                f"Supported: {sorted(self.parameterizations.keys())}"
            )
        self.parameterization = parameterization
        self.max_pt = max_pt

    @staticmethod
    def branchName(source, scale):
        return f"weight_top_pt_{scale}"

    pt_branch = "top_pt_forWeight"
    sf_branch = "top_pt_sf"
    weight_branch = "top_pt_reweight"

    def _pt_expr(self):
        """The top pT the SF is evaluated at, clamped to max_pt when one is set."""
        pt = f"ROOT::VecOps::RVec<float>({self.branch})"
        if self.max_pt is None:
            return pt
        return f"ROOT::VecOps::Where({pt} > {float(self.max_pt)}f, {float(self.max_pt)}f, {pt})"

    def _sf_expr(self):
        """Per-top SF, clamped at zero so the geometric mean cannot become NaN."""
        sf = self.parameterizations[self.parameterization].format(pt=self.pt_branch)
        return f"ROOT::VecOps::Where(({sf}) < 0.f, 0.f, {sf})"

    def _reweight_expr(self):
        """Geometric mean of the per-top SFs; 1 if there are none."""
        return (
            f"{self.sf_branch}.empty() ? 1.0f : static_cast<float>(std::pow("
            f"ROOT::VecOps::Product({self.sf_branch}), "
            f"1.0f / static_cast<float>({self.sf_branch}.size())))"
        )

    def _central_expr(self):
        """Not applied to the nominal."""
        return "1.0f"

    def _variation_expr(self, scale):
        """Up and Down both carry the full reweighting."""
        if scale in (up, down):
            return self.weight_branch
        raise RuntimeError(f"TopPtCorrProducer: unsupported variation '{scale}'.")

    def getWeight(
        self,
        df,
        return_variations=True,
        return_list_of_branches=False,
        enabled=True,
    ):
        sf_sources = TopPtCorrProducer.uncSource if return_variations else []
        branches = []

        has_input = False
        if enabled:
            columns = {str(c) for c in df.GetColumnNames()}
            if any(c.startswith("weight_top_pt_") for c in columns):
                raise RuntimeError(
                    "TopPtCorrProducer: weight_top_pt_* columns already exist. Defining "
                    "them again would shadow the persisted values. Set enabled: false "
                    "for top_pt at this stage."
                )
            has_input = self.branch in columns
            if not has_input:
                if not TopPtCorrProducer.warned_missing:
                    TopPtCorrProducer.warned_missing = True
                    print(
                        f"WARNING: '{self.branch}' not found; the top pT reweighting "
                        "will be a no-op for this dataset.",
                        file=sys.stderr,
                    )
            elif self.weight_branch not in columns:
                df = df.Define(self.pt_branch, self._pt_expr())
                df = df.Define(self.sf_branch, self._sf_expr())
                df = df.Define(
                    self.weight_branch, f"static_cast<float>({self._reweight_expr()})"
                )

        for source in [central] + sf_sources:
            for scale in getScales(source):
                branch_name = TopPtCorrProducer.branchName(source, scale)
                if enabled:
                    if source == central:
                        expr = self._central_expr()
                    elif has_input:
                        expr = self._variation_expr(scale)
                    else:
                        expr = "1.f"
                    df = df.Define(branch_name, f"static_cast<float>({expr})")
                    branches.append(branch_name)

        if return_list_of_branches:
            return df, branches
        return df
