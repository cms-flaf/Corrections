# Corrections

Various MC corrections.
Code is partially based on https://gitlab.cern.ch/cms-phys-ciemat

## How a correction is attached to a dataframe

A `Corrections` instance is created for one dataset, era and stage, and creates its producers
(`pu.py`, `jet.py`, …) on first use. Each producer creates its C++ providers as ordinary objects
through `CorrectionsCore.CppProvider`, and refers to them in RDataFrame expressions through the
provider's `ref`, a `const` pointer to that object:

```python
self.provider = CppProvider("correction::puCorrProvider", json_file, json_name)
df = df.Define("weight_pu_Central", f"{self.provider.ref}->getWeight(::correction::UncScale::Central, Pileup_nTrueInt)")
```

The C++ classes are declared once per process (`declareProviderHeader`); several Run 3 eras in
one process each get their own objects. Run 2 and Run 3 trigger corrections cannot share a
process, since `triggers.h` and `triggersRun3.h` both define `correction::TrigCorrProvider`.
Since `ref` holds the object's address, the `Corrections` instance must live as long as every
dataframe built with it.

`era` is the FLAF era (`Run3_2022`, …) and `campaign` the POG campaign of the correction files
(`2022_Summer22`, …); `CorrectionsCore.campaign_names` maps one onto the other.

Tests: `test_no_global_state.py` and `test_electron_id_sf_year.py` read the sources only; the
other `test_*.py` need ROOT, correctionlib, `FLAF_PATH` and /cvmfs (an analysis environment).
The `repo-sanity-checks` workflow runs `test_no_global_state.py` on every pull request, and FLAF's
`run_tools/check_era_rename.py` (from FLAF `main`) for leftovers of the `period` → `era` rename. The
`test_corrections` job of the integration pipeline
([cms-flaf/flaf_integration](https://gitlab.cern.ch/cms-flaf/flaf_integration)) runs every
`test_*.py`, one process per file, in the environment of the first active analysis's build and
against the Corrections version that build checks out; it fails if that version has no
`test_*.py`.
