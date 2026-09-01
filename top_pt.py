from .CorrectionsCore import *


class TopPtCorrProducer:
    """Top pT reweighting for SM ttbar.

    The top pT spectrum in data is softer than POWHEG+PYTHIA8 predicts. The
    correction is a per-top scale factor whose event weight is the geometric mean over
    the tops in the event, following
    https://twiki.cern.ch/twiki/bin/view/CMS/TopPtReweighting -- for the ttbar pair the
    TWiki prescribes, that is sqrt(SF(t) * SF(tbar)).

    The tops arrive as one or more vector branches named by `top_pt_branches`, so the
    number of tops is whatever the event has rather than a fixed pair.

    **The reweighting is not applied to the nominal.** As (Down, Central, Up) the weight
    is (SF, 1, SF): the nominal is the unreweighted POWHEG+PYTHIA8 prediction and both
    variations are the reweighted one. The uncertain thing is whether the reweighting
    applies at all, not which direction it goes, so the nuisance is a one-sided envelope
    given symmetrically -- appropriate for a correction whose coefficients are unverified
    and whose applicability at 13.6 TeV is unestablished. See `_variation_expr` for what
    equal Up and Down templates mean once Combine morphs them. To apply the reweighting
    centrally instead, return it from `_central_expr`.

    Unlike the other reweightings in this directory the correction is a closed-form
    function rather than a correctionlib payload, so there is no JSON to load and no
    header to declare -- a plain Define is enough.

    Two things about the inputs are worth repeating here, because getting either
    wrong silently produces a plausible but invalid weight:

    * The pT must come from the `isLastCopy` parton-level top -- after radiation and
      before decay. The TWiki is explicit that a reco- or particle-level proxy gives
      an invalid reweighting. In particular the LHE-level tops the anaTuple also
      carries are taken *before* radiation and are not a substitute.
    * Only SM ttbar is reweighted, never single top or tops from BSM production. That
      scoping is done in global.yaml with a `processes:` list, the same way the DY
      reweighting is scoped.
    """

    # UNVERIFIED: these coefficients could not be sourced from any public reference --
    # the TWiki is behind CERN SSO. Confirm them against
    # https://twiki.cern.ch/twiki/bin/view/CMS/TopPtReweighting before trusting a
    # result. Both parameterizations are derived from Run 2 13 TeV measurements
    # (TOP-16-011, TOP-16-008); whether they apply to Run 3 at 13.6 TeV is a separate
    # question the analysis has to answer deliberately.
    #
    # Each entry is a C++ expression for the per-top scale factor, with `{pt}` standing
    # in for the top pT. `{pt}` is an RVec, so these are evaluated elementwise and must
    # use ROOT::VecOps::exp -- std::exp has no RVec overload and fails to compile.
    parameterizations = {
        # ratio of data to NLO (POWHEG+PYTHIA8)
        "data_nlo": "ROOT::VecOps::exp(0.0615f - 0.0005f * ({pt}))",
        # ratio of the NNLO QCD + NLO EW prediction to NLO
        "nnlo_nlo": (
            "0.103f * ROOT::VecOps::exp(-0.0118f * ({pt}))"
            " - 0.000134f * ({pt}) + 0.973f"
        ),
    }

    default_variations = [up, down]

    central_branch = "weight_top_pt_central"

    #: Vector branches holding the gen top pT, concatenated before averaging.
    default_top_pt_branches = ["genTop_pt"]

    def __init__(
        self,
        era,
        *,
        top_pt_branches=None,
        parameterization="nnlo_nlo",
        max_pt=None,
        variations=None,
    ):
        self.era = era

        if parameterization not in self.parameterizations:
            raise RuntimeError(
                f"TopPtCorrProducer: unknown parameterization '{parameterization}'. "
                f"Supported: {sorted(self.parameterizations.keys())}"
            )

        if isinstance(top_pt_branches, str):
            top_pt_branches = [top_pt_branches]
        self.top_pt_branches = list(
            self.default_top_pt_branches if top_pt_branches is None else top_pt_branches
        )
        if not self.top_pt_branches:
            raise RuntimeError(
                "TopPtCorrProducer: top_pt_branches is empty, so there is nothing to "
                "reweight. Drop the correction instead of configuring it with no input."
            )
        self.parameterization = parameterization
        # The TWiki quotes a validity range for the fitted functions. It is left unset
        # rather than guessed: pass max_pt to clamp the pT the SF is evaluated at once
        # the number is confirmed.
        self.max_pt = max_pt
        self.variations = list(
            self.default_variations if variations is None else variations
        )

    #: Per-event column holding the top pT the SF is evaluated at.
    pt_branch = "top_pt_forWeight"
    #: Per-event column holding the per-top scale factors.
    sf_branch = "top_pt_sf"
    #: Per-event column holding the reweighting itself, prod(SF_i)^(1/n).
    weight_branch = "top_pt_reweight"

    def _pt_expr(self):
        """The configured branches concatenated into one RVec of top pT.

        Each must be a vector branch; a scalar would be read as a size, not a value.
        """
        expr = f"ROOT::VecOps::RVec<float>({self.top_pt_branches[0]})"
        for branch in self.top_pt_branches[1:]:
            expr = (
                f"ROOT::VecOps::Concatenate({expr}, "
                f"ROOT::VecOps::RVec<float>({branch}))"
            )
        if self.max_pt is not None:
            expr = (
                f"ROOT::VecOps::Where({expr} > {float(self.max_pt)}f, "
                f"{float(self.max_pt)}f, {expr})"
            )
        return expr

    def _sf_expr(self):
        """The per-top scale factor, elementwise, clamped to be non-negative.

        The nnlo_nlo parameterization carries a linear term and so turns negative for
        absurdly large pT. A negative factor would make the product negative and its
        n-th root NaN, poisoning the whole event weight rather than just that one top.

        Written with RVec arithmetic rather than a loop because an RDataFrame `Define`
        string cannot hold an immediately-invoked lambda -- it is parsed for column
        names before it is compiled, and any lambda form fails there with "cannot form
        a reference to 'void'" even though the same code compiles standalone.
        """
        sf = self.parameterizations[self.parameterization].format(pt=self.pt_branch)
        return f"ROOT::VecOps::Where(({sf}) < 0.f, 0.f, {sf})"

    def _reweight_expr(self):
        """The geometric mean of the per-top scale factors: prod(SF_i)^(1/n).

        For the ttbar pair the TWiki prescribes, this is sqrt(SF(t) * SF(tbar)) --
        verified bitwise identical to the previous two-scalar implementation over a
        range of pT, since pow(x, 1/2) and sqrt(x) agree here. Any other multiplicity
        follows from the same definition rather than from a special case.

        An event with no gen top gets 1. The branches are written for every MC sample
        and are empty wherever there is no last-copy top, which covers every non-ttbar
        sample and any ttbar event with an incomplete gen record, so returning 1 makes
        the correction a no-op there rather than an error.
        """
        return (
            f"{self.sf_branch}.empty() ? 1.0f : static_cast<float>(std::pow("
            f"ROOT::VecOps::Product({self.sf_branch}), "
            f"1.0f / static_cast<float>({self.sf_branch}.size())))"
        )

    def _central_expr(self):
        """Unity: the reweighting is not applied to the nominal.

        The correction is carried entirely by the nuisance instead. The nominal is the
        unreweighted POWHEG+PYTHIA8 prediction, `Up` is that prediction reweighted, and
        `Down` is the mirror image. That is the right shape for a correction whose
        applicability is itself in doubt -- these are Run 2 13 TeV derivations and the
        coefficients are unverified -- since it lets the fit pull towards the
        reweighting without presupposing it.

        The branch is kept, rather than dropped from the weight, so the plumbing is
        unchanged and turning the reweighting back on in the nominal is a one-line
        change here rather than a change to every consumer.
        """
        return "1.0f"

    def _variation_expr(self, scale):
        """The reweighting itself, for both directions: (Down, Central, Up) = (SF, 1, SF).

        The two variations are deliberately the same template. The direction of the top
        pT reweighting is not the uncertain thing -- whether it should be applied at all
        is -- so the nuisance is a one-sided envelope written symmetrically: the fit sits
        at the unreweighted prediction when the parameter is 0 and reaches the fully
        reweighted one at |theta| = 1, with the sign carrying no meaning.

        Note what this does in Combine. Template morphing runs through (Down, Nominal,
        Up); with Down == Up the odd term cancels and only the even one survives, so the
        response is quadratic in theta and the yield moves the *same* way whichever way
        the parameter is pulled. That is the intended reading here, but it also means the
        nuisance has no linear response at theta = 0, so its impact comes out one-sided
        in a ranking and the minimiser sees a flat direction at the starting point.
        """
        if scale in (up, down):
            return f"static_cast<float>({self.weight_branch})"
        raise RuntimeError(f"TopPtCorrProducer: unsupported variation '{scale}'.")

    def getWeight(
        self,
        df,
        return_variations=True,
        return_list_of_branches=False,
        enabled=True,
    ):
        if not enabled:
            if return_list_of_branches:
                return df, []
            return df

        branches = []

        # Intermediate, not saved: the pT the SF is evaluated at, and the per-top SF.
        # Two columns rather than one nested expression so the parameterization appears
        # once, and so both are inspectable when a weight looks wrong.
        df = df.Define(self.pt_branch, self._pt_expr())
        df = df.Define(self.sf_branch, self._sf_expr())
        df = df.Define(
            self.weight_branch, f"static_cast<float>({self._reweight_expr()})"
        )

        df = df.Define(
            self.central_branch, f"static_cast<float>({self._central_expr()})"
        )
        branches.append(self.central_branch)

        if return_variations:
            for scale in self.variations:
                branch_name = f"weight_top_pt_{scale}"
                df = df.Define(branch_name, self._variation_expr(scale))
                branches.append(branch_name)

                # weights.yaml multiplies a relative branch by final_weight, which
                # already carries the central weight -- the convention every other
                # correction follows (see DY_hhbbtautau.py). The central branch is
                # always defined by the time this runs.
                rel_branch = f"{branch_name}_rel"
                df = df.Define(
                    rel_branch,
                    f"static_cast<float>({self.central_branch} != 0.f "
                    f"? {branch_name} / {self.central_branch} : 1.f)",
                )
                branches.append(rel_branch)

        if return_list_of_branches:
            return df, branches
        return df
