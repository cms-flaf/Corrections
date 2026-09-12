import os
import sys

import ROOT

from .CorrectionsCore import *


class psWeightProducer:
    """Parton-shower ISR/FSR variations from the NanoAOD PSWeight vector.

    These are Pythia8 shower weights, not LHE ones: PSWeight is produced after the
    matrix element, which is why it has no LHE prefix even though anaTupleDef lists it
    next to LHEPdfWeight and LHEScaleWeight.

    The weights are already w_var / w_nominal, so there is no correction to apply
    centrally -- the nominal sample *is* the nominal shower. `weight_ps_Central` is
    therefore the literal 1.f, and no GetWeight hook is needed in the analysis. What
    makes the resulting nuisance shape-only is the anaCache denominator: each variation
    is divided by its own inclusive sum of weights in Corrections' `base` block, so the
    inclusive yield is unchanged and only the acceptance difference survives.

    See parton_shower.h for the index ordering and why the size guard matters.
    """

    initialized = False

    uncSource = ["isr", "fsr"]

    # (source, scale) -> index into PSWeight, per the CMSSW ordering quoted in the
    # header. Note [0]/[2] are the ISR pair and [1]/[3] the FSR pair, i.e. up and down
    # of one source are not adjacent.
    indices = {
        ("isr", up): 0,
        ("fsr", up): 1,
        ("isr", down): 2,
        ("fsr", down): 3,
    }

    warned_missing = set()

    def __init__(self, branch="PSWeight"):
        # PSWeight, not PS_Weight. The anaCache denominator is accumulated in
        # anaTupleProducer.updateDenomEntry, which runs before addAllVariables defines
        # the renamed PS_Weight column, so only the original NanoAOD name is available
        # at that point. RDF's Define does not consume the source column, so PSWeight
        # is still live at the other AnaTuple call site too.
        self.branch = branch
        if not psWeightProducer.initialized:
            headers_dir = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(headers_dir, "parton_shower.h")
            ROOT.gInterpreter.Declare(f'#include "{header_path}"')
            psWeightProducer.initialized = True

    @staticmethod
    def branchName(source, scale):
        return f"weight_ps_{getSystName(source, scale)}"

    def getWeight(
        self,
        df,
        return_variations=True,
        return_list_of_branches=False,
        enabled=True,
    ):
        sf_sources = psWeightProducer.uncSource if return_variations else []
        branches = []

        if enabled:
            columns = {str(c) for c in df.GetColumnNames()}
            has_input = self.branch in columns
            if not has_input:
                # A stage where the branch has been renamed away (AnaTupleMerge holds
                # PS_Weight, not PSWeight) must not silently define 1.f on top of the
                # correct values already persisted -- that would shadow them and make
                # the nuisance null with nothing to show for it. The producer is meant
                # to be disabled there via `enabled` in global.yaml.
                already_built = any(c.startswith("weight_ps_") for c in columns)
                if already_built:
                    raise RuntimeError(
                        f"psWeightProducer: '{self.branch}' is not available but "
                        "weight_ps_* columns already exist. Defining them again would "
                        "shadow the persisted values. Set enabled: false for "
                        "parton_shower at this stage."
                    )
                if self.branch not in psWeightProducer.warned_missing:
                    psWeightProducer.warned_missing.add(self.branch)
                    print(
                        f"WARNING: '{self.branch}' not found; ps_isr/ps_fsr will be a "
                        "no-op for this dataset.",
                        file=sys.stderr,
                    )

        for source in [central] + sf_sources:
            for scale in getScales(source):
                branch_name = psWeightProducer.branchName(source, scale)
                if enabled:
                    if source == central:
                        # Exactly 1.0f. This is what keeps the pileup denominators
                        # bit-identical when this producer is added: multiplying by an
                        # IEEE-754 1.0f is the identity.
                        expr = "1.f"
                    elif has_input:
                        idx = psWeightProducer.indices[(source, scale)]
                        expr = f"::correction::psWeight({self.branch}, {idx})"
                    else:
                        expr = "1.f"
                    df = df.Define(branch_name, expr)
                    branches.append(branch_name)

        if return_list_of_branches:
            return df, branches
        return df
