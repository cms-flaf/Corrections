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

### Era handling

- `CorrectionsCore.py` maps FLAF period names (`Run3_2022`, `Run3_2022EE`, `Run3_2023`,
  `Run3_2023BPix`, `Run3_2024`, …) onto the campaign strings the POG files use
  (`2022_Summer22`, …). A new era needs an entry here **and** in every correction that switches on
  the period.
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

Verified 2026-08-27; re-check before relying on any of it.

| | |
|---|---|
| Entry points | `Corrections.py` (`initializeGlobal`, per-stage wiring), `CorrectionsCore.py` (period names, scale handling) |
| Per-object modules | `tau`, `jet`, `fatjet`, `electron`, `mu`, `btag`, `pu`, `met`, `triggers`, `triggersRun3`, `puJetID`, `Vpt`, `lumi`, `JetVetoMap`, `MuonScaRe*`, analysis-specific `DY_hhbbtautau` / `DY_hhbbww` |
| Data | `data/` (BTV, EGM, MUO, TAU, TRG, EWK_Corr_Vpt, golden_json) plus JSON POG files from CVMFS |
| Dependencies | ROOT (PyROOT), `correctionlib`, CVMFS |
| Workflows | `formatting-check`, `repo-sanity-checks`, `trigger-flaf-integration`. Formatting is checked automatically — do not comment on it |
| Integration test | Triggered by `@cms-flaf-bot please test`; the pipeline configuration lives in `cms-flaf/FLAF_ci` |
