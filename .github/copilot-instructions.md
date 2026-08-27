# Corrections — instructions for Copilot code review

Monte-Carlo corrections for the CMS analyses built on
[FLAF](https://github.com/cms-flaf/FLAF): scale factors, energy scales and their systematic
variations for jets, taus, muons, electrons, b-tagging, pileup, MET and triggers, across Run 2 and
Run 3. Used as a submodule by HH_bbtautau, HH_bbWW and H_mumu.

**Read `FLAF/.github/copilot-instructions.md` first** for the shared rules on what a useful review
comment looks like here and what not to flag. This file adds what is specific to corrections.

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
