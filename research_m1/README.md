# M1 Clean-room research package

Scientific authority: `docs/M1_SINGLE_AUTHORITY.md`. Round 2 engineering findings: `docs/ROUND2_EXECUTION_REPORT.md` and `docs/evidence_review.md`.

From the repository root, install the explicitly recorded numerical dependencies and run the independent tests:

```powershell
python -m pip install -r research_m1/requirements.txt
python -m unittest discover -s research_m1/tests -v
$env:PYTHONPATH = (Resolve-Path research_m1/src).Path
python -m m1_research status
python -m m1_research reference
python -m m1_research synthetic-pair
```

The single runtime configuration is `config/study.yaml`. Unknown scientific parameters remain null; the entry point refuses formal trajectory generation while required qualification is missing.

`reference` exports source-traced 16R coded RF/TF segments and a conditional 16L LOC final. It preserves source conflicts, the RF/TF position gap, unresolved RNAV access and cross-date evidence limits. It does not output a qualified continuous Tianjin execution path. `synthetic-pair` is an explicitly synthetic interface demonstration with the two aircraft identities on one scenario-relative time axis; it is not aircraft performance evidence or a Tianjin simulation.

No historical project implementation is required at runtime. No original AIP or track data is redistributed. Refer to the source manifest for evidence fingerprints and allowed scope. M1/M2 scientific qualification remains open.
