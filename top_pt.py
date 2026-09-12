import sys

from .CorrectionsCore import *


class TopPtCorrProducer:
    """Top pT reweighting for SM ttbar, as a shape weight.

    The top pT spectrum in data is softer than POWHEG+PYTHIA8 predicts. The
    correction is a per-top scale factor whose event weight is the geometric mean over
    the tops in the event, following
    https://twiki.cern.ch/twiki/bin/view/CMS/TopPtReweighting -- for the ttbar pair the
    TWiki prescribes, that is sqrt(SF(t) * SF(tbar)).

    **The reweighting is not applied to the nominal.** As (Down, Central, Up) the weight
    is (SF, 1, SF): the nominal is the unreweighted POWHEG+PYTHIA8 prediction and both
    variations are the reweighted one. The uncertain thing is whether the reweighting
    applies at all, not which direction it goes, so the nuisance is a one-sided envelope
    given symmetrically -- appropriate for a correction whose coefficients are unverified
    and whose applicability at 13.6 TeV is unestablished. See `_variation_expr` for what
    equal Up and Down templates mean once Combine morphs them. To apply the reweighting
    centrally instead, return it from `_central_expr`.

    The producer is registered in Corrections.shape_weight_producers, next to pileup and
    the parton shower, so it is renormalised the same way they are: each variation is
    divided by its own inclusive sum of weights in the anaCache denominator, and Corrections'
    `base` block writes weight_base_top_pt{Up,Down}_rel. The inclusive ttbar yield is
    therefore unchanged by the nuisance and only the shape of the reweighting survives.
    `weight_top_pt_Central` is the literal 1.f, which is also what keeps the existing
    pileup and parton-shower denominators bit-identical when this producer is added.

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

    uncSource = ["top_pt"]

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

    # The tops are read from the NanoAOD GenPart collection, not from a branch the
    # analysis defines. The anaCache denominator is accumulated in
    # anaTupleProducer.updateDenomEntry, which runs before addAllVariables, so only the
    # original NanoAOD columns are available at that point -- the same constraint that
    # makes parton_shower.py read PSWeight rather than PS_Weight.
    input_branches = ["GenPart_pt", "GenPart_pdgId", "GenPart_statusFlags"]

    # Bit index of isLastCopy in GenPart_statusFlags, as in FLAF/include/GenStatusFlags.h
    # (GenStatusFlags::kIsLastCopy). A bitwise mask rather than the enum so the
    # expression does not depend on that header being declared, and does not pin the
    # storage type of GenPart_statusFlags, which varies between NanoAOD versions.
    is_last_copy_bit = 13

    warned_missing = False

    def __init__(self, era, *, parameterization="nnlo_nlo", max_pt=None):
        self.era = era

        if parameterization not in self.parameterizations:
            raise RuntimeError(
                f"TopPtCorrProducer: unknown parameterization '{parameterization}'. "
                f"Supported: {sorted(self.parameterizations.keys())}"
            )
        self.parameterization = parameterization
        # The TWiki quotes a validity range for the fitted functions. It is left unset
        # rather than guessed: pass max_pt to clamp the pT the SF is evaluated at once
        # the number is confirmed.
        self.max_pt = max_pt

    @staticmethod
    def branchName(source, scale):
        """Branch holding this producer's weight for variation (source, scale).

        Keyed on the scale alone, as for pileup: the producer owns a single source, so
        the scale already identifies the branch.
        """
        return f"weight_top_pt_{scale}"

    #: Per-event column holding the top pT the SF is evaluated at.
    pt_branch = "top_pt_forWeight"
    #: Per-event column holding the per-top scale factors.
    sf_branch = "top_pt_sf"
    #: Per-event column holding the reweighting itself, prod(SF_i)^(1/n).
    weight_branch = "top_pt_reweight"

    def _pt_expr(self):
        """The pT of every last-copy top and antitop in the event, as one RVec."""
        is_top = "(GenPart_pdgId == 6 || GenPart_pdgId == -6)"
        is_last_copy = f"(GenPart_statusFlags & (1 << {self.is_last_copy_bit})) != 0"
        expr = f"ROOT::VecOps::RVec<float>(GenPart_pt[{is_top} && ({is_last_copy})])"
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

        For the ttbar pair the TWiki prescribes, this is sqrt(SF(t) * SF(tbar)). Any
        other multiplicity follows from the same definition rather than from a special
        case.

        An event with no last-copy top gets 1, which covers every non-ttbar sample and
        any ttbar event with an incomplete gen record, so the correction is a no-op
        there rather than an error.
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

        if enabled:
            columns = {str(c) for c in df.GetColumnNames()}
            has_input = all(b in columns for b in self.input_branches)
            if not has_input:
                # A stage without GenPart (AnaTupleMerge reads a tuple that does not
                # carry it) must not silently define 1.f on top of the values already
                # persisted -- that would shadow them and make the nuisance null with
                # nothing to show for it. The producer is meant to be disabled there via
                # `enabled` in global.yaml.
                already_built = any(c.startswith("weight_top_pt_") for c in columns)
                if already_built:
                    raise RuntimeError(
                        "TopPtCorrProducer: GenPart is not available but "
                        "weight_top_pt_* columns already exist. Defining them again "
                        "would shadow the persisted values. Set enabled: false for "
                        "top_pt at this stage."
                    )
                if not TopPtCorrProducer.warned_missing:
                    TopPtCorrProducer.warned_missing = True
                    print(
                        "WARNING: GenPart not found; the top pT reweighting will be a "
                        "no-op for this dataset.",
                        file=sys.stderr,
                    )
            elif self.weight_branch not in columns:
                # Intermediate, not saved: the pT the SF is evaluated at, and the
                # per-top SF. Two columns rather than one nested expression so the
                # parameterization appears once, and so both are inspectable when a
                # weight looks wrong.
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
