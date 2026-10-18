# Corrections — instructions for Copilot code review

Monte-Carlo corrections for the CMS analyses built on
[FLAF](https://github.com/cms-flaf/FLAF): scale factors, energy scales and their systematic
variations for jets, taus, muons, electrons, b-tagging, pileup, MET and triggers, across Run 2 and
Run 3. Used as a submodule by HH_bbtautau, HH_bbWW and H_mumu.

**Read `FLAF/.github/copilot-instructions.md` first** for the shared rules on what a useful review
comment looks like here and what not to flag. The rule that documentation ships in the same PR
applies here too, and is restated below — it works differently for this repository, which has no
documentation site of its own. This file adds what is specific to corrections.

## What costs the most here

Every correction multiplies an event weight, and a wrong one is **invisible**: the jobs succeed,
the plots look plausible, and the error is found — if at all — much later, in a comparison with
another analysis. There is no test that catches a scale factor applied with the wrong year, the
wrong working point, or the wrong systematic sign.

So the questions worth asking of a diff are: *is this reading the right file for this era?*, *does
the systematic vary in the direction it claims?*, and *does every era that reaches this code path
have an entry?*

## Invariants

### Python and C++ must stay in step

Most corrections are a `.py`/`.h` pair: the Python side resolves the era, locates the JSON and
declares the C++, and the header applies it inside RDataFrame. A change to one without the other
compiles and then misbehaves at runtime. Check that new arguments, enum values and working-point
names appear on both sides, in the same order.

### Providers are objects, one per era and configuration

- A process may build corrections for several Run 3 eras (a law process merging AnaTuples of
  two eras, for one). Run 2 and Run 3 trigger corrections cannot share a process: `triggers.h`
  and `triggersRun3.h` both define `correction::TrigCorrProvider`, so declaring the second one
  raises. Every C++ provider is an ordinary object created and owned by its Python
  producer through `CorrectionsCore.CppProvider`, and every JIT string reaches it through the
  provider's `ref` (`f"{self.provider.ref}->getWeight(...)"`). There is no global `Corrections`
  instance, no static `Initialize`/`getGlobal`, no `initialized` flag and no era value stored on
  a class; a header holds no mutable function-local `static` (it would be shared by every object
  and every RDataFrame thread). Two tests cover part of this. `test_no_global_state.py` searches
  the sources for those patterns, for era, campaign or year values and providers (`CppProvider`
  objects, `_shared` or `*provider*` attributes) stored on a class, and for providers created at
  module level. `test_multi_era.py` builds the pileup and tau producers of two eras in one
  multithreaded dataframe and compares their values with correctionlib. Shared state in another
  form passes both, so a diff that adds state to a class or a module still needs reading.
- Two kinds of process-level state are deliberate, and both tests allow them:
  `CorrectionsCore._source_scales` (filled by `registerSourceScales`) holds the members of an
  indexed source such as the PDF set, keyed by the source name alone, so every instance in a
  process has to use the same member list (the PDF `n_members` comes from the analysis's
  `global.yaml`, default 103); the class-level `warned_missing` flags of `pdf.py`,
  `qcd_scale.py`, `top_pt.py` and `parton_shower.py` print each missing-input warning once per
  process. Any further process-level state needs a reason of the same kind.
- `ref` is a raw address: the producer, and the `Corrections` instance that owns it, must outlive
  every dataframe built with it (FLAF keeps the instance on the `DataFrameWrapper`). `ref` is
  `const`, so a provider method used from a JIT string must be `const`.
- Headers are declared once per process (`declareHeader`, `declareProviderHeader`); a new era
  creates new objects, it never compiles the classes again.

### Era handling

- The FLAF era (`Run3_2022`, `Run3_2022EE`, `Run3_2023`, `Run3_2023BPix`, `Run3_2024`, …) is
  called `era`; the POG campaign string the files use (`2022_Summer22`, …) is called `campaign`.
  `CorrectionsCore.campaign_names` maps one onto the other. A new era needs an entry there **and**
  in every correction that switches on the era or the campaign.
- Eras sometimes have to borrow another era's file when a POG has not published theirs. That is
  legitimate, but it must be explicit and commented with which year is being substituted and why —
  a silent fallback to a neighbouring year is exactly the invisible error above.
- A correction that has no entry for an era should fail loudly rather than return 1.0.

### Data files

- Correction inputs live under `data/` (BTV, EGM, MUO, TAU, TRG, …) or come from CVMFS. Adding a
  large file to `data/` grows every analysis that vendors this repo — prefer CVMFS where the POG
  publishes there, and never commit a binary outside Git LFS.
- A JSON referenced by the code must actually exist for every era that can reach it.

### Systematics

Up and down variations must be distinguishable and correctly signed. A copy-pasted branch that
returns the central value for one direction produces a systematic of zero width, which no test
notices. Check that the variation name reaching `correctionlib` differs between the two branches.

In the tree of a scale source, the objects the source shifts take their shifted p4 and every other
object keeps its Central one (`applyScaleUncertainties`). The MET of that tree must describe the
same objects: `met.py` subtracts the source's deltas and the Central deltas of the objects it does
not shift, all relative to the NanoAOD p4 (`<obj>_p4_<syst>_delta = <obj>_p4_<syst> - <obj>_p4_nano`).
A new p4 correction of a MET object therefore has to define its Central delta and register the
object under `Central` in `source_dict`, or every other tree loses it from MET; a new object type
that enters MET also has to be added to `MET_objs` in `met.py`.

## Documentation must ship with the change

A PR must update the documentation **in the same PR** whenever it changes anything a user of the
framework can observe. Treat this as a review item of the same weight as correctness — docs
drifting from the code is the failure that motivated the current documentation, and a PR that
lands without them is not complete.

Ask, for every diff: does it add, rename or remove any of these?

- a task or DAG node, or the arguments/parameters of one;
- a command, a CLI flag, or the meaning of an existing one;
- a configuration key — `global.yaml`, `user_custom.yaml`, `processes.yaml`, `phys_models.yaml`,
  cross-sections, `fs_*` storage keys, bundle flavours, processor entries;
- a dataset, era, process or physics-model name;
- the environment, installation or setup steps;
- storage locations, output paths or log locations;
- a CI workflow, or how the integration test is triggered or configured;
- any behaviour a user relies on, including a default that changes.

If the answer is yes and the diff touches **no** documentation file, say so and name the page that
should have changed. If the author states the change is internal-only, that is a legitimate
answer — a pure refactor or bugfix with no user-visible effect is exempt — but it should be
stated in the PR, not left implicit.

Also flag the inverse: documentation edited to describe behaviour the diff does not implement, and
new pages added without being wired into `mkdocs.yml`'s `nav` (the build fails on that, but the
review should catch it first).

Where it goes: **this repository has no documentation site of its own.** Corrections are described
in the framework documentation, so a user-visible change here — a new correction, a new era, a
renamed configuration key, a changed default — needs a companion PR against `cms-flaf/FLAF`
updating the relevant page under `FLAF/docs/` (`concepts/eras.md`, `concepts/configuration.md`,
`configuration/datasets.md`, `troubleshooting.md` and the glossary are the ones that mention
corrections). Flag the absence of that companion PR; do not accept an undocumented change on the
grounds that this repository has nowhere to put it.

## Do not flag

- The `.py`/`.h` split itself, or C++ declared from Python strings — that is how the framework
  works.
- Repetition between the per-object modules; they are kept parallel on purpose so a correction can
  be read in isolation.
- Missing unit tests for code that needs CVMFS or a grid proxy.

## Repository facts

Verified 2026-10-17; re-check before relying on any of it.

| | |
|---|---|
| Entry points | `Corrections.py` (one instance per dataset, era and stage; per-stage wiring), `CorrectionsCore.py` (`CppProvider`, campaign names, scale handling) |
| Per-object modules | `tau`, `jet`, `fatjet`, `electron`, `mu`, `btag`, `pu`, `met`, `triggers`, `triggersRun3`, `puJetID`, `Vpt`, `lumi`, `JetVetoMap`, `bosonicRecoil`, `pdf`, `qcd_scale`, `parton_shower`, `top_pt`, `MuonEnergyScale_corr` (with `MuonScaReProvider.h`, `MuonFsrRecoveryProvider.h`), analysis-specific `DY_hhbbtautau` / `DY_hhbbww` |
| Data | `data/` (AK8Jet, BTV, DY_corr_hbt, DY_corr_hhbbww, EGM, EWK_Corr_Vpt, MUO, TAU, TRG, golden_json, hleprare) plus JSON POG files from CVMFS |
| Dependencies | ROOT (PyROOT), `correctionlib`, CVMFS |
| Workflows | `formatting-check`, `repo-sanity-checks` (FLAF's sanity checks plus `test_no_global_state.py`), `trigger-flaf-integration`. Formatting is checked automatically — do not comment on it |
| Integration test | Triggered by `@cms-flaf-bot please test`; the pipeline configuration lives in `cms-flaf/FLAF_ci`; its `test_corrections` job runs every `test_*.py` in an analysis environment |
